# GitHubPRReviewBot

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.0+-blue.svg)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [GitHub App Setup](#github-app-setup)

## Overview

**GitHubPRReviewBot** is an intelligent GitHub bot designed to automatically review pull requests (PRs) using OpenAI's language models. By integrating seamlessly with GitHub's webhook system, this bot listens for PR events, analyzes code diffs, and provides constructive feedback to streamline the code review process.

## Features

- **Automated Reviews:** Leverages OpenAI to generate insightful and constructive PR reviews.
- **Webhook Integration:** Listens to GitHub webhook events for real-time PR activity.
- **Secure:** Verifies webhook signatures to ensure authenticity and integrity.
- **Scalable:** Supports multiple GitHub App installations with efficient token caching.
- **Customizable:** Easily adjust prompts and configurations to fit your project's needs.

## Installation

### Prerequisites

- Python 3.8 or higher
- GitHub Account with permissions to create GitHub Apps
- OpenAI API Key

### Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/awsomedod/GitHubPRReviewBot.git
   cd GitHubPRReviewBot
   ```

2. **Create and Activate a Virtual Environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**

   Create a `.env` file in the root directory:

   ```bash
   touch .env
   ```

   Add the following variables to `.env`:

   ```env
   GITHUB_APP_ID=your_github_app_id
   GITHUB_PRIVATE_KEY_PATH=path/to/your/private-key.pem
   WEBHOOK_SECRET=your_webhook_secret
   OPENAI_API_KEY=your_openai_api_key
   PORT=5000  # Optional: Defaults to 5000 if not set
   ```

## Configuration

### Environment Variables

- `GITHUB_APP_ID`: Your GitHub App's ID.
- `GITHUB_PRIVATE_KEY_PATH`: Path to the GitHub App's private key file.
- `WEBHOOK_SECRET`: Secret key to verify incoming GitHub webhooks.
- `OPENAI_API_KEY`: Your OpenAI API key.
- `PORT`: Port number on which the Flask app will run (default is `5000`).

### GitHub App Credentials

Ensure that your GitHub App has the necessary permissions to read pull requests and post comments. Download the private key when setting up the GitHub App and specify its path in the `.env` file.

## Usage

1. **Run the Flask Application**

   ```bash
   python app.py
   ```

   The app will start and listen for incoming webhook events on the specified `PORT`.

2. **Set Up Webhooks**

   Configure your GitHub repository to send webhook events to your server's `/webhook` endpoint. Ensure that the webhook secret matches the `WEBHOOK_SECRET` in your `.env` file.

3. **Review PRs**

   When a pull request is opened or synchronized, the bot will automatically generate a review and post it as a comment on the PR.

## GitHub App Setup

1. **Create a GitHub App**

   - Navigate to [GitHub Settings > Developer settings > GitHub Apps](https://github.com/settings/apps).
   - Click on "New GitHub App" and fill in the required details.
   - Set the **Webhook URL** to your server's `/webhook` endpoint.
   - Generate a new **Private Key** and save it securely.
   - Configure the necessary **Permissions**:
     - **Pull requests**: Read & Write
     - **Contents**: Read
   - Subscribe to the following **Events**:
     - `Pull request`

2. **Install the GitHub App**

   - After creating the app, install it on the desired repositories.