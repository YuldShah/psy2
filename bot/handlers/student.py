from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from bot.states.states import StudentStates
from bot.database.main import get_db_pool
from bot.keyboards.student import get_main_menu, get_profile_menu

router = Router()

# --- Registration Flow ---

@router.message(StudentStates.register_name)
async def process_register_name(message: types.Message, state: FSMContext):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT banned, ban_reason FROM users WHERE id = $1", message.from_user.id)
        if user and user['banned']:
            ban_msg = "🚫 <b>You are banned from using this bot.</b>"
            if user['ban_reason']:
                ban_msg += f"\n\n<b>Reason:</b> {user['ban_reason']}"
            await message.answer(ban_msg)
            await state.clear()
            return
    
    await state.update_data(full_name=message.text)
    await message.answer("Great! Now please enter your Student ID.")
    await state.set_state(StudentStates.register_student_id)

@router.message(StudentStates.register_student_id)
async def process_register_student_id(message: types.Message, state: FSMContext):
    data = await state.get_data()
    full_name = data.get("full_name")
    student_id = message.text
    user_id = message.from_user.id
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (id, full_name, student_id) VALUES ($1, $2, $3)",
            user_id, full_name, student_id
        )
    
    await message.answer("Registration complete!", reply_markup=get_main_menu())
    await state.clear()

# --- Profile Management ---

@router.message(F.text == "👤 Profile")
async def show_profile(message: types.Message):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", message.from_user.id)
        
        if user:
            await message.answer(
                f"👤 <b>Your Profile</b>\n\n"
                f"<b>Name:</b> {user['full_name']}\n"
                f"<b>Student ID:</b> {user['student_id']}",
                reply_markup=get_profile_menu()
            )

@router.message(F.text == "🔙 Back")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()  # Clear any active state
    await message.answer("Main Menu", reply_markup=get_main_menu())

@router.message(F.text == "✏️ Edit Name")
async def edit_name(message: types.Message, state: FSMContext):
    await message.answer("Please enter your new full name.")
    await state.set_state(StudentStates.editing_name)

@router.message(StudentStates.editing_name)
async def process_edit_name(message: types.Message, state: FSMContext):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT banned, ban_reason FROM users WHERE id = $1", message.from_user.id)
        if user and user['banned']:
            ban_msg = "🚫 <b>You are banned from using this bot.</b>"
            if user['ban_reason']:
                ban_msg += f"\n\n<b>Reason:</b> {user['ban_reason']}"
            await message.answer(ban_msg)
            await state.clear()
            return
        
        await conn.execute(
            "UPDATE users SET full_name = $1 WHERE id = $2",
            message.text, message.from_user.id
        )
    
    await message.answer("Name updated!", reply_markup=get_profile_menu())
    await state.clear()

@router.message(F.text == "🆔 Edit Student ID")
async def edit_student_id(message: types.Message, state: FSMContext):
    await message.answer("Please enter your new Student ID.")
    await state.set_state(StudentStates.editing_student_id)

@router.message(StudentStates.editing_student_id)
async def process_edit_student_id(message: types.Message, state: FSMContext):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT banned, ban_reason FROM users WHERE id = $1", message.from_user.id)
        if user and user['banned']:
            ban_msg = "🚫 <b>You are banned from using this bot.</b>"
            if user['ban_reason']:
                ban_msg += f"\n\n<b>Reason:</b> {user['ban_reason']}"
            await message.answer(ban_msg)
            await state.clear()
            return
        
        await conn.execute(
            "UPDATE users SET student_id = $1 WHERE id = $2",
            message.text, message.from_user.id
        )
    
    await message.answer("Student ID updated!", reply_markup=get_profile_menu())
    await state.clear()
