from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Appointments"), KeyboardButton(text="💬 Chat")],
            [KeyboardButton(text="👤 Profile")]
        ],
        resize_keyboard=True
    )

def get_profile_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✏️ Edit Name"), KeyboardButton(text="🆔 Edit Student ID")],
            [KeyboardButton(text="🔙 Back")]
        ],
        resize_keyboard=True
    )
