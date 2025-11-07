"""Pydantic models for data validation and serialization."""

import json
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator


class WorkflowPhase(str, Enum):
    """Workflow phases."""
    INTAKE = "intake"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    FINANCIAL_MODELING = "financial_modeling"
    VALIDATION = "validation"
    SYNTHESIS = "synthesis"
    HUMAN_REVIEW = "human_review"
    COMPLETED = "completed"


class AgentType(str, Enum):
    """Agent types in the system."""
    ORCHESTRATOR = "orchestrator"
    INTAKE = "intake"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    FINANCIAL = "financial"
    VALIDATION = "validation"
    SYNTHESIS = "synthesis"


# === Business Submission Models ===

class BusinessOverview(BaseModel):
    """Business overview information."""
    name: str = Field(default="", description="Business name")
    industry: str = Field(default="", description="Industry/sector")
    stage: str = Field(default="", description="Business stage (idea, MVP, early-stage, growth)")
    problem: str = Field(default="", description="Problem being solved")
    solution: str = Field(default="", description="Proposed solution")


class ValueProposition(BaseModel):
    """Value proposition details."""
    unique_value: str = Field(default="", description="Unique value proposition")
    differentiators: List[str] = Field(default_factory=list, description="Key differentiators from competitors")
    target_customer: str = Field(default="", description="Target customer description")


class MarketInfo(BaseModel):
    """Market and customer information."""
    target_segments: List[str] = Field(default_factory=list, description="Target market segments")
    market_size: Optional[str] = Field(None, description="Market size description")
    tam: Optional[float] = Field(None, description="Total Addressable Market (TAM) in $")
    sam: Optional[float] = Field(None, description="Serviceable Addressable Market (SAM) in $")
    som: Optional[float] = Field(None, description="Serviceable Obtainable Market (SOM) in $")
    geography: List[str] = Field(default_factory=list, description="Geographic markets")


class BusinessModelInfo(BaseModel):
    """Business model details."""
    revenue_model: str = Field(default="", description="Revenue model (subscription, transaction, etc.)")
    pricing: str = Field(default="", description="Pricing structure")
    cost_structure: str = Field(default="", description="Key cost drivers")
    distribution_channels: List[str] = Field(default_factory=list, description="Distribution channels")


class FinancialProjections(BaseModel):
    """Financial projection inputs."""
    year1_revenue: Optional[float] = Field(None, description="Year 1 projected revenue")
    year2_revenue: Optional[float] = Field(None, description="Year 2 projected revenue")
    year3_revenue: Optional[float] = Field(None, description="Year 3 projected revenue")
    gross_margin: Optional[float] = Field(None, description="Expected gross margin %")
    funding_needed: Optional[float] = Field(None, description="Funding amount needed")
    burn_rate: Optional[float] = Field(None, description="Monthly burn rate")


class TeamInfo(BaseModel):
    """Team composition and traction."""
    team_size: Optional[int] = Field(default=0, description="Current team size")
    key_roles: List[str] = Field(default_factory=list, description="Key team roles filled")
    relevant_experience: str = Field(default="", description="Team's relevant experience")
    current_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Current traction metrics"
    )
    milestones: List[str] = Field(default_factory=list, description="Key milestones achieved")


class BusinessSubmission(BaseModel):
    """Complete business submission from Intake Agent."""
    submission_id: str = Field(description="Unique submission identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    overview: BusinessOverview
    value_proposition: ValueProposition
    market: MarketInfo
    business_model: BusinessModelInfo
    financials: FinancialProjections
    team: TeamInfo
    additional_info: Dict[str, Any] = Field(default_factory=dict)
    completeness_score: float = Field(
        ge=0.0, le=100.0,
        description="Completeness score (0-100)"
    )


# === Research Agent Output ===

class CompanyComparable(BaseModel):
    """Comparable company data."""
    name: str
    description: str
    stage: str
    metrics: Dict[str, Any] = Field(default_factory=dict)
    sources: List[str] = Field(default_factory=list)


class MarketResearch(BaseModel):
    """Market research output from Research Agent."""
    market_overview: str = Field(default="", description="Market overview and trends")
    market_size_validation: str = Field(default="", description="Market size validation")
    competitive_landscape: str = Field(default="", description="Competitive landscape analysis")
    industry_benchmarks: Dict[str, Any] = Field(
        default_factory=dict,
        description="Industry benchmark metrics"
    )
    comparable_companies: List[CompanyComparable] = Field(
        default_factory=list,
        description="5-10 comparable companies"
    )
    opportunities: List[str] = Field(default_factory=list)
    threats: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list, description="Research sources")
    confidence_score: float = Field(ge=0.0, le=100.0, default=70.0)

    @field_validator('market_overview', mode='before')
    @classmethod
    def normalize_market_overview(cls, v: Any) -> str:
        """Convert dict to string if needed."""
        if isinstance(v, dict):
            # Try to extract description field, otherwise convert to readable format
            if 'description' in v:
                return str(v['description'])
            # Convert dict to formatted string
            parts = []
            for key, value in v.items():
                if isinstance(value, (str, int, float)):
                    parts.append(f"{key}: {value}")
                elif isinstance(value, list):
                    parts.append(f"{key}: {', '.join(str(item) for item in value[:3])}")
            return " | ".join(parts) if parts else json.dumps(v, indent=2)
        return str(v) if v is not None else ""

    @field_validator('market_size_validation', mode='before')
    @classmethod
    def normalize_market_size_validation(cls, v: Any) -> str:
        """Convert dict to string if needed."""
        if isinstance(v, dict):
            if 'description' in v:
                return str(v['description'])
            if 'claimed_size' in v:
                return f"Claimed size: {v.get('claimed_size', 'N/A')}. {v.get('validation', '')}"
            return json.dumps(v, indent=2)
        return str(v) if v is not None else ""

    @field_validator('competitive_landscape', mode='before')
    @classmethod
    def normalize_competitive_landscape(cls, v: Any) -> str:
        """Convert dict to string if needed."""
        if isinstance(v, dict):
            if 'description' in v:
                return str(v['description'])
            if 'direct_competitors' in v:
                competitors = v.get('direct_competitors', [])
                comp_list = ', '.join([c.get('name', str(c)) if isinstance(c, dict) else str(c) for c in competitors[:5]])
                return f"Direct competitors: {comp_list}. {v.get('analysis', '')}"
            return json.dumps(v, indent=2)
        return str(v) if v is not None else ""

    @field_validator('opportunities', mode='before')
    @classmethod
    def normalize_opportunities(cls, v: Any) -> List[str]:
        """Convert list of dicts to list of strings if needed."""
        if not v:
            return []
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, dict):
                    # Extract title and description if available
                    title = item.get('title', '')
                    desc = item.get('description', '')
                    timeframe = item.get('timeframe', '')
                    if title:
                        opp_str = title
                        if desc:
                            opp_str += f": {desc}"
                        if timeframe:
                            opp_str += f" (Timeframe: {timeframe})"
                        result.append(opp_str)
                    else:
                        # Fallback: convert dict to readable string
                        result.append(json.dumps(item, indent=2))
                else:
                    result.append(str(item))
            return result
        return [str(v)]

    @field_validator('threats', mode='before')
    @classmethod
    def normalize_threats(cls, v: Any) -> List[str]:
        """Convert list of dicts to list of strings if needed."""
        if not v:
            return []
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, dict):
                    # Extract title and description if available
                    title = item.get('title', '')
                    desc = item.get('description', '')
                    severity = item.get('severity', '')
                    if title:
                        threat_str = title
                        if desc:
                            threat_str += f": {desc}"
                        if severity:
                            threat_str += f" (Severity: {severity})"
                        result.append(threat_str)
                    else:
                        # Fallback: convert dict to readable string
                        result.append(json.dumps(item, indent=2))
                else:
                    result.append(str(item))
            return result
        return [str(v)]

    @field_validator('sources', mode='before')
    @classmethod
    def normalize_sources(cls, v: Any) -> List[str]:
        """Convert list of dicts to list of strings if needed."""
        if not v:
            return []
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, dict):
                    # Extract title and url if available
                    title = item.get('title', '')
                    url = item.get('url', '')
                    if title:
                        source_str = title
                        if url:
                            source_str += f" ({url})"
                        result.append(source_str)
                    elif url:
                        result.append(url)
                    else:
                        # Fallback: convert dict to readable string
                        result.append(json.dumps(item, indent=2))
                else:
                    result.append(str(item))
            return result
        return [str(v)]


# === Analysis Agent Output ===

class RiskItem(BaseModel):
    """Risk assessment item."""
    category: str = Field(default="", description="Risk category (market, operational, financial, etc.)")
    description: str = Field(default="", description="Risk description")
    severity: str = Field(default="medium", description="Severity level (low, medium, high, critical)")
    probability: str = Field(default="medium", description="Probability (low, medium, high)")
    mitigation: str = Field(default="", description="Mitigation strategy")


class EvaluationScore(BaseModel):
    """Evaluation score for a dimension."""
    dimension: str = Field(default="", description="Evaluation dimension")
    score: float = Field(ge=0.0, le=10.0, default=5.0, description="Score (0-10)")
    weight: float = Field(ge=0.0, le=1.0, default=0.1, description="Weight in overall score")
    justification: str = Field(default="", description="Justification for score")


class BusinessAnalysis(BaseModel):
    """Business analysis output from Analysis Agent."""
    executive_summary: str = Field(default="", description="Executive summary of analysis")
    evaluation_scores: List[EvaluationScore] = Field(default_factory=list, description="Scores across dimensions")
    overall_score: float = Field(ge=0.0, le=10.0, default=5.0, description="Weighted overall score")
    unit_economics_assessment: str = Field(default="", description="Unit economics viability assessment")
    key_assumptions: List[str] = Field(default_factory=list, description="Key assumptions identified")
    risks: List[RiskItem] = Field(default_factory=list, description="Identified risks")
    recommendations: List[str] = Field(default_factory=list, description="Strategic recommendations")
    confidence_score: float = Field(ge=0.0, le=100.0, default=70.0)


# === Financial Modeling Agent Output ===

class ScenarioProjection(BaseModel):
    """Financial projection for a scenario."""
    scenario_name: str = Field(default="base", description="Scenario name (optimistic, base, pessimistic)")
    assumptions: Dict[str, Any] = Field(default_factory=dict, description="Key assumptions")
    year1_revenue: float = 0.0
    year2_revenue: float = 0.0
    year3_revenue: float = 0.0
    year1_costs: float = 0.0
    year2_costs: float = 0.0
    year3_costs: float = 0.0
    year1_profit: float = 0.0
    year2_profit: float = 0.0
    year3_profit: float = 0.0


class UnitEconomics(BaseModel):
    """Unit economics calculations."""
    cac: Optional[float] = Field(None, description="Customer Acquisition Cost")
    ltv: Optional[float] = Field(None, description="Lifetime Value")
    ltv_cac_ratio: Optional[float] = Field(None, description="LTV:CAC ratio")
    payback_period_months: Optional[float] = Field(None, description="Payback period in months")
    contribution_margin: Optional[float] = Field(None, description="Contribution margin %")
    gross_margin: Optional[float] = Field(None, description="Gross margin %")


class FinancialModel(BaseModel):
    """Financial model output from Financial Modeling Agent."""
    scenarios: List[ScenarioProjection] = Field(default_factory=list, description="Scenario projections")
    unit_economics: UnitEconomics = Field(default_factory=UnitEconomics, description="Unit economics calculations")
    key_drivers: Dict[str, Any] = Field(default_factory=dict, description="Key financial drivers")
    sensitivity_analysis: Dict[str, Any] = Field(
        default_factory=dict,
        description="Sensitivity analysis results"
    )
    spreadsheet_path: Optional[str] = Field(None, description="Path to Excel spreadsheet")
    confidence_score: float = Field(ge=0.0, le=100.0, default=70.0)


# === Validation Agent Output ===

class ValidationIssue(BaseModel):
    """Validation issue found."""
    severity: str = Field(default="info", description="Issue severity (info, warning, error, critical)")
    category: str = Field(default="", description="Issue category")
    description: str = Field(default="", description="Issue description")
    location: str = Field(default="", description="Where the issue was found")
    recommendation: str = Field(default="", description="Recommendation to address")


class ValidationReport(BaseModel):
    """Validation report from Validation Agent."""
    overall_status: str = Field(default="passed", description="Overall validation status (passed, warning, failed)")
    confidence_score: float = Field(ge=0.0, le=100.0, default=70.0, description="Overall confidence score")
    issues: List[ValidationIssue] = Field(default_factory=list, description="Issues found")
    checks_performed: List[str] = Field(default_factory=list, description="List of validation checks performed")
    requires_human_review: bool = Field(default=False, description="Whether human review needed")
    human_review_reason: Optional[str] = Field(None, description="Reason for human review")
    validated_sections: Dict[str, float] = Field(
        default_factory=dict,
        description="Confidence scores by section"
    )


# === Synthesis Agent Output ===

class FinalReport(BaseModel):
    """Final report from Synthesis Agent."""
    submission_id: str = ""
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    executive_summary: str = Field(default="", description="Executive summary")
    recommendation: str = Field(default="", description="Overall recommendation")
    overall_score: float = Field(ge=0.0, le=10.0, default=5.0, description="Overall score")

    # Detailed sections
    market_analysis: str = Field(default="", description="Market analysis section")
    business_evaluation: str = Field(default="", description="Business evaluation section")
    financial_analysis: str = Field(default="", description="Financial analysis section")
    risk_assessment: str = Field(default="", description="Risk assessment section")

    # Supporting data
    key_findings: List[str] = Field(default_factory=list, description="Key findings")
    critical_assumptions: List[str] = Field(default_factory=list, description="Critical assumptions")
    next_steps: List[str] = Field(default_factory=list, description="Recommended next steps")

    # Attachments
    report_pdf_path: Optional[str] = Field(None, description="Path to PDF report")
    financial_model_path: Optional[str] = Field(None, description="Path to Excel model")
    dashboard_url: Optional[str] = Field(None, description="Interactive dashboard URL")

    # Audit trail
    sources: List[str] = Field(default_factory=list, description="All sources used")
    audit_trail: Dict[str, Any] = Field(default_factory=dict, description="Audit trail")


# === Workflow State ===

class WorkflowState(BaseModel):
    """Overall workflow state maintained by Orchestrator."""
    submission_id: str
    current_phase: WorkflowPhase
    started_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Data from each phase
    business_submission: Optional[BusinessSubmission] = None
    market_research: Optional[MarketResearch] = None
    business_analysis: Optional[BusinessAnalysis] = None
    financial_model: Optional[FinancialModel] = None
    validation_report: Optional[ValidationReport] = None
    final_report: Optional[FinalReport] = None

    # Workflow metadata
    phase_history: List[Dict[str, Any]] = Field(default_factory=list)
    requires_human_review: bool = False
    human_review_notes: Optional[str] = None

    # Status tracking
    is_complete: bool = False
    error_message: Optional[str] = None


# === Agent Response ===

class AgentResponse(BaseModel):
    """Standard response format from agents."""
    agent_type: AgentType
    success: bool
    message: str
    data: Optional[Any] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    next_phase: Optional[WorkflowPhase] = None
    requires_human_review: bool = False
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
