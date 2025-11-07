"""Main workflow runner for the Business Evaluation System."""

import json
import os
from datetime import datetime
from typing import Optional

from .agents.orchestrator import OrchestratorAgent
from .models.schemas import WorkflowState, WorkflowPhase
from .utils.config import settings
from .utils.logger import setup_logger, get_logger


class BusinessEvaluationWorkflow:
    """
    Main workflow class for business evaluation.
    Provides high-level interface for running evaluations.
    """

    def __init__(self):
        """Initialize the workflow."""
        setup_logger()
        self.logger = get_logger("workflow")
        self.orchestrator = OrchestratorAgent()

        # Ensure output directories exist
        os.makedirs(settings.output_dir, exist_ok=True)
        os.makedirs(settings.reports_dir, exist_ok=True)
        os.makedirs(settings.models_dir, exist_ok=True)

    def evaluate_business(
        self,
        business_description: str,
        save_results: bool = True,
    ) -> WorkflowState:
        """
        Evaluate a business idea end-to-end.

        Args:
            business_description: Initial business idea description
            save_results: Whether to save results to disk

        Returns:
            WorkflowState with all evaluation results
        """
        try:
            self.logger.info(
                "evaluation_started",
                description_length=len(business_description),
            )

            # Execute workflow
            workflow_state = self.orchestrator.execute_workflow(business_description)

            # Save results if requested
            if save_results:
                self._save_workflow_state(workflow_state)

            # Log completion
            if workflow_state.is_complete:
                self.logger.info(
                    "evaluation_completed",
                    submission_id=workflow_state.submission_id,
                    overall_score=workflow_state.final_report.overall_score if workflow_state.final_report else None,
                )
            elif workflow_state.requires_human_review:
                self.logger.warning(
                    "evaluation_requires_human_review",
                    submission_id=workflow_state.submission_id,
                    current_phase=workflow_state.current_phase.value,
                )
            else:
                self.logger.error(
                    "evaluation_incomplete",
                    submission_id=workflow_state.submission_id,
                    error=workflow_state.error_message,
                )

            return workflow_state

        except Exception as e:
            self.logger.error("evaluation_failed", error=str(e))
            raise

    def get_workflow_summary(self, workflow_state: WorkflowState) -> dict:
        """
        Get a summary of workflow results.

        Args:
            workflow_state: Completed workflow state

        Returns:
            Summary dictionary
        """
        summary = {
            "submission_id": workflow_state.submission_id,
            "status": "completed" if workflow_state.is_complete else "incomplete",
            "current_phase": workflow_state.current_phase.value,
            "requires_human_review": workflow_state.requires_human_review,
            "duration_seconds": (
                workflow_state.updated_at - workflow_state.started_at
            ).total_seconds(),
        }

        if workflow_state.business_submission:
            summary["business_name"] = workflow_state.business_submission.overview.name
            summary["completeness_score"] = workflow_state.business_submission.completeness_score

        if workflow_state.business_analysis:
            summary["overall_score"] = workflow_state.business_analysis.overall_score
            summary["num_risks"] = len(workflow_state.business_analysis.risks)

        if workflow_state.validation_report:
            summary["validation_status"] = workflow_state.validation_report.overall_status
            summary["validation_confidence"] = workflow_state.validation_report.confidence_score

        if workflow_state.final_report:
            summary["recommendation"] = workflow_state.final_report.recommendation
            summary["report_generated"] = True
            summary["financial_model_path"] = workflow_state.final_report.financial_model_path

        if workflow_state.error_message:
            summary["error"] = workflow_state.error_message

        return summary

    def _save_workflow_state(self, workflow_state: WorkflowState):
        """Save workflow state to disk."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"workflow_{workflow_state.submission_id}_{timestamp}.json"
            filepath = os.path.join(settings.output_dir, filename)

            # Convert to dict for JSON serialization
            state_dict = workflow_state.model_dump()

            with open(filepath, "w") as f:
                json.dump(state_dict, f, indent=2, default=str)

            self.logger.info(
                "workflow_state_saved",
                filepath=filepath,
                submission_id=workflow_state.submission_id,
            )

        except Exception as e:
            self.logger.error("workflow_state_save_failed", error=str(e))

    def print_summary(self, workflow_state: WorkflowState):
        """Print a human-readable summary of the workflow results."""
        print("\n" + "=" * 80)
        print("BUSINESS EVALUATION SUMMARY")
        print("=" * 80)

        if workflow_state.business_submission:
            print(f"\nBusiness: {workflow_state.business_submission.overview.name}")
            print(f"Industry: {workflow_state.business_submission.overview.industry}")
            print(f"Stage: {workflow_state.business_submission.overview.stage}")

        print(f"\nStatus: {workflow_state.current_phase.value.upper()}")
        print(f"Completed: {workflow_state.is_complete}")
        print(f"Requires Human Review: {workflow_state.requires_human_review}")

        if workflow_state.business_analysis:
            print(f"\n--- EVALUATION RESULTS ---")
            print(f"Overall Score: {workflow_state.business_analysis.overall_score}/10")
            print(f"\nTop Evaluation Scores:")
            for score in workflow_state.business_analysis.evaluation_scores[:5]:
                print(f"  - {score.dimension}: {score.score}/10")

        if workflow_state.financial_model:
            print(f"\n--- FINANCIAL MODEL ---")
            ue = workflow_state.financial_model.unit_economics
            if ue.cac:
                print(f"CAC: ${ue.cac:,.0f}")
            if ue.ltv:
                print(f"LTV: ${ue.ltv:,.0f}")
            if ue.ltv_cac_ratio:
                print(f"LTV:CAC Ratio: {ue.ltv_cac_ratio:.1f}x")

            if workflow_state.financial_model.scenarios:
                base_scenario = next(
                    (s for s in workflow_state.financial_model.scenarios
                     if "base" in s.scenario_name.lower()),
                    workflow_state.financial_model.scenarios[0]
                )
                print(f"\nBase Case Projections:")
                print(f"  Year 3 Revenue: ${base_scenario.year3_revenue:,.0f}")
                print(f"  Year 3 Profit: ${base_scenario.year3_profit:,.0f}")

        if workflow_state.validation_report:
            print(f"\n--- VALIDATION ---")
            print(f"Status: {workflow_state.validation_report.overall_status.upper()}")
            print(f"Confidence: {workflow_state.validation_report.confidence_score:.0f}%")
            print(f"Issues Found: {len(workflow_state.validation_report.issues)}")

        if workflow_state.final_report:
            print(f"\n--- FINAL RECOMMENDATION ---")
            print(f"Recommendation: {workflow_state.final_report.recommendation}")
            print(f"\nKey Findings:")
            for finding in workflow_state.final_report.key_findings[:5]:
                print(f"  - {finding}")

            if workflow_state.final_report.financial_model_path:
                print(f"\nFinancial Model: {workflow_state.final_report.financial_model_path}")

        duration = (workflow_state.updated_at - workflow_state.started_at).total_seconds()
        print(f"\nTotal Duration: {duration:.1f} seconds")

        print("\n" + "=" * 80)


def main():
    """Main entry point for running the workflow."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.workflow <business_description>")
        print("\nOr provide business description as a file:")
        print("python -m src.workflow --file <path_to_file>")
        sys.exit(1)

    # Get business description
    if sys.argv[1] == "--file":
        if len(sys.argv) < 3:
            print("Error: Please provide a file path")
            sys.exit(1)
        with open(sys.argv[2], "r") as f:
            business_description = f.read()
    else:
        business_description = " ".join(sys.argv[1:])

    # Run workflow
    workflow = BusinessEvaluationWorkflow()
    result = workflow.evaluate_business(business_description)

    # Print summary
    workflow.print_summary(result)

    # Exit with appropriate code
    if result.is_complete:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
