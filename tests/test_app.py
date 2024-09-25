import os
import json
import pytest
from unittest.mock import patch, MagicMock
from app import app

@pytest.fixture
def client():
    """
    Pytest fixture to create a test client for the Flask application.
    Configures the app for testing and provides a client for sending HTTP requests.
    """
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@patch('app.verify_signature')
@patch('app.github_client')
@patch('app.openai_client')
def test_webhook_invalid_signature(mock_openai_client, mock_github_client, mock_verify_signature, client):
    """
    Test that the webhook endpoint returns a 403 status code when the signature is invalid.

    Mocks the signature verification to return False and asserts the appropriate response.
    """
    mock_verify_signature.return_value = False

    response = client.post('/webhook', data=json.dumps({}), headers={
        'X-Hub-Signature-256': 'sha256=invalidsignature',
        'X-GitHub-Event': 'pull_request'
    })

    assert response.status_code == 403
    assert response.get_json() == {'status': 'invalid signature'}
    mock_verify_signature.assert_called_once()

@patch('app.verify_signature')
@patch('app.github_client')
@patch('app.openai_client')
def test_webhook_ignored_event(mock_openai_client, mock_github_client, mock_verify_signature, client):
    """
    Test that the webhook endpoint ignores events other than pull requests.

    Mocks the signature verification to return True and sends a 'push' event, expecting an ignored status.
    """
    mock_verify_signature.return_value = True

    response = client.post('/webhook', data=json.dumps({}), headers={
        'X-Hub-Signature-256': 'sha256=validsignature',
        'X-GitHub-Event': 'push'
    })

    assert response.status_code == 200
    assert response.get_json() == {'status': 'ignored event'}
    mock_verify_signature.assert_called_once()

@patch('app.verify_signature')
@patch('app.github_client')
@patch('app.openai_client')
def test_webhook_action_ignored(mock_openai_client, mock_github_client, mock_verify_signature, client):
    """
    Test that the webhook endpoint ignores specific pull request actions.

    Mocks the signature verification to return True and sends a 'closed' action,
    expecting an action ignored status.
    """
    mock_verify_signature.return_value = True

    payload = {
        'action': 'closed',
        'repository': {'full_name': 'owner/repo'},
        'pull_request': {'number': 1},
        'installation': {'id': 123}
    }

    response = client.post('/webhook', json=payload, headers={
        'X-Hub-Signature-256': 'sha256=validsignature',
        'X-GitHub-Event': 'pull_request'
    })

    assert response.status_code == 200
    assert response.get_json() == {'status': 'action ignored'}
    mock_verify_signature.assert_called_once()

@patch('app.verify_signature')
@patch('app.github_client')
@patch('app.openai_client')
def test_webhook_successful_review(mock_openai_client, mock_github_client, mock_verify_signature, client):
    """
    Test that the webhook endpoint successfully generates and posts a review comment.

    Mocks necessary components to simulate a successful pull request review process.
    """
    mock_verify_signature.return_value = True

    payload = {
        'action': 'opened',
        'repository': {'full_name': 'owner/repo'},
        'pull_request': {'number': 1},
        'installation': {'id': 123}
    }

    # Mock the GitHub client's method to return a dummy diff
    mock_github_client.get_pull_request_diff.return_value = 'diff content'
    # Mock the OpenAI client's method to return a dummy review comment
    mock_openai_client.generate_review.return_value = 'Review comment'

    response = client.post('/webhook', json=payload, headers={
        'X-Hub-Signature-256': 'sha256=validsignature',
        'X-GitHub-Event': 'pull_request'
    })

    assert response.status_code == 200
    assert response.get_json() == {'status': 'review posted'}
    mock_verify_signature.assert_called_once()
    mock_github_client.get_pull_request_diff.assert_called_once_with('owner/repo', 1, 123)
    mock_openai_client.generate_review.assert_called_once_with('diff content')
    mock_github_client.post_review_comment.assert_called_once_with('owner/repo', 1, 'Review comment', 123)
