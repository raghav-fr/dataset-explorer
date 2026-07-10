from app.services import qdrant_store, gemini_client

SYSTEM_INSTRUCTION = (
    "You are a data analyst assistant. Answer the user's question about their "
    "dataset using ONLY the provided context chunks. If the context does not "
    "contain enough information to answer confidently, say so explicitly "
    "rather than guessing. Be concise and cite specific numbers from the "
    "context where relevant."
)


def answer_question(dataset_id: str, question: str, top_k: int = 6) -> tuple[str, list[str]]:
    chunks = qdrant_store.search(dataset_id, question, top_k=top_k)

    if not chunks:
        return (
            "I couldn't find relevant indexed data for this dataset. "
            "Make sure the dataset has been processed for chat first.",
            [],
        )

    context = "\n\n---\n\n".join(chunks)
    prompt = f"""
Context chunks from the dataset:
{context}

Question: {question}

Answer using only the context above.
"""
    answer = gemini_client.generate_text(prompt, system_instruction=SYSTEM_INSTRUCTION)
    return answer, chunks
