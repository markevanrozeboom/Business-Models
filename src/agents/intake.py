"""Intake Agent - Conducts structured information gathering from users."""

import json
import uuid
from datetime import datetime
from typing import Dict, Any

from .base import BaseAgent
from ..models.schemas import (
    AgentType,
    AgentResponse,
    BusinessSubmission,
    BusinessOverview,
    ValueProposition,
    MarketInfo,
    BusinessModelInfo,
    FinancialProjections,
    TeamInfo,
)


class IntakeAgent(BaseAgent):
    """
    Intake Agent conducts structured interviews to gather business information.
    Validates completeness and ensures all critical parameters are collected.
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.INTAKE,
            temperature=0.7,  # More conversational for interviews
        )

    def get_system_prompt(self) -> str:
        return """You are an expert business analyst extracting structured information from business descriptions.

Your goal is to extract whatever information is present in the description and structure it as JSON. 
Partial data is completely acceptable - use null, empty strings, or empty arrays for missing fields.

IMPORTANT: 
- Extract only what is explicitly stated or can be reasonably inferred
- Do NOT require all fields to be filled
- Use defaults (null, empty strings, empty arrays) for any missing information
- Even if only basic information (name, problem, solution) is provided, that's sufficient
- Calculate completeness score based on what's available, not what's missing

JSON structure (all fields optional, use defaults for missing):
```json
{
  "overview": {
    "name": "Business Name or empty string",
    "industry": "Industry or empty string",
    "stage": "idea/MVP/early-stage/growth or empty string",
    "problem": "Problem description or empty string",
    "solution": "Solution description or empty string"
  },
  "value_proposition": {
    "unique_value": "Value prop or empty string",
    "differentiators": ["diff1", "diff2"] or [],
    "target_customer": "Customer description or empty string"
  },
  "market": {
    "target_segments": ["segment1"] or [],
    "market_size": "Description or null",
    "tam": 1000000 or null,
    "sam": 500000 or null,
    "som": 100000 or null,
    "geography": ["location1"] or []
  },
  "business_model": {
    "revenue_model": "subscription/transaction/etc or empty string",
    "pricing": "Pricing details or empty string",
    "cost_structure": "Cost structure or empty string",
    "distribution_channels": ["channel1"] or []
  },
  "financials": {
    "year1_revenue": 100000 or null,
    "year2_revenue": 500000 or null,
    "year3_revenue": 1000000 or null,
    "gross_margin": 70.0 or null,
    "funding_needed": 500000 or null,
    "burn_rate": 50000 or null
  },
  "team": {
    "team_size": 3 or 0,
    "key_roles": ["CEO", "CTO"] or [],
    "relevant_experience": "experience details or empty string",
    "milestones": ["milestone1"] or []
  },
  "additional_info": {},
  "completeness_score": 30.0
}
```

Completeness Scoring: 
- Score 0-100 based on information depth
- Even 20-30% completeness is acceptable if core info (name, problem, solution) exists
- Be generous - partial information is valuable
- Output JSON only - no explanations."""

    def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Process business idea submission through structured interview.

        Args:
            input_data: Dict containing either:
                - "initial_submission": Free-form business description
                - "conversation_history": List of previous Q&A exchanges

        Returns:
            AgentResponse with BusinessSubmission data or follow-up questions
        """
        try:
            self.logger.info("intake_process_started", input_data_keys=list(input_data.keys()))

            # Build conversation based on input
            messages = self._build_conversation(input_data)

            # Get response from Claude
            response = self._create_message(messages=messages)

            # Extract response text
            response_text = response.content[0].text

            # Try to extract structured JSON
            structured_data = self._extract_json_from_response(response_text)

            if structured_data:
                # Create submission even if completeness is low
                # If completeness_score not provided, calculate it or use a default
                if "completeness_score" not in structured_data:
                    # Try to create a temporary submission to calculate completeness
                    try:
                        temp_submission = self._create_business_submission(structured_data)
                        structured_data["completeness_score"] = self.calculate_completeness(temp_submission)
                    except Exception:
                        # If we can't create submission yet, estimate based on available fields
                        structured_data["completeness_score"] = 25.0  # Default for partial data
                
                submission = self._create_business_submission(structured_data)
                
                # Recalculate completeness to ensure accuracy
                submission.completeness_score = self.calculate_completeness(submission)

                self.logger.info(
                    "intake_completed",
                    submission_id=submission.submission_id,
                    completeness_score=submission.completeness_score,
                )

                return self.create_response(
                    success=True,
                    message="Business information gathered successfully",
                    data=submission.model_dump(),
                    confidence_score=submission.completeness_score,
                )
            else:
                # If we can't extract JSON, create a minimal submission from the text
                self.logger.warning("intake_json_extraction_failed", response_length=len(response_text))
                
                # Create minimal submission with just the raw text
                minimal_data = {
                    "overview": {
                        "name": "",
                        "industry": "",
                        "stage": "",
                        "problem": "",
                        "solution": response_text[:500] if response_text else ""  # Use first 500 chars as solution
                    },
                    "value_proposition": {},
                    "market": {},
                    "business_model": {},
                    "financials": {},
                    "team": {},
                    "additional_info": {"raw_response": response_text},
                    "completeness_score": 15.0  # Very low but proceed anyway
                }
                
                submission = self._create_business_submission(minimal_data)
                submission.completeness_score = self.calculate_completeness(submission)

                self.logger.info(
                    "intake_minimal_submission_created",
                    submission_id=submission.submission_id,
                    completeness_score=submission.completeness_score,
                )

                return self.create_response(
                    success=True,
                    message="Business information extracted (minimal data available)",
                    data=submission.model_dump(),
                    confidence_score=submission.completeness_score,
                )

        except Exception as e:
            self.logger.error("intake_process_failed", error=str(e))
            return self.create_response(
                success=False,
                message=f"Intake process failed: {str(e)}",
                errors=[str(e)],
            )

    def _build_conversation(self, input_data: Dict[str, Any]) -> list:
        """Build conversation messages from input data."""
        messages = []

        if "initial_submission" in input_data:
            # First interaction
            messages.append({
                "role": "user",
                "content": f"""I have a business idea I'd like you to evaluate. Here's the business description:

{input_data['initial_submission']}

Please extract whatever information is available from this description and structure it as JSON according to the BusinessSubmission schema. 

- Extract only what is explicitly stated or can be reasonably inferred
- Use null, empty strings, or empty arrays for any missing fields
- Partial data is completely acceptable - even if only basic information is provided
- Calculate a completeness score (0-100) based on what's available
- Be generous with the completeness score - 20-30% is acceptable if core info exists
- Output the JSON immediately - proceed with whatever information is available"""
            })

        elif "conversation_history" in input_data:
            # Ongoing conversation
            for exchange in input_data["conversation_history"]:
                messages.append({"role": "user", "content": exchange.get("user", "")})
                messages.append({"role": "assistant", "content": exchange.get("assistant", "")})

            # Add latest user response
            if "latest_response" in input_data:
                messages.append({"role": "user", "content": input_data["latest_response"]})

        return messages

    def _create_business_submission(self, data: Dict[str, Any]) -> BusinessSubmission:
        """Create BusinessSubmission from structured data."""
        submission_id = str(uuid.uuid4())

        return BusinessSubmission(
            submission_id=submission_id,
            timestamp=datetime.utcnow(),
            overview=BusinessOverview(**data.get("overview", {})),
            value_proposition=ValueProposition(**data.get("value_proposition", {})),
            market=MarketInfo(**data.get("market", {})),
            business_model=BusinessModelInfo(**data.get("business_model", {})),
            financials=FinancialProjections(**data.get("financials", {})),
            team=TeamInfo(**data.get("team", {})),
            additional_info=data.get("additional_info", {}),
            completeness_score=data.get("completeness_score", 0.0),
        )

    def calculate_completeness(self, submission: BusinessSubmission) -> float:
        """
        Calculate completeness score for a business submission.
        More lenient scoring - rewards what's available rather than penalizing what's missing.

        Args:
            submission: BusinessSubmission to evaluate

        Returns:
            Completeness score (0-100)
        """
        score = 0.0
        total_weight = 0.0

        # Define weights for each section
        weights = {
            "overview": 25.0,  # Increased weight for core info
            "value_proposition": 15.0,
            "market": 20.0,
            "business_model": 15.0,
            "financials": 15.0,  # Reduced weight - often missing
            "team": 10.0,
        }

        # Check overview completeness - more lenient, partial credit
        overview = submission.overview
        overview_fields = [
            bool(overview.name),
            bool(overview.industry),
            bool(overview.stage),
            bool(overview.problem),
            bool(overview.solution),
        ]
        overview_completeness = sum(overview_fields) / len(overview_fields)
        # Core requirement: at least name, problem, or solution
        if any([overview.name, overview.problem, overview.solution]):
            score += weights["overview"] * overview_completeness
        total_weight += weights["overview"]

        # Check value proposition - partial credit
        vp = submission.value_proposition
        vp_fields = [
            bool(vp.unique_value),
            bool(vp.differentiators),
            bool(vp.target_customer),
        ]
        vp_completeness = sum(vp_fields) / len(vp_fields) if vp_fields else 0
        if any([vp.unique_value, vp.differentiators, vp.target_customer]):
            score += weights["value_proposition"] * vp_completeness
        total_weight += weights["value_proposition"]

        # Check market info - partial credit
        market = submission.market
        market_has_data = bool(
            market.target_segments or 
            market.tam or 
            market.sam or 
            market.som or 
            market.market_size or 
            market.geography
        )
        if market_has_data:
            # Give partial credit based on what's available
            market_fields = [
                bool(market.target_segments),
                bool(market.tam or market.sam or market.som or market.market_size),
                bool(market.geography),
            ]
            market_completeness = sum(market_fields) / len(market_fields)
            score += weights["market"] * market_completeness
        total_weight += weights["market"]

        # Check business model - partial credit
        bm = submission.business_model
        bm_fields = [
            bool(bm.revenue_model),
            bool(bm.pricing),
            bool(bm.cost_structure),
            bool(bm.distribution_channels),
        ]
        bm_completeness = sum(bm_fields) / len(bm_fields) if bm_fields else 0
        if any([bm.revenue_model, bm.pricing, bm.cost_structure, bm.distribution_channels]):
            score += weights["business_model"] * bm_completeness
        total_weight += weights["business_model"]

        # Check financials - very lenient, any financial data counts
        fin = submission.financials
        fin_has_data = bool(
            fin.year1_revenue or 
            fin.year2_revenue or 
            fin.year3_revenue or 
            fin.gross_margin or 
            fin.funding_needed or 
            fin.burn_rate
        )
        if fin_has_data:
            # Give partial credit for any financial data
            fin_fields = [
                bool(fin.year1_revenue or fin.year2_revenue or fin.year3_revenue),
                bool(fin.gross_margin),
                bool(fin.funding_needed),
                bool(fin.burn_rate),
            ]
            fin_completeness = sum(fin_fields) / len(fin_fields)
            score += weights["financials"] * fin_completeness
        total_weight += weights["financials"]

        # Check team - very lenient
        team = submission.team
        team_has_data = bool(
            team.team_size > 0 or 
            team.key_roles or 
            team.relevant_experience or 
            team.milestones
        )
        if team_has_data:
            team_fields = [
                bool(team.team_size > 0),
                bool(team.key_roles),
                bool(team.relevant_experience),
                bool(team.milestones),
            ]
            team_completeness = sum(team_fields) / len(team_fields)
            score += weights["team"] * team_completeness
        total_weight += weights["team"]

        final_score = (score / total_weight) * 100 if total_weight > 0 else 0.0
        
        # Ensure minimum score if core info exists (name, problem, or solution)
        if any([overview.name, overview.problem, overview.solution]):
            final_score = max(final_score, 20.0)  # Minimum 20% if core info exists
        
        return final_score
