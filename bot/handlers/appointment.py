from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from bot.states.states import StudentStates, PsychologistStates
from bot.database.main import get_db_pool
from bot.keyboards.appointment import get_date_keyboard, get_time_keyboard, get_psychologist_action_keyboard
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import ADMIN_IDS
from datetime import datetime

router = Router()

# --- Student Booking Flow ---

@router.message(F.text == "📅 Appointments")
async def start_booking(message: types.Message, state: FSMContext):
    await message.answer("Please select a date for your appointment:", reply_markup=get_date_keyboard())
    await state.set_state(StudentStates.booking_date)

@router.callback_query(F.data.startswith("appt_date_"))
async def date_selected(callback: types.CallbackQuery, state: FSMContext):
    # Extract date from callback_data: "appt_date_YYYY-MM-DD"
    date_str = callback.data.split("_")[2]  # Gets YYYY-MM-DD
    # Convert to DD.MM format for display
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    display_date = date_obj.strftime("%d.%m")
    
    await state.update_data(date=display_date, full_date=date_str)
    
    await callback.message.edit_text(
        f"Date selected: {display_date}\nNow please select a time:",
        reply_markup=get_time_keyboard(date_str)
    )
    await state.set_state(StudentStates.booking_time)

@router.callback_query(F.data == "appt_back_date")
async def back_to_date(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Please select a date:", reply_markup=get_date_keyboard())
    await state.set_state(StudentStates.booking_date)

@router.callback_query(F.data.startswith("appt_time_"))
async def time_selected(callback: types.CallbackQuery, state: FSMContext):
    # Extract time from callback_data: "appt_time_YYYY-MM-DD_HH:MM"
    parts = callback.data.split("_")
    time_str = parts[3]  # Gets HH:MM
    
    data = await state.get_data()
    date_str = data.get("date")
    
    await callback.message.edit_text(
        f"Date: {date_str}\nTime: {time_str}\n\nPlease enter the reason for your appointment:"
    )
    await state.set_state(StudentStates.booking_reason)
    await state.update_data(time=time_str)

@router.message(StudentStates.booking_reason)
async def reason_submitted(message: types.Message, state: FSMContext):
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
            await state.clear()
            return
        
        reason = message.text
        data = await state.get_data()
    date_str = data.get("date")
    time_str = data.get("time")
    user_id = message.from_user.id
    
    # Parse datetime (simplified for MVP)
    dt_str = f"{date_str} {time_str}"
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get user details
        user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        
        # Create Appointment
        # Note: time_slot should be timestamp, but for MVP we might store string or parse it.
        # Let's assume schema has TIMESTAMPTZ, so we need a datetime object.
        # Format: DD.MM HH:MM. Year is current year.
        current_year = datetime.now().year
        dt_obj = datetime.strptime(f"{date_str}.{current_year} {time_str}", "%d.%m.%Y %H:%M")
        
        appt_id = await conn.fetchval(
            """
            INSERT INTO appointments (student_id, time_slot, reason, status)
            VALUES ($1, $2, $3, 'pending')
            RETURNING id
            """,
            user_id, dt_obj, reason
        )
        
        await message.answer("Appointment request sent! Waiting for confirmation.")
        await state.clear()
        
        # Notify Psychologists
        appt_text = (
            f"📅 <b>New Appointment Request</b>\n\n"
            f"👤 <b>Student:</b> {user['full_name']} (ID: {user['student_id']})\n"
            f"🗓 <b>Time:</b> {dt_str}\n"
            f"📝 <b>Reason:</b> {reason}"
        )
        
        # Sync to Sheets
        from bot.services.sheets import sheets_client
        sheets_client.add_appointment(
            appt_id, 
            user['full_name'], 
            user['student_id'], 
            date_str, 
            time_str, 
            reason, 
            'pending'
        )
        
        for admin_id in ADMIN_IDS:
            try:
                await message.bot.send_message(
                    chat_id=admin_id,
                    text=appt_text,
                    reply_markup=get_psychologist_action_keyboard(appt_id, user_id)
                )
            except Exception as e:
                print(f"Failed to notify admin {admin_id}: {e}")

# --- Psychologist Actions ---

@router.callback_query(F.data.startswith("psy_accept_"))
async def accept_appointment(callback: types.CallbackQuery):
    appt_id = int(callback.data.split("_")[2])
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        await conn.execute("UPDATE appointments SET status = 'confirmed' WHERE id = $1", appt_id)
        
        # Sync to Sheets
        from bot.services.sheets import sheets_client
        sheets_client.update_status(appt_id, 'confirmed')
        
        # Get appointment details
        appt = await conn.fetchrow("SELECT * FROM appointments WHERE id = $1", appt_id)
        
        if appt:
            try:
                await callback.bot.send_message(
                    chat_id=appt['student_id'],
                    text="✅ Your appointment has been confirmed!"
                )
            except Exception as e:
                print(f"Failed to notify student: {e}")
                
    await callback.message.edit_text(f"{callback.message.text}\n\n✅ <b>Accepted</b>")
    await callback.answer("Appointment confirmed.")

@router.callback_query(F.data.startswith("psy_cancel_"))
async def cancel_appointment(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    appt_id = int(callback.data.split("_")[2])
    
    await state.update_data(cancel_appt_id=appt_id)
    
    # Create inline keyboard for optional reason
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Add Reason", callback_data=f"cancel_addreason_{appt_id}")],
        [InlineKeyboardButton(text="Skip", callback_data=f"cancel_confirm_{appt_id}")]
    ])
    
    await callback.message.answer(
        "❌ <b>Cancel Appointment</b>\n\n"
        "Do you want to add a cancellation reason? (Optional)",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data.startswith("cancel_addreason_"))
async def cancel_add_reason(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    await callback.message.edit_text(
        "📝 <b>Cancellation Reason</b>\n\n"
        "Please type the reason for cancellation:"
    )
    await state.set_state(PsychologistStates.cancel_reason)
    await callback.answer()

@router.message(PsychologistStates.cancel_reason)
async def process_cancel_reason(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    data = await state.get_data()
    appt_id = data.get('cancel_appt_id')
    cancel_reason = message.text
    
    await perform_cancellation(message.bot, appt_id, cancel_reason)
    await message.answer(f"✅ Appointment cancelled with reason: <i>{cancel_reason}</i>")
    await state.clear()

@router.callback_query(F.data.startswith("cancel_confirm_"))
async def confirm_cancel(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    appt_id = int(callback.data.split("_")[2])
    
    await perform_cancellation(callback.bot, appt_id, None)
    await callback.message.edit_text("✅ Appointment cancelled.")
    await state.clear()
    await callback.answer()

async def perform_cancellation(bot, appt_id: int, cancel_reason: str = None):
    """Helper function to perform appointment cancellation"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE appointments SET status = 'cancelled', cancellation_reason = $1 WHERE id = $2",
            cancel_reason, appt_id
        )
        
        # Sync to Sheets
        from bot.services.sheets import sheets_client
        sheets_client.update_status(appt_id, 'cancelled')
        
        # Get appointment details
        appt = await conn.fetchrow("SELECT * FROM appointments WHERE id = $1", appt_id)
        
        if appt:
            try:
                notif = "❌ Your appointment has been cancelled."
                if cancel_reason:
                    notif += f"\n\n<b>Reason:</b> {cancel_reason}"
                
                await bot.send_message(
                    chat_id=appt['student_id'],
                    text=notif
                )
            except Exception as e:
                print(f"Failed to notify student: {e}")

@router.callback_query(F.data.startswith("psy_ignore_"))
async def ignore_appointment(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer("Ignored.")

@router.callback_query(F.data.startswith("psy_reschedule_"))
async def reschedule_appointment(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    appt_id = int(callback.data.split("_")[2])
    
    await state.update_data(reschedule_appt_id=appt_id)
    await callback.message.answer(
        "📅 <b>Reschedule Appointment</b>\n\nPlease select a new date:",
        reply_markup=get_date_keyboard()
    )
    await state.set_state(PsychologistStates.reschedule_date)
    await callback.answer()

@router.callback_query(F.data.startswith("appt_date_"), PsychologistStates.reschedule_date)
async def reschedule_date_selected(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    date_str = callback.data.split("_")[2]
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    display_date = date_obj.strftime("%d.%m")
    
    await state.update_data(reschedule_date=display_date, reschedule_full_date=date_str)
    
    await callback.message.edit_text(
        f"Date selected: {display_date}\nNow select a new time:",
        reply_markup=get_time_keyboard(date_str)
    )
    await state.set_state(PsychologistStates.reschedule_time)

@router.callback_query(F.data.startswith("appt_time_"), PsychologistStates.reschedule_time)
async def reschedule_time_selected(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    parts = callback.data.split("_")
    time_str = parts[3]
    
    data = await state.get_data()
    appt_id = data.get('reschedule_appt_id')
    date_str = data.get('reschedule_date')
    full_date = data.get('reschedule_full_date')
    
    # Parse new datetime
    current_year = datetime.now().year
    dt_obj = datetime.strptime(f"{date_str}.{current_year} {time_str}", "%d.%m.%Y %H:%M")
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Update appointment
        await conn.execute(
            "UPDATE appointments SET time_slot = $1 WHERE id = $2",
            dt_obj, appt_id
        )
        
        # Get appointment details for notification
        appt = await conn.fetchrow("SELECT * FROM appointments WHERE id = $1", appt_id)
        
        # Sync to Sheets
        from bot.services.sheets import sheets_client
        sheets_client.update_appointment(appt_id, date_str, time_str)
        
        # Notify student
        if appt:
            try:
                await callback.bot.send_message(
                    chat_id=appt['student_id'],
                    text=f"📅 <b>Appointment Rescheduled</b>\n\n"
                         f"Your appointment has been rescheduled to:\n"
                         f"<b>Date:</b> {date_str}\n"
                         f"<b>Time:</b> {time_str}"
                )
            except Exception as e:
                print(f"Failed to notify student: {e}")
    
    await callback.message.edit_text(
        f"✅ <b>Appointment Rescheduled</b>\n\n"
        f"<b>New Date:</b> {date_str}\n"
        f"<b>New Time:</b> {time_str}"
    )
    await state.clear()
    await callback.answer("Appointment rescheduled successfully.")

# --- Show User from Appointment ---

@router.callback_query(F.data.startswith("show_user_"))
async def show_user_from_appointment(callback: types.CallbackQuery):
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
        
        # Send new message
        await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=text,
            reply_markup=keyboard
        )
        await callback.answer()

