from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_psychologist_menu():
    keyboard = [
        [KeyboardButton(text="📊 Dashboard")],
        [KeyboardButton(text="👥 Users")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
