"""
Basic tests for integration modules.

These tests verify the basic structure and imports of the integration modules.
They do NOT require actual Google API credentials to run.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


def test_integration_module_imports():
    """Test that integration modules can be imported."""
    from src.integrations import (
        GmailIntegration,
        GoogleFormsIntegration,
        EmailQuestioner
    )
    
    assert GmailIntegration is not None
    assert GoogleFormsIntegration is not None
    assert EmailQuestioner is not None


def test_gmail_integration_initialization():
    """Test GmailIntegration can be instantiated with mocked credentials."""
    from src.integrations.gmail_integration import GmailIntegration
    
    # Mock the authentication method to avoid needing real credentials
    with patch.object(GmailIntegration, '_authenticate'):
        integration = GmailIntegration(
            credentials_path='fake_credentials.json',
            token_path='fake_token.pickle'
        )
        
        assert integration.credentials_path == 'fake_credentials.json'
        assert integration.token_path == 'fake_token.pickle'
        assert integration.watch_label == 'INBOX'
        assert len(integration.trigger_keywords) > 0


def test_gmail_integration_trigger_keywords():
    """Test that default trigger keywords are set correctly."""
    from src.integrations.gmail_integration import GmailIntegration
    
    with patch.object(GmailIntegration, '_authenticate'):
        integration = GmailIntegration()
        
        # Check default keywords exist
        assert 'business evaluation' in integration.trigger_keywords
        assert 'evaluate business' in integration.trigger_keywords


def test_google_forms_integration_initialization():
    """Test GoogleFormsIntegration can be instantiated with mocked credentials."""
    from src.integrations.google_forms_integration import GoogleFormsIntegration
    
    with patch.object(GoogleFormsIntegration, '_authenticate'):
        integration = GoogleFormsIntegration(
            form_id='test_form_id',
            credentials_path='fake_credentials.json'
        )
        
        assert integration.form_id == 'test_form_id'
        assert integration.credentials_path == 'fake_credentials.json'


def test_google_forms_template_generation():
    """Test that form template can be generated."""
    from src.integrations.google_forms_integration import GoogleFormsIntegration
    
    with patch.object(GoogleFormsIntegration, '_authenticate'):
        integration = GoogleFormsIntegration(form_id='test_id')
        template = integration.create_standard_evaluation_form_link()
        
        assert 'Business Name' in template
        assert 'Email' in template
        assert 'Problem Statement' in template


def test_email_questioner_initialization():
    """Test EmailQuestioner can be instantiated."""
    from src.integrations.email_questioner import EmailQuestioner
    from src.integrations.gmail_integration import GmailIntegration
    
    with patch.object(GmailIntegration, '_authenticate'):
        gmail = GmailIntegration()
        questioner = EmailQuestioner(gmail)
        
        assert questioner.gmail == gmail
        assert questioner.max_follow_up_rounds == 3
        assert questioner.response_timeout_hours == 48
        assert isinstance(questioner.active_conversations, dict)


def test_email_questioner_identify_missing_info():
    """Test that missing information can be identified."""
    from src.integrations.email_questioner import EmailQuestioner
    from src.integrations.gmail_integration import GmailIntegration
    from src.models.schemas import (
        BusinessSubmission,
        BusinessOverview,
        ValueProposition,
        MarketInfo,
        BusinessModelInfo,
        FinancialProjections,
        TeamInfo
    )
    
    with patch.object(GmailIntegration, '_authenticate'):
        gmail = GmailIntegration()
        questioner = EmailQuestioner(gmail)
        
        # Create a minimal submission
        submission = BusinessSubmission(
            overview=BusinessOverview(
                name="Test Business",
                industry="",
                stage="",
                problem="",
                solution=""
            ),
            value_proposition=ValueProposition(
                unique_value="",
                differentiators=[],
                target_customer=""
            ),
            market=MarketInfo(
                target_segments=[],
                market_size=None,
                tam=None,
                sam=None,
                som=None,
                geography=[]
            ),
            business_model=BusinessModelInfo(
                revenue_model="",
                pricing="",
                cost_structure="",
                distribution_channels=[]
            ),
            financials=FinancialProjections(
                year1_revenue=None,
                year2_revenue=None,
                year3_revenue=None,
                gross_margin=None,
                unit_cac=None,
                unit_ltv=None,
                monthly_burn=None
            ),
            team=TeamInfo(
                founders=[],
                team_size=None,
                key_hires=[],
                advisors=[]
            ),
            completeness_score=20.0
        )
        
        missing = questioner._identify_missing_information(submission)
        
        # Should identify multiple missing categories
        assert len(missing) > 0
        assert 'business_overview' in missing or 'solution_description' in missing


def test_email_questioner_generate_questions():
    """Test that follow-up questions can be generated."""
    from src.integrations.email_questioner import EmailQuestioner
    from src.integrations.gmail_integration import GmailIntegration
    
    with patch.object(GmailIntegration, '_authenticate'):
        gmail = GmailIntegration()
        questioner = EmailQuestioner(gmail)
        
        missing_info = ['market_information', 'revenue_model', 'team_information']
        questions = questioner._generate_follow_up_questions(missing_info)
        
        # Should generate questions for each missing category
        assert len(questions) > 0
        assert any('market' in q.lower() or 'customer' in q.lower() for q in questions)


def test_gmail_integration_message_parsing():
    """Test that Gmail message parsing logic works."""
    from src.integrations.gmail_integration import GmailIntegration
    
    with patch.object(GmailIntegration, '_authenticate'):
        integration = GmailIntegration()
        
        # Test _extract_message_body with simple payload
        test_payload = {
            'body': {
                'data': 'VGVzdCBtZXNzYWdlIGJvZHk='  # Base64 encoded "Test message body"
            }
        }
        
        body = integration._extract_message_body(test_payload)
        assert body == 'Test message body'


def test_forms_integration_response_parsing():
    """Test that form response parsing works."""
    from src.integrations.google_forms_integration import GoogleFormsIntegration
    
    with patch.object(GoogleFormsIntegration, '_authenticate'):
        integration = GoogleFormsIntegration(form_id='test_id')
        
        # Test _parse_response with mock data
        test_response = {
            'responseId': 'test_response_id',
            'createTime': '2024-01-01T12:00:00Z',
            'lastSubmittedTime': '2024-01-01T12:00:00Z',
            'respondentEmail': 'test@example.com',
            'answers': {
                'q1': {
                    'textAnswers': {
                        'answers': [
                            {'value': 'Answer 1'}
                        ]
                    }
                },
                'q2': {
                    'textAnswers': {
                        'answers': [
                            {'value': 'Answer 2'}
                        ]
                    }
                }
            }
        }
        
        parsed = integration._parse_response(test_response)
        
        assert parsed['response_id'] == 'test_response_id'
        assert parsed['email'] == 'test@example.com'
        assert 'q1' in parsed['answers']
        assert parsed['answers']['q1'] == ['Answer 1']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
