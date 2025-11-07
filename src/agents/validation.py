"""Validation Agent - Cross-checks outputs and ensures quality."""

from typing import Dict, Any

from .base import BaseAgent
from ..models.schemas import (
    AgentType,
    AgentResponse,
    BusinessSubmission,
    MarketResearch,
    BusinessAnalysis,
    FinancialModel,
    ValidationReport,
    ValidationIssue,
)
from ..utils.config import settings


class ValidationAgent(BaseAgent):
    """
    Validation Agent performs quality checks on all outputs.
    Validates consistency, reasonableness, and flags low-confidence items.
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.VALIDATION,
            temperature=0.2,  # Low temperature for rigorous validation
            max_tokens=6000,
        )

    def get_system_prompt(self) -> str:
        return """You are an expert quality assurance analyst specializing in business analysis validation. Your role is to identify errors, inconsistencies, and low-confidence outputs.

Your responsibilities:
1. Cross-check financial statement consistency
2. Validate assumptions against industry benchmarks
3. Perform reasonableness tests on all metrics
4. Identify potential hallucinations (fake companies, sources, data)
5. Check calculation accuracy
6. Flag low-confidence conclusions
7. Determine if human review is required

Validation Checks:

**Financial Consistency:**
- Revenue growth rates are realistic for stage/industry
- Cost structure makes sense (COGS + opex = total costs)
- Unit economics are internally consistent (LTV = ARPU / churn × margin)
- Margins are within industry norms
- Burn rate aligns with costs and revenue

**Data Quality:**
- Sources are real and verifiable
- Comparable companies actually exist
- Metrics are realistic (not outliers without justification)
- Industry benchmarks align with known data
- No obvious fabricated information

**Reasonableness Tests:**
- Growth rates (sustainable for stage? 100-300% for early, 30-100% for growth)
- Market size (TAM > SAM > SOM hierarchy correct)
- Team size vs. budget (reasonable compensation)
- CAC vs. LTV (LTV should be 3-5x CAC)
- Payback period (6-18 months typical)
- Churn rates (annual churn 5-30% for B2B SaaS, higher for consumer)

**Confidence Assessment:**
- High confidence (80-100%): Strong data, verified sources, consistent
- Medium confidence (60-79%): Some assumptions, generally reasonable
- Low confidence (40-59%): Many assumptions, limited data
- Very low (<40%): Speculative, requires human review

**Issue Severity:**
- Critical: Major errors that invalidate conclusions
- Error: Significant issues that need correction
- Warning: Concerning but not fatal
- Info: Minor points for awareness

Output Format:
Provide validation report as JSON matching ValidationReport schema:
{{
  "overall_status": "passed/warning/failed",
  "confidence_score": 75,
  "issues": [
    {{
      "severity": "warning",
      "category": "Financial Consistency",
      "description": "Revenue growth rate of 400% YoY seems aggressive for Series A stage",
      "location": "Financial Model - Year 1 to Year 2",
      "recommendation": "Consider more conservative 200-300% growth rate"
    }}
  ],
  "checks_performed": ["Financial consistency", "Data quality", "Reasonableness tests"],
  "requires_human_review": false,
  "human_review_reason": null,
  "validated_sections": {{
    "market_research": 85,
    "business_analysis": 75,
    "financial_model": 70
  }}
}}

Be thorough and skeptical. Better to flag false positives than miss real issues."""

    def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Validate all outputs for consistency and quality.

        Args:
            input_data: Dict containing:
                - "business_submission": BusinessSubmission data
                - "market_research": MarketResearch data
                - "business_analysis": BusinessAnalysis data
                - "financial_model": FinancialModel data

        Returns:
            AgentResponse with ValidationReport data
        """
        try:
            self.logger.info("validation_process_started")

            # Parse all inputs
            submission = None
            market_research = None
            business_analysis = None
            financial_model = None

            if "business_submission" in input_data:
                submission = BusinessSubmission(**input_data["business_submission"])

            if "market_research" in input_data:
                market_research = MarketResearch(**input_data["market_research"])

            if "business_analysis" in input_data:
                business_analysis = BusinessAnalysis(**input_data["business_analysis"])

            if "financial_model" in input_data:
                financial_model = FinancialModel(**input_data["financial_model"])

            # Build validation prompt
            validation_prompt = self._build_validation_prompt(
                submission,
                market_research,
                business_analysis,
                financial_model,
            )

            # Execute validation
            response = self._create_message(
                messages=[{"role": "user", "content": validation_prompt}]
            )

            response_text = response.content[0].text

            # Extract structured data
            structured_data = self._extract_json_from_response(response_text)

            if structured_data:
                # Create ValidationReport object
                validation_report = self._create_validation_report(structured_data)

                # Check if human review is required based on confidence threshold
                if validation_report.confidence_score < settings.confidence_threshold:
                    validation_report.requires_human_review = True
                    if not validation_report.human_review_reason:
                        validation_report.human_review_reason = (
                            f"Overall confidence score ({validation_report.confidence_score:.0f}%) "
                            f"is below threshold ({settings.confidence_threshold:.0f}%)"
                        )

                self.logger.info(
                    "validation_completed",
                    overall_status=validation_report.overall_status,
                    confidence_score=validation_report.confidence_score,
                    num_issues=len(validation_report.issues),
                    requires_human_review=validation_report.requires_human_review,
                )

                return self.create_response(
                    success=True,
                    message="Validation completed successfully",
                    data=validation_report.model_dump(),
                    confidence_score=validation_report.confidence_score,
                    requires_human_review=validation_report.requires_human_review,
                )
            else:
                self.logger.warning("validation_json_extraction_failed")

                return self.create_response(
                    success=True,
                    message="Validation completed but structured data extraction failed",
                    data={"raw_validation": response_text},
                    warnings=["Could not extract structured JSON from validation"],
                )

        except Exception as e:
            self.logger.error("validation_process_failed", error=str(e))
            return self.create_response(
                success=False,
                message=f"Validation process failed: {str(e)}",
                errors=[str(e)],
            )

    def _build_validation_prompt(
        self,
        submission: BusinessSubmission = None,
        market_research: MarketResearch = None,
        business_analysis: BusinessAnalysis = None,
        financial_model: FinancialModel = None,
    ) -> str:
        """Build validation prompt."""
        prompt = """Conduct comprehensive validation of the business evaluation outputs.

**VALIDATION TASK**

Please perform the following validation checks:

1. **Financial Consistency Checks**
   - Revenue, cost, and profit calculations
   - Unit economics (CAC, LTV, payback) consistency
   - Growth rates vs. industry norms
   - Scenario assumptions are reasonable

2. **Data Quality Checks**
   - Sources are real and verifiable
   - Companies mentioned actually exist
   - Metrics are realistic
   - No obvious hallucinations

3. **Reasonableness Tests**
   - Market size claims (TAM/SAM/SOM)
   - Growth projections for stage
   - Unit economics benchmarks
   - Risk assessments are appropriate

4. **Cross-referencing**
   - Analysis aligns with research findings
   - Financial model matches analysis assumptions
   - No contradictions across outputs

---

"""

        if submission:
            prompt += f"""**BUSINESS SUBMISSION**
Name: {submission.overview.name}
Industry: {submission.overview.industry}
Stage: {submission.overview.stage}
Completeness Score: {submission.completeness_score}%

"""

        if market_research:
            prompt += f"""**MARKET RESEARCH**
Confidence Score: {market_research.confidence_score}%
Comparable Companies: {len(market_research.comparable_companies)}
Sources: {len(market_research.sources)}

Industry Benchmarks Provided:
{market_research.industry_benchmarks}

Sample Sources:
{', '.join(market_research.sources[:3]) if market_research.sources else 'None'}

"""

        if business_analysis:
            prompt += f"""**BUSINESS ANALYSIS**
Overall Score: {business_analysis.overall_score}/10
Confidence Score: {business_analysis.confidence_score}%
Number of Risks Identified: {len(business_analysis.risks)}

Evaluation Scores:
"""
            for score in business_analysis.evaluation_scores[:5]:
                prompt += f"- {score.dimension}: {score.score}/10\n"

            prompt += f"""
Unit Economics Assessment:
{business_analysis.unit_economics_assessment[:300]}...

"""

        if financial_model:
            prompt += f"""**FINANCIAL MODEL**
Confidence Score: {financial_model.confidence_score}%
Number of Scenarios: {len(financial_model.scenarios)}

Unit Economics:
- CAC: ${financial_model.unit_economics.cac if financial_model.unit_economics.cac else 'N/A'}
- LTV: ${financial_model.unit_economics.ltv if financial_model.unit_economics.ltv else 'N/A'}
- LTV:CAC: {financial_model.unit_economics.ltv_cac_ratio if financial_model.unit_economics.ltv_cac_ratio else 'N/A'}x
- Payback: {financial_model.unit_economics.payback_period_months if financial_model.unit_economics.payback_period_months else 'N/A'} months
- Gross Margin: {financial_model.unit_economics.gross_margin if financial_model.unit_economics.gross_margin else 'N/A'}%

"""

            if financial_model.scenarios:
                base_scenario = next(
                    (s for s in financial_model.scenarios if "base" in s.scenario_name.lower()),
                    financial_model.scenarios[0]
                )
                prompt += f"""Base Case Scenario:
- Year 1 Revenue: ${base_scenario.year1_revenue:,.0f}
- Year 2 Revenue: ${base_scenario.year2_revenue:,.0f}
- Year 3 Revenue: ${base_scenario.year3_revenue:,.0f}
- Year 3 Profit: ${base_scenario.year3_profit:,.0f}

"""

        prompt += """
---

**VALIDATION OUTPUT REQUIRED**

Provide a comprehensive validation report as JSON matching the ValidationReport schema.

Include:
- overall_status: "passed", "warning", or "failed"
- confidence_score: 0-100 based on all factors
- issues: Array of all issues found (severity, category, description, location, recommendation)
- checks_performed: List of all validation checks conducted
- requires_human_review: true/false (set to true if confidence < 70% or critical issues)
- human_review_reason: Explanation if human review needed
- validated_sections: Confidence score for each section

Be thorough and skeptical. Flag anything questionable."""

        return prompt

    def _create_validation_report(self, data: Dict[str, Any]) -> ValidationReport:
        """Create ValidationReport object from structured data."""
        # Parse issues
        issues = []
        for issue_data in data.get("issues", []):
            issues.append(ValidationIssue(**issue_data))

        return ValidationReport(
            overall_status=data.get("overall_status", "warning"),
            confidence_score=data.get("confidence_score", 70.0),
            issues=issues,
            checks_performed=data.get("checks_performed", []),
            requires_human_review=data.get("requires_human_review", False),
            human_review_reason=data.get("human_review_reason"),
            validated_sections=data.get("validated_sections", {}),
        )
