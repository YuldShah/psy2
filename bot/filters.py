from aiogram.filters import Filter
from aiogram.types import Message
from bot.database.main import get_db_pool
from bot.config import ADMIN_IDS

class IsBannedFilter(Filter):
    """Filter to check if a user is banned"""
    
    async def __call__(self, message: Message) -> bool:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT banned FROM users WHERE id = $1",
                message.from_user.id
            )
            return user and user['banned']

class IsAdminFilter(Filter):
    """Filter to check if a user is an admin"""
    
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ADMIN_IDS
