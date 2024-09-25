import os
import json
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from app import app as flask_app
import hmac
import hashlib
from copy import deepcopy

def generate_signature(payload: dict, secret: str) -> str:
    """
    Generate a HMAC SHA256 signature for the given payload using the provided secret.
    """
    payload_bytes = json.dumps(payload).encode('utf-8')
    signature = 'sha256=' + hmac.new(
        secret.encode(),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()
    return signature

@pytest.fixture
def webhook_secret():
    """
    Fixture to provide the webhook secret.
    """
    return os.environ.get('WEBHOOK_SECRET', 'testsecret')

@pytest.fixture
def generate_valid_signature(webhook_secret):
    """
    Fixture that returns a function to generate signatures for given payloads.
    """
    def _generate(payload: dict) -> str:
        return generate_signature(payload, webhook_secret)
    
    return _generate

@pytest.fixture
def client():
    """
    Pytest fixture to create a test client for the Flask application.

    Configures the app for testing and provides a client for sending HTTP requests.
    """
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client

@pytest.fixture
def sample_payload():
    """
    Fixture that provides a sample payload for pull request events.

    Returns:
        dict: A sample payload mimicking a GitHub pull request event.
    """
    return {
        "action": "opened",
        "repository": {
            "full_name": "owner/repo"
        },
        "pull_request": {
            "number": 1,
            "url": "https://api.github.com/repos/owner/repo/pulls/1"
        },
        "installation": {
            "id": 123456
        }
    }

@patch('app.github_client')
@patch('app.openai_client')
def test_webhook_integration(mock_openai_client, mock_github_client, client, sample_payload, generate_valid_signature):
    """
    Integration test for the webhook endpoint handling a valid pull request event.

    Mocks external GitHub and OpenAI clients to simulate generating and posting a review comment.
    """
    # Deep copy the sample payload to avoid side effects
    test_payload = deepcopy(sample_payload)
    
    # Generate a valid signature for the payload
    valid_signature = generate_valid_signature(test_payload)
    
    # Mock GitHubClient methods to return predefined responses
    mock_github_client.get_pull_request_diff.return_value = "diff content"
    mock_github_client.post_review_comment.return_value = True
    
    # Mock OpenAIClient method to return a predefined review comment
    mock_openai_client.generate_review.return_value = "Review comment"
    
    # Send POST request to /webhook with the sample payload and valid signature
    response = client.post(
        '/webhook',
        data=json.dumps(test_payload),
        headers={
            'X-Hub-Signature-256': valid_signature,
            'X-GitHub-Event': 'pull_request',
            'Content-Type': 'application/json'
        }
    )
    
    # Assert that the response status and content are as expected
    assert response.status_code == 200
    assert response.get_json() == {'status': 'review posted'}
    
    # Verify that GitHubClient and OpenAIClient methods were called with correct arguments
    mock_github_client.get_pull_request_diff.assert_called_once_with(
        'owner/repo',
        1,
        123456
    )
    mock_openai_client.generate_review.assert_called_once_with("diff content")
    mock_github_client.post_review_comment.assert_called_once_with(
        'owner/repo',
        1,
        'Review comment',
        123456
    )

@patch('app.github_client')
@patch('app.openai_client')
def test_webhook_no_changes(mock_openai_client, mock_github_client, client, sample_payload, generate_valid_signature):
    """
    Integration test for the webhook endpoint when no changes are detected in the pull request.

    Mocks GitHubClient to return an empty diff, expecting no review comment to be generated.
    """
    # Create a deep copy of the sample payload and modify the action to 'synchronize'
    test_payload = deepcopy(sample_payload)
    test_payload['action'] = 'synchronize'
    
    # Generate a valid signature for the modified payload
    valid_signature = generate_valid_signature(test_payload)
    
    # Mock GitHubClient to return an empty diff, indicating no changes
    mock_github_client.get_pull_request_diff.return_value = ""
    
    # Send POST request to /webhook with the modified payload and valid signature
    response = client.post(
        '/webhook',
        data=json.dumps(test_payload),
        headers={
            'X-Hub-Signature-256': valid_signature,
            'X-GitHub-Event': 'pull_request',
            'Content-Type': 'application/json'
        }
    )
    
    # Assert that the response indicates no changes detected
    assert response.status_code == 200
    assert response.get_json() == {'status': 'no changes detected'}
    
    # Verify that only get_pull_request_diff was called and no review was generated
    mock_github_client.get_pull_request_diff.assert_called_once_with(
        'owner/repo',
        1,
        123456
    )
    mock_openai_client.generate_review.assert_not_called()
    mock_github_client.post_review_comment.assert_not_called()

@patch('app.verify_signature', return_value=False)
@patch('app.github_client')
@patch('app.openai_client')
def test_webhook_invalid_signature(mock_openai_client, mock_github_client, mock_verify_signature, client, sample_payload):
    """
    Integration test for the webhook endpoint when the signature verification fails.

    Mocks signature verification to return False and expects a 403 Forbidden response.
    """
    # Use the original sample_payload without modifications
    test_payload = deepcopy(sample_payload)
    
    # Send POST request with invalid signature
    response = client.post(
        '/webhook',
        data=json.dumps(test_payload),
        headers={
            'X-Hub-Signature-256': 'sha256=invalidsignature',
            'X-GitHub-Event': 'pull_request',
            'Content-Type': 'application/json'
        }
    )
    
    # Assert that the response indicates an invalid signature
    assert response.status_code == 403
    assert response.get_json() == {'status': 'invalid signature'}
    mock_verify_signature.assert_called_once()
