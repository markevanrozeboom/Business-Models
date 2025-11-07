"""Orchestrator Agent - Manages overall workflow and agent coordination."""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List

from .base import BaseAgent
from .intake import IntakeAgent
from .research import ResearchAgent
from .analysis import AnalysisAgent
from .financial import FinancialAgent
from .validation import ValidationAgent
from .synthesis import SynthesisAgent

from ..models.schemas import (
    AgentType,
    AgentResponse,
    WorkflowPhase,
    WorkflowState,
)
from ..utils.logger import get_logger


class OrchestratorAgent:
    """
    Orchestrator manages the overall workflow progression.
    Routes tasks to specialized agents and maintains workflow state.
    """

    def __init__(self):
        self.agent_type = AgentType.ORCHESTRATOR
        self.logger = get_logger("agent.orchestrator")

        # Initialize all specialized agents
        self.intake_agent = IntakeAgent()
        self.research_agent = ResearchAgent()
        self.analysis_agent = AnalysisAgent()
        self.financial_agent = FinancialAgent()
        self.validation_agent = ValidationAgent()
        self.synthesis_agent = SynthesisAgent()

    def create_workflow(self, initial_submission: str) -> WorkflowState:
        """
        Create a new workflow from initial business submission.

        Args:
            initial_submission: Initial business idea description

        Returns:
            WorkflowState initialized for processing
        """
        import uuid

        workflow_state = WorkflowState(
            submission_id=str(uuid.uuid4()),
            current_phase=WorkflowPhase.INTAKE,
            started_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.logger.info(
            "workflow_created",
            submission_id=workflow_state.submission_id,
        )

        return workflow_state

    def execute_workflow(self, initial_submission: str) -> WorkflowState:
        """
        Execute complete workflow from submission to final report.

        Args:
            initial_submission: Initial business idea description

        Returns:
            Completed WorkflowState with all results
        """
        try:
            self.logger.info("workflow_execution_started")

            # Create workflow
            workflow_state = self.create_workflow(initial_submission)

            # Phase 1: Intake
            workflow_state = self._execute_intake_phase(
                workflow_state, initial_submission
            )

            if not workflow_state.business_submission:
                workflow_state.error_message = "Intake phase failed"
                return workflow_state

            # Phase 2: Research & Analysis (parallel)
            workflow_state = self._execute_research_and_analysis_phase(workflow_state)

            # Phase 3: Financial Modeling
            workflow_state = self._execute_financial_modeling_phase(workflow_state)

            # Phase 4: Validation
            workflow_state = self._execute_validation_phase(workflow_state)

            # Check if human review is required
            if workflow_state.requires_human_review:
                workflow_state.current_phase = WorkflowPhase.HUMAN_REVIEW
                self.logger.warning(
                    "human_review_required",
                    submission_id=workflow_state.submission_id,
                )
                return workflow_state

            # Phase 5: Synthesis
            workflow_state = self._execute_synthesis_phase(workflow_state)

            # Mark as completed
            workflow_state.current_phase = WorkflowPhase.COMPLETED
            workflow_state.is_complete = True
            workflow_state.updated_at = datetime.utcnow()

            self.logger.info(
                "workflow_execution_completed",
                submission_id=workflow_state.submission_id,
                duration_seconds=(
                    workflow_state.updated_at - workflow_state.started_at
                ).total_seconds(),
            )

            return workflow_state

        except Exception as e:
            self.logger.error("workflow_execution_failed", error=str(e))
            workflow_state.error_message = f"Workflow failed: {str(e)}"
            return workflow_state

    def _execute_intake_phase(
        self, workflow_state: WorkflowState, initial_submission: str
    ) -> WorkflowState:
        """Execute Phase 1: Intake."""
        try:
            self.logger.info(
                "phase_started",
                phase=WorkflowPhase.INTAKE.value,
                submission_id=workflow_state.submission_id,
            )

            workflow_state.current_phase = WorkflowPhase.INTAKE
            workflow_state.updated_at = datetime.utcnow()

            # Process intake
            response = self.intake_agent.process({
                "initial_submission": initial_submission
            })

            # Always try to create BusinessSubmission if response is successful
            if response.success and response.data:
                try:
                    from ..models.schemas import BusinessSubmission, BusinessOverview, ValueProposition, MarketInfo, BusinessModelInfo, FinancialProjections, TeamInfo
                    
                    # Try to create with provided data, using defaults for missing fields
                    data = response.data.copy() if isinstance(response.data, dict) else {}
                    
                    # Ensure all nested objects have defaults
                    if "overview" not in data:
                        data["overview"] = {}
                    if "value_proposition" not in data:
                        data["value_proposition"] = {}
                    if "market" not in data:
                        data["market"] = {}
                    if "business_model" not in data:
                        data["business_model"] = {}
                    if "financials" not in data:
                        data["financials"] = {}
                    if "team" not in data:
                        data["team"] = {}
                    
                    workflow_state.business_submission = BusinessSubmission(**data)

                    # Log completeness score
                    completeness = workflow_state.business_submission.completeness_score
                    
                    self._record_phase_completion(
                        workflow_state,
                        WorkflowPhase.INTAKE,
                        response.confidence_score,
                    )

                    if completeness < 30.0:
                        self.logger.warning(
                            "intake_low_completeness",
                            phase=WorkflowPhase.INTAKE.value,
                            completeness_score=completeness,
                            message="Proceeding with low completeness - downstream agents will fill gaps",
                        )
                    else:
                        self.logger.info(
                            "phase_completed",
                            phase=WorkflowPhase.INTAKE.value,
                            completeness_score=completeness,
                        )
                except Exception as e:
                    self.logger.error(
                        "intake_submission_creation_failed",
                        error=str(e),
                        response_data_keys=list(response.data.keys()) if isinstance(response.data, dict) else None,
                    )
                    # Try to create minimal submission as fallback
                    try:
                        from ..models.schemas import BusinessSubmission, BusinessOverview, ValueProposition, MarketInfo, BusinessModelInfo, FinancialProjections, TeamInfo
                        import uuid
                        
                        minimal_submission = BusinessSubmission(
                            submission_id=str(uuid.uuid4()),
                            overview=BusinessOverview(),
                            value_proposition=ValueProposition(),
                            market=MarketInfo(),
                            business_model=BusinessModelInfo(),
                            financials=FinancialProjections(),
                            team=TeamInfo(),
                            completeness_score=10.0,
                        )
                        workflow_state.business_submission = minimal_submission
                        self.logger.warning(
                            "intake_fallback_created",
                            message="Created minimal submission as fallback",
                        )
                    except Exception as fallback_error:
                        self.logger.error(
                            "intake_fallback_failed",
                            error=str(fallback_error),
                        )
                        workflow_state.error_message = f"Failed to create BusinessSubmission: {str(e)}"
            else:
                self.logger.error(
                    "intake_failed",
                    success=response.success,
                    message=response.message,
                    errors=response.errors,
                )
                workflow_state.error_message = f"Intake phase failed: {response.message}"

            return workflow_state

        except Exception as e:
            self.logger.error("intake_phase_failed", error=str(e))
            workflow_state.error_message = f"Intake phase failed: {str(e)}"
            return workflow_state

    def _execute_research_and_analysis_phase(
        self, workflow_state: WorkflowState
    ) -> WorkflowState:
        """Execute Phase 2: Research & Analysis (parallel)."""
        try:
            self.logger.info(
                "phase_started",
                phase="research_and_analysis",
                submission_id=workflow_state.submission_id,
            )

            workflow_state.current_phase = WorkflowPhase.RESEARCH
            workflow_state.updated_at = datetime.utcnow()

            # Run research and analysis in parallel
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            research_response, analysis_response = loop.run_until_complete(
                self._run_research_and_analysis_parallel(workflow_state)
            )

            loop.close()

            # Process research results with quality gate
            if research_response.success and research_response.data:
                from ..models.schemas import MarketResearch
                try:
                    market_research = MarketResearch(**research_response.data)
                    
                    # Quality gate: Check if output meets minimum standards
                    quality_check = self._check_output_quality(
                        market_research.model_dump(),
                        phase="research",
                        min_confidence=50.0,  # Minimum confidence threshold
                        required_fields=["market_overview", "competitive_landscape"],
                        min_required_fields=1,  # At least 1 of 2 required
                    )
                    
                    if quality_check["passed"]:
                        workflow_state.market_research = market_research
                        self._record_phase_completion(
                            workflow_state,
                            WorkflowPhase.RESEARCH,
                            research_response.confidence_score,
                        )
                        self.logger.info(
                            "phase_completed",
                            phase=WorkflowPhase.RESEARCH.value,
                            confidence=research_response.confidence_score,
                        )
                    else:
                        # Soft failure - log warning but continue
                        self.logger.warning(
                            "research_quality_gate_failed",
                            reasons=quality_check["reasons"],
                            confidence=research_response.confidence_score,
                            message="Continuing with low-quality research output",
                        )
                        workflow_state.market_research = market_research  # Still use it
                        self._record_phase_completion(
                            workflow_state,
                            WorkflowPhase.RESEARCH,
                            research_response.confidence_score,
                        )
                except Exception as e:
                    self.logger.error(
                        "research_creation_failed",
                        error=str(e),
                    )
                    # Continue without research

            # Process analysis results with quality gate
            if analysis_response.success and analysis_response.data:
                from ..models.schemas import BusinessAnalysis
                try:
                    business_analysis = BusinessAnalysis(**analysis_response.data)
                    
                    # Quality gate: Check if output meets minimum standards
                    quality_check = self._check_output_quality(
                        business_analysis.model_dump(),
                        phase="analysis",
                        min_confidence=50.0,
                        required_fields=["executive_summary", "evaluation_scores", "risks"],
                        min_required_fields=2,  # At least 2 of 3 required
                    )
                    
                    if quality_check["passed"]:
                        workflow_state.business_analysis = business_analysis
                        self._record_phase_completion(
                            workflow_state,
                            WorkflowPhase.ANALYSIS,
                            analysis_response.confidence_score,
                        )
                        self.logger.info(
                            "phase_completed",
                            phase=WorkflowPhase.ANALYSIS.value,
                            confidence=analysis_response.confidence_score,
                        )
                    else:
                        # Soft failure - log warning but continue
                        self.logger.warning(
                            "analysis_quality_gate_failed",
                            reasons=quality_check["reasons"],
                            confidence=analysis_response.confidence_score,
                            message="Continuing with low-quality analysis output",
                        )
                        workflow_state.business_analysis = business_analysis  # Still use it
                        self._record_phase_completion(
                            workflow_state,
                            WorkflowPhase.ANALYSIS,
                            analysis_response.confidence_score,
                        )
                except Exception as e:
                    self.logger.error(
                        "analysis_creation_failed",
                        error=str(e),
                    )
                    # Continue without analysis

            return workflow_state

        except Exception as e:
            self.logger.error("research_analysis_phase_failed", error=str(e))
            workflow_state.error_message = f"Research/Analysis phase failed: {str(e)}"
            return workflow_state

    async def _run_research_and_analysis_parallel(
        self, workflow_state: WorkflowState
    ) -> tuple:
        """Run research and analysis agents in parallel."""
        submission_data = workflow_state.business_submission.model_dump()

        # Create tasks
        research_task = asyncio.create_task(
            self._async_agent_process(
                self.research_agent,
                {"business_submission": submission_data}
            )
        )

        analysis_task = asyncio.create_task(
            self._async_agent_process(
                self.analysis_agent,
                {"business_submission": submission_data}
            )
        )

        # Wait for both to complete
        research_response, analysis_response = await asyncio.gather(
            research_task, analysis_task
        )

        return research_response, analysis_response

    async def _async_agent_process(self, agent, input_data: Dict[str, Any]) -> AgentResponse:
        """Run agent process asynchronously."""
        return await asyncio.to_thread(agent.process, input_data)

    def _execute_financial_modeling_phase(
        self, workflow_state: WorkflowState
    ) -> WorkflowState:
        """Execute Phase 3: Financial Modeling."""
        try:
            self.logger.info(
                "phase_started",
                phase=WorkflowPhase.FINANCIAL_MODELING.value,
                submission_id=workflow_state.submission_id,
            )

            workflow_state.current_phase = WorkflowPhase.FINANCIAL_MODELING
            workflow_state.updated_at = datetime.utcnow()

            input_data = {
                "business_submission": workflow_state.business_submission.model_dump(),
            }

            if workflow_state.market_research:
                input_data["market_research"] = workflow_state.market_research.model_dump()

            response = self.financial_agent.process(input_data)

            if response.success and response.data:
                from ..models.schemas import FinancialModel
                try:
                    financial_model = FinancialModel(**response.data)
                    
                    # Quality gate: Check if output meets minimum standards
                    quality_check = self._check_output_quality(
                        financial_model.model_dump(),
                        phase="financial",
                        min_confidence=50.0,
                        required_fields=["scenarios", "unit_economics"],
                        min_required_fields=1,  # At least 1 of 2 required
                    )
                    
                    # Also check for validation warnings from financial agent
                    has_warnings = len(response.warnings) > 0
                    
                    if quality_check["passed"] and not has_warnings:
                        workflow_state.financial_model = financial_model
                        self._record_phase_completion(
                            workflow_state,
                            WorkflowPhase.FINANCIAL_MODELING,
                            response.confidence_score,
                        )
                        self.logger.info(
                            "phase_completed",
                            phase=WorkflowPhase.FINANCIAL_MODELING.value,
                            confidence=response.confidence_score,
                        )
                    else:
                        # Soft failure - log warning but continue
                        reasons = quality_check.get("reasons", [])
                        if has_warnings:
                            reasons.extend(response.warnings)
                        self.logger.warning(
                            "financial_quality_gate_failed",
                            reasons=reasons,
                            confidence=response.confidence_score,
                            message="Continuing with financial model (may have validation warnings)",
                        )
                        workflow_state.financial_model = financial_model  # Still use it
                        self._record_phase_completion(
                            workflow_state,
                            WorkflowPhase.FINANCIAL_MODELING,
                            response.confidence_score,
                        )
                except Exception as e:
                    self.logger.error(
                        "financial_creation_failed",
                        error=str(e),
                    )
                    # Continue without financial model

            return workflow_state

        except Exception as e:
            self.logger.error("financial_modeling_phase_failed", error=str(e))
            workflow_state.error_message = f"Financial modeling phase failed: {str(e)}"
            return workflow_state

    def _execute_validation_phase(
        self, workflow_state: WorkflowState
    ) -> WorkflowState:
        """Execute Phase 4: Validation."""
        try:
            self.logger.info(
                "phase_started",
                phase=WorkflowPhase.VALIDATION.value,
                submission_id=workflow_state.submission_id,
            )

            workflow_state.current_phase = WorkflowPhase.VALIDATION
            workflow_state.updated_at = datetime.utcnow()

            input_data = {
                "business_submission": workflow_state.business_submission.model_dump(),
            }

            if workflow_state.market_research:
                input_data["market_research"] = workflow_state.market_research.model_dump()

            if workflow_state.business_analysis:
                input_data["business_analysis"] = workflow_state.business_analysis.model_dump()

            if workflow_state.financial_model:
                input_data["financial_model"] = workflow_state.financial_model.model_dump()

            response = self.validation_agent.process(input_data)

            if response.success and response.data:
                from ..models.schemas import ValidationReport
                workflow_state.validation_report = ValidationReport(**response.data)

                # Check if human review is required
                workflow_state.requires_human_review = (
                    workflow_state.validation_report.requires_human_review
                )

                self._record_phase_completion(
                    workflow_state,
                    WorkflowPhase.VALIDATION,
                    response.confidence_score,
                )

                self.logger.info(
                    "phase_completed",
                    phase=WorkflowPhase.VALIDATION.value,
                    requires_human_review=workflow_state.requires_human_review,
                )

            return workflow_state

        except Exception as e:
            self.logger.error("validation_phase_failed", error=str(e))
            workflow_state.error_message = f"Validation phase failed: {str(e)}"
            return workflow_state

    def _execute_synthesis_phase(
        self, workflow_state: WorkflowState
    ) -> WorkflowState:
        """Execute Phase 5: Synthesis."""
        try:
            self.logger.info(
                "phase_started",
                phase=WorkflowPhase.SYNTHESIS.value,
                submission_id=workflow_state.submission_id,
            )

            workflow_state.current_phase = WorkflowPhase.SYNTHESIS
            workflow_state.updated_at = datetime.utcnow()

            input_data = {
                "business_submission": workflow_state.business_submission.model_dump(),
            }

            if workflow_state.market_research:
                input_data["market_research"] = workflow_state.market_research.model_dump()

            if workflow_state.business_analysis:
                input_data["business_analysis"] = workflow_state.business_analysis.model_dump()

            if workflow_state.financial_model:
                input_data["financial_model"] = workflow_state.financial_model.model_dump()

            if workflow_state.validation_report:
                input_data["validation_report"] = workflow_state.validation_report.model_dump()

            response = self.synthesis_agent.process(input_data)

            if response.success and response.data:
                from ..models.schemas import FinalReport
                workflow_state.final_report = FinalReport(**response.data)

                self._record_phase_completion(
                    workflow_state,
                    WorkflowPhase.SYNTHESIS,
                    response.confidence_score,
                )

                self.logger.info(
                    "phase_completed",
                    phase=WorkflowPhase.SYNTHESIS.value,
                )

            return workflow_state

        except Exception as e:
            self.logger.error("synthesis_phase_failed", error=str(e))
            workflow_state.error_message = f"Synthesis phase failed: {str(e)}"
            return workflow_state

    def _check_output_quality(
        self,
        data: Dict[str, Any],
        phase: str,
        min_confidence: float = 50.0,
        required_fields: Optional[List[str]] = None,
        min_required_fields: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Check if agent output meets quality standards.
        
        Args:
            data: Output data to validate
            phase: Phase name for logging
            min_confidence: Minimum confidence score threshold
            required_fields: List of required field paths
            min_required_fields: Minimum number of required fields that must be populated
            
        Returns:
            Dict with 'passed' (bool) and 'reasons' (list of strings)
        """
        reasons = []
        
        # Check confidence score if present
        if "confidence_score" in data:
            confidence = data.get("confidence_score", 0.0)
            if confidence < min_confidence:
                reasons.append(f"Confidence score {confidence:.1f}% below minimum {min_confidence:.1f}%")
        
        # Check required fields if specified
        if required_fields:
            missing = []
            for field in required_fields:
                parts = field.split(".")
                value = data
                for part in parts:
                    if isinstance(value, dict):
                        value = value.get(part)
                    else:
                        value = None
                        break
                
                is_empty = (
                    value is None or
                    value == "" or
                    (isinstance(value, list) and len(value) == 0) or
                    (isinstance(value, dict) and len(value) == 0)
                )
                
                if is_empty:
                    missing.append(field)
            
            if min_required_fields is not None:
                if len(missing) > (len(required_fields) - min_required_fields):
                    reasons.append(f"Too many missing fields: {missing}")
            elif len(missing) > 0:
                reasons.append(f"Missing required fields: {missing}")
        
        passed = len(reasons) == 0
        
        return {
            "passed": passed,
            "reasons": reasons,
        }

    def _record_phase_completion(
        self,
        workflow_state: WorkflowState,
        phase: WorkflowPhase,
        confidence_score: Optional[float],
    ):
        """Record phase completion in workflow history."""
        workflow_state.phase_history.append({
            "phase": phase.value,
            "completed_at": datetime.utcnow().isoformat(),
            "confidence_score": confidence_score,
        })
