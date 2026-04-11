"""
Re-embed all chunks and alumni profiles using Bedrock Titan Embed Text v2.

Run after migration 006:
    docker compose exec api python reembed_bedrock.py
"""
import asyncio
import json
import logging
import time
from sqlalchemy import select, text, update
from app.core.database import async_session as AsyncSessionLocal
from app.services.ai_providers import get_embedding_provider

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)

BATCH_SIZE = 20  # Titan supports up to 25 texts/request via individual calls


async def reembed_chunks():
    from app.models.models import Chunk
    provider = get_embedding_provider()

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Chunk.id, Chunk.content))
        rows = result.all()
        log.info(f"Re-embedding {len(rows)} chunks...")

        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i: i + BATCH_SIZE]
            ids = [r.id for r in batch]
            texts = [r.content for r in batch]

            embeddings = await provider.embed(texts)

            for chunk_id, emb in zip(ids, embeddings):
                await db.execute(
                    update(Chunk).where(Chunk.id == chunk_id).values(embedding=emb)
                )
            await db.commit()

            done = min(i + BATCH_SIZE, len(rows))
            log.info(f"  chunks {done}/{len(rows)}")
            time.sleep(0.1)  # gentle rate limiting

    log.info("Chunks re-embedded.")


async def reembed_alumni():
    from app.models.models import AlumniProfile
    provider = get_embedding_provider()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(
                AlumniProfile.id,
                AlumniProfile.bio,
                AlumniProfile.skills,
                AlumniProfile.interests,
                AlumniProfile.major,
                AlumniProfile.current_role,
                AlumniProfile.current_company,
            )
        )
        rows = result.all()
        log.info(f"Re-embedding {len(rows)} alumni profiles...")

        for row in rows:
            profile_text = " ".join(filter(None, [
                row.bio,
                row.major,
                row.current_role,
                row.current_company,
            ]))
            skills_text = json.dumps(row.skills) if row.skills else ""
            interests_text = json.dumps(row.interests) if row.interests else ""

            texts = [
                profile_text or "SBU alumni",
                skills_text or "no skills listed",
                interests_text or "no interests listed",
            ]
            embeddings = await provider.embed(texts)

            await db.execute(
                update(AlumniProfile)
                .where(AlumniProfile.id == row.id)
                .values(
                    profile_embedding=embeddings[0],
                    skills_embedding=embeddings[1],
                    interests_embedding=embeddings[2],
                )
            )
            await db.commit()

        log.info(f"Alumni profiles re-embedded.")


async def main():
    log.info("Starting Bedrock re-embedding...")
    await reembed_chunks()
    await reembed_alumni()
    log.info("Done.")


if __name__ == "__main__":
    asyncio.run(main())
