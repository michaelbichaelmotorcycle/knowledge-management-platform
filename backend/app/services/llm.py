from google import genai

MODEL_NAME = "gemini-3.5-flash"

# Initialized lazily so the module can be imported without a Google API key.
# Tests patch this with @patch("app.services.llm.client").
client = None


def _ensure_client():
    """Initialize the Gemini client on first use if not already set."""
    global client
    if client is None:
        client = genai.Client()
    return client


def generate_answer(prompt: str) -> str:
    _ensure_client()
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )

    return response.text
