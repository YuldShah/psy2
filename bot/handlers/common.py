from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from bot.database.main import get_db_pool
from bot.states.states import StudentStates
from bot.keyboards.student import get_main_menu

router = Router()

from bot.config import ADMIN_IDS

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    pool = await get_db_pool()
    user_id = message.from_user.id
    
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        
        # Check if banned
        if user and user['banned']:
            ban_msg = "🚫 <b>You are banned from using this bot.</b>"
            if user['ban_reason']:
                ban_msg += f"\n\n<b>Reason:</b> {user['ban_reason']}"
            await message.answer(ban_msg)
            return
        
        if not user:
            if user_id in ADMIN_IDS:
                # Admin registration
                await conn.execute(
                    "INSERT INTO users (id, full_name, role) VALUES ($1, $2, 'psychologist')",
                    user_id, message.from_user.full_name
                )
                from bot.keyboards.psychologist import get_psychologist_menu
                await message.answer("Welcome, Psychologist! You have been registered.", reply_markup=get_psychologist_menu())
            else:
                # Student registration
                await message.answer("Welcome! It seems you are new here.\nPlease enter your Full Name to register:")
                await state.set_state(StudentStates.register_name)
        else:
            if user['role'] == 'student':
                from bot.keyboards.student import get_main_menu
                await message.answer(f"Welcome back, {user['full_name']}!", reply_markup=get_main_menu())
            else:
                from bot.keyboards.psychologist import get_psychologist_menu
                await message.answer(f"Welcome back, {user['role']}!", reply_markup=get_psychologist_menu())
