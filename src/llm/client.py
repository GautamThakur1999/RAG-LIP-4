from groq import Groq
import os
import sys

# Add project root to sys.path if not there
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import settings

class GroqClient:
    def __init__(self):
        # We allow it to instantiate even if key is empty (for testing)
        self.api_key = settings.groq_api_key or os.getenv("GROQ_API_KEY", "")
        self.model = "llama-3.1-8b-instant" # Switched to 8b to bypass 70b rate limits
        
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
        else:
            self.client = None

    def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
        """
        Sends the system and user prompt to Groq and returns the generated text.
        """
        if not self.client:
            return "Error: GROQ_API_KEY is not set in config or .env"
            
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
                model=self.model,
                temperature=temperature,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            return f"Error connecting to Groq API: {str(e)}"

if __name__ == "__main__":
    client = GroqClient()
    if client.client:
        print(client.complete("You are a helpful assistant.", "Say hello world!"))
    else:
        print("Skipping test, no API key found.")
