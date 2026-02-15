import pytest
from unittest.mock import MagicMock
import sys
import os

# Add repo root to path so we can import 'skills' and 'skillware'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def mock_anthropic():
    """Mocks the Anthropic client."""
    mock_client = MagicMock()
    # Mock the messages.create return structure
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text='{"field_id": "value"}')]
    return mock_client


@pytest.fixture
def mock_skill_loader():
    """Mocks the SkillLoader to return a dummy skill bundle."""
    # This might not be needed if we import the class directly, but good to have.
    return MagicMock()
