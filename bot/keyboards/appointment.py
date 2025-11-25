from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

def get_date_keyboard() -> InlineKeyboardMarkup:
    keyboard = []
    today = datetime.now()
    
    # Next 5 working days (Mon-Fri)
    dates = []
    current_date = today
    
    while len(dates) < 5:
        if current_date.weekday() < 5: # 0-4 is Mon-Fri
            date_str = current_date.strftime("%d.%m")
            day_name = current_date.strftime("%a")
            callback_data = f"appt_date_{current_date.strftime('%Y-%m-%d')}"
            dates.append(InlineKeyboardButton(text=f"{day_name} - {date_str}", callback_data=callback_data))
        current_date += timedelta(days=1)
    
    # First row: 3 buttons, Second row: 2 buttons
    keyboard.append(dates[:3])
    keyboard.append(dates[3:5])
        
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_time_keyboard(date_str: str) -> InlineKeyboardMarkup:
    keyboard = []
    # 10:00 to 16:00, 30 min slots. Exclude 13:00-14:00
    # Slots: 10:00, 10:30, 11:00, 11:30, 12:00, 12:30, 14:00, 14:30, 15:00, 15:30
    
    slots = [
        "10:00", "10:30", "11:00", "11:30", "12:00", "12:30",
        "14:00", "14:30", "15:00", "15:30"
    ]
    
    # Arrange in 2 columns
    row = []
    for slot in slots:
        callback_data = f"appt_time_{date_str}_{slot}"
        row.append(InlineKeyboardButton(text=slot, callback_data=callback_data))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="appt_back_date")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_psychologist_action_keyboard(appointment_id: int, student_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Accept", callback_data=f"psy_accept_{appointment_id}"),
                InlineKeyboardButton(text="❌ Cancel", callback_data=f"psy_cancel_{appointment_id}")
            ],
            [
                InlineKeyboardButton(text="🔄 Reschedule", callback_data=f"psy_reschedule_{appointment_id}"),
                InlineKeyboardButton(text="🚫 Ignore", callback_data=f"psy_ignore_{appointment_id}")
            ],
            [
                InlineKeyboardButton(text="👤 Show User", callback_data=f"show_user_{student_id}")
            ]
        ]
    )
