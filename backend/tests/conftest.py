"""
Pytest configuration and fixtures for Core Website Vitals backend tests.
"""

import asyncio
import pytest
from unittest.mock import Mock, MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
from supabase import Client

# Test configuration
pytest_plugins = ["pytest_asyncio"]

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client for testing."""
    mock_client = Mock(spec=Client)
    
    # Mock table operations
    mock_table = Mock()
    mock_table.select.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.delete.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.execute.return_value = Mock(data=[])
    
    mock_client.table.return_value = mock_table
    
    # Mock auth operations
    mock_auth = Mock()
    mock_auth.sign_up.return_value = Mock(user=Mock(id="test-user-id"))
    mock_auth.sign_in_with_password.return_value = Mock(user=Mock(id="test-user-id"))
    mock_client.auth = mock_auth
    
    return mock_client

@pytest.fixture
def mock_celery_task():
    """Create a mock Celery task for testing."""
    mock_task = Mock()
    mock_task.delay.return_value = Mock(id="test-task-id")
    mock_task.AsyncResult.return_value = Mock(
        state="PENDING",
        result=None,
        info=None
    )
    return mock_task

@pytest.fixture
def test_user_data():
    """Test user data for authentication tests."""
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "full_name": "Test User",
        "subscription_tier": "free"
    }

@pytest.fixture
def test_analysis_task_data():
    """Test analysis task data."""
    return {
        "id": "test-task-id",
        "user_id": "test-user-id",
        "url_analyzed": "https://example.com",
        "status": "PENDING",
        "analysis_type": "full_seo",
        "celery_task_id": "celery-task-id"
    }

@pytest.fixture
def test_seo_results():
    """Test SEO analysis results."""
    return {
        "seo_attributes": {
            "OnPageAnalyzer": {
                "title": "Test Website",
                "isTitle": True,
                "titleLength": 12,
                "isTitleEnoughLong": False,
                "titleDuplicateWords": 0,
                "metaDescription": "Test description",
                "isMetaDescription": True,
                "descriptionLength": 16,
                "isMetaDescriptionEnoughLong": False,
                "isH1": True,
                "h1": ["Test Heading"],
                "h1Count": 1,
                "isH1OnlyOne": True,
                "wordsCount": 250,
                "isContentEnoughLong": False,
                "linksCount": 3,
                "isTooEnoughlinks": False,
                "total_images_on_page": 2,
                "notOptimizedImagesCount": 1,
                "on_page_analysis_status": "completed"
            },
            "TechnicalSEOAnalyzer": {
                "hasHttps": True,
                "robotsTxtStatus": "found",
                "robotsTxtDisallowsAll": False,
                "hasSitemap": True,
                "hasCanonicalTag": True,
                "mobileResponsive": True,
                "hasSchema": False,
                "metaRobots": "index, follow",
                "hasMetaNoindex": False,
                "httpVersion": "HTTP/2",
                "hstsHeader": True,
                "hasMixedContent": False,
                "hasRedirects": False,
                "hasCustom404PageHeuristic": True,
                "htmlPageSize": 150000,
                "domSize": 800,
                "htmlCompressionGzipTest": "gzip",
                "pageCacheHeaders": {"Cache-Control": "max-age=3600"},
                "favicon": True,
                "isCharacterEncode": True,
                "isDoctype": True,
                "technical_seo_analysis_status": "completed"
            },
            "ContentAnalyzer": {
                "flesch_reading_ease_score": 65.2,
                "keywordUsage": {
                    "test": {"phrase_count": 5, "density": 2.1}
                },
                "target_keywords_analyzed": ["test", "example"],
                "mostCommonKeywords": ["test", "example", "website"],
                "textToHtmlRatioPercent": 15.5,
                "textToHtmlRatioStatus": "calculated",
                "spellCheck": {
                    "status": "completed",
                    "misspelled_words_count": 0
                },
                "content_analysis_status": "completed"
            },
            "ScoringModule": {
                "on_page_score_percent": 72.5,
                "technical_score_percent": 85.0,
                "content_score_percent": 68.3,
                "overall_seo_score_percent": 75.2,
                "on_page_issues": ["Title length suboptimal", "Meta description too short"],
                "technical_issues": ["No structured data found"],
                "content_issues": ["Content may be too short"],
                "on_page_successes": ["H1 tag present", "HTTPS enabled"],
                "technical_successes": ["HTTPS enabled", "Robots.txt accessible"],
                "content_successes": ["Good readability score"],
                "scoring_status": "completed"
            }
        },
        "analysis_timestamp": "2025-01-17T10:00:00Z",
        "target_url": "https://example.com",
        "domain": "example.com"
    }

@pytest.fixture
def app():
    """Create FastAPI app instance for testing."""
    # This will be implemented when we create the main FastAPI app
    from app.main import app
    return app

@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)

@pytest.fixture
async def async_client(app):
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def auth_headers():
    """Create authentication headers for testing."""
    return {
        "Authorization": "Bearer test-jwt-token",
        "Content-Type": "application/json"
    }

# Test markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "auth: marks tests related to authentication"
    )
    config.addinivalue_line(
        "markers", "celery: marks tests related to Celery tasks"
    )
    config.addinivalue_line(
        "markers", "supabase: marks tests related to Supabase"
    )