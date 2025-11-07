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

Extract ALL available information and structure it as JSON. Use null or empty strings for missing data.

Required JSON structure:
```json
{
  "overview": {
    "name": "Business Name",
    "industry": "Industry",
    "stage": "idea/MVP/early-stage/growth",
    "problem": "Problem description",
    "solution": "Solution description"
  },
  "value_proposition": {
    "unique_value": "Value prop",
    "differentiators": ["diff1", "diff2"],
    "target_customer": "Customer description"
  },
  "market": {
    "target_segments": ["segment1"],
    "market_size": "Description",
    "tam": 1000000,
    "sam": 500000,
    "som": 100000,
    "geography": ["location1"]
  },
  "business_model": {
    "revenue_model": "subscription/transaction/etc",
    "pricing": "Pricing details",
    "cost_structure": "Cost structure",
    "distribution_channels": ["channel1"]
  },
  "financials": {
    "year1_revenue": 100000,
    "year2_revenue": 500000,
    "year3_revenue": 1000000,
    "gross_margin": 70.0,
    "funding_needed": 500000,
    "burn_rate": 50000
  },
  "team": {
    "team_size": 3,
    "key_roles": ["CEO", "CTO"],
    "experience": ["experience details"],
    "milestones": ["milestone1"]
  },
  "additional_info": {},
  "completeness_score": 75.0
}
```

Scoring: Rate 0-100 based on information depth. Output JSON only - no explanations."""

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

            if structured_data and "completeness_score" in structured_data:
                # We have a complete submission
                submission = self._create_business_submission(structured_data)

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
                # Still gathering information
                self.logger.info("intake_in_progress", response_length=len(response_text))

                return self.create_response(
                    success=True,
                    message=response_text,
                    data={"requires_more_info": True, "response": response_text},
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

Please extract ALL available information from this description and structure it as JSON according to the BusinessSubmission schema. Use null or "Not provided" for any missing fields. Calculate a completeness score and output the JSON immediately - do not ask follow-up questions."""
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

        Args:
            submission: BusinessSubmission to evaluate

        Returns:
            Completeness score (0-100)
        """
        score = 0.0
        total_weight = 0.0

        # Define weights for each section
        weights = {
            "overview": 20.0,
            "value_proposition": 15.0,
            "market": 20.0,
            "business_model": 15.0,
            "financials": 20.0,
            "team": 10.0,
        }

        # Check overview completeness
        overview = submission.overview
        if all([overview.name, overview.industry, overview.stage, overview.problem, overview.solution]):
            score += weights["overview"]
        total_weight += weights["overview"]

        # Check value proposition
        vp = submission.value_proposition
        if all([vp.unique_value, vp.differentiators, vp.target_customer]):
            score += weights["value_proposition"]
        total_weight += weights["value_proposition"]

        # Check market info
        market = submission.market
        if market.target_segments and (market.tam or market.market_size):
            score += weights["market"]
        total_weight += weights["market"]

        # Check business model
        bm = submission.business_model
        if all([bm.revenue_model, bm.pricing, bm.cost_structure]):
            score += weights["business_model"]
        total_weight += weights["business_model"]

        # Check financials
        fin = submission.financials
        if fin.year1_revenue or fin.funding_needed:
            score += weights["financials"]
        total_weight += weights["financials"]

        # Check team
        team = submission.team
        if team.team_size > 0 and team.key_roles:
            score += weights["team"]
        total_weight += weights["team"]

        return (score / total_weight) * 100 if total_weight > 0 else 0.0
