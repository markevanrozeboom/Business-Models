#!/usr/bin/env python3
"""
Google Forms Monitor Script

This script monitors a Google Form for new business evaluation submissions and
processes them through the evaluation workflow. It can also send follow-up
questions via email when more information is needed.

Setup:
1. Create a Google Form for business evaluations (see template in script)
2. Enable Google Forms API and Gmail API in Google Cloud Console
3. Download OAuth 2.0 credentials as 'credentials.json'
4. Place credentials.json in the project root directory
5. Get your Form ID from the form URL (between /d/ and /edit)
6. Run this script with --form-id parameter
7. The script will open a browser for OAuth authentication on first run
"""

import os
import sys
import time
import json
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.integrations.google_forms_integration import GoogleFormsIntegration
from src.integrations.gmail_integration import GmailIntegration
from src.integrations.email_questioner import EmailQuestioner
from src.workflow import BusinessEvaluationWorkflow
from src.utils.logger import setup_logger, get_logger


# Standard question mapping for business evaluation form
STANDARD_QUESTION_MAPPING = {
    'business_name': 'Business Name',
    'email': 'Email Address',
    'industry': 'Industry/Sector',
    'stage': 'Business Stage',
    'problem': 'Problem Statement',
    'solution': 'Solution Description',
    'target_customer': 'Target Customer',
    'value_prop': 'Unique Value Proposition',
    'market_size': 'Market Size (TAM/SAM/SOM)',
    'revenue_model': 'Revenue Model',
    'pricing': 'Pricing Strategy',
    'financials': 'Financial Projections',
    'team': 'Team Background',
    'traction': 'Current Traction',
    'funding': 'Funding Sought',
    'additional': 'Additional Information'
}


def main():
    """Main function to run Google Forms monitoring."""
    parser = argparse.ArgumentParser(
        description='Monitor Google Form for business evaluation submissions'
    )
    parser.add_argument(
        '--form-id',
        required=True,
        help='Google Form ID (from form URL between /d/ and /edit)'
    )
    parser.add_argument(
        '--credentials',
        default='credentials.json',
        help='Path to Google API credentials file (default: credentials.json)'
    )
    parser.add_argument(
        '--token',
        default='token_forms.pickle',
        help='Path to save/load authentication token (default: token_forms.pickle)'
    )
    parser.add_argument(
        '--processed-file',
        default='processed_responses.json',
        help='File to track processed response IDs (default: processed_responses.json)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Check interval in seconds (default: 300 = 5 minutes)'
    )
    parser.add_argument(
        '--single-run',
        action='store_true',
        help='Run once and exit (default: continuous monitoring)'
    )
    parser.add_argument(
        '--show-form-template',
        action='store_true',
        help='Show Google Form template and exit'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logger()
    logger = get_logger("forms_monitor")
    
    # Show form template if requested
    if args.show_form_template:
        forms_integration = GoogleFormsIntegration(form_id='dummy')
        print(forms_integration.create_standard_evaluation_form_link())
        sys.exit(0)
    
    logger.info("Starting Google Forms monitor for business evaluation submissions")
    
    # Check if credentials file exists
    if not os.path.exists(args.credentials):
        logger.error(
            f"Credentials file not found: {args.credentials}\n"
            "Please download OAuth 2.0 credentials from Google Cloud Console:\n"
            "1. Go to https://console.cloud.google.com/\n"
            "2. Create a new project or select existing one\n"
            "3. Enable Google Forms API and Gmail API\n"
            "4. Create OAuth 2.0 credentials (Desktop application)\n"
            "5. Download credentials and save as 'credentials.json'"
        )
        sys.exit(1)
    
    try:
        # Initialize Google Forms integration
        forms = GoogleFormsIntegration(
            form_id=args.form_id,
            credentials_path=args.credentials,
            token_path=args.token
        )
        
        # Get form info
        form_info = forms.get_form_info()
        if form_info:
            logger.info(f"Monitoring form: {form_info['title']}")
            logger.info(f"Form has {len(form_info['questions'])} questions")
        
        # Initialize Gmail integration for follow-ups
        gmail = GmailIntegration(
            credentials_path=args.credentials,
            token_path='token.pickle'
        )
        
        # Initialize email questioner
        questioner = EmailQuestioner(gmail)
        
        # Initialize workflow
        workflow = BusinessEvaluationWorkflow()
        
        # Load processed response IDs
        processed_ids = _load_processed_ids(args.processed_file)
        logger.info(f"Loaded {len(processed_ids)} processed response IDs")
        
        logger.info("Google Forms monitor initialized successfully")
        logger.info(f"Checking for new submissions every {args.interval} seconds")
        
        while True:
            try:
                logger.info("Checking for new form submissions...")
                
                # Get new responses
                responses = forms.get_new_responses(processed_response_ids=processed_ids)
                
                for response in responses:
                    response_id = response['response_id']
                    email = response.get('email', '')
                    
                    if not email:
                        logger.warning(f"Response {response_id} has no email address. Skipping.")
                        processed_ids.append(response_id)
                        continue
                    
                    logger.info(f"Processing form response from {email}")
                    
                    # Format response as business description
                    business_description = forms.format_response_as_business_description(
                        response,
                        question_mapping=STANDARD_QUESTION_MAPPING
                    )
                    
                    # Process submission through questioner
                    result = questioner.process_initial_submission(
                        sender_email=email,
                        subject=f"Business Evaluation - {response.get('business_name', 'Submission')}",
                        body=business_description,
                        thread_id=f"form_{response_id}",  # Synthetic thread ID
                        message_id=response_id
                    )
                    
                    # Mark as processed
                    processed_ids.append(response_id)
                    _save_processed_ids(args.processed_file, processed_ids)
                    
                    if result['status'] == 'complete':
                        # Submission is complete, start evaluation
                        logger.info(
                            f"Complete form submission from {email}. "
                            f"Completeness: {result['completeness']:.0f}%. Starting evaluation..."
                        )
                        
                        # Run evaluation workflow
                        try:
                            workflow_result = workflow.evaluate_business(
                                business_description,
                                save_results=True
                            )
                            
                            # Send results email
                            if workflow_result.is_complete and workflow_result.final_report:
                                summary = _format_results_email(workflow_result)
                                gmail.send_email(
                                    to=email,
                                    subject="Business Evaluation - Results Ready",
                                    body=summary
                                )
                                logger.info(f"Evaluation complete. Results sent to {email}")
                            else:
                                # Evaluation failed
                                error_msg = workflow_result.error_message or "Unknown error"
                                gmail.send_email(
                                    to=email,
                                    subject="Business Evaluation - Issue",
                                    body=f"We encountered an issue evaluating your business:\n\n{error_msg}\n\nPlease contact support.",
                                )
                                logger.error(f"Evaluation failed for {email}: {error_msg}")
                        
                        except Exception as e:
                            logger.error(f"Error running evaluation: {e}")
                            gmail.send_email(
                                to=email,
                                subject="Business Evaluation - Processing Error",
                                body=f"We encountered an error processing your evaluation. Our team has been notified.\n\nError: {str(e)}",
                            )
                    
                    elif result['status'] == 'incomplete':
                        # Follow-up questions sent via email
                        logger.info(
                            f"Incomplete form submission from {email}. "
                            f"Completeness: {result['completeness']:.0f}%. "
                            f"Follow-up questions sent via email."
                        )
                    
                    else:
                        # Error processing
                        logger.error(f"Error processing form response from {email}: {result.get('error')}")
                
                logger.info(f"Check complete. Processed {len(responses)} new form submissions")
                
                # Exit if single run mode
                if args.single_run:
                    logger.info("Single run mode - exiting")
                    break
                
                # Wait for next interval
                logger.info(f"Waiting {args.interval} seconds until next check...")
                time.sleep(args.interval)
            
            except KeyboardInterrupt:
                logger.info("Received interrupt signal. Shutting down gracefully...")
                break
            
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                if args.single_run:
                    raise
                else:
                    logger.info(f"Continuing monitoring after error. Next check in {args.interval} seconds...")
                    time.sleep(args.interval)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


def _load_processed_ids(filepath: str) -> list:
    """Load list of processed response IDs from file."""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_processed_ids(filepath: str, processed_ids: list):
    """Save list of processed response IDs to file."""
    try:
        with open(filepath, 'w') as f:
            json.dump(processed_ids, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save processed IDs: {e}")


def _format_results_email(workflow_result):
    """Format workflow results as an email summary."""
    lines = [
        "Thank you for your business evaluation submission!",
        "",
        "Your evaluation is complete. Here's a summary:",
        "",
        "=" * 60,
        ""
    ]
    
    if workflow_result.business_submission:
        lines.append(f"Business: {workflow_result.business_submission.overview.name}")
        lines.append("")
    
    if workflow_result.business_analysis:
        lines.append(f"OVERALL SCORE: {workflow_result.business_analysis.overall_score}/10")
        lines.append("")
        
        lines.append("Top Evaluation Scores:")
        for score in workflow_result.business_analysis.evaluation_scores[:5]:
            lines.append(f"  • {score.dimension}: {score.score}/10")
        lines.append("")
    
    if workflow_result.final_report:
        lines.append(f"RECOMMENDATION: {workflow_result.final_report.recommendation}")
        lines.append("")
        
        lines.append("Key Findings:")
        for finding in workflow_result.final_report.key_findings[:5]:
            lines.append(f"  • {finding}")
        lines.append("")
    
    if workflow_result.financial_model:
        lines.append("Financial Highlights:")
        ue = workflow_result.financial_model.unit_economics
        if ue.ltv_cac_ratio:
            lines.append(f"  • LTV:CAC Ratio: {ue.ltv_cac_ratio:.1f}x")
        
        if workflow_result.financial_model.scenarios:
            base_scenario = next(
                (s for s in workflow_result.financial_model.scenarios
                 if "base" in s.scenario_name.lower()),
                workflow_result.financial_model.scenarios[0]
            )
            lines.append(f"  • Year 3 Revenue (Base Case): ${base_scenario.year3_revenue:,.0f}")
        lines.append("")
    
    if workflow_result.validation_report:
        lines.append(f"Validation Confidence: {workflow_result.validation_report.confidence_score:.0f}%")
        lines.append("")
    
    lines.append("=" * 60)
    lines.append("")
    lines.append("Full detailed reports and financial models have been generated.")
    lines.append("Please contact us to access the complete evaluation package.")
    
    return '\n'.join(lines)


if __name__ == '__main__':
    main()
