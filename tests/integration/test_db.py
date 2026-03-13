# TODO: integrate this with pytest in the future, in the meantime it's fine

import asyncio
from sqlalchemy import text
from core.database import AsyncSessionLocal, engine

async def test():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        print("DB connection OK:", result.scalar())

    await engine.dispose()

asyncio.run(test())