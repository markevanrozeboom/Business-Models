"""Google Forms Integration for receiving business evaluation requests."""

import os
import pickle
from typing import Optional, List, Dict, Any
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..utils.logger import get_logger


# Google Forms and Sheets API scopes
SCOPES = [
    'https://www.googleapis.com/auth/forms.responses.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly'
]


class GoogleFormsIntegration:
    """
    Google Forms Integration for receiving business evaluation submissions.
    
    This class monitors a Google Form for new responses and extracts
    business information to initiate the evaluation workflow.
    """
    
    def __init__(
        self,
        form_id: str,
        credentials_path: str = 'credentials.json',
        token_path: str = 'token_forms.pickle',
        response_sheet_id: Optional[str] = None
    ):
        """
        Initialize Google Forms integration.
        
        Args:
            form_id: Google Form ID to monitor
            credentials_path: Path to OAuth 2.0 credentials JSON file
            token_path: Path to save/load OAuth token
            response_sheet_id: Optional Google Sheets ID where responses are saved
        """
        self.logger = get_logger("integration.google_forms")
        self.form_id = form_id
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.response_sheet_id = response_sheet_id
        
        self.forms_service = None
        self.sheets_service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Forms and Sheets API using OAuth 2.0."""
        creds = None
        
        # Load existing token if available
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                self.logger.info("Refreshing expired credentials")
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Google Forms credentials file not found at {self.credentials_path}. "
                        "Please download OAuth 2.0 credentials from Google Cloud Console."
                    )
                
                self.logger.info("Starting OAuth flow for Google Forms authentication")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for future use
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        self.forms_service = build('forms', 'v1', credentials=creds)
        self.sheets_service = build('sheets', 'v4', credentials=creds)
        self.logger.info("Google Forms authentication successful")
    
    def get_form_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the form structure.
        
        Returns:
            Dictionary with form title, description, and questions
        """
        try:
            form = self.forms_service.forms().get(formId=self.form_id).execute()
            
            info = {
                'title': form.get('info', {}).get('title', ''),
                'description': form.get('info', {}).get('description', ''),
                'questions': []
            }
            
            # Extract questions
            for item in form.get('items', []):
                if 'questionItem' in item:
                    question = item['questionItem']['question']
                    info['questions'].append({
                        'id': question['questionId'],
                        'title': item.get('title', ''),
                        'type': list(question.keys())[0] if question else 'unknown'
                    })
            
            self.logger.info(f"Form info retrieved: {info['title']}")
            return info
            
        except HttpError as error:
            self.logger.error(f"Error getting form info: {error}")
            return None
    
    def get_new_responses(
        self,
        processed_response_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get new form responses that haven't been processed yet.
        
        Args:
            processed_response_ids: List of response IDs that have been processed
        
        Returns:
            List of new form responses with submitter email and answers
        """
        processed_response_ids = processed_response_ids or []
        
        try:
            # Get all responses
            result = self.forms_service.forms().responses().list(
                formId=self.form_id
            ).execute()
            
            responses = result.get('responses', [])
            
            # Filter out already processed responses
            new_responses = []
            for response in responses:
                response_id = response['responseId']
                
                if response_id not in processed_response_ids:
                    parsed_response = self._parse_response(response)
                    new_responses.append(parsed_response)
            
            self.logger.info(f"Found {len(new_responses)} new form responses")
            return new_responses
            
        except HttpError as error:
            self.logger.error(f"Error getting form responses: {error}")
            return []
    
    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a form response into a structured format.
        
        Args:
            response: Raw form response from API
        
        Returns:
            Parsed response with email, timestamp, and answers
        """
        parsed = {
            'response_id': response['responseId'],
            'timestamp': response.get('createTime', ''),
            'last_submitted': response.get('lastSubmittedTime', ''),
            'email': response.get('respondentEmail', ''),
            'answers': {}
        }
        
        # Extract answers
        answers = response.get('answers', {})
        for question_id, answer in answers.items():
            # Get the actual answer value based on type
            if 'textAnswers' in answer:
                values = answer['textAnswers'].get('answers', [])
                parsed['answers'][question_id] = [v.get('value', '') for v in values]
            elif 'fileUploadAnswers' in answer:
                files = answer['fileUploadAnswers'].get('answers', [])
                parsed['answers'][question_id] = [f.get('fileId', '') for f in files]
            else:
                parsed['answers'][question_id] = str(answer)
        
        return parsed
    
    def get_responses_from_sheet(
        self,
        range_name: str = 'Form Responses 1!A:Z'
    ) -> List[Dict[str, Any]]:
        """
        Get form responses from linked Google Sheet (alternative method).
        
        This is useful when form responses are automatically saved to a sheet.
        
        Args:
            range_name: Sheet range to read from
        
        Returns:
            List of responses as dictionaries
        """
        if not self.response_sheet_id:
            self.logger.warning("No response sheet ID configured")
            return []
        
        try:
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.response_sheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                self.logger.info("No data found in response sheet")
                return []
            
            # First row contains headers
            headers = values[0]
            responses = []
            
            # Parse each row as a response
            for row in values[1:]:
                response = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        response[header] = row[i]
                    else:
                        response[header] = ''
                responses.append(response)
            
            self.logger.info(f"Retrieved {len(responses)} responses from sheet")
            return responses
            
        except HttpError as error:
            self.logger.error(f"Error reading from sheet: {error}")
            return []
    
    def format_response_as_business_description(
        self,
        response: Dict[str, Any],
        question_mapping: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Format a form response into a business description for evaluation.
        
        Args:
            response: Parsed form response
            question_mapping: Optional mapping of question IDs to field names
        
        Returns:
            Formatted business description string
        """
        lines = []
        
        # Add timestamp and email
        if response.get('email'):
            lines.append(f"Submitted by: {response['email']}")
        if response.get('timestamp'):
            lines.append(f"Submission time: {response['timestamp']}")
        lines.append("")  # Empty line
        
        # Add all answers
        for question_id, answer in response.get('answers', {}).items():
            if isinstance(answer, list):
                answer_text = ', '.join(answer)
            else:
                answer_text = str(answer)
            
            # Use mapping if provided, otherwise use question ID
            field_name = question_mapping.get(question_id, f"Question {question_id}") if question_mapping else f"Q-{question_id}"
            
            if answer_text:
                lines.append(f"{field_name}: {answer_text}")
        
        return '\n'.join(lines)
    
    def create_standard_evaluation_form_link(self) -> str:
        """
        Generate a link to create a standard business evaluation form.
        
        Returns:
            Informational message about creating the form
        """
        template = """
        To create a Google Form for business evaluations, include these questions:
        
        1. Business Name* (Short answer)
        2. Your Email* (Email)
        3. Industry/Sector* (Short answer)
        4. Business Stage* (Multiple choice: Idea, MVP, Early Stage, Growth)
        5. Problem Statement* (Paragraph)
        6. Solution Description* (Paragraph)
        7. Target Customer (Paragraph)
        8. Unique Value Proposition (Paragraph)
        9. Market Size (TAM/SAM/SOM) (Paragraph)
        10. Revenue Model (Short answer)
        11. Pricing Strategy (Paragraph)
        12. Financial Projections (Paragraph)
        13. Team Background (Paragraph)
        14. Current Traction (Paragraph)
        15. Funding Sought (Short answer)
        16. Additional Information (Paragraph)
        
        * Required fields
        
        After creating the form:
        1. Go to form settings and enable "Collect email addresses"
        2. Get the Form ID from the URL (between /d/ and /edit)
        3. Configure this integration with the Form ID
        """
        return template.strip()
