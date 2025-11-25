from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_user_info_keyboard(user_id: int):
    """Keyboard for user info display with ban and close options"""
    keyboard = [
        [InlineKeyboardButton(text="🚫 Ban User", callback_data=f"ban_prompt_{user_id}")],
        [InlineKeyboardButton(text="✖️ Close", callback_data=f"close_userinfo_{user_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_ban_confirm_keyboard(user_id: int, has_reason: bool = False):
    """Keyboard for ban confirmation with optional reason"""
    keyboard = []
    
    if not has_reason:
        keyboard.append([InlineKeyboardButton(text="📝 Add Reason", callback_data=f"ban_addreason_{user_id}")])
    
    keyboard.append([
        InlineKeyboardButton(text="❌ Cancel", callback_data=f"ban_cancel_{user_id}"),
        InlineKeyboardButton(text="✅ Confirm", callback_data=f"ban_confirm_{user_id}")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_users_list_keyboard(users_data: list, page: int = 0, total_pages: int = 1, show_type: str = "all"):
    """Keyboard for paginated users list"""
    keyboard = []
    
    # User buttons (max 5 per page)
    for user in users_data:
        user_id = user['id']
        full_name = user.get('full_name', 'Unknown')
        status = "🚫" if user.get('banned') else "✅"
        keyboard.append([InlineKeyboardButton(
            text=f"{status} {full_name[:30]}",
            callback_data=f"viewuser_{user_id}"
        )])
    
    # Pagination
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Prev", callback_data=f"users_page_{show_type}_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="➡️ Next", callback_data=f"users_page_{show_type}_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_users_menu_keyboard():
    """Main users menu keyboard"""
    keyboard = [
        [InlineKeyboardButton(text="📋 All Users", callback_data="users_list_all")],
        [InlineKeyboardButton(text="🚫 Banned Users", callback_data="users_list_banned")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_unban_keyboard(user_id: int):
    """Keyboard for unbanning a user"""
    keyboard = [
        [InlineKeyboardButton(text="✅ Unban", callback_data=f"unban_confirm_{user_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
