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

Output Format:
Provide your research as a structured JSON object matching the MarketResearch schema, including:
- market_overview: Comprehensive market analysis
- market_size_validation: Validation of claimed market size
- competitive_landscape: Analysis of competitive dynamics
- industry_benchmarks: Key metrics with sources
- comparable_companies: 5-10 companies with detailed metrics
- opportunities: List of market opportunities
- threats: List of potential threats
- sources: All sources used
- confidence_score: Your confidence in the research (0-100)

Be thorough and analytical. If you cannot find specific information, state that clearly rather than making assumptions."""

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
        return f"""Conduct comprehensive market research for the following business:

**Business Overview:**
- Name: {submission.overview.name}
- Industry: {submission.overview.industry}
- Stage: {submission.overview.stage}
- Problem: {submission.overview.problem}
- Solution: {submission.overview.solution}

**Value Proposition:**
- Unique Value: {submission.value_proposition.unique_value}
- Target Customer: {submission.value_proposition.target_customer}
- Differentiators: {', '.join(submission.value_proposition.differentiators)}

**Market Information:**
- Target Segments: {', '.join(submission.market.target_segments)}
- Market Size: {submission.market.market_size or 'Not provided'}
- TAM: ${submission.market.tam:,.0f if submission.market.tam else 'Not provided'}
- SAM: ${submission.market.sam:,.0f if submission.market.sam else 'Not provided'}
- Geography: {', '.join(submission.market.geography) if submission.market.geography else 'Not specified'}

**Business Model:**
- Revenue Model: {submission.business_model.revenue_model}
- Pricing: {submission.business_model.pricing}
- Channels: {', '.join(submission.business_model.distribution_channels)}

Please conduct thorough market research covering:
1. Market size validation and growth trends
2. Competitive landscape analysis
3. 5-10 comparable companies with metrics
4. Industry benchmarks (CAC, LTV, margins, growth rates, etc.)
5. Key opportunities and threats

Provide your research as a JSON object matching this structure:
{{
  "market_overview": "Detailed market analysis...",
  "market_size_validation": "Validation of market size claims...",
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

Be thorough and cite all sources."""

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
