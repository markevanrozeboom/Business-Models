"""Research Agent - Conducts market analysis and competitive intelligence."""

from typing import Dict, Any

from .base import BaseAgent
from ..models.schemas import (
    AgentType,
    AgentResponse,
    BusinessSubmission,
    MarketResearch,
    CompanyComparable,
)


class ResearchAgent(BaseAgent):
    """
    Research Agent conducts market analysis and competitive intelligence.
    Gathers industry benchmarks, identifies comparables, and assesses market trends.
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.RESEARCH,
            temperature=0.5,  # Balanced for factual research
            max_tokens=8000,  # More tokens for comprehensive research
        )

    def get_system_prompt(self) -> str:
        return """You are an expert market researcher and competitive intelligence analyst with deep experience in business strategy and market analysis.

Your role is to:
1. Conduct comprehensive market analysis for the given business
2. Identify and analyze 5-10 comparable companies
3. Gather industry benchmarks (CAC, LTV, margins, growth rates)
4. Assess market size, growth trends, and dynamics
5. Identify key opportunities and threats
6. Provide sources for all claims and data

IMPORTANT: The business submission may have incomplete or missing information. Your job is to:
- Work with whatever information is available
- Infer reasonable assumptions when data is missing (and clearly state these assumptions)
- Use industry knowledge to fill gaps where appropriate
- Be creative and resourceful - don't let missing data stop you from providing valuable research

Research Areas:
- Market Overview: Size, growth rate, key trends, regulatory environment
- Competitive Landscape: Direct/indirect competitors, market positioning
- Comparable Companies: Similar businesses with relevant metrics
- Industry Benchmarks: Standard metrics for the industry (CAC, LTV, margins, etc.)
- Opportunities: Market gaps, growth drivers, favorable trends
- Threats: Competitive pressure, market risks, barriers

Important Guidelines:
- Cite sources for all data points and claims
- Distinguish between verified data and estimates
- Provide context for all numbers (e.g., "For SaaS companies at Series A stage...")
- Flag when information is limited or unavailable
- Focus on recent data (last 2-3 years preferred)
- Consider geographic market differences
- When business details are missing, use industry standards and comparable companies to infer likely characteristics

Output Format:
Provide your research as a structured JSON object matching the MarketResearch schema, including:
- market_overview: Comprehensive market analysis
- market_size_validation: Validation of claimed market size (or estimate if not provided)
- competitive_landscape: Analysis of competitive dynamics
- industry_benchmarks: Key metrics with sources
- comparable_companies: 5-10 companies with detailed metrics
- opportunities: List of market opportunities
- threats: List of potential threats
- sources: All sources used
- confidence_score: Your confidence in the research (0-100)

Be thorough and analytical. If you cannot find specific information, state that clearly and use industry knowledge to provide reasonable estimates."""

    def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Conduct market research based on business submission.

        Args:
            input_data: Dict containing:
                - "business_submission": BusinessSubmission data

        Returns:
            AgentResponse with MarketResearch data
        """
        try:
            self.logger.info("research_process_started")

            # Parse business submission
            if "business_submission" not in input_data:
                return self.create_response(
                    success=False,
                    message="Missing business_submission in input data",
                    errors=["business_submission is required"],
                )

            submission_data = input_data["business_submission"]
            submission = BusinessSubmission(**submission_data)

            # Build research prompt
            research_prompt = self._build_research_prompt(submission)

            # Execute research
            response = self._create_message(
                messages=[{"role": "user", "content": research_prompt}]
            )

            response_text = response.content[0].text

            # Extract structured data
            structured_data = self._extract_json_from_response(response_text)

            if structured_data:
                # Create MarketResearch object
                market_research = self._create_market_research(structured_data)

                self.logger.info(
                    "research_completed",
                    num_comparables=len(market_research.comparable_companies),
                    confidence_score=market_research.confidence_score,
                )

                return self.create_response(
                    success=True,
                    message="Market research completed successfully",
                    data=market_research.model_dump(),
                    confidence_score=market_research.confidence_score,
                )
            else:
                # Return raw research if JSON extraction failed
                self.logger.warning("research_json_extraction_failed")

                return self.create_response(
                    success=True,
                    message="Research completed but structured data extraction failed",
                    data={"raw_research": response_text},
                    warnings=["Could not extract structured JSON from research"],
                )

        except Exception as e:
            self.logger.error("research_process_failed", error=str(e))
            return self.create_response(
                success=False,
                message=f"Research process failed: {str(e)}",
                errors=[str(e)],
            )

    def _build_research_prompt(self, submission: BusinessSubmission) -> str:
        """Build research prompt from business submission."""
        # Helper to format optional fields
        def fmt_field(value, default="Not provided"):
            return value if value else default
        
        def fmt_list(value_list, default="Not specified"):
            return ', '.join(value_list) if value_list else default
        
        return f"""Conduct comprehensive market research for the following business:

**Business Overview:**
- Name: {fmt_field(submission.overview.name)}
- Industry: {fmt_field(submission.overview.industry)}
- Stage: {fmt_field(submission.overview.stage)}
- Problem: {fmt_field(submission.overview.problem)}
- Solution: {fmt_field(submission.overview.solution)}

**Value Proposition:**
- Unique Value: {fmt_field(submission.value_proposition.unique_value)}
- Target Customer: {fmt_field(submission.value_proposition.target_customer)}
- Differentiators: {fmt_list(submission.value_proposition.differentiators)}

**Market Information:**
- Target Segments: {fmt_list(submission.market.target_segments)}
- Market Size: {fmt_field(submission.market.market_size)}
- TAM: {'$' + f'{submission.market.tam:,.0f}' if submission.market.tam else 'Not provided'}
- SAM: {'$' + f'{submission.market.sam:,.0f}' if submission.market.sam else 'Not provided'}
- Geography: {fmt_list(submission.market.geography)}

**Business Model:**
- Revenue Model: {fmt_field(submission.business_model.revenue_model)}
- Pricing: {fmt_field(submission.business_model.pricing)}
- Channels: {fmt_list(submission.business_model.distribution_channels)}

NOTE: Some information may be missing or incomplete. Use your industry knowledge to:
- Infer reasonable market characteristics based on the business description
- Research comparable companies even if specific details are missing
- Provide industry benchmarks that would apply to this type of business
- Make educated estimates where appropriate (and clearly label them as estimates)

Please conduct thorough market research covering:
1. Market size validation and growth trends (estimate if not provided)
2. Competitive landscape analysis
3. 5-10 comparable companies with metrics
4. Industry benchmarks (CAC, LTV, margins, growth rates, etc.)
5. Key opportunities and threats

Provide your research as a JSON object matching this structure:
{{
  "market_overview": "Detailed market analysis...",
  "market_size_validation": "Validation of market size claims or estimates...",
  "competitive_landscape": "Competitive analysis...",
  "industry_benchmarks": {{
    "avg_cac": 100,
    "avg_ltv": 500,
    "avg_gross_margin": 70,
    "avg_growth_rate": 50
  }},
  "comparable_companies": [
    {{
      "name": "Company Name",
      "description": "What they do",
      "stage": "Series A/B/etc",
      "metrics": {{"arr": 10000000, "growth_rate": 100}},
      "sources": ["url1", "url2"]
    }}
  ],
  "opportunities": ["Opportunity 1", "Opportunity 2"],
  "threats": ["Threat 1", "Threat 2"],
  "sources": ["All sources used"],
  "confidence_score": 75
}}

Be thorough and cite all sources. Use industry knowledge to fill gaps when information is missing."""

    def _create_market_research(self, data: Dict[str, Any]) -> MarketResearch:
        """Create MarketResearch object from structured data."""
        # Parse comparable companies
        comparables = []
        for comp_data in data.get("comparable_companies", []):
            comparables.append(CompanyComparable(**comp_data))

        return MarketResearch(
            market_overview=data.get("market_overview", ""),
            market_size_validation=data.get("market_size_validation", ""),
            competitive_landscape=data.get("competitive_landscape", ""),
            industry_benchmarks=data.get("industry_benchmarks", {}),
            comparable_companies=comparables,
            opportunities=data.get("opportunities", []),
            threats=data.get("threats", []),
            sources=data.get("sources", []),
            confidence_score=data.get("confidence_score", 70.0),
        )
