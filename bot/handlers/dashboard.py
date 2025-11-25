from aiogram import Router, types, F
from aiogram.filters import Command
from bot.database.main import get_db_pool
from bot.config import ADMIN_IDS, GOOGLE_SHEET_ID
from bot.services.sheets import sheets_client

router = Router()

@router.message(Command("dashboard"))
@router.message(F.text == "📊 Dashboard")
async def show_dashboard(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return # Ignore non-admins

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get Stats
        total_appts = await conn.fetchval("SELECT count(*) FROM appointments")
        pending_appts = await conn.fetchval("SELECT count(*) FROM appointments WHERE status = 'pending'")
        confirmed_appts = await conn.fetchval("SELECT count(*) FROM appointments WHERE status = 'confirmed'")
        cancelled_appts = await conn.fetchval("SELECT count(*) FROM appointments WHERE status = 'cancelled'")
        
        text = (
            f"📊 <b>Psychologist Dashboard</b>\n\n"
            f"<b>Total Appointments:</b> {total_appts}\n"
            f"<b>Pending:</b> {pending_appts}\n"
            f"<b>Confirmed:</b> {confirmed_appts}\n"
            f"<b>Cancelled:</b> {cancelled_appts}\n\n"
            f"<i>Google Sheets Sync is active.</i>"
        )
        
        # Build keyboard with Google Sheets link and Sync button
        buttons = []
        if GOOGLE_SHEET_ID:
            sheet_url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}"
            buttons.append([types.InlineKeyboardButton(text="📄 Open Google Sheet", url=sheet_url)])
        buttons.append([types.InlineKeyboardButton(text="🔄 Sync Now", callback_data="dashboard_sync")])
        
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data == "dashboard_sync")
async def sync_dashboard(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return

    await callback.answer("Syncing...", show_alert=False)
    
    # Placeholder for sync logic
    await callback.message.answer("✅ Manual sync completed (Placeholder). Real-time sync is active.")
