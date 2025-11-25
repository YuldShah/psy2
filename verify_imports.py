import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    from bot.config import BOT_TOKEN, DATABASE_URL
    from bot.database.main import init_db, get_db_pool
    from bot.states.states import StudentStates, PsychologistStates
    from bot.keyboards.student import get_main_menu, get_profile_menu
    from bot.keyboards.chat import get_show_user_keyboard
    from bot.keyboards.appointment import get_date_keyboard, get_time_keyboard, get_psychologist_action_keyboard
    from bot.handlers import common, student, chat, appointment, dashboard
    from bot.services.sheets import sheets_client
    from run import main
    
    print("All modules imported successfully.")
except Exception as e:
    print(f"Import failed: {e}")
    sys.exit(1)
