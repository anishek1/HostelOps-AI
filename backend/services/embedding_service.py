"""
services/embedding_service.py — HostelOps AI
===============================================
Generates text embeddings via HuggingFace Inference API (free tier).
Used for semantic deduplication of complaints.

If HF_API_KEY is not set, all functions return None gracefully —
the system falls back to category+location matching.
"""
import logging
from typing import Optional

import httpx
from config import settings

logger = logging.getLogger(__name__)

HF_API_URL = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{settings.EMBEDDING_MODEL}"


async def generate_embedding(text: str) -> Optional[list[float]]:
    """
    Generate a 384-dim embedding vector for the given text.
    Returns None if HF_API_KEY is not configured or the API call fails.
    """
    if not settings.HF_API_KEY:
        return None

    headers = {"Authorization": f"Bearer {settings.HF_API_KEY}"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                HF_API_URL,
                headers=headers,
                json={"inputs": text, "options": {"wait_for_model": True}},
            )
            response.raise_for_status()
            embedding = response.json()

            if isinstance(embedding, list) and len(embedding) == settings.EMBEDDING_DIM:
                return embedding
            # Some models return [[...]], unwrap
            if isinstance(embedding, list) and len(embedding) == 1:
                return embedding[0]
            logger.warning(f"[embedding] Unexpected response shape: {type(embedding)}")
            return None

    except Exception as e:
        logger.warning(f"[embedding] HuggingFace API call failed: {e}")
        return None


async def find_similar_by_vector(
    embedding: list[float],
    hostel_id: str,
    exclude_id: str | None = None,
    threshold: float | None = None,
    limit: int = 5,
    db=None,
) -> list[dict]:
    """
    Find complaints with similar embeddings using pgvector cosine distance.
    Returns list of {id, similarity, category, status} dicts.
    """
    if db is None:
        return []
    if threshold is None:
        threshold = settings.SIMILARITY_THRESHOLD

    import uuid
    from sqlalchemy import select, text
    from models.complaint import Complaint

    # pgvector cosine distance: 1 - (a <=> b) gives similarity
    # Filter to same hostel, open statuses, above similarity threshold
    sql = text("""
        SELECT id, category, status,
               1 - (embedding <=> :vec::vector) AS similarity
        FROM complaints
        WHERE hostel_id = :hostel_id
          AND embedding IS NOT NULL
          AND (:exclude_id IS NULL OR id != :exclude_id::uuid)
          AND status IN ('INTAKE', 'CLASSIFIED', 'AWAITING_APPROVAL', 'ASSIGNED', 'IN_PROGRESS')
          AND 1 - (embedding <=> :vec::vector) >= :threshold
        ORDER BY embedding <=> :vec::vector
        LIMIT :lim
    """)

    result = await db.execute(
        sql,
        {
            "vec": str(embedding),
            "hostel_id": str(hostel_id),
            "exclude_id": exclude_id,
            "threshold": threshold,
            "lim": limit,
        },
    )
    rows = result.fetchall()

    return [
        {
            "id": str(row.id),
            "category": row.category,
            "status": row.status,
            "similarity": round(float(row.similarity), 3),
        }
        for row in rows
    ]
