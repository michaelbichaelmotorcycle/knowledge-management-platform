from google import genai

MODEL_NAME = "gemini-3.5-flash"

client = genai.Client()


def generate_answer(prompt: str) -> str:
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )

    return response.text
