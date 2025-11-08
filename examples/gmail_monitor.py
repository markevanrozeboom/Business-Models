#!/usr/bin/env python3
"""
Gmail Monitor Script

This script monitors a Gmail inbox for business evaluation requests and
processes them through the evaluation workflow. It can also handle follow-up
questions via email when more information is needed.

Setup:
1. Enable Gmail API in Google Cloud Console
2. Download OAuth 2.0 credentials as 'credentials.json'
3. Place credentials.json in the project root directory
4. Run this script - it will open a browser for OAuth authentication on first run
5. The authentication token will be saved as 'token.pickle' for future use
"""

import os
import sys
import time
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.integrations.gmail_integration import GmailIntegration
from src.integrations.email_questioner import EmailQuestioner
from src.workflow import BusinessEvaluationWorkflow
from src.utils.logger import setup_logger, get_logger


def main():
    """Main function to run Gmail monitoring."""
    parser = argparse.ArgumentParser(
        description='Monitor Gmail for business evaluation requests'
    )
    parser.add_argument(
        '--credentials',
        default='credentials.json',
        help='Path to Gmail API credentials file (default: credentials.json)'
    )
    parser.add_argument(
        '--token',
        default='token.pickle',
        help='Path to save/load authentication token (default: token.pickle)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Check interval in seconds (default: 300 = 5 minutes)'
    )
    parser.add_argument(
        '--max-results',
        type=int,
        default=10,
        help='Maximum emails to check per interval (default: 10)'
    )
    parser.add_argument(
        '--single-run',
        action='store_true',
        help='Run once and exit (default: continuous monitoring)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logger()
    logger = get_logger("gmail_monitor")
    
    logger.info("Starting Gmail monitor for business evaluation requests")
    
    # Check if credentials file exists
    if not os.path.exists(args.credentials):
        logger.error(
            f"Credentials file not found: {args.credentials}\n"
            "Please download OAuth 2.0 credentials from Google Cloud Console:\n"
            "1. Go to https://console.cloud.google.com/\n"
            "2. Create a new project or select existing one\n"
            "3. Enable Gmail API\n"
            "4. Create OAuth 2.0 credentials (Desktop application)\n"
            "5. Download credentials and save as 'credentials.json'"
        )
        sys.exit(1)
    
    try:
        # Initialize Gmail integration
        gmail = GmailIntegration(
            credentials_path=args.credentials,
            token_path=args.token
        )
        
        # Initialize email questioner for interactive follow-ups
        questioner = EmailQuestioner(gmail)
        
        # Initialize workflow
        workflow = BusinessEvaluationWorkflow()
        
        # Track processed message IDs to avoid duplicates
        processed_ids = set()
        
        logger.info("Gmail monitor initialized successfully")
        logger.info(f"Checking for new requests every {args.interval} seconds")
        
        while True:
            try:
                logger.info(f"Checking for new business evaluation requests...")
                
                # Check for new evaluation requests
                messages = gmail.check_for_new_requests(
                    max_results=args.max_results,
                    since_hours=24
                )
                
                for msg in messages:
                    msg_id = msg['id']
                    
                    # Skip if already processed
                    if msg_id in processed_ids:
                        continue
                    
                    logger.info(f"Processing message from {msg['sender']}: {msg['subject']}")
                    
                    # Process initial submission
                    result = questioner.process_initial_submission(
                        sender_email=msg['sender'],
                        subject=msg['subject'],
                        body=msg['body'],
                        thread_id=msg['thread_id'],
                        message_id=msg_id
                    )
                    
                    # Mark as processed
                    processed_ids.add(msg_id)
                    gmail.mark_as_read(msg_id)
                    gmail.add_label(msg_id, 'BusinessEvaluation')
                    
                    if result['status'] == 'complete':
                        # Submission is complete, start evaluation
                        logger.info(
                            f"Complete submission received from {msg['sender']}. "
                            f"Completeness: {result['completeness']:.0f}%. Starting evaluation..."
                        )
                        
                        # Run evaluation workflow
                        try:
                            workflow_result = workflow.evaluate_business(
                                msg['body'],
                                save_results=True
                            )
                            
                            # Send results email
                            if workflow_result.is_complete and workflow_result.final_report:
                                summary = _format_results_email(workflow_result)
                                gmail.send_email(
                                    to=msg['sender'],
                                    subject=f"Re: {msg['subject']} - Evaluation Complete",
                                    body=summary,
                                    thread_id=msg['thread_id']
                                )
                                logger.info(f"Evaluation complete. Results sent to {msg['sender']}")
                            else:
                                # Evaluation failed or incomplete
                                error_msg = workflow_result.error_message or "Unknown error"
                                gmail.send_email(
                                    to=msg['sender'],
                                    subject=f"Re: {msg['subject']} - Evaluation Issue",
                                    body=f"We encountered an issue evaluating your business:\n\n{error_msg}\n\nPlease contact support for assistance.",
                                    thread_id=msg['thread_id']
                                )
                                logger.error(f"Evaluation failed for {msg['sender']}: {error_msg}")
                        
                        except Exception as e:
                            logger.error(f"Error running evaluation: {e}")
                            gmail.send_email(
                                to=msg['sender'],
                                subject=f"Re: {msg['subject']} - Processing Error",
                                body=f"We encountered an error processing your evaluation. Our team has been notified.\n\nError: {str(e)}",
                                thread_id=msg['thread_id']
                            )
                    
                    elif result['status'] == 'incomplete':
                        # Follow-up questions sent
                        logger.info(
                            f"Incomplete submission from {msg['sender']}. "
                            f"Completeness: {result['completeness']:.0f}%. "
                            f"Follow-up questions sent."
                        )
                    
                    else:
                        # Error processing
                        logger.error(f"Error processing message from {msg['sender']}: {result.get('error')}")
                
                # Check for follow-up responses
                logger.info("Checking for follow-up responses...")
                follow_up_responses = questioner.check_for_follow_up_responses()
                
                for response in follow_up_responses:
                    if response['status'] == 'complete':
                        # Now have enough information, start evaluation
                        logger.info(
                            f"Complete submission after {response['rounds_completed']} follow-ups "
                            f"from {response['sender_email']}. Starting evaluation..."
                        )
                        
                        # Format submission for evaluation
                        submission_text = questioner._merge_submission_and_response(
                            response['submission'].model_dump(),
                            ""
                        )
                        
                        # Run evaluation
                        try:
                            workflow_result = workflow.evaluate_business(
                                submission_text,
                                save_results=True
                            )
                            
                            if workflow_result.is_complete and workflow_result.final_report:
                                summary = _format_results_email(workflow_result)
                                gmail.send_email(
                                    to=response['sender_email'],
                                    subject="Business Evaluation - Results",
                                    body=summary,
                                    thread_id=response['thread_id']
                                )
                                logger.info(f"Evaluation complete. Results sent to {response['sender_email']}")
                        
                        except Exception as e:
                            logger.error(f"Error running evaluation: {e}")
                
                logger.info(f"Check complete. Processed {len(messages)} new requests, {len(follow_up_responses)} follow-up responses")
                
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


def _format_results_email(workflow_result):
    """Format workflow results as an email summary."""
    lines = [
        "Your business evaluation is complete! Here's a summary:",
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
