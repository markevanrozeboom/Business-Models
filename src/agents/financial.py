"""Financial Modeling Agent - Builds financial projections and unit economics models."""

import os
from datetime import datetime
from typing import Dict, Any, Optional

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows

from .base import BaseAgent
from ..models.schemas import (
    AgentType,
    AgentResponse,
    BusinessSubmission,
    MarketResearch,
    FinancialModel,
    ScenarioProjection,
    UnitEconomics,
)
from ..utils.config import settings


class FinancialAgent(BaseAgent):
    """
    Financial Modeling Agent builds comprehensive financial projections.
    Creates 3-year models with scenario analysis and unit economics.
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.FINANCIAL,
            temperature=0.2,  # Low temperature for numerical accuracy
            max_tokens=8000,
        )

    def get_system_prompt(self) -> str:
        return """You are an expert financial modeler with extensive experience in building financial projections for startups and growth companies. You specialize in unit economics, scenario planning, and driver-based modeling.

Your role is to:
1. Build 3-year monthly P&L projections
2. Calculate unit economics (CAC, LTV, payback period, contribution margin)
3. Create scenario analysis (optimistic, base, pessimistic)
4. Identify key financial drivers
5. Perform sensitivity analysis on critical assumptions

Financial Model Components:

**Revenue Model:**
- Driver-based (units × price, or usage-based)
- Consider seasonality, churn, expansion revenue
- Apply realistic growth rates based on stage and market

**Cost Model:**
- COGS (variable costs)
- Fixed operating expenses (personnel, marketing, G&A, R&D)
- Scale COGS with revenue, step-function for fixed costs

**Unit Economics:**
- CAC (Customer Acquisition Cost): Marketing & sales / new customers
- LTV (Lifetime Value): ARPU × gross margin × (1 / churn rate)
- LTV:CAC Ratio: Should be > 3x for healthy business
- Payback Period: CAC / monthly profit per customer (ideally < 12 months)
- Contribution Margin: (Revenue - variable costs) / Revenue

**Scenario Analysis:**
- Optimistic: Better-than-expected growth, lower costs (70% probability adjusted)
- Base: Most likely case based on current trajectory
- Pessimistic: Slower growth, higher costs, market challenges

**Key Drivers to Model:**
- Customer acquisition rate
- Pricing and ARPU
- Churn/retention rate
- Gross margin
- Marketing efficiency (CAC)
- Operating leverage

Output Format:
Provide financial model as JSON matching the FinancialModel schema:
{{
  "scenarios": [
    {{
      "scenario_name": "Base Case",
      "assumptions": {{"growth_rate": 100, "cac": 500, "churn": 5}},
      "year1_revenue": 1000000,
      "year1_costs": 1200000,
      "year1_profit": -200000,
      "year2_revenue": 3000000,
      "year2_costs": 2500000,
      "year2_profit": 500000,
      "year3_revenue": 7000000,
      "year3_costs": 4500000,
      "year3_profit": 2500000
    }},
    ...
  ],
  "unit_economics": {{
    "cac": 500,
    "ltv": 2000,
    "ltv_cac_ratio": 4.0,
    "payback_period_months": 12,
    "contribution_margin": 70,
    "gross_margin": 75
  }},
  "key_drivers": {{
    "monthly_customer_acquisition": 100,
    "monthly_churn_rate": 2.5,
    "arpu": 50
  }},
  "sensitivity_analysis": {{
    "revenue_sensitivity_to_growth": "+/- 20% growth = +/- 45% revenue",
    "cac_sensitivity": "+20% CAC = -15% profitability"
  }},
  "confidence_score": 75
}}

Be realistic and conservative in assumptions. Flag where data is limited."""

    def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Build financial model based on submission and research.

        Args:
            input_data: Dict containing:
                - "business_submission": BusinessSubmission data
                - "market_research": Optional MarketResearch data

        Returns:
            AgentResponse with FinancialModel data and spreadsheet path
        """
        try:
            self.logger.info("financial_modeling_started")

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

            # Build financial modeling prompt
            modeling_prompt = self._build_modeling_prompt(submission, market_research)

            # Execute modeling
            response = self._create_message(
                messages=[{"role": "user", "content": modeling_prompt}]
            )

            response_text = response.content[0].text

            # Extract structured data
            structured_data = self._extract_json_from_response(response_text)

            if structured_data:
                # Create FinancialModel object
                financial_model = self._create_financial_model(structured_data)

                # Generate Excel spreadsheet
                spreadsheet_path = self._generate_spreadsheet(
                    submission, financial_model
                )
                financial_model.spreadsheet_path = spreadsheet_path

                self.logger.info(
                    "financial_modeling_completed",
                    num_scenarios=len(financial_model.scenarios),
                    spreadsheet_path=spreadsheet_path,
                    confidence_score=financial_model.confidence_score,
                )

                return self.create_response(
                    success=True,
                    message="Financial model created successfully",
                    data=financial_model.model_dump(),
                    confidence_score=financial_model.confidence_score,
                )
            else:
                self.logger.warning("financial_json_extraction_failed")

                return self.create_response(
                    success=True,
                    message="Financial modeling completed but structured data extraction failed",
                    data={"raw_model": response_text},
                    warnings=["Could not extract structured JSON from financial model"],
                )

        except Exception as e:
            self.logger.error("financial_modeling_failed", error=str(e))
            return self.create_response(
                success=False,
                message=f"Financial modeling failed: {str(e)}",
                errors=[str(e)],
            )

    def _build_modeling_prompt(
        self,
        submission: BusinessSubmission,
        market_research: Optional[MarketResearch] = None,
    ) -> str:
        """Build financial modeling prompt."""
        prompt = f"""Build a comprehensive 3-year financial model for:

**BUSINESS DETAILS**

Name: {submission.overview.name}
Industry: {submission.overview.industry}
Stage: {submission.overview.stage}

Revenue Model: {submission.business_model.revenue_model}
Pricing: {submission.business_model.pricing}
Cost Structure: {submission.business_model.cost_structure}

Current Financial Inputs:
- Year 1 Revenue Target: ${submission.financials.year1_revenue:,.0f if submission.financials.year1_revenue else 'Not provided'}
- Year 2 Revenue Target: ${submission.financials.year2_revenue:,.0f if submission.financials.year2_revenue else 'Not provided'}
- Year 3 Revenue Target: ${submission.financials.year3_revenue:,.0f if submission.financials.year3_revenue else 'Not provided'}
- Gross Margin: {submission.financials.gross_margin if submission.financials.gross_margin else 'Not provided'}%
- Monthly Burn Rate: ${submission.financials.burn_rate:,.0f if submission.financials.burn_rate else 'Not provided'}
- Funding Needed: ${submission.financials.funding_needed:,.0f if submission.financials.funding_needed else 'Not provided'}
"""

        if market_research and market_research.industry_benchmarks:
            benchmarks = market_research.industry_benchmarks
            prompt += f"""

**INDUSTRY BENCHMARKS** (use for validation and gap-filling)
{benchmarks}
"""

        prompt += """

**MODELING REQUIREMENTS**

Create three scenarios (Optimistic, Base, Pessimistic) with:

1. **Revenue Projections** (3 years)
   - Build up from key drivers (customers, ARPU, etc.)
   - Apply realistic growth rates for stage and industry

2. **Cost Projections** (3 years)
   - COGS (variable with revenue)
   - Operating expenses (personnel, marketing, G&A)
   - Show path to profitability if achievable

3. **Unit Economics**
   - CAC: Customer Acquisition Cost
   - LTV: Lifetime Value
   - LTV:CAC ratio (target > 3x)
   - Payback period (target < 12 months)
   - Contribution margin
   - Gross margin

4. **Key Financial Drivers**
   - What drives revenue?
   - What drives costs?
   - Critical assumptions?

5. **Sensitivity Analysis**
   - Which variables have biggest impact?
   - What happens if key assumptions change?

**Scenario Definitions:**
- **Optimistic**: 70th percentile outcome, strong execution
- **Base**: 50th percentile, expected case
- **Pessimistic**: 30th percentile, challenges occur

Output comprehensive financial model as JSON matching FinancialModel schema.

Be realistic and data-driven. Use industry benchmarks where specific data is lacking."""

        return prompt

    def _create_financial_model(self, data: Dict[str, Any]) -> FinancialModel:
        """Create FinancialModel object from structured data."""
        # Parse scenarios
        scenarios = []
        for scenario_data in data.get("scenarios", []):
            scenarios.append(ScenarioProjection(**scenario_data))

        # Parse unit economics
        unit_econ_data = data.get("unit_economics", {})
        unit_economics = UnitEconomics(**unit_econ_data)

        return FinancialModel(
            scenarios=scenarios,
            unit_economics=unit_economics,
            key_drivers=data.get("key_drivers", {}),
            sensitivity_analysis=data.get("sensitivity_analysis", {}),
            confidence_score=data.get("confidence_score", 70.0),
        )

    def _generate_spreadsheet(
        self,
        submission: BusinessSubmission,
        model: FinancialModel,
    ) -> str:
        """Generate Excel spreadsheet with financial model."""
        try:
            # Create output directory
            os.makedirs(settings.models_dir, exist_ok=True)

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{submission.overview.name.replace(' ', '_')}_{timestamp}.xlsx"
            filepath = os.path.join(settings.models_dir, filename)

            # Create workbook
            wb = Workbook()

            # Create Summary sheet
            self._create_summary_sheet(wb, submission, model)

            # Create Scenarios sheet
            self._create_scenarios_sheet(wb, model)

            # Create Unit Economics sheet
            self._create_unit_economics_sheet(wb, model)

            # Save workbook
            wb.save(filepath)

            self.logger.info("spreadsheet_generated", filepath=filepath)

            return filepath

        except Exception as e:
            self.logger.error("spreadsheet_generation_failed", error=str(e))
            return ""

    def _create_summary_sheet(self, wb: Workbook, submission: BusinessSubmission, model: FinancialModel):
        """Create summary sheet."""
        ws = wb.active
        ws.title = "Summary"

        # Header
        ws["A1"] = f"Financial Model: {submission.overview.name}"
        ws["A1"].font = Font(size=16, bold=True)

        # Business details
        row = 3
        ws[f"A{row}"] = "Business Overview"
        ws[f"A{row}"].font = Font(bold=True)
        row += 1
        ws[f"A{row}"] = "Industry:"
        ws[f"B{row}"] = submission.overview.industry
        row += 1
        ws[f"A{row}"] = "Stage:"
        ws[f"B{row}"] = submission.overview.stage
        row += 1
        ws[f"A{row}"] = "Revenue Model:"
        ws[f"B{row}"] = submission.business_model.revenue_model

        # Unit Economics
        row += 2
        ws[f"A{row}"] = "Unit Economics"
        ws[f"A{row}"].font = Font(bold=True)
        row += 1

        ue = model.unit_economics
        if ue.cac:
            ws[f"A{row}"] = "CAC:"
            ws[f"B{row}"] = f"${ue.cac:,.0f}"
            row += 1
        if ue.ltv:
            ws[f"A{row}"] = "LTV:"
            ws[f"B{row}"] = f"${ue.ltv:,.0f}"
            row += 1
        if ue.ltv_cac_ratio:
            ws[f"A{row}"] = "LTV:CAC:"
            ws[f"B{row}"] = f"{ue.ltv_cac_ratio:.1f}x"
            row += 1
        if ue.payback_period_months:
            ws[f"A{row}"] = "Payback Period:"
            ws[f"B{row}"] = f"{ue.payback_period_months:.0f} months"
            row += 1
        if ue.gross_margin:
            ws[f"A{row}"] = "Gross Margin:"
            ws[f"B{row}"] = f"{ue.gross_margin:.0f}%"

    def _create_scenarios_sheet(self, wb: Workbook, model: FinancialModel):
        """Create scenarios comparison sheet."""
        ws = wb.create_sheet("Scenarios")

        # Headers
        ws["A1"] = "Scenario Comparison"
        ws["A1"].font = Font(size=14, bold=True)

        row = 3
        ws[f"A{row}"] = "Metric"
        col_idx = 2
        for scenario in model.scenarios:
            ws.cell(row, col_idx, scenario.scenario_name)
            ws.cell(row, col_idx).font = Font(bold=True)
            col_idx += 1

        # Revenue rows
        row += 1
        ws[f"A{row}"] = "Year 1 Revenue"
        col_idx = 2
        for scenario in model.scenarios:
            ws.cell(row, col_idx, scenario.year1_revenue)
            col_idx += 1

        row += 1
        ws[f"A{row}"] = "Year 2 Revenue"
        col_idx = 2
        for scenario in model.scenarios:
            ws.cell(row, col_idx, scenario.year2_revenue)
            col_idx += 1

        row += 1
        ws[f"A{row}"] = "Year 3 Revenue"
        col_idx = 2
        for scenario in model.scenarios:
            ws.cell(row, col_idx, scenario.year3_revenue)
            col_idx += 1

        # Profit rows
        row += 1
        ws[f"A{row}"] = "Year 3 Profit"
        col_idx = 2
        for scenario in model.scenarios:
            ws.cell(row, col_idx, scenario.year3_profit)
            col_idx += 1

    def _create_unit_economics_sheet(self, wb: Workbook, model: FinancialModel):
        """Create unit economics details sheet."""
        ws = wb.create_sheet("Unit Economics")

        ws["A1"] = "Unit Economics Analysis"
        ws["A1"].font = Font(size=14, bold=True)

        row = 3
        ue = model.unit_economics

        metrics = [
            ("Customer Acquisition Cost (CAC)", ue.cac),
            ("Lifetime Value (LTV)", ue.ltv),
            ("LTV:CAC Ratio", ue.ltv_cac_ratio),
            ("Payback Period (months)", ue.payback_period_months),
            ("Contribution Margin (%)", ue.contribution_margin),
            ("Gross Margin (%)", ue.gross_margin),
        ]

        for metric_name, value in metrics:
            if value is not None:
                ws[f"A{row}"] = metric_name
                ws[f"B{row}"] = value
                row += 1
