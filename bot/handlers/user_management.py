from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from bot.database.main import get_db_pool
from bot.config import ADMIN_IDS
from bot.states.states import BanStates
from bot.keyboards.user_management import (
    get_user_info_keyboard,
    get_ban_confirm_keyboard,
    get_users_list_keyboard,
    get_users_menu_keyboard,
    get_unban_keyboard
)

router = Router()

# --- Users Menu ---

@router.message(F.text == "👥 Users")
async def show_users_menu(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    await message.answer(
        "👥 <b>User Management</b>\n\nSelect an option:",
        reply_markup=get_users_menu_keyboard()
    )

@router.callback_query(F.data == "users_menu")
async def users_menu_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    await callback.message.edit_text(
        "👥 <b>User Management</b>\n\nSelect an option:",
        reply_markup=get_users_menu_keyboard()
    )

@router.callback_query(F.data == "users_close")
async def close_users_menu(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    await callback.message.delete()
    await callback.answer()

# --- List Users ---

@router.callback_query(F.data == "users_list_all")
async def list_all_users(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        users = await conn.fetch(
            "SELECT id, full_name, banned FROM users ORDER BY created_at DESC LIMIT 5"
        )
        
        if not users:
            await callback.answer("No users found.", show_alert=True)
            return
        
        await callback.message.edit_text(
            f"📋 <b>All Users</b> ({len(users)} shown)\n\nClick to view details:",
            reply_markup=get_users_list_keyboard(users, 0, 1, "all")
        )

@router.callback_query(F.data == "users_list_banned")
async def list_banned_users(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        users = await conn.fetch(
            "SELECT id, full_name, banned, ban_reason FROM users WHERE banned = TRUE ORDER BY created_at DESC"
        )
        
        if not users:
            await callback.answer("No banned users.", show_alert=True)
            return
        
        await callback.message.edit_text(
            f"🚫 <b>Banned Users</b> ({len(users)})\n\nClick to view details:",
            reply_markup=get_users_list_keyboard(users, 0, 1, "banned")
        )

# --- View User ---

@router.callback_query(F.data.startswith("viewuser_"))
async def view_user_details(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    user_id = int(callback.data.split("_")[1])
    
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
        
        if user['banned']:
            keyboard = get_unban_keyboard(user_id)
        else:
            keyboard = get_user_info_keyboard(user_id)
        
        await callback.message.edit_text(text, reply_markup=keyboard)

# --- Ban User ---

@router.callback_query(F.data.startswith("ban_prompt_"))
async def ban_user_prompt(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    user_id = int(callback.data.split("_")[2])
    
    await callback.message.edit_text(
        f"⚠️ <b>Ban User</b>\n\nAre you sure you want to ban this user?\n\n"
        f"You can optionally add a reason.",
        reply_markup=get_ban_confirm_keyboard(user_id, False)
    )
    await state.update_data(ban_user_id=user_id, ban_reason=None)

@router.callback_query(F.data.startswith("ban_addreason_"))
async def add_ban_reason_prompt(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    await callback.answer()
    await callback.message.edit_text(
        "📝 <b>Enter Ban Reason</b>\n\nPlease type the reason for banning this user:"
    )
    await state.set_state(BanStates.adding_reason)

@router.message(BanStates.adding_reason)
async def process_ban_reason(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    data = await state.get_data()
    user_id = data.get('ban_user_id')
    
    await state.update_data(ban_reason=message.text)
    await state.clear()
    
    await message.answer(
        f"✅ Reason added: <i>{message.text}</i>\n\nConfirm ban?",
        reply_markup=get_ban_confirm_keyboard(user_id, True)
    )

@router.callback_query(F.data.startswith("ban_cancel_"))
async def cancel_ban(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    await state.clear()
    await callback.message.delete()
    await callback.answer("Ban cancelled.")

@router.callback_query(F.data.startswith("ban_confirm_"))
async def confirm_ban(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    user_id = int(callback.data.split("_")[2])
    data = await state.get_data()
    ban_reason = data.get('ban_reason')
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET banned = TRUE, ban_reason = $1 WHERE id = $2",
            ban_reason, user_id
        )
    
    # Notify user
    try:
        notif_text = "🚫 <b>You have been banned from using this bot.</b>"
        if ban_reason:
            notif_text += f"\n\n<b>Reason:</b> {ban_reason}"
        
        await callback.bot.send_message(user_id, notif_text)
    except Exception as e:
        print(f"Failed to notify user {user_id}: {e}")
    
    await callback.message.edit_text(
        f"✅ User has been banned.\n\n"
        f"<b>User ID:</b> <code>{user_id}</code>\n"
        f"<b>Reason:</b> {ban_reason or 'No reason provided'}"
    )
    await state.clear()
    await callback.answer("User banned successfully.")

# --- Unban User ---

@router.callback_query(F.data.startswith("unban_confirm_"))
async def unban_user(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    user_id = int(callback.data.split("_")[2])
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET banned = FALSE, ban_reason = NULL WHERE id = $1",
            user_id
        )
    
    # Notify user
    try:
        await callback.bot.send_message(
            user_id,
            "✅ <b>You have been unbanned!</b>\n\nYou can now use the bot again. Use /start to continue."
        )
    except Exception as e:
        print(f"Failed to notify user {user_id}: {e}")
    
    await callback.message.edit_text(
        f"✅ User has been unbanned.\n\n<b>User ID:</b> <code>{user_id}</code>"
    )
    await callback.answer("User unbanned successfully.")

# --- Close User Info ---

@router.callback_query(F.data.startswith("close_userinfo_"))
async def close_user_info(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    await callback.message.delete()
    await callback.answer()
