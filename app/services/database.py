import asyncpg
import logging
import os

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.dsn = os.getenv("DATABASE_URL")
        self.pool = None

    async def connect(self):
        if not self.dsn:
            logger.error("DATABASE_URL is not set in environment variables.")
            raise ValueError("Missing DATABASE_URL")

        try:
            # Если Railway требует SSL — убери ssl=False
            self.pool = await asyncpg.create_pool(dsn=self.dsn, ssl=False)
            logger.info("Database pool created")
        except Exception as e:
            logger.error("Failed to connect to DB: %s", str(e))
            raise

    async def execute(self, query, *args):
        if self.pool is None:
            await self.connect()

        try:
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")  # Пинг
                return await conn.execute(query, *args)
        except Exception as e:
            logger.error("DB execution failed: %s", str(e))
            raise
