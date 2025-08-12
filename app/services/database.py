import asyncpg
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, dsn):
        self.dsn = dsn
        self.pool = None

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(dsn=self.dsn)
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
