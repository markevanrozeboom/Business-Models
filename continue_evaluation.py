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
    workflow_state.current_phase = WorkflowPhase.RESEARCH
    workflow_state.updated_at = datetime.utcnow()
    
    # Initialize orchestrator
    orchestrator = OrchestratorAgent()
    
    # Continue from research phase
    try:
        # Phase 2: Research & Analysis (parallel)
        workflow_state = orchestrator._execute_research_and_analysis_phase(workflow_state)
        
        # Phase 3: Financial Modeling
        workflow_state = orchestrator._execute_financial_modeling_phase(workflow_state)
        
        # Phase 4: Validation (skip human review this time)
        workflow_state = orchestrator._execute_validation_phase(workflow_state)
        workflow_state.requires_human_review = False  # Override again if needed
        
        # Phase 5: Synthesis
        workflow_state = orchestrator._execute_synthesis_phase(workflow_state)
        
        # Mark as completed
        workflow_state.current_phase = WorkflowPhase.COMPLETED
        workflow_state.is_complete = True
        workflow_state.updated_at = datetime.utcnow()
        
        # Save final state
        orchestrator._save_workflow_state(workflow_state)
        
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
