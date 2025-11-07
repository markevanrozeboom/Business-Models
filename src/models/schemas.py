"""Pydantic models for data validation and serialization."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
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
    name: str = Field(description="Business name")
    industry: str = Field(description="Industry/sector")
    stage: str = Field(description="Business stage (idea, MVP, early-stage, growth)")
    problem: str = Field(description="Problem being solved")
    solution: str = Field(description="Proposed solution")


class ValueProposition(BaseModel):
    """Value proposition details."""
    unique_value: str = Field(description="Unique value proposition")
    differentiators: List[str] = Field(description="Key differentiators from competitors")
    target_customer: str = Field(description="Target customer description")


class MarketInfo(BaseModel):
    """Market and customer information."""
    target_segments: List[str] = Field(description="Target market segments")
    market_size: Optional[str] = Field(None, description="Market size description")
    tam: Optional[float] = Field(None, description="Total Addressable Market (TAM) in $")
    sam: Optional[float] = Field(None, description="Serviceable Addressable Market (SAM) in $")
    som: Optional[float] = Field(None, description="Serviceable Obtainable Market (SOM) in $")
    geography: List[str] = Field(default_factory=list, description="Geographic markets")


class BusinessModelInfo(BaseModel):
    """Business model details."""
    revenue_model: str = Field(description="Revenue model (subscription, transaction, etc.)")
    pricing: str = Field(description="Pricing structure")
    cost_structure: str = Field(description="Key cost drivers")
    distribution_channels: List[str] = Field(description="Distribution channels")


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
    team_size: int = Field(description="Current team size")
    key_roles: List[str] = Field(description="Key team roles filled")
    relevant_experience: str = Field(description="Team's relevant experience")
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
    market_overview: str = Field(description="Market overview and trends")
    market_size_validation: str = Field(description="Market size validation")
    competitive_landscape: str = Field(description="Competitive landscape analysis")
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


# === Analysis Agent Output ===

class RiskItem(BaseModel):
    """Risk assessment item."""
    category: str = Field(description="Risk category (market, operational, financial, etc.)")
    description: str = Field(description="Risk description")
    severity: str = Field(description="Severity level (low, medium, high, critical)")
    probability: str = Field(description="Probability (low, medium, high)")
    mitigation: str = Field(description="Mitigation strategy")


class EvaluationScore(BaseModel):
    """Evaluation score for a dimension."""
    dimension: str = Field(description="Evaluation dimension")
    score: float = Field(ge=0.0, le=10.0, description="Score (0-10)")
    weight: float = Field(ge=0.0, le=1.0, description="Weight in overall score")
    justification: str = Field(description="Justification for score")


class BusinessAnalysis(BaseModel):
    """Business analysis output from Analysis Agent."""
    executive_summary: str = Field(description="Executive summary of analysis")
    evaluation_scores: List[EvaluationScore] = Field(description="Scores across dimensions")
    overall_score: float = Field(ge=0.0, le=10.0, description="Weighted overall score")
    unit_economics_assessment: str = Field(description="Unit economics viability assessment")
    key_assumptions: List[str] = Field(description="Key assumptions identified")
    risks: List[RiskItem] = Field(description="Identified risks")
    recommendations: List[str] = Field(description="Strategic recommendations")
    confidence_score: float = Field(ge=0.0, le=100.0, default=70.0)


# === Financial Modeling Agent Output ===

class ScenarioProjection(BaseModel):
    """Financial projection for a scenario."""
    scenario_name: str = Field(description="Scenario name (optimistic, base, pessimistic)")
    assumptions: Dict[str, Any] = Field(description="Key assumptions")
    year1_revenue: float
    year2_revenue: float
    year3_revenue: float
    year1_costs: float
    year2_costs: float
    year3_costs: float
    year1_profit: float
    year2_profit: float
    year3_profit: float


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
    scenarios: List[ScenarioProjection] = Field(description="Scenario projections")
    unit_economics: UnitEconomics = Field(description="Unit economics calculations")
    key_drivers: Dict[str, Any] = Field(description="Key financial drivers")
    sensitivity_analysis: Dict[str, Any] = Field(
        default_factory=dict,
        description="Sensitivity analysis results"
    )
    spreadsheet_path: Optional[str] = Field(None, description="Path to Excel spreadsheet")
    confidence_score: float = Field(ge=0.0, le=100.0, default=70.0)


# === Validation Agent Output ===

class ValidationIssue(BaseModel):
    """Validation issue found."""
    severity: str = Field(description="Issue severity (info, warning, error, critical)")
    category: str = Field(description="Issue category")
    description: str = Field(description="Issue description")
    location: str = Field(description="Where the issue was found")
    recommendation: str = Field(description="Recommendation to address")


class ValidationReport(BaseModel):
    """Validation report from Validation Agent."""
    overall_status: str = Field(description="Overall validation status (passed, warning, failed)")
    confidence_score: float = Field(ge=0.0, le=100.0, description="Overall confidence score")
    issues: List[ValidationIssue] = Field(default_factory=list, description="Issues found")
    checks_performed: List[str] = Field(description="List of validation checks performed")
    requires_human_review: bool = Field(default=False, description="Whether human review needed")
    human_review_reason: Optional[str] = Field(None, description="Reason for human review")
    validated_sections: Dict[str, float] = Field(
        default_factory=dict,
        description="Confidence scores by section"
    )


# === Synthesis Agent Output ===

class FinalReport(BaseModel):
    """Final report from Synthesis Agent."""
    submission_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    executive_summary: str = Field(description="Executive summary")
    recommendation: str = Field(description="Overall recommendation")
    overall_score: float = Field(ge=0.0, le=10.0, description="Overall score")

    # Detailed sections
    market_analysis: str = Field(description="Market analysis section")
    business_evaluation: str = Field(description="Business evaluation section")
    financial_analysis: str = Field(description="Financial analysis section")
    risk_assessment: str = Field(description="Risk assessment section")

    # Supporting data
    key_findings: List[str] = Field(description="Key findings")
    critical_assumptions: List[str] = Field(description="Critical assumptions")
    next_steps: List[str] = Field(description="Recommended next steps")

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
