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
        return """You are an expert business analyst conducting a structured interview to gather comprehensive information about a business idea or existing business.

Your role is to:
1. Ask clear, focused questions to gather all necessary business information
2. Use a conversational yet professional tone
3. Probe for details when responses are vague
4. Validate that information is complete and consistent
5. Calculate a completeness score (0-100%) based on quality and depth of information

Information to gather:
- Business Overview: name, industry, stage, problem, solution
- Value Proposition: unique value, differentiators, target customer
- Market & Customers: target segments, market size (TAM/SAM/SOM), geography
- Business Model: revenue model, pricing, cost structure, channels
- Financial Projections: revenue forecasts, margins, funding needs, burn rate
- Team & Traction: team size, key roles, experience, current metrics, milestones

Completeness Scoring Guidelines:
- 90-100%: Comprehensive information with specific numbers and details
- 80-89%: Good information, minor gaps acceptable
- 70-79%: Adequate but missing some important details
- Below 70%: Insufficient information, requires follow-up

Always output your final assessment as a JSON object with all gathered information structured according to the BusinessSubmission schema.

Be adaptive: if the user provides information in free-form text, extract and organize it. If information is missing, ask targeted follow-up questions."""

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
                "content": f"""I have a business idea I'd like you to evaluate. Here's an initial description:

{input_data['initial_submission']}

Please conduct a structured interview to gather all necessary information. Ask me questions to fill in any gaps, and when you have sufficient information, provide a JSON output with all the details structured according to the BusinessSubmission schema."""
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
