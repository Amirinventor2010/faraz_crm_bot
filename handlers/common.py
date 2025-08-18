from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from db.base import AsyncSessionLocal
from db import crud
from utils.constants import ROLE_ADMIN, ROLE_STAFF
from keyboards.common import entry_menu_kb, BACK_TEXT
from keyboards.admin import admin_main_kb
from keyboards.staff import staff_main_kb
from config import ADMIN_TELEGRAM_IDS

router = Router()

@router.message(Command("start"))
async def start(msg: types.Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "به بات مدیریت مارکتینگ فراز خوش آمدید.\n"
        "نوع پنل را انتخاب کنید:",
        reply_markup=entry_menu_kb()
    )

@router.callback_query(F.data.in_({"enter_admin", "enter_staff", "enter_customer"}))
async def entry_choose_role(cb: types.CallbackQuery, state: FSMContext):
    user_tg_id = cb.from_user.id
    choice = cb.data

    async with AsyncSessionLocal() as session:
        if choice == "enter_admin":
            user = await crud.get_user_by_telegram_id(session, user_tg_id)
            in_cfg = str(user_tg_id) in ADMIN_TELEGRAM_IDS
            if (user and user.role == ROLE_ADMIN) or in_cfg:
                await cb.message.answer("ورود مدیر موفق بود.")
                await cb.message.answer("پنل مدیر:", reply_markup=admin_main_kb())
            else:
                await cb.message.answer("⚠️ شما دسترسی به پنل مدیر ندارید.")
            return

        if choice == "enter_staff":
            user = await crud.get_user_by_telegram_id(session, user_tg_id)
            if user and user.role == ROLE_STAFF:
                await cb.message.answer("ورود نیروی مارکتینگ موفق بود.")
                await cb.message.answer("پنل نیرو:", reply_markup=staff_main_kb())
            else:
                await cb.message.answer("⚠️ شما دسترسی به پنل نیرو ندارید.")
            return

        if choice == "enter_customer":
            client = await crud.get_client_by_telegram_id(session, user_tg_id)
            if client:
                await cb.message.answer("ورود مشتری موفق بود. (پنل مشتری به‌زودی)")
            else:
                await cb.message.answer("⚠️ شما به عنوان مشتری ثبت نشده‌اید.")
            return

@router.callback_query(F.data == "back_to_entry")
async def back_to_entry_cb(cb: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.answer(
        "بازگشت به منوی شروع.\n"
        "نوع پنل را انتخاب کنید:",
        reply_markup=entry_menu_kb()
    )

@router.message(F.text == BACK_TEXT)
async def back_to_entry_msg(msg: types.Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "بازگشت به منوی شروع.\n"
        "نوع پنل را انتخاب کنید:",
        reply_markup=entry_menu_kb()
    )
