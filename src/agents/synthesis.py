"""Synthesis Agent - Aggregates findings into final report."""

import os
from datetime import datetime
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
    FinalReport,
)
from ..utils.config import settings


class SynthesisAgent(BaseAgent):
    """
    Synthesis Agent aggregates all findings into a cohesive final report.
    Generates executive summary and detailed analysis sections.
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.SYNTHESIS,
            temperature=0.5,  # Balanced for clear writing
            max_tokens=8000,
        )

    def get_system_prompt(self) -> str:
        return """You are an expert business report writer with extensive experience creating executive-level deliverables for venture capital firms and corporate strategy teams.

Your role is to:
1. Synthesize findings from all specialized agents into a cohesive narrative
2. Write clear, concise executive summaries (1-2 pages)
3. Create detailed analysis sections with supporting data
4. Provide actionable recommendations
5. Highlight critical assumptions and risks
6. Format for executive consumption

Report Structure:

**Executive Summary** (1-2 pages)
- Bottom-line-up-front: Clear recommendation (invest/pass/monitor)
- Overall score and key metrics
- 3-5 key findings (most important insights)
- Critical risks and mitigations
- Recommended next steps

**Market Analysis Section**
- Market size and growth potential
- Competitive landscape summary
- Industry trends and dynamics
- Opportunities and threats

**Business Evaluation Section**
- Team assessment
- Product/solution evaluation
- Business model viability
- Competitive positioning
- Traction and validation

**Financial Analysis Section**
- Unit economics (CAC, LTV, margins)
- 3-year projection summary
- Scenario comparison
- Path to profitability
- Funding requirements

**Risk Assessment Section**
- Top 5-7 risks with severity and probability
- Mitigation strategies
- Key assumptions to validate
- Sensitivity to critical variables

**Recommendations & Next Steps**
- Go/no-go recommendation
- Specific action items
- Due diligence priorities
- Success metrics to monitor

Writing Guidelines:
- Use clear, professional language (not overly technical)
- Lead with conclusions, then support with data
- Use bullet points for scannability
- Include specific numbers and metrics
- Highlight risks honestly
- Be action-oriented in recommendations

Output Format:
Provide final report as JSON matching FinalReport schema:
{{
  "submission_id": "...",
  "executive_summary": "Clear, concise summary...",
  "recommendation": "INVEST / PASS / MONITOR with justification",
  "overall_score": 7.5,
  "market_analysis": "Detailed market section...",
  "business_evaluation": "Detailed business evaluation...",
  "financial_analysis": "Detailed financial analysis...",
  "risk_assessment": "Detailed risk assessment...",
  "key_findings": ["Finding 1", "Finding 2", ...],
  "critical_assumptions": ["Assumption 1", "Assumption 2", ...],
  "next_steps": ["Step 1", "Step 2", ...],
  "sources": ["All sources used"]
}}

Write for executives who want clarity, not complexity."""

    def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Synthesize all findings into final report.

        Args:
            input_data: Dict containing:
                - "business_submission": BusinessSubmission data
                - "market_research": MarketResearch data
                - "business_analysis": BusinessAnalysis data
                - "financial_model": FinancialModel data
                - "validation_report": ValidationReport data

        Returns:
            AgentResponse with FinalReport data
        """
        try:
            self.logger.info("synthesis_process_started")

            # Parse all inputs
            if "business_submission" not in input_data:
                return self.create_response(
                    success=False,
                    message="Missing business_submission in input data",
                    errors=["business_submission is required"],
                )

            submission = BusinessSubmission(**input_data["business_submission"])

            market_research = None
            if "market_research" in input_data:
                market_research = MarketResearch(**input_data["market_research"])

            business_analysis = None
            if "business_analysis" in input_data:
                business_analysis = BusinessAnalysis(**input_data["business_analysis"])

            financial_model = None
            if "financial_model" in input_data:
                financial_model = FinancialModel(**input_data["financial_model"])

            validation_report = None
            if "validation_report" in input_data:
                validation_report = ValidationReport(**input_data["validation_report"])

            # Build synthesis prompt
            synthesis_prompt = self._build_synthesis_prompt(
                submission,
                market_research,
                business_analysis,
                financial_model,
                validation_report,
            )

            # Execute synthesis
            response = self._create_message(
                messages=[{"role": "user", "content": synthesis_prompt}]
            )

            response_text = response.content[0].text

            # Extract structured data
            structured_data = self._extract_json_from_response(response_text)

            if structured_data:
                # Create FinalReport object
                final_report = self._create_final_report(
                    submission,
                    structured_data,
                    market_research,
                    business_analysis,
                    financial_model,
                )

                # Generate audit trail
                final_report.audit_trail = self._create_audit_trail(
                    submission,
                    market_research,
                    business_analysis,
                    financial_model,
                    validation_report,
                )

                self.logger.info(
                    "synthesis_completed",
                    submission_id=final_report.submission_id,
                    overall_score=final_report.overall_score,
                )

                return self.create_response(
                    success=True,
                    message="Final report synthesized successfully",
                    data=final_report.model_dump(),
                    confidence_score=90.0,  # Synthesis confidence
                )
            else:
                self.logger.warning("synthesis_json_extraction_failed")

                return self.create_response(
                    success=True,
                    message="Synthesis completed but structured data extraction failed",
                    data={"raw_report": response_text},
                    warnings=["Could not extract structured JSON from synthesis"],
                )

        except Exception as e:
            self.logger.error("synthesis_process_failed", error=str(e))
            return self.create_response(
                success=False,
                message=f"Synthesis process failed: {str(e)}",
                errors=[str(e)],
            )

    def _build_synthesis_prompt(
        self,
        submission: BusinessSubmission,
        market_research: MarketResearch = None,
        business_analysis: BusinessAnalysis = None,
        financial_model: FinancialModel = None,
        validation_report: ValidationReport = None,
    ) -> str:
        """Build synthesis prompt from all inputs."""
        prompt = f"""Create a comprehensive final report synthesizing all analysis for:

**{submission.overview.name}**

---

**BUSINESS SUBMISSION SUMMARY**
- Industry: {submission.overview.industry}
- Stage: {submission.overview.stage}
- Problem: {submission.overview.problem}
- Solution: {submission.overview.solution}
- Revenue Model: {submission.business_model.revenue_model}

"""

        if market_research:
            prompt += f"""**MARKET RESEARCH SUMMARY**
Confidence: {market_research.confidence_score}%

Market Overview (excerpt):
{market_research.market_overview[:500]}...

Comparable Companies: {len(market_research.comparable_companies)}

Key Opportunities:
{chr(10).join(f'- {opp}' for opp in market_research.opportunities[:5])}

Key Threats:
{chr(10).join(f'- {threat}' for threat in market_research.threats[:5])}

"""

        if business_analysis:
            prompt += f"""**BUSINESS ANALYSIS SUMMARY**
Overall Score: {business_analysis.overall_score}/10
Confidence: {business_analysis.confidence_score}%

Evaluation Scores:
"""
            for score in business_analysis.evaluation_scores:
                prompt += f"- {score.dimension}: {score.score}/10 (weight: {score.weight*100:.0f}%)\n"

            prompt += f"""
Top Risks:
"""
            for risk in business_analysis.risks[:5]:
                prompt += f"- [{risk.severity.upper()}] {risk.category}: {risk.description}\n"

            prompt += f"""
Key Recommendations:
{chr(10).join(f'- {rec}' for rec in business_analysis.recommendations[:5])}

"""

        if financial_model:
            prompt += f"""**FINANCIAL MODEL SUMMARY**
Confidence: {financial_model.confidence_score}%

Unit Economics:
- CAC: ${financial_model.unit_economics.cac:,.0f} if financial_model.unit_economics.cac else 'N/A'}
- LTV: ${financial_model.unit_economics.ltv:,.0f} if financial_model.unit_economics.ltv else 'N/A'}
- LTV:CAC Ratio: {financial_model.unit_economics.ltv_cac_ratio:.1f}x if financial_model.unit_economics.ltv_cac_ratio else 'N/A'}
- Payback Period: {financial_model.unit_economics.payback_period_months:.0f} months if financial_model.unit_economics.payback_period_months else 'N/A'}
- Gross Margin: {financial_model.unit_economics.gross_margin:.0f}% if financial_model.unit_economics.gross_margin else 'N/A'}

Scenarios:
"""
            for scenario in financial_model.scenarios:
                prompt += f"""
{scenario.scenario_name}:
  - Year 1 Revenue: ${scenario.year1_revenue:,.0f}
  - Year 3 Revenue: ${scenario.year3_revenue:,.0f}
  - Year 3 Profit: ${scenario.year3_profit:,.0f}
"""

        if validation_report:
            prompt += f"""
**VALIDATION SUMMARY**
Status: {validation_report.overall_status.upper()}
Confidence: {validation_report.confidence_score}%
Issues Found: {len(validation_report.issues)}
Requires Human Review: {validation_report.requires_human_review}

"""
            if validation_report.issues:
                prompt += "Critical Issues:\n"
                critical = [i for i in validation_report.issues if i.severity in ["critical", "error"]]
                for issue in critical[:3]:
                    prompt += f"- [{issue.severity.upper()}] {issue.description}\n"

        prompt += """
---

**SYNTHESIS TASK**

Create a comprehensive final report that:

1. **Executive Summary**:
   - Clear recommendation (INVEST/PASS/MONITOR)
   - Overall score and justification
   - 3-5 key findings
   - Critical risks
   - Next steps

2. **Detailed Sections**:
   - Market Analysis (synthesize research findings)
   - Business Evaluation (team, product, model, traction)
   - Financial Analysis (unit economics, projections, scenarios)
   - Risk Assessment (top risks with mitigations)

3. **Key Outputs**:
   - Key findings list
   - Critical assumptions to validate
   - Recommended next steps
   - All sources used

Output as JSON matching FinalReport schema.

Write clearly for executive audience. Be honest about strengths and weaknesses."""

        return prompt

    def _create_final_report(
        self,
        submission: BusinessSubmission,
        data: Dict[str, Any],
        market_research: MarketResearch = None,
        business_analysis: BusinessAnalysis = None,
        financial_model: FinancialModel = None,
    ) -> FinalReport:
        """Create FinalReport object from structured data."""
        # Compile all sources
        all_sources = []
        if market_research:
            all_sources.extend(market_research.sources)

        if "sources" in data:
            all_sources.extend(data["sources"])

        # Remove duplicates
        all_sources = list(set(all_sources))

        return FinalReport(
            submission_id=submission.submission_id,
            generated_at=datetime.utcnow(),
            executive_summary=data.get("executive_summary", ""),
            recommendation=data.get("recommendation", ""),
            overall_score=data.get("overall_score", 0.0),
            market_analysis=data.get("market_analysis", ""),
            business_evaluation=data.get("business_evaluation", ""),
            financial_analysis=data.get("financial_analysis", ""),
            risk_assessment=data.get("risk_assessment", ""),
            key_findings=data.get("key_findings", []),
            critical_assumptions=data.get("critical_assumptions", []),
            next_steps=data.get("next_steps", []),
            financial_model_path=financial_model.spreadsheet_path if financial_model else None,
            sources=all_sources,
        )

    def _create_audit_trail(
        self,
        submission: BusinessSubmission,
        market_research: MarketResearch = None,
        business_analysis: BusinessAnalysis = None,
        financial_model: FinancialModel = None,
        validation_report: ValidationReport = None,
    ) -> Dict[str, Any]:
        """Create audit trail of all decisions and handoffs."""
        return {
            "submission_timestamp": submission.timestamp.isoformat(),
            "completeness_score": submission.completeness_score,
            "research_confidence": market_research.confidence_score if market_research else None,
            "analysis_confidence": business_analysis.confidence_score if business_analysis else None,
            "financial_confidence": financial_model.confidence_score if financial_model else None,
            "validation_status": validation_report.overall_status if validation_report else None,
            "validation_confidence": validation_report.confidence_score if validation_report else None,
            "requires_human_review": validation_report.requires_human_review if validation_report else False,
        }
