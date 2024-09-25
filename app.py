import os
from flask import Flask, request, jsonify
from github_client import GitHubClient
from openai_client import OpenAIClient
from dotenv import load_dotenv
import hmac
import hashlib

# Load environment variables from .env
load_dotenv()

# Determine the absolute path for app.log
# log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.log')

# print(log_file_path)

# # Configure logging
# logging.basicConfig(
#     filename=log_file_path,     # Absolute path to log file
#     filemode='a',                # Append mode ('w' for overwrite)
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Log format
#     level=logging.INFO
# )
# logger = logging.getLogger(__name__)
# logger.info("Starting the application...")

# Initialize the Flask application
app = Flask(__name__)

# Initialize GitHub Client
try:
    github_client = GitHubClient()
except ValueError as ve:
    exit(1)

# Initialize OpenAI Client
openai_client = OpenAIClient()

def verify_signature(request):
    """
    Verify GitHub webhook signature to ensure payload authenticity.

    Args:
        request (flask.Request): The incoming HTTP request from GitHub.

    Returns:
        bool: True if the signature is valid, False otherwise.
    """
    # Retrieve the signature from the request headers
    signature = request.headers.get('X-Hub-Signature-256')
    if signature is None:
        return False
    # Split the signature into hash algorithm and hash value
    sha_name, signature = signature.split('=')
    if sha_name != 'sha256':
        return False
    # Create HMAC object using the webhook secret and request data
    mac = hmac.new(os.environ.get('WEBHOOK_SECRET').encode(), msg=request.data, digestmod=hashlib.sha256)
    # Compare the calculated hash with the signature provided
    return hmac.compare_digest(mac.hexdigest(), signature)

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Handle GitHub webhook events for pull requests.

    This endpoint listens for GitHub webhook events, verifies their authenticity,
    processes pull request actions (opened or synchronized), generates a review
    using OpenAI, and posts the review as a comment on the pull request.

    Returns:
        flask.Response: JSON response with the status of the operation.
    """
    # Verify webhook signature
    if not verify_signature(request):
        return jsonify({'status': 'invalid signature'}), 403

    # Get the GitHub event type from headers
    event = request.headers.get('X-GitHub-Event')
    if event != 'pull_request':
        return jsonify({'status': 'ignored event'}), 200

    # Parse the JSON payload from the request
    payload = request.json
    action = payload.get('action')

    # Only process specific pull request actions
    if action not in ['opened', 'synchronize']:
        return jsonify({'status': 'action ignored'}), 200

    # Extract necessary details from the payload
    repo_full_name = payload['repository']['full_name']
    pr_number = payload['pull_request']['number']
    installation_id = payload.get('installation', {}).get('id')

    if not installation_id:
        return jsonify({'status': 'installation ID missing'}), 400

    # Fetch PR diff using the correct installation
    pr_diff = github_client.get_pull_request_diff(repo_full_name, pr_number, installation_id)

    if not pr_diff:
        return jsonify({'status': 'no changes detected'}), 200

    # Generate review using OpenAI
    review = openai_client.generate_review(pr_diff)

    # Post review as a comment on the PR
    github_client.post_review_comment(repo_full_name, pr_number, review, installation_id)

    return jsonify({'status': 'review posted'}), 200

if __name__ == '__main__':
    """
    Entry point of the Flask application.
    Runs the app on the specified PORT or defaults to 5000.
    """
    PORT = int(os.environ.get('PORT', 5000))
    app.run(debug=True, port=PORT)