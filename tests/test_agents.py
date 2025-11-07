"""Tests for agent implementations."""

import pytest
from unittest.mock import Mock, patch

from src.agents.base import BaseAgent
from src.agents.intake import IntakeAgent
from src.models.schemas import AgentType, BusinessSubmission


class TestIntakeAgent:
    """Tests for IntakeAgent."""

    def test_agent_initialization(self):
        """Test IntakeAgent initializes correctly."""
        agent = IntakeAgent()
        assert agent.agent_type == AgentType.INTAKE
        assert agent.temperature == 0.7

    def test_completeness_calculation(self):
        """Test completeness score calculation."""
        agent = IntakeAgent()

        # Create a well-formed submission
        submission_data = {
            "overview": {
                "name": "Test Business",
                "industry": "SaaS",
                "stage": "seed",
                "problem": "Big problem",
                "solution": "Great solution"
            },
            "value_proposition": {
                "unique_value": "Unique",
                "differentiators": ["Diff 1", "Diff 2"],
                "target_customer": "B2B"
            },
            "market": {
                "target_segments": ["Segment 1"],
                "tam": 1000000000
            },
            "business_model": {
                "revenue_model": "Subscription",
                "pricing": "$500/mo",
                "cost_structure": "Low",
                "distribution_channels": ["Direct"]
            },
            "financials": {
                "year1_revenue": 500000
            },
            "team": {
                "team_size": 4,
                "key_roles": ["CEO", "CTO"],
                "relevant_experience": "10 years"
            }
        }

        submission = agent._create_business_submission({
            **submission_data,
            "completeness_score": 90.0
        })

        score = agent.calculate_completeness(submission)
        assert score > 80.0  # Should be high quality


class TestBaseAgent:
    """Tests for BaseAgent functionality."""

    def test_create_response(self):
        """Test response creation."""
        # Create a minimal concrete implementation for testing
        class TestAgent(BaseAgent):
            def get_system_prompt(self):
                return "Test prompt"

            def process(self, input_data):
                return self.create_response(
                    success=True,
                    message="Test successful",
                    confidence_score=85.0
                )

        agent = TestAgent(agent_type=AgentType.INTAKE)
        response = agent.process({})

        assert response.success is True
        assert response.message == "Test successful"
        assert response.confidence_score == 85.0
        assert response.agent_type == AgentType.INTAKE
