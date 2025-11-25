from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from bot.database.main import get_db_pool
from bot.states.states import StudentStates, PsychologistStates
from bot.keyboards.student import get_main_menu
from bot.keyboards.chat import get_show_user_keyboard
from bot.config import ADMIN_IDS

router = Router()

# --- Student Chat Flow ---

@router.message(F.text == "💬 Chat")
async def enter_chat_mode(message: types.Message, state: FSMContext):
    await state.set_state(StudentStates.chatting)
    await message.answer("You are now in chat mode. Every message you send will be forwarded to the psychologist.", reply_markup=types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text="🔙 Back")]], resize_keyboard=True))


@router.message(F.text == "🔙 Back", StudentStates.chatting)
async def exit_chat_mode(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Exited chat mode.", reply_markup=get_main_menu())

@router.message(StudentStates.chatting)
async def forward_message_to_psychologist(message: types.Message):
    user_id = message.from_user.id
    pool = await get_db_pool()
    
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
            # Should not happen if registered, but safety check
            return

        # Format message
        student_id_line = f"🆔 <code>{user['student_id']}</code>\n" if user['student_id'] else ""
        formatted_text = (
            f"💬 <b>From</b>\n"
            f"<blockquote>"
            f"👤 {user['full_name']}\n"
            f"{student_id_line}"
            f"</blockquote>\n\n"
            f"<i>{message.text}</i>"
        )
        
        # Send to ALL Psychologists
        for admin_id in ADMIN_IDS:
            try:
                sent_msg = await message.bot.send_message(
                    chat_id=admin_id,
                    text=formatted_text,
                    parse_mode="HTML",
                    reply_markup=get_show_user_keyboard(user_id)
                )
                
                # Save mapping
                await conn.execute(
                    """
                    INSERT INTO forwarded_messages (admin_id, forwarded_message_id, student_id, student_message_id)
                    VALUES ($1, $2, $3, $4)
                    """,
                    admin_id, sent_msg.message_id, user_id, message.message_id
                )
            except Exception as e:
                print(f"Failed to send to admin {admin_id}: {e}")
        
        await message.answer("Message sent.", reply_markup=types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text="🔙 Back")]], resize_keyboard=True))


# --- Psychologist Reply Flow ---

@router.message(lambda m: m.reply_to_message is not None and m.from_user.id in ADMIN_IDS)
async def handle_psychologist_reply(message: types.Message):
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        # Find the original sender
        mapping = await conn.fetchrow(
            """
            SELECT student_id, student_message_id FROM forwarded_messages 
            WHERE forwarded_message_id = $1 AND admin_id = $2
            """,
            message.reply_to_message.message_id, message.from_user.id
        )
        
        if mapping:
            student_id = mapping['student_id']
            student_msg_id = mapping['student_message_id']
            
            reply_text = (
                f"🧑‍⚕️ <b>Reply from Psychologist:</b>\n\n"
                f"{message.text}"
            )
            
            try:
                await message.bot.send_message(
                    chat_id=student_id,
                    text=reply_text,
                    parse_mode="HTML",
                    reply_to_message_id=student_msg_id
                )
                await message.reply("Reply sent!")
            except Exception as e:
                await message.reply(f"Failed to send reply: {e}")
        else:
            # Not a reply to a forwarded message, or mapping lost
            await message.reply("Could not find the student to reply to.")


# --- Callback Handlers ---

@router.callback_query(F.data.startswith("show_user_"))
async def show_user_callback(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[2])
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        
        if not user:
            await callback.answer("User not found.", show_alert=True)
            return
        
        # Fetch Telegram user info
        try:
            tg_user = await callback.bot.get_chat(user_id)
            tg_full_name = tg_user.full_name
        except:
            tg_full_name = "Unknown"
        
        status = "🚫 Banned" if user['banned'] else "✅ Active"
        ban_info = f"\n<b>Ban Reason:</b> {user['ban_reason']}" if user['banned'] and user['ban_reason'] else ""
        
        text = (
            f"👤 <b>User Information</b>\n\n"
            f"<b>Telegram Name:</b> {tg_full_name}\n"
            f"<b>Telegram ID:</b> <code>{user_id}</code>\n"
            f"<b>Registered Name:</b> {user['full_name'] or 'N/A'}\n"
            f"<b>Student ID:</b> {user['student_id'] or 'N/A'}\n"
            f"<b>Role:</b> {user['role']}\n"
            f"<b>Status:</b> {status}{ban_info}"
        )
        
        from bot.keyboards.user_management import get_user_info_keyboard, get_unban_keyboard
        
        if user['banned']:
            keyboard = get_unban_keyboard(user_id)
        else:
            keyboard = get_user_info_keyboard(user_id)
        
        # Send new message instead of answer
        await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=text,
            reply_markup=keyboard
        )
        await callback.answer()
