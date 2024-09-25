import os
import time
from github import Github, GithubIntegration, PullRequest
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configure logging
# logger = logging.getLogger(__name__)

class GitHubClient:
    """
    Client to interact with GitHub API as a GitHub App.
    Supports multiple installations.

    Attributes:
        app_id (str): GitHub App ID.
        private_key_path (str): Path to the GitHub App's private key.
        private_key (str): Contents of the private key.
        integration (GithubIntegration): GitHub Integration instance.
        token_cache (dict): In-memory cache for installation access tokens.
    """

    def __init__(self):
        """
        Initialize the GitHubClient with necessary credentials.

        Raises:
            ValueError: If GITHUB_APP_ID or GITHUB_PRIVATE_KEY_PATH is not set.
        """
        # Retrieve GitHub App credentials from environment variables
        self.app_id = os.environ.get('GITHUB_APP_ID')
        self.private_key_path = os.environ.get('GITHUB_PRIVATE_KEY_PATH')
        self.private_key = self._load_private_key()
        
        # Validate that necessary credentials are present
        if not self.app_id or not self.private_key:
            raise ValueError("GITHUB_APP_ID and GITHUB_PRIVATE_KEY_PATH must be set in the .env file.")

        # Initialize GithubIntegration with the App ID and private key
        self.integration = GithubIntegration(self.app_id, self.private_key)

        # In-memory cache for installation access tokens to reduce API calls
        self.token_cache = {}

    def _load_private_key(self) -> str:
        """
        Load the private key from the specified path.

        Returns:
            str: Contents of the private key file.
        """
        try:
            with open(self.private_key_path, 'r') as key_file:
                return key_file.read()
        except Exception as e:
            return ""

    def _get_installation_access_token(self, installation_id: int) -> Optional[str]:
        """
        Generate and retrieve an installation access token.
        Caches tokens in-memory to minimize requests.

        Args:
            installation_id (int): GitHub installation ID.

        Returns:
            Optional[str]: Installation access token if successful, None otherwise.
        """
        # Check if token is cached and not expired
        cached_token = self.token_cache.get(installation_id)
        if cached_token and cached_token['expires_at'] > time.time():
            return cached_token['token']
        
        try:
            # Generate a new access token using the integration
            access_token_response = self.integration.get_access_token(installation_id)
            access_token = access_token_response.token
            expires_at = access_token_response.expires_at.timestamp()
            
            # Cache the token with its expiration time
            self.token_cache[installation_id] = {
                'token': access_token,
                'expires_at': expires_at
            }
            return access_token
        except Exception as e:
            return None

    def get_github_client(self, installation_id: int) -> Optional[Github]:
        """
        Get an authenticated Github client for the given installation ID.

        Args:
            installation_id (int): GitHub installation ID.

        Returns:
            Optional[Github]: Authenticated Github client or None if authentication fails.
        """
        # Retrieve the installation access token
        access_token = self._get_installation_access_token(installation_id)
        if not access_token:
            return None

        # Initialize and return the authenticated Github client
        return Github(access_token)

    def get_pull_request_diff(self, repo_full_name: str, pr_number: int, installation_id: int) -> Optional[str]:
        """
        Fetch the diff of a specific pull request for a given installation.

        Args:
            repo_full_name (str): Full name of the repository (e.g., "owner/repo").
            pr_number (int): Pull request number.
            installation_id (int): GitHub installation ID.

        Returns:
            Optional[str]: Diff of the pull request if available, None otherwise.
        """
        try:
            # Get the authenticated Github client
            github_client = self.get_github_client(installation_id)
            if not github_client:
                return None

            # Access the repository and pull request
            repo = github_client.get_repo(repo_full_name)
            pr: PullRequest.PullRequest = repo.get_pull(pr_number)
            files = pr.get_files()
            
            diff = ""
            # Iterate through each file in the pull request and collect diffs
            for file in files:
                if file.patch:  # Ensure there's a diff available
                    diff += f"File: {file.filename}\n"
                    diff += f"{file.patch}\n\n"
            return diff if diff else None
        except Exception as e:
            return None

    def post_review_comment(self, repo_full_name: str, pr_number: int, comment: str, installation_id: int):
        """
        Post a comment on the specified pull request for a given installation.

        Args:
            repo_full_name (str): Full name of the repository (e.g., "owner/repo").
            pr_number (int): Pull request number.
            comment (str): The comment content to post.
            installation_id (int): GitHub installation ID.
        """
        try:
            # Get the authenticated Github client
            github_client = self.get_github_client(installation_id)
            if not github_client:
                return

            # Access the repository and pull request
            repo = github_client.get_repo(repo_full_name)
            pr: PullRequest.PullRequest = repo.get_pull(pr_number)
            # Post the comment on the pull request
            pr.create_issue_comment(comment)
        except Exception as e:
            return