import asyncpg
import logging
from bot.config import DATABASE_URL

pool = None

async def init_db():
    global pool
    try:
        pool = await asyncpg.create_pool(dsn=DATABASE_URL)
        logging.info("Database pool created.")
        
        # Create tables
        async with pool.acquire() as conn:
            with open('bot/database/schema.sql', 'r') as f:
                schema = f.read()
            await conn.execute(schema)
            logging.info("Database schema initialized.")
            
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")
        raise

async def get_db_pool():
    global pool
    return pool

async def close_db():
    global pool
    if pool:
        await pool.close()
        logging.info("Database pool closed.")
