import os
import openai
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class OpenAIClient:
    """
    Client to interact with OpenAI API.

    Attributes:
        api_key (str): OpenAI API key.
        client (openai.OpenAI): OpenAI client instance.
    """

    def __init__(self):
        """
        Initialize the OpenAIClient with the API key.

        """
        # Initialize the OpenAI client with the API key
        openai.api_key = os.environ.get('OPENAI_API_KEY')
        self.client = openai.OpenAI()

    def generate_review(self, diff: str) -> str:
        """
        Generate a review based on the provided diff using OpenAI's GPT model.

        Args:
            diff (str): The diff of the pull request to review.

        Returns:
            str: Generated review text.
        """
        # Define the system prompt to set the behavior of the AI
        system_prompt = (
            "You are a GitHub bot that provides constructive reviews for pull requests."
        )

        # Define the user prompt including the diff of the pull request
        user_prompt = (
            "Analyze the following code changes and provide a detailed, helpful review.\n\n"
            f"{diff}"
        )

        try:
            # Make a request to the OpenAI API to generate the review
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                max_tokens=2048,
            )
            # Extract the generated review from the response
            review = response.choices[0].message.content
            return review
        except Exception as e:
            # Handle any errors that occur during the API call
            print(f"Error generating review: {e}")
            return "Sorry, I couldn't generate a review at this time."