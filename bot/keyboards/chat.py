from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_show_user_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Show User", callback_data=f"show_user_{user_id}")]
        ]
    )
