"""Run once (after setting MOSS_PROJECT_ID / MOSS_PROJECT_KEY) to create the Moss
index from the curated troubleshooting doc set:

    python -m scripts.seed_index

Re-run any time app/data/docs.py changes - create_index recreates the index.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data.docs import DOCS
from app.moss_client import seed_index


async def main():
    print(f"Seeding {len(DOCS)} documents into Moss index...")
    await seed_index(DOCS)
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
