"""Tests for data models."""

import pytest
from datetime import datetime

from src.models.schemas import (
    BusinessOverview,
    ValueProposition,
    MarketInfo,
    BusinessModelInfo,
    FinancialProjections,
    TeamInfo,
    BusinessSubmission,
    WorkflowPhase,
    WorkflowState,
)


def test_business_overview_creation():
    """Test BusinessOverview model creation."""
    overview = BusinessOverview(
        name="Test Business",
        industry="Technology",
        stage="early-stage",
        problem="Test problem",
        solution="Test solution"
    )

    assert overview.name == "Test Business"
    assert overview.industry == "Technology"
    assert overview.stage == "early-stage"


def test_business_submission_creation():
    """Test complete BusinessSubmission creation."""
    submission = BusinessSubmission(
        submission_id="test-123",
        timestamp=datetime.utcnow(),
        overview=BusinessOverview(
            name="Test Co",
            industry="SaaS",
            stage="seed",
            problem="Problem statement",
            solution="Solution statement"
        ),
        value_proposition=ValueProposition(
            unique_value="Unique value",
            differentiators=["Diff 1", "Diff 2"],
            target_customer="B2B companies"
        ),
        market=MarketInfo(
            target_segments=["Segment 1"],
            tam=1000000000,
            sam=100000000,
            som=10000000
        ),
        business_model=BusinessModelInfo(
            revenue_model="Subscription",
            pricing="$500/month",
            cost_structure="SaaS typical",
            distribution_channels=["Direct sales"]
        ),
        financials=FinancialProjections(
            year1_revenue=500000,
            year2_revenue=2000000,
            year3_revenue=5000000
        ),
        team=TeamInfo(
            team_size=4,
            key_roles=["CEO", "CTO"],
            relevant_experience="10 years in industry"
        ),
        completeness_score=85.0
    )

    assert submission.submission_id == "test-123"
    assert submission.overview.name == "Test Co"
    assert submission.completeness_score == 85.0


def test_workflow_state_creation():
    """Test WorkflowState model creation."""
    state = WorkflowState(
        submission_id="test-456",
        current_phase=WorkflowPhase.INTAKE,
    )

    assert state.submission_id == "test-456"
    assert state.current_phase == WorkflowPhase.INTAKE
    assert state.is_complete is False
    assert state.requires_human_review is False


def test_completeness_score_validation():
    """Test that completeness score is validated."""
    with pytest.raises(ValueError):
        BusinessSubmission(
            submission_id="test",
            overview=BusinessOverview(
                name="Test",
                industry="Tech",
                stage="seed",
                problem="Problem",
                solution="Solution"
            ),
            value_proposition=ValueProposition(
                unique_value="Value",
                differentiators=["Diff"],
                target_customer="Customer"
            ),
            market=MarketInfo(
                target_segments=["Segment"]
            ),
            business_model=BusinessModelInfo(
                revenue_model="Sub",
                pricing="$100",
                cost_structure="Low",
                distribution_channels=["Direct"]
            ),
            financials=FinancialProjections(),
            team=TeamInfo(
                team_size=1,
                key_roles=["CEO"],
                relevant_experience="Experience"
            ),
            completeness_score=150.0  # Invalid: > 100
        )
