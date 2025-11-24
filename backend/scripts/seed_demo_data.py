#!/usr/bin/env python
"""
Seed demo data for hackathon/testing.

This script:
1. Loads sample RBI regulations
2. Creates embeddings
3. Stores in database
"""
import asyncio
import json
from pathlib import Path

from loguru import logger

from app.config import get_settings
from app.database import db
from app.models.database import RegulationChunkQueries
from app.services.embeddings import embeddings_service
from app.workers.queue import job_queue

settings = get_settings()


# Sample RBI regulations
SAMPLE_REGULATIONS = [
    {
        "rule_id": "RBI_AUTH_001",
        "source_document": "RBI Master Direction - Digital Payment Security",
        "chunks": [
            {
                "section": "Authentication Requirements",
                "text": "All digital payment systems must implement multi-factor authentication (MFA) "
                "for transactions above ₹5,000. MFA must include at least two of the following: "
                "something the user knows (password/PIN), something the user has (OTP/hardware token), "
                "or something the user is (biometric verification).",
            },
            {
                "section": "Session Management",
                "text": "Payment application sessions must timeout after 10 minutes of inactivity. "
                "Users must be required to re-authenticate after session expiry. Session tokens "
                "must be securely generated using cryptographic random number generators.",
            },
        ],
    },
    {
        "rule_id": "RBI_DATA_001",
        "source_document": "RBI Guidelines on Data Localization",
        "chunks": [
            {
                "section": "Data Storage Requirements",
                "text": "All payment system operators must ensure that payment data is stored only in India. "
                "A copy of the data may be stored abroad for overseas operations, but the entire data "
                "must be stored in systems located in India.",
            },
            {
                "section": "Data Encryption",
                "text": "All sensitive payment data must be encrypted at rest and in transit using "
                "industry-standard encryption algorithms (AES-256 or higher). Encryption keys must "
                "be managed using a secure key management system with role-based access controls.",
            },
        ],
    },
    {
        "rule_id": "RBI_AUDIT_001",
        "source_document": "RBI Cyber Security Framework",
        "chunks": [
            {
                "section": "Audit Logging",
                "text": "All payment systems must maintain comprehensive audit logs of all transactions, "
                "authentication attempts, and administrative actions. Logs must be retained for "
                "a minimum of 5 years and must be tamper-proof. Log entries must include timestamp, "
                "user ID, action performed, and IP address.",
            },
            {
                "section": "Security Monitoring",
                "text": "Payment service providers must implement real-time security monitoring and "
                "alerting systems. Suspicious activities such as multiple failed login attempts, "
                "unusual transaction patterns, or access from blacklisted IP addresses must trigger "
                "immediate alerts to the security team.",
            },
        ],
    },
    {
        "rule_id": "RBI_API_001",
        "source_document": "RBI Guidelines on APIs for Payment Systems",
        "chunks": [
            {
                "section": "API Rate Limiting",
                "text": "All payment APIs must implement rate limiting to prevent abuse and DoS attacks. "
                "Rate limits must be enforced per API key/user and should be configurable based on "
                "the sensitivity of the endpoint. Exceeded rate limits must result in HTTP 429 responses.",
            },
            {
                "section": "API Authentication",
                "text": "Payment APIs must use OAuth 2.0 or equivalent token-based authentication. "
                "API keys must be transmitted securely via HTTPS and must never be exposed in URLs "
                "or client-side code. API keys must have expiration dates and rotation policies.",
            },
        ],
    },
]


async def seed_regulations():
    """Seed regulation chunks into database."""
    logger.info("Starting demo data seeding...")

    # Connect
    await db.connect()
    await job_queue.connect_async()

    all_chunks = []

    for regulation in SAMPLE_REGULATIONS:
        rule_id = regulation["rule_id"]
        source_doc = regulation["source_document"]

        logger.info(f"Processing regulation: {rule_id}")

        for i, chunk_data in enumerate(regulation["chunks"]):
            chunk_text = chunk_data["text"]

            # Compute hash
            import hashlib

            chunk_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()

            # Generate embedding
            logger.info(f"  Generating embedding for chunk {i+1}/{len(regulation['chunks'])}")
            embedding = await embeddings_service.embed_text(chunk_text)

            chunk = {
                "rule_id": rule_id,
                "rule_section": chunk_data["section"],
                "source_document": source_doc,
                "chunk_text": chunk_text,
                "chunk_index": i,
                "chunk_hash": chunk_hash,
                "embedding": embedding,
                "nl_summary": None,  # Could generate with LLM
                "metadata": {"category": "compliance", "demo": True},
            }

            all_chunks.append(chunk)

    # Insert into database
    logger.info(f"Inserting {len(all_chunks)} regulation chunks into database...")
    async with db.acquire() as conn:
        count = await RegulationChunkQueries.insert_batch(conn, all_chunks)

    logger.info(f"✅ Successfully seeded {count} regulation chunks")

    # Disconnect
    await job_queue.disconnect_async()
    await db.disconnect()


async def create_sample_installation():
    """Create a sample installation for testing (optional)."""
    logger.info("Creating sample installation...")

    await db.connect()

    sample_installation = {
        "installation_id": 99999,
        "account_id": 12345,
        "account_login": "demo-org",
        "app_id": settings.github_app_id,
        "target_type": "Organization",
        "permissions": {"contents": "read", "metadata": "read"},
        "events": ["push", "pull_request"],
        "repositories": [
            {"id": 1, "name": "demo-fintech-app", "full_name": "demo-org/demo-fintech-app"}
        ],
    }

    from app.models.database import InstallationQueries

    async with db.acquire() as conn:
        installation_id = await InstallationQueries.upsert(conn, sample_installation)

    logger.info(f"✅ Created sample installation: {installation_id}")

    await db.disconnect()


def main():
    """Main entry point."""
    if not settings.enable_demo_seed:
        logger.warning("Demo seeding disabled (ENABLE_DEMO_SEED=false)")
        return

    logger.info("=" * 60)
    logger.info("Fintech Compliance Engine - Demo Data Seeding")
    logger.info("=" * 60)

    # Seed regulations
    asyncio.run(seed_regulations())

    # Optional: create sample installation
    # asyncio.run(create_sample_installation())

    logger.info("=" * 60)
    logger.info("✅ Demo data seeding complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
