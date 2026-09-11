"""
Embedding generation using multilingual-e5-large.
Runs on GPU if available, otherwise CPU.
"""

import logging
from typing import List, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import os

logger = logging.getLogger(__name__)

MODEL_NAME = "intfloat/multilingual-e5-large"


class EmbeddingEngine:
    """Generate text embeddings for listings using multilingual-e5-large."""

    def __init__(self, device: Optional[str] = None):
        """
        Initialize embedding model.

        Args:
            device: 'cuda', 'cpu', or None for auto-detect
        """
        if device is None:
            device = "cuda" if self._has_cuda() else "cpu"

        self.device = device
        logger.info(f"Loading {MODEL_NAME} on device: {device}")

        self.model = SentenceTransformer(MODEL_NAME, device=device)
        self.dimension = 1024  # multilingual-e5-large output size

    @staticmethod
    def _has_cuda() -> bool:
        """Check if CUDA/GPU is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Embed a list of texts.

        Args:
            texts: List of text strings to embed
            batch_size: Batch size for processing

        Returns:
            np.ndarray of shape (len(texts), 1024)
        """
        if not texts:
            return np.array([])

        logger.debug(f"Embedding {len(texts)} texts with batch_size={batch_size}")

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        return embeddings

    def embed_single(self, text: str) -> np.ndarray:
        """Embed a single text string."""
        return self.embed_texts([text])[0]

    def embed_listing(self, title: str, description: str = "") -> np.ndarray:
        """
        Embed a marketplace listing (title + description).

        Standard format for e5 models: "passage: {text}"
        """
        text = f"passage: {title}"
        if description:
            text += f" {description[:200]}"

        return self.embed_single(text)

    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two embedding vectors."""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(vec1, vec2) / (norm1 * norm2))


class BatchEmbedder:
    """
    Batch embedding processor - embeds listings in batches and saves to DB.
    Designed for async workers.
    """

    def __init__(self, device: Optional[str] = None):
        self.engine = EmbeddingEngine(device=device)

    async def embed_batch(
        self,
        listings: List[dict],
        db_session=None,
    ) -> int:
        """
        Embed a batch of listings and save embeddings to database.

        Args:
            listings: List of listing dicts with 'id', 'title', 'description'
            db_session: SQLAlchemy session for saving

        Returns:
            Number of successfully embedded listings
        """
        if not listings:
            return 0

        # Prepare texts for embedding
        texts = []
        listing_ids = []

        for listing in listings:
            title = listing.get("title", "")
            description = listing.get("description", "")

            if not title:
                continue

            text = f"passage: {title}"
            if description:
                text += f" {description[:200]}"

            texts.append(text)
            listing_ids.append(listing.get("id"))

        if not texts:
            return 0

        # Generate embeddings
        embeddings = self.engine.embed_texts(texts)

        # Save to database (if session provided)
        count = 0
        if db_session is not None:
            from sqlalchemy import update
            from db.models import Listing  # Will be created later

            for listing_id, embedding in zip(listing_ids, embeddings):
                try:
                    # Convert numpy array to list for PostgreSQL
                    db_session.execute(
                        update(Listing).where(Listing.id == listing_id)
                        .values(embedding=embedding.tolist())
                    )
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to save embedding for listing {listing_id}: {e}")

            try:
                db_session.commit()
            except Exception as e:
                logger.error(f"Database commit failed: {e}")
                db_session.rollback()

        return count

    def embed_and_return(self, listings: List[dict]) -> List[Tuple[str, List[float]]]:
        """
        Embed listings without saving, return embeddings.

        Returns:
            List of (listing_id, embedding) tuples
        """
        if not listings:
            return []

        texts = []
        listing_ids = []

        for listing in listings:
            title = listing.get("title", "")
            if not title:
                continue

            description = listing.get("description", "")
            text = f"passage: {title}"
            if description:
                text += f" {description[:200]}"

            texts.append(text)
            listing_ids.append(listing.get("id"))

        if not texts:
            return []

        embeddings = self.engine.embed_texts(texts)

        return [
            (lid, emb.tolist()) for lid, emb in zip(listing_ids, embeddings)
        ]
