#!/usr/bin/env python3
"""Continue evaluation after human review."""

import json
import sys
from pathlib import Path
from datetime import datetime

from src.agents.orchestrator import OrchestratorAgent
from src.models.schemas import WorkflowState, WorkflowPhase
from src.utils.logger import get_logger

logger = get_logger(__name__)


def continue_evaluation(workflow_file: str):
    """Continue evaluation from saved workflow state."""
    
    # Load the workflow state
    with open(workflow_file, 'r') as f:
        workflow_data = json.load(f)
    
    # Convert to WorkflowState object
    workflow_state = WorkflowState(**workflow_data)
    
    logger.info(
        "continuing_evaluation",
        submission_id=workflow_state.submission_id,
        current_phase=workflow_state.current_phase.value,
        completeness=workflow_state.business_submission.completeness_score,
    )
    
    # Override human review requirement
    workflow_state.requires_human_review = False
    workflow_state.updated_at = datetime.utcnow()
    
    # Initialize orchestrator
    orchestrator = OrchestratorAgent()
    
    # Determine what phases are already complete
    has_research = workflow_state.market_research is not None
    has_analysis = workflow_state.business_analysis is not None
    has_financial = workflow_state.financial_model is not None
    has_validation = workflow_state.validation_report is not None
    
    logger.info(
        "phase_status",
        has_research=has_research,
        has_analysis=has_analysis,
        has_financial=has_financial,
        has_validation=has_validation,
    )
    
    # Continue from where we left off
    try:
        # Phase 2: Research & Analysis (only if missing)
        if not has_research or not has_analysis:
            logger.info("running_research_and_analysis")
            workflow_state = orchestrator._execute_research_and_analysis_phase(workflow_state)
        
        # Phase 3: Financial Modeling (only if missing)
        if not has_financial:
            logger.info("running_financial_modeling")
            workflow_state = orchestrator._execute_financial_modeling_phase(workflow_state)
        
        # Phase 4: Validation (only if missing)
        if not has_validation:
            logger.info("running_validation")
            workflow_state = orchestrator._execute_validation_phase(workflow_state)
            workflow_state.requires_human_review = False  # Override
        
        # Phase 5: Synthesis (always run this to generate final report)
        logger.info("running_synthesis")
        workflow_state = orchestrator._execute_synthesis_phase(workflow_state)
        
        # Mark as completed
        workflow_state.current_phase = WorkflowPhase.COMPLETED
        workflow_state.is_complete = True
        workflow_state.updated_at = datetime.utcnow()
        
        # Save final state
        import os
        from src.utils.config import settings
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"workflow_{workflow_state.submission_id}_{timestamp}.json"
        filepath = os.path.join(settings.output_dir, filename)
        
        # Convert to dict for JSON serialization
        state_dict = workflow_state.model_dump()
        
        with open(filepath, "w") as f:
            json.dump(state_dict, f, indent=2, default=str)
        
        logger.info(
            "workflow_state_saved",
            filepath=filepath,
            submission_id=workflow_state.submission_id,
        )
        
        duration = (workflow_state.updated_at - workflow_state.started_at).total_seconds()
        
        logger.info(
            "evaluation_completed",
            submission_id=workflow_state.submission_id,
            total_duration_seconds=duration,
        )
        
        # Print summary
        print("\n" + "="*80)
        print("EVALUATION COMPLETED SUCCESSFULLY")
        print("="*80)
        print(f"\nBusiness: {workflow_state.business_submission.overview.name}")
        print(f"Industry: {workflow_state.business_submission.overview.industry}")
        print(f"Total Duration: {duration:.1f} seconds")
        print(f"\nValidation Status: {workflow_state.validation_report.overall_status}")
        print(f"Confidence Score: {workflow_state.validation_report.confidence_score}%")
        
        if workflow_state.final_report:
            print(f"\n{workflow_state.final_report.executive_summary}")
        
        print(f"\n📁 Outputs saved to: ./outputs/")
        print(f"📊 Financial model: ./models/")
        
        return workflow_state
        
    except Exception as e:
        logger.error("continuation_failed", error=str(e))
        raise


if __name__ == "__main__":
    if len(sys.argv) > 1:
        workflow_file = sys.argv[1]
    else:
        # Find the most recent workflow file
        outputs_dir = Path("./outputs")
        workflow_files = list(outputs_dir.glob("workflow_*.json"))
        if not workflow_files:
            print("❌ No workflow files found in ./outputs/")
            sys.exit(1)
        
        workflow_file = str(max(workflow_files, key=lambda p: p.stat().st_mtime))
        print(f"📂 Using most recent workflow: {workflow_file}")
    
    continue_evaluation(workflow_file)
