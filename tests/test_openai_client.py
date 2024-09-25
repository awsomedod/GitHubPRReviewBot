import os
import pytest
from unittest.mock import patch, MagicMock, Mock
from openai_client import OpenAIClient
import openai

@patch.dict(os.environ, {'OPENAI_API_KEY': 'fake_api_key'})
@patch('openai_client.openai.OpenAI')
def test_init_openai_client(mock_openai,):
    """
    Test that OpenAIClient initializes the OpenAI API client with the correct API key.

    Mocks the OpenAI library to verify client initialization.
    """
    client = OpenAIClient()
    openai.OpenAI.assert_called_once()
    assert client.client == mock_openai()

@patch('openai_client.openai.OpenAI')
def test_generate_review_success(mock_openai_class):
    """
    Test that OpenAIClient successfully generates a review comment given a diff.

    Mocks the OpenAI API response to return a predefined review content.
    """
    mock_instance = mock_openai_class.return_value
    mock_instance.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content='Review content'))]
    )
    client = OpenAIClient()
    diff = "diff content"
    review = client.generate_review(diff)
    mock_instance.chat.completions.create.assert_called_once()
    assert review == 'Review content'

@patch('openai_client.openai.OpenAI')
def test_generate_review_failure(mock_openai_class, capsys):
    """
    Test that OpenAIClient handles exceptions gracefully when the API call fails.

    Mocks the OpenAI API to raise an exception and checks the fallback response.
    """
    mock_instance = mock_openai_class.return_value
    mock_instance.chat.completions.create.side_effect = Exception("API error")
    client = OpenAIClient()
    diff = "diff content"
    review = client.generate_review(diff)
    
    # Capture the standard output to verify error logging
    captured = capsys.readouterr()
    assert "Error generating review: API error" in captured.out
    assert review == "Sorry, I couldn't generate a review at this time."
