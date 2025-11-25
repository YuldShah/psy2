from aiogram.fsm.state import State, StatesGroup

class StudentStates(StatesGroup):
    # Registration
    register_name = State()
    register_student_id = State()
    
    # Profile
    profile_menu = State()
    editing_name = State()
    editing_student_id = State()
    
    # Other
    appointment_menu = State()
    chatting = State()
    
    # Appointment Booking
    booking_date = State()
    booking_time = State()
    booking_reason = State()

class PsychologistStates(StatesGroup):
    reschedule_date = State()
    reschedule_time = State()
    cancel_reason = State()

class BanStates(StatesGroup):
    adding_reason = State()
