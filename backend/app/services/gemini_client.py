import requests
import json
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def generate_text(prompt: str, system_instruction: str | None = None) -> str:
    if not settings.openrouter_api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Add it to your .env file."
        )

    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.openrouter_model,
        "messages": messages,
        "stream": True
    }

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        data=json.dumps(payload),
        stream=True,
        timeout=60
    )
    response.raise_for_status()

    full_text = ""
    from loguru import logger

    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8').strip()
            if decoded_line.startswith("data: "):
                data_str = decoded_line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    chunk_json = json.loads(data_str)
                    choices = chunk_json.get('choices', [])
                    if choices:
                        delta = choices[0].get('delta', {})
                        content = delta.get('content')
                        if content:
                            full_text += content

                    # Usage info / reasoning tokens in the final chunk
                    usage = chunk_json.get('usage')
                    if usage:
                        reasoning_tokens = usage.get('reasoning_tokens') or usage.get('reasoningTokens')
                        if reasoning_tokens is not None:
                            logger.info(f"Reasoning tokens: {reasoning_tokens}")
                except Exception:
                    pass

    return full_text.strip()


def embed_batch_openrouter(texts: list[str]) -> list[list[float]]:
    if not settings.openrouter_api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Add it to your .env file."
        )
    url = "https://openrouter.ai/api/v1/embeddings"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.openrouter_api_key}"
    }

    # Custom structured input payload as requested
    input_data = [
        {
            "content": [
                {"type": "text", "text": text}
            ]
        }
        for text in texts
    ]

    payload = {
        "model": settings.openrouter_embedding_model,
        "input": input_data,
        "encodingFormat": "float"
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    response_json = response.json()
    return [item["embedding"] for item in response_json["data"]]


def embed_text_openrouter(text: str) -> list[float]:
    return embed_batch_openrouter([text])[0]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def embed_text(text: str, task_type: str = "retrieval_document") -> list[float]:
    return embed_text_openrouter(text)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def embed_batch(texts: list[str], task_type: str = "retrieval_document") -> list[list[float]]:
    return embed_batch_openrouter(texts)
