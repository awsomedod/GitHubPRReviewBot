import os
import time
import pytest
from unittest.mock import patch, MagicMock
from github_client import GitHubClient
from datetime import datetime, timedelta

@pytest.fixture
def github_client_instance():
    """
    Pytest fixture to create an instance of GitHubClient with mocked GithubIntegration.

    Mocks the access token retrieval to return a fake token with an expiration time.
    """
    with patch('github_client.GithubIntegration') as mock_integration:
        # Mock expires_at as a datetime object set to 1000 seconds in the future
        mock_integration.return_value.get_access_token.return_value = MagicMock(
            token='fake_token', 
            expires_at=datetime.now() + timedelta(seconds=1000)
        )
        client = GitHubClient()
        yield client

@patch('github_client.open')
def test_load_private_key(mock_open, github_client_instance):
    """
    Test that GitHubClient correctly loads the private key from the specified path.

    Mocks the file open operation to return a fake private key.
    """
    mock_open.return_value.__enter__.return_value.read.return_value = 'fake_private_key'
    client = GitHubClient()
    assert client.private_key == 'fake_private_key'
    mock_open.assert_called_once_with(os.environ.get('GITHUB_PRIVATE_KEY_PATH'), 'r')

@patch('github_client.time.time')
def test_get_installation_access_token_cached(mock_time, github_client_instance):
    """
    Test that GitHubClient returns a cached access token if it is still valid.

    Mocks the current time to simulate token caching behavior.
    """
    installation_id = 123
    # Current mocked time
    mock_time.return_value = 1000
    # First call to cache the token
    token = github_client_instance._get_installation_access_token(installation_id)
    assert token == 'fake_token'
    # Ensure the token is cached with correct token value
    assert installation_id in github_client_instance.token_cache
    assert github_client_instance.token_cache[installation_id]['token'] == 'fake_token'
    
    # Advance time to within the token's valid period
    mock_time.return_value = 1500
    token = github_client_instance._get_installation_access_token(installation_id)
    assert token == 'fake_token'
    # The cached token should still be used, so no new access token request
    github_client_instance.integration.get_access_token.assert_called_once()

@patch('github_client.time.time')
def test_get_installation_access_token_expired(mock_time, github_client_instance):
    """
    Test that GitHubClient fetches a new access token when the cached token has expired.

    Mocks the current time to simulate token expiration and renewal.
    """
    installation_id = 123
    # Initial time
    initial_time = datetime.now()
    mock_time.return_value = initial_time.timestamp()
    
    # First call to cache the token
    token = github_client_instance._get_installation_access_token(installation_id)
    assert token == 'fake_token'
    
    # Advance time beyond the token's expiration
    new_time = initial_time + timedelta(seconds=1500)
    mock_time.return_value = new_time.timestamp()
    
    with patch.object(github_client_instance.integration, 'get_access_token') as mock_get_token:
        mock_get_token.return_value = MagicMock(
            token='new_fake_token', 
            expires_at=new_time + timedelta(seconds=1000)
        )
        token = github_client_instance._get_installation_access_token(installation_id)
        assert token == 'new_fake_token'
        mock_get_token.assert_called_once()

@patch('github_client.Github')
def test_get_github_client(mock_github, github_client_instance):
    """
    Test that GitHubClient correctly initializes a GitHub client with the access token.

    Mocks the PyGithub Github class to verify client initialization.
    """
    installation_id = 123
    client = github_client_instance.get_github_client(installation_id)
    assert client is not None
    mock_github.assert_called_once_with('fake_token')

@patch('github_client.Github')
def test_get_pull_request_diff(mock_github, github_client_instance):
    """
    Test that GitHubClient can fetch the diff of a pull request.

    Mocks the GitHub API responses to return a predefined diff content.
    """
    repo_mock = MagicMock()
    pr_mock = MagicMock()
    file_mock = MagicMock()
    file_mock.patch = 'diff content'
    file_mock.filename = 'file.py'
    pr_mock.get_files.return_value = [file_mock]
    repo_mock.get_pull.return_value = pr_mock
    mock_repo = MagicMock()
    mock_repo.get_repo.return_value = repo_mock
    mock_github.return_value = mock_repo

    diff = github_client_instance.get_pull_request_diff('owner/repo', 1, 123)
    expected_diff = "File: file.py\ndiff content\n\n"
    assert diff == expected_diff

@patch('github_client.Github')
def test_post_review_comment(mock_github, github_client_instance):
    """
    Test that GitHubClient can post a review comment on a pull request.

    Mocks the GitHub API to verify that the comment is posted with correct content.
    """
    repo_mock = MagicMock()
    pr_mock = MagicMock()
    repo_mock.get_pull.return_value = pr_mock
    mock_repo = MagicMock()
    mock_repo.get_repo.return_value = repo_mock
    mock_github.return_value = mock_repo

    github_client_instance.post_review_comment('owner/repo', 1, 'Great work!', 123)
    pr_mock.create_issue_comment.assert_called_once_with('Great work!')
