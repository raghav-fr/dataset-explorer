from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.config import settings
from app.services import gemini_client

_client: QdrantClient | None = None


def get_client() -> QdrantClient:
    global _client

    if _client is None:
        _client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )

    return _client


def collection_name(dataset_id: str) -> str:
    return f"{settings.qdrant_collection_prefix}{dataset_id}"


def get_embedding_dimension() -> int:
    """
    Detect embedding dimension automatically.
    Works for any embedding model.
    """
    embedding = gemini_client.embed_text(
        "dimension check",
        task_type="retrieval_document",
    )

    return len(embedding)


def ensure_collection(dataset_id: str):

    client = get_client()

    name = collection_name(dataset_id)

    dimension = get_embedding_dimension()

    if client.collection_exists(name):
        info = client.get_collection(name)

        current_dim = info.config.params.vectors.size

        if current_dim != dimension:
            print(
                f"Embedding dimension changed "
                f"({current_dim} -> {dimension}), recreating collection..."
            )

            client.delete_collection(name)

    if not client.collection_exists(name):
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=dimension,
                distance=Distance.COSINE,
            ),
        )

    return name


def index_chunks(dataset_id: str, chunks: list[str], batch_size: int = 256):

    client = get_client()

    name = ensure_collection(dataset_id)

    total = 0

    for start in range(0, len(chunks), batch_size):

        batch = chunks[start:start + batch_size]

        vectors = gemini_client.embed_batch(
            batch,
            task_type="retrieval_document",
        )

        points = [

            PointStruct(
                id=start + i,
                vector=vectors[i],
                payload={
                    "text": batch[i],
                    "chunk_index": start + i,
                },
            )

            for i in range(len(batch))

        ]

        client.upsert(
            collection_name=name,
            points=points,
        )

        total += len(batch)

    return total


def search(dataset_id: str, query: str, top_k: int = 6):

    client = get_client()

    name = collection_name(dataset_id)

    if not client.collection_exists(name):
        return []

    query_vector = gemini_client.embed_text(
        query,
        task_type="retrieval_query",
    )

    results = client.query_points(
        collection_name=name,
        query=query_vector,
        limit=top_k,
    ).points

    return [
        r.payload["text"]
        for r in results
        if r.payload and "text" in r.payload
    ]


def is_indexed(dataset_id: str) -> bool:
    client = get_client()
    name = collection_name(dataset_id)
    if not client.collection_exists(name):
        return False
    info = client.get_collection(name)
    return info.points_count > 0