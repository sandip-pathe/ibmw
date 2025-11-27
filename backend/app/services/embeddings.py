"""
Embeddings service with Azure OpenAI and OpenAI providers.
"""
import hashlib
from typing import Optional

import httpx
from loguru import logger
from openai import AsyncAzureOpenAI, AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.core.exceptions import EmbeddingProviderError

settings = get_settings()


class EmbeddingsService:
    """Unified embeddings service supporting Azure OpenAI and OpenAI."""

    def __init__(self):
        self.provider = settings.embeddings_provider
        self.dimension = settings.embedding_dimension
        self.batch_size = settings.embedding_batch_size

        if self.provider == "azure":
            if not settings.azure_openai_endpoint or not settings.azure_openai_key:
                raise EmbeddingProviderError("Azure OpenAI credentials not configured")

            self.client = AsyncAzureOpenAI(
                api_key=settings.azure_openai_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint,
            )
            # Use the model name directly (deployment not required for some endpoints)
            self.model = settings.azure_openai_deployment_embedding or "text-embedding-ada-002"
            logger.info(f"Initialized Azure OpenAI embeddings: {self.model}")

        elif self.provider == "openai":
            if not settings.openai_api_key:
                raise EmbeddingProviderError("OpenAI API key not configured")

            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            self.model = "text-embedding-3-small"
            logger.info(f"Initialized OpenAI embeddings: {self.model}")

        else:
            raise EmbeddingProviderError(f"Unknown provider: {self.provider}")

    @staticmethod
    def compute_text_hash(text: str) -> str:
        """Compute SHA256 hash of text for caching."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            # For Azure OpenAI, try deployment name first, fall back to direct API call
            if self.provider == "azure":
                try:
                    response = await self.client.embeddings.create(
                        model=self.model, input=text, encoding_format="float"
                    )
                except Exception as deploy_error:
                    # If deployment not found, try using Azure OpenAI REST API directly
                    logger.warning(f"Deployment {self.model} not found, trying direct API call")
                    return await self._embed_via_direct_api(text)
            else:
                response = await self.client.embeddings.create(
                    model=self.model, input=text, encoding_format="float"
                )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding for text ({len(text)} chars)")
            return embedding

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise EmbeddingProviderError(f"Failed to generate embedding: {e}")
    
    async def _embed_via_direct_api(self, text: str) -> list[float]:
        """
        Use Azure OpenAI REST API directly (no deployment needed).
        Uses the raw REST endpoint with api-key authentication.
        """
        import httpx
        
        # Azure OpenAI REST API endpoint (not the v1 endpoint)
        # Try available models in order of preference
        models_to_try = [
            "text-embedding-ada-002",
            "text-embedding-3-small", 
            "text-embedding-3-large"
        ]
        
        for model_name in models_to_try:
            url = f"{settings.azure_openai_endpoint.rstrip('/')}/openai/deployments/{model_name}/embeddings?api-version={settings.azure_openai_api_version}"
            
            headers = {
                "Content-Type": "application/json",
                "api-key": settings.azure_openai_key,
            }
            
            payload = {
                "input": text
            }
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, json=payload, headers=headers, timeout=30.0)
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"Successfully used model: {model_name}")
                        return data["data"][0]["embedding"]
                    elif response.status_code == 404:
                        logger.debug(f"Model {model_name} not deployed, trying next...")
                        continue
                    else:
                        response.raise_for_status()
            except Exception as e:
                logger.debug(f"Failed with {model_name}: {e}")
                continue
        
        # If all models fail, raise error
        raise Exception(
            f"No embedding models available. Please deploy one of these models in Azure Portal: "
            f"{', '.join(models_to_try)}"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts in batch.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        try:
            # Process in batches
            all_embeddings = []
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i : i + self.batch_size]

                response = await self.client.embeddings.create(
                    model=self.model, input=batch, encoding_format="float"
                )

                embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(embeddings)

                logger.debug(f"Generated {len(embeddings)} embeddings (batch {i // self.batch_size + 1})")

            return all_embeddings

        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            raise EmbeddingProviderError(f"Failed to generate batch embeddings: {e}")

    async def embed_with_cache(
        self, text: str, redis_client, cache_prefix: str = "emb"
    ) -> list[float]:
        """
        Generate embedding with Redis cache.

        Args:
            text: Text to embed
            redis_client: Redis client instance
            cache_prefix: Cache key prefix

        Returns:
            Embedding vector
        """
        # Compute cache key
        text_hash = self.compute_text_hash(text)
        cache_key = f"{cache_prefix}:{text_hash}"

        try:
            # Check cache
            cached = await redis_client.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for embedding: {cache_key}")
                import json

                return json.loads(cached)

            # Generate embedding
            embedding = await self.embed_text(text)

            # Store in cache
            import json

            await redis_client.setex(
                cache_key, settings.cache_ttl_embeddings, json.dumps(embedding)
            )

            return embedding

        except Exception as e:
            logger.warning(f"Cache operation failed, generating without cache: {e}")
            return await self.embed_text(text)


# Global service instance
embeddings_service = EmbeddingsService()

