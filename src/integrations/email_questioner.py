"""Email-based questioner for interactive intake with follow-up questions."""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import time

from ..agents.intake import IntakeAgent
from ..models.schemas import BusinessSubmission
from .gmail_integration import GmailIntegration
from ..utils.logger import get_logger


class EmailQuestioner:
    """
    Interactive questioner that can ask follow-up questions via email
    when the initial submission lacks sufficient information.
    """
    
    def __init__(
        self,
        gmail_integration: GmailIntegration,
        max_follow_up_rounds: int = 3,
        response_timeout_hours: int = 48
    ):
        """
        Initialize email questioner.
        
        Args:
            gmail_integration: Configured GmailIntegration instance
            max_follow_up_rounds: Maximum number of follow-up question rounds
            response_timeout_hours: Hours to wait for response before timeout
        """
        self.logger = get_logger("integration.email_questioner")
        self.gmail = gmail_integration
        self.intake_agent = IntakeAgent()
        self.max_follow_up_rounds = max_follow_up_rounds
        self.response_timeout_hours = response_timeout_hours
        
        # Track ongoing conversations
        self.active_conversations: Dict[str, Dict[str, Any]] = {}
    
    def process_initial_submission(
        self,
        sender_email: str,
        subject: str,
        body: str,
        thread_id: str,
        message_id: str
    ) -> Dict[str, Any]:
        """
        Process initial submission and determine if follow-up is needed.
        
        Args:
            sender_email: Email address of sender
            subject: Email subject
            body: Email body with business description
            thread_id: Gmail thread ID for continuing conversation
            message_id: Gmail message ID
        
        Returns:
            Dictionary with submission status and next steps
        """
        self.logger.info(f"Processing initial submission from {sender_email}")
        
        # Try to extract business submission
        try:
            submission = self.intake_agent.extract_business_info(body)
            completeness = submission.completeness_score
            
            self.logger.info(f"Initial submission completeness: {completeness}%")
            
            # If sufficiently complete, proceed with evaluation
            if completeness >= 80:
                return {
                    'status': 'complete',
                    'completeness': completeness,
                    'submission': submission,
                    'needs_follow_up': False
                }
            
            # If not complete, identify missing information and ask questions
            missing_info = self._identify_missing_information(submission)
            
            if not missing_info:
                # Edge case: low completeness but no specific missing info
                return {
                    'status': 'complete',
                    'completeness': completeness,
                    'submission': submission,
                    'needs_follow_up': False
                }
            
            # Generate follow-up questions
            questions = self._generate_follow_up_questions(missing_info)
            
            # Send follow-up email
            self._send_follow_up_email(
                sender_email,
                subject,
                questions,
                thread_id,
                round_number=1
            )
            
            # Track this conversation
            self.active_conversations[thread_id] = {
                'sender_email': sender_email,
                'initial_submission': submission.model_dump(),
                'current_round': 1,
                'started_at': datetime.utcnow().isoformat(),
                'last_interaction': datetime.utcnow().isoformat(),
                'message_id': message_id,
                'missing_info': missing_info
            }
            
            return {
                'status': 'incomplete',
                'completeness': completeness,
                'submission': submission,
                'needs_follow_up': True,
                'missing_info': missing_info,
                'questions_sent': questions
            }
            
        except Exception as e:
            self.logger.error(f"Error processing submission: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'needs_follow_up': False
            }
    
    def process_follow_up_response(
        self,
        thread_id: str,
        response_body: str,
        message_id: str
    ) -> Dict[str, Any]:
        """
        Process a follow-up response and determine if more info is needed.
        
        Args:
            thread_id: Gmail thread ID
            response_body: Response body from user
            message_id: Gmail message ID
        
        Returns:
            Dictionary with updated submission status
        """
        if thread_id not in self.active_conversations:
            self.logger.warning(f"Received response for unknown thread: {thread_id}")
            return {
                'status': 'error',
                'error': 'Unknown conversation thread',
                'needs_follow_up': False
            }
        
        conversation = self.active_conversations[thread_id]
        self.logger.info(
            f"Processing follow-up response for thread {thread_id}, "
            f"round {conversation['current_round']}"
        )
        
        # Merge original submission with new information
        original_submission = conversation['initial_submission']
        merged_description = self._merge_submission_and_response(
            original_submission,
            response_body
        )
        
        # Re-extract business info with merged data
        try:
            updated_submission = self.intake_agent.extract_business_info(merged_description)
            completeness = updated_submission.completeness_score
            
            self.logger.info(f"Updated completeness: {completeness}%")
            
            # Check if now complete
            if completeness >= 80:
                # Send confirmation email
                self._send_completion_email(
                    conversation['sender_email'],
                    thread_id
                )
                
                # Clean up conversation
                del self.active_conversations[thread_id]
                
                return {
                    'status': 'complete',
                    'completeness': completeness,
                    'submission': updated_submission,
                    'needs_follow_up': False,
                    'rounds_completed': conversation['current_round']
                }
            
            # Check if we've reached max follow-up rounds
            if conversation['current_round'] >= self.max_follow_up_rounds:
                self.logger.info(
                    f"Max follow-up rounds reached for thread {thread_id}. "
                    "Proceeding with incomplete submission."
                )
                
                # Send notification about proceeding with incomplete info
                self._send_max_rounds_email(
                    conversation['sender_email'],
                    thread_id,
                    completeness
                )
                
                # Clean up conversation
                del self.active_conversations[thread_id]
                
                return {
                    'status': 'complete_with_gaps',
                    'completeness': completeness,
                    'submission': updated_submission,
                    'needs_follow_up': False,
                    'rounds_completed': conversation['current_round']
                }
            
            # Need more follow-up
            missing_info = self._identify_missing_information(updated_submission)
            questions = self._generate_follow_up_questions(missing_info)
            
            # Send next round of follow-up questions
            next_round = conversation['current_round'] + 1
            self._send_follow_up_email(
                conversation['sender_email'],
                f"Re: Business Evaluation Follow-up #{next_round}",
                questions,
                thread_id,
                round_number=next_round
            )
            
            # Update conversation state
            conversation['current_round'] = next_round
            conversation['last_interaction'] = datetime.utcnow().isoformat()
            conversation['initial_submission'] = updated_submission.model_dump()
            conversation['missing_info'] = missing_info
            
            return {
                'status': 'incomplete',
                'completeness': completeness,
                'submission': updated_submission,
                'needs_follow_up': True,
                'missing_info': missing_info,
                'questions_sent': questions,
                'current_round': next_round
            }
            
        except Exception as e:
            self.logger.error(f"Error processing follow-up response: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'needs_follow_up': False
            }
    
    def _identify_missing_information(
        self,
        submission: BusinessSubmission
    ) -> List[str]:
        """
        Identify what information is missing from the submission.
        
        Args:
            submission: Business submission to analyze
        
        Returns:
            List of missing information categories
        """
        missing = []
        
        # Check business overview
        if not submission.overview.name or not submission.overview.problem:
            missing.append('business_overview')
        
        if not submission.overview.solution:
            missing.append('solution_description')
        
        # Check market info
        if not submission.market.target_segments or not submission.market.market_size:
            missing.append('market_information')
        
        # Check business model
        if not submission.business_model.revenue_model:
            missing.append('revenue_model')
        
        if not submission.business_model.pricing:
            missing.append('pricing_strategy')
        
        # Check financials
        if not submission.financials.year1_revenue:
            missing.append('financial_projections')
        
        # Check team
        if not submission.team.founders or not submission.team.team_size:
            missing.append('team_information')
        
        return missing
    
    def _generate_follow_up_questions(
        self,
        missing_info: List[str]
    ) -> List[str]:
        """
        Generate specific follow-up questions based on missing information.
        
        Args:
            missing_info: List of missing information categories
        
        Returns:
            List of follow-up questions
        """
        question_templates = {
            'business_overview': [
                "What is the name of your business?",
                "What specific problem are you solving?"
            ],
            'solution_description': [
                "Please describe your solution in more detail. How does it solve the problem?"
            ],
            'market_information': [
                "Who are your target customers?",
                "What is the size of your target market? (TAM/SAM/SOM estimates)"
            ],
            'revenue_model': [
                "How does your business generate revenue? (e.g., subscription, transaction fees, licensing)"
            ],
            'pricing_strategy': [
                "What is your pricing strategy? How much do customers pay?"
            ],
            'financial_projections': [
                "What are your revenue projections for the next 1-3 years?",
                "What are your main costs and expected margins?"
            ],
            'team_information': [
                "Tell us about your team. Who are the founders and key team members?",
                "What relevant experience does your team have?"
            ]
        }
        
        questions = []
        for category in missing_info:
            if category in question_templates:
                questions.extend(question_templates[category])
        
        return questions
    
    def _send_follow_up_email(
        self,
        to: str,
        subject: str,
        questions: List[str],
        thread_id: str,
        round_number: int
    ):
        """Send follow-up email with questions."""
        body = f"""Thank you for your business evaluation submission!

We've reviewed your initial information and need some additional details to provide a comprehensive evaluation.

Please answer the following questions:

"""
        for i, question in enumerate(questions, 1):
            body += f"{i}. {question}\n\n"
        
        body += """
Please reply to this email with your answers. We'll process your complete submission once we have this information.

If you have any questions, feel free to reply.

Best regards,
Business Evaluation System
"""
        
        self.gmail.send_email(to, subject, body, thread_id)
        self.logger.info(f"Follow-up email #{round_number} sent to {to}")
    
    def _send_completion_email(self, to: str, thread_id: str):
        """Send email confirming submission is complete and evaluation is starting."""
        subject = "Business Evaluation - Processing Your Submission"
        body = """Thank you for providing the additional information!

Your business evaluation submission is now complete. We're processing your evaluation and will send you the results within 24 hours.

You'll receive:
- Overall business score and recommendation
- Market analysis and competitive assessment
- Financial projections and unit economics
- Risk assessment and key findings

Best regards,
Business Evaluation System
"""
        self.gmail.send_email(to, subject, body, thread_id)
        self.logger.info(f"Completion email sent to {to}")
    
    def _send_max_rounds_email(
        self,
        to: str,
        thread_id: str,
        completeness: float
    ):
        """Send email when max follow-up rounds reached."""
        subject = "Business Evaluation - Proceeding with Available Information"
        body = f"""Thank you for your responses!

We've reached our follow-up limit, but we have enough information ({completeness:.0f}% complete) to proceed with your evaluation.

We'll work with the information provided and send you the results within 24 hours. The evaluation may note areas where additional information would strengthen the analysis.

Best regards,
Business Evaluation System
"""
        self.gmail.send_email(to, subject, body, thread_id)
        self.logger.info(f"Max rounds notification sent to {to}")
    
    def _merge_submission_and_response(
        self,
        original_submission: Dict[str, Any],
        response_body: str
    ) -> str:
        """
        Merge original submission data with follow-up response.
        
        Args:
            original_submission: Original submission dict
            response_body: Text response from user
        
        Returns:
            Merged description string
        """
        # Convert original submission to readable text
        lines = ["=== Original Submission ==="]
        
        def add_section(title: str, data: Dict[str, Any]):
            lines.append(f"\n{title}:")
            for key, value in data.items():
                if value and value != '' and value != [] and value is not None:
                    lines.append(f"  {key}: {value}")
        
        if original_submission.get('overview'):
            add_section("Business Overview", original_submission['overview'])
        
        if original_submission.get('value_proposition'):
            add_section("Value Proposition", original_submission['value_proposition'])
        
        if original_submission.get('market'):
            add_section("Market", original_submission['market'])
        
        if original_submission.get('business_model'):
            add_section("Business Model", original_submission['business_model'])
        
        if original_submission.get('financials'):
            add_section("Financials", original_submission['financials'])
        
        if original_submission.get('team'):
            add_section("Team", original_submission['team'])
        
        # Add follow-up response
        lines.append("\n\n=== Follow-up Response ===")
        lines.append(response_body)
        
        return '\n'.join(lines)
    
    def check_for_follow_up_responses(self) -> List[Dict[str, Any]]:
        """
        Check Gmail for responses to follow-up questions.
        
        Returns:
            List of processed responses
        """
        processed_responses = []
        
        # Check each active conversation for responses
        for thread_id, conversation in list(self.active_conversations.items()):
            # Search for new messages in this thread
            try:
                # Get messages in thread
                thread = self.gmail.service.users().threads().get(
                    userId='me',
                    id=thread_id
                ).execute()
                
                messages = thread.get('messages', [])
                
                # Find messages after our last interaction
                last_interaction_time = datetime.fromisoformat(
                    conversation['last_interaction']
                )
                
                for message in messages:
                    msg_time_ms = int(message.get('internalDate', 0))
                    msg_time = datetime.fromtimestamp(msg_time_ms / 1000)
                    
                    # If message is newer than our last interaction
                    if msg_time > last_interaction_time:
                        # Extract message details
                        full_msg = self.gmail._get_message_details(message['id'])
                        
                        if full_msg and full_msg['sender'] == conversation['sender_email']:
                            # Process this follow-up response
                            result = self.process_follow_up_response(
                                thread_id,
                                full_msg['body'],
                                message['id']
                            )
                            
                            result['thread_id'] = thread_id
                            result['sender_email'] = conversation['sender_email']
                            processed_responses.append(result)
                            
                            # Mark as read
                            self.gmail.mark_as_read(message['id'])
                
            except Exception as e:
                self.logger.error(f"Error checking thread {thread_id}: {e}")
        
        return processed_responses
