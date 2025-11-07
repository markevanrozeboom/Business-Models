"""Analysis Agent - Evaluates business model viability using VC/PE frameworks."""

from typing import Dict, Any

from .base import BaseAgent
from ..models.schemas import (
    AgentType,
    AgentResponse,
    BusinessSubmission,
    MarketResearch,
    BusinessAnalysis,
    EvaluationScore,
    RiskItem,
)


class AnalysisAgent(BaseAgent):
    """
    Analysis Agent evaluates business model viability using professional frameworks.
    Assesses team, market, product, and traction with weighted scoring.
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.ANALYSIS,
            temperature=0.3,  # Lower temperature for analytical rigor
            max_tokens=16000,  # Increased for comprehensive analysis (was 8000)
        )

    def get_system_prompt(self) -> str:
        return """You are an expert venture capital and private equity analyst with 15+ years of experience evaluating businesses. You use rigorous analytical frameworks to assess investment opportunities.

Your role is to:
1. Evaluate business model viability using VC/PE frameworks
2. Score the business across multiple dimensions (0-10 scale)
3. Assess unit economics and financial sustainability
4. Identify key assumptions that need validation
5. Flag risks across categories (market, operational, financial, strategic)
6. Provide actionable recommendations

IMPORTANT: The business submission may have incomplete or missing information. Your job is to:
- Work with whatever information is available
- Make reasonable inferences based on the business description
- Use industry knowledge to assess viability even with partial data
- Clearly note when information is missing and how that affects your assessment
- Be creative in evaluating the opportunity based on what's provided

Evaluation Dimensions (with weights):
1. **Team Quality (20%)**: Founder experience, domain expertise, execution capability
2. **Market Opportunity (25%)**: Market size, growth rate, accessibility
3. **Product/Solution (20%)**: Differentiation, scalability, technical feasibility
4. **Business Model (15%)**: Revenue model clarity, unit economics, scalability
5. **Competitive Position (10%)**: Defensibility, barriers to entry, competitive advantages
6. **Traction/Validation (10%)**: Customer validation, revenue, growth metrics

Scoring Guidelines:
- 9-10: Exceptional - top 10% of opportunities
- 7-8: Strong - clear path to success
- 5-6: Adequate - significant work needed
- 3-4: Weak - major concerns
- 0-2: Critical issues - not viable as-is

When information is missing:
- Use industry standards and comparable companies to make reasonable assessments
- Note uncertainty in justifications
- Adjust confidence scores based on data completeness
- Don't penalize heavily for missing information - focus on what's available

Risk Categories:
- **Market Risk**: Market size, adoption rate, competition
- **Operational Risk**: Execution challenges, scaling issues
- **Financial Risk**: Burn rate, funding needs, unit economics
- **Strategic Risk**: Business model, competitive threats
- **Team Risk**: Key person dependencies, skill gaps

For each risk, assess:
- Severity: low/medium/high/critical
- Probability: low/medium/high
- Mitigation strategy

Output Format:
Provide analysis as JSON matching the BusinessAnalysis schema:
{{
  "executive_summary": "Clear summary of findings...",
  "evaluation_scores": [
    {{"dimension": "Team Quality", "score": 7.5, "weight": 0.20, "justification": "..."}},
    ...
  ],
  "overall_score": 7.2,
  "unit_economics_assessment": "Detailed assessment...",
  "key_assumptions": ["Assumption 1", "Assumption 2"],
  "risks": [
    {{"category": "Market Risk", "description": "...", "severity": "high", "probability": "medium", "mitigation": "..."}},
    ...
  ],
  "recommendations": ["Recommendation 1", "Recommendation 2"],
  "confidence_score": 80
}}

Be rigorous, objective, and analytical. Base scores on evidence when available, and use industry knowledge to fill gaps when information is missing."""

    def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Analyze business viability based on submission and research.

        Args:
            input_data: Dict containing:
                - "business_submission": BusinessSubmission data
                - "market_research": MarketResearch data

        Returns:
            AgentResponse with BusinessAnalysis data
        """
        try:
            self.logger.info("analysis_process_started")

            # Validate inputs
            if "business_submission" not in input_data:
                return self.create_response(
                    success=False,
                    message="Missing business_submission in input data",
                    errors=["business_submission is required"],
                )

            submission_data = input_data["business_submission"]
            submission = BusinessSubmission(**submission_data)

            market_research = None
            if "market_research" in input_data:
                research_data = input_data["market_research"]
                market_research = MarketResearch(**research_data)

            # Build analysis prompt
            analysis_prompt = self._build_analysis_prompt(submission, market_research)

            # Execute analysis
            response = self._create_message(
                messages=[{"role": "user", "content": analysis_prompt}]
            )

            response_text = response.content[0].text

            # Extract structured data with improved extraction
            structured_data = self._extract_json_from_response(response_text)

            # Retry with refined prompt if extraction fails or output is incomplete
            max_retries = 2
            for attempt in range(max_retries + 1):
                if attempt > 0:
                    # Refine prompt for retry
                    retry_prompt = f"""The previous response did not contain complete structured data.
Please provide a complete JSON response with all required fields populated:
- executive_summary (detailed summary)
- evaluation_scores (list with at least 4-6 dimensions)
- overall_score (calculated from evaluation_scores)
- unit_economics_assessment (detailed assessment)
- key_assumptions (list)
- risks (list with at least 3-5 risks)
- recommendations (list)

Original response: {response_text[:500]}...

Please provide the complete JSON now."""
                    
                    retry_response = self._create_message(
                        messages=[{"role": "user", "content": retry_prompt}],
                        retry=False,
                    )
                    response_text = retry_response.content[0].text
                    structured_data = self._extract_json_from_response(response_text)

                if structured_data:
                    # Validate output completeness
                    required_fields = [
                        "executive_summary",
                        "evaluation_scores",
                        "risks",
                    ]
                    is_valid, missing = self._validate_output_completeness(
                        structured_data,
                        required_fields,
                        min_required=2,  # At least 2 of 3 required
                    )
                    
                    if is_valid or attempt == max_retries:
                        # Create BusinessAnalysis object
                        analysis = self._create_business_analysis(structured_data)
                        
                        if not is_valid:
                            self.logger.warning(
                                "analysis_incomplete_output",
                                missing_fields=missing,
                                attempt=attempt + 1,
                            )

                        self.logger.info(
                            "analysis_completed",
                            overall_score=analysis.overall_score,
                            num_risks=len(analysis.risks),
                            confidence_score=analysis.confidence_score,
                        )

                        warnings = []
                        if not is_valid:
                            warnings.append(f"Incomplete output: missing {', '.join(missing)}")

                        return self.create_response(
                            success=True,
                            message="Business analysis completed successfully",
                            data=analysis.model_dump(),
                            confidence_score=analysis.confidence_score,
                            warnings=warnings,
                        )
                elif attempt < max_retries:
                    self.logger.warning(
                        "analysis_json_extraction_failed_retrying",
                        attempt=attempt + 1,
                    )
                    continue

            # Final fallback
            self.logger.warning("analysis_json_extraction_failed_final")

            return self.create_response(
                success=True,
                message="Analysis completed but structured data extraction failed",
                data={"raw_analysis": response_text},
                warnings=["Could not extract structured JSON from analysis"],
            )

        except Exception as e:
            self.logger.error("analysis_process_failed", error=str(e))
            return self.create_response(
                success=False,
                message=f"Analysis process failed: {str(e)}",
                errors=[str(e)],
            )

    def _build_analysis_prompt(
        self,
        submission: BusinessSubmission,
        market_research: MarketResearch = None,
    ) -> str:
        """Build analysis prompt from inputs."""
        # Helper to format optional fields
        def fmt_field(value, default="Not provided"):
            return value if value else default
        
        def fmt_list(value_list, default="None"):
            return ', '.join(value_list) if value_list else default
        
        prompt = f"""Conduct comprehensive business analysis for the following opportunity:

**BUSINESS SUBMISSION**

Business: {fmt_field(submission.overview.name)}
Industry: {fmt_field(submission.overview.industry)}
Stage: {fmt_field(submission.overview.stage)}

Problem: {fmt_field(submission.overview.problem)}
Solution: {fmt_field(submission.overview.solution)}

Value Proposition: {fmt_field(submission.value_proposition.unique_value)}
Target Customer: {fmt_field(submission.value_proposition.target_customer)}
Differentiators: {fmt_list(submission.value_proposition.differentiators)}

Market Segments: {fmt_list(submission.market.target_segments)}
Market Size (TAM): {'$' + f'{submission.market.tam:,.0f}' if submission.market.tam else 'Not provided'}

Revenue Model: {fmt_field(submission.business_model.revenue_model)}
Pricing: {fmt_field(submission.business_model.pricing)}
Cost Structure: {fmt_field(submission.business_model.cost_structure)}

Team Size: {submission.team.team_size}
Key Roles: {fmt_list(submission.team.key_roles)}
Experience: {fmt_field(submission.team.relevant_experience)}
Current Metrics: {submission.team.current_metrics if submission.team.current_metrics else 'None'}
Milestones: {fmt_list(submission.team.milestones)}

Financial Projections:
- Year 1 Revenue: {'$' + f'{submission.financials.year1_revenue:,.0f}' if submission.financials.year1_revenue else 'Not provided'}
- Year 2 Revenue: {'$' + f'{submission.financials.year2_revenue:,.0f}' if submission.financials.year2_revenue else 'Not provided'}
- Year 3 Revenue: {'$' + f'{submission.financials.year3_revenue:,.0f}' if submission.financials.year3_revenue else 'Not provided'}
- Gross Margin: {f'{submission.financials.gross_margin}%' if submission.financials.gross_margin else 'Not provided'}
- Funding Needed: {'$' + f'{submission.financials.funding_needed:,.0f}' if submission.financials.funding_needed else 'Not provided'}
- Burn Rate: {'$' + f'{submission.financials.burn_rate:,.0f}' if submission.financials.burn_rate else 'Not provided'} /month

NOTE: Some information may be missing or incomplete. Use your industry knowledge and analytical frameworks to:
- Make reasonable assessments even with partial data
- Use comparable companies and industry standards to fill gaps
- Clearly note uncertainty in your analysis
- Focus on evaluating what's available rather than penalizing what's missing
"""

        if market_research:
            prompt += f"""

**MARKET RESEARCH FINDINGS**

Market Overview: {market_research.market_overview[:500]}...

Industry Benchmarks: {market_research.industry_benchmarks}

Number of Comparable Companies Analyzed: {len(market_research.comparable_companies)}

Key Opportunities: {', '.join(market_research.opportunities[:5])}
Key Threats: {', '.join(market_research.threats[:5])}

Research Confidence: {market_research.confidence_score}%
"""

        prompt += """

**ANALYSIS REQUIRED**

Please conduct a rigorous VC-style analysis covering:

1. **Team Quality (20% weight)**: Evaluate founder/team capability
2. **Market Opportunity (25% weight)**: Assess market size, growth, accessibility
3. **Product/Solution (20% weight)**: Evaluate differentiation and feasibility
4. **Business Model (15% weight)**: Assess revenue model and unit economics
5. **Competitive Position (10% weight)**: Analyze defensibility and advantages
6. **Traction/Validation (10% weight)**: Review customer validation and metrics

For each dimension:
- Provide a score (0-10)
- Include weight
- Give detailed justification

Also provide:
- Executive summary
- Overall weighted score
- Unit economics assessment
- Key assumptions to validate
- Risk matrix with mitigations
- Strategic recommendations
- Confidence score (0-100)

Output as JSON matching BusinessAnalysis schema."""

        return prompt

    def _create_business_analysis(self, data: Dict[str, Any]) -> BusinessAnalysis:
        """Create BusinessAnalysis object from structured data."""
        # Parse evaluation scores
        scores = []
        for score_data in data.get("evaluation_scores", []):
            scores.append(EvaluationScore(**score_data))

        # Parse risks
        risks = []
        for risk_data in data.get("risks", []):
            risks.append(RiskItem(**risk_data))

        return BusinessAnalysis(
            executive_summary=data.get("executive_summary", ""),
            evaluation_scores=scores,
            overall_score=data.get("overall_score", 0.0),
            unit_economics_assessment=data.get("unit_economics_assessment", ""),
            key_assumptions=data.get("key_assumptions", []),
            risks=risks,
            recommendations=data.get("recommendations", []),
            confidence_score=data.get("confidence_score", 70.0),
        )
