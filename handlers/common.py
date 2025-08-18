from __future__ import annotations

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from db.base import AsyncSessionLocal
from db import crud
from utils.constants import ROLE_ADMIN, ROLE_STAFF
from keyboards.common import entry_menu_kb, BACK_TEXT
from keyboards.admin import admin_main_kb
from keyboards.staff import staff_main_kb
from keyboards.customer import customer_main_kb  # ✅ پنل مشتری
from config import ADMIN_TELEGRAM_IDS

router = Router()


def _is_admin_tg(tg_id: int) -> bool:
    """
    ADMIN_TELEGRAM_IDS ممکن است در config به‌صورت str "1,2" یا لیست باشد.
    این تابع مقدار را نرمال می‌کند و بررسی می‌کند tg_id داخلش هست یا نه.
    """
    ids = ADMIN_TELEGRAM_IDS
    if isinstance(ids, (list, tuple, set)):
        norm = {str(x).strip() for x in ids if str(x).strip()}
    else:
        norm = {s.strip() for s in str(ids).split(",") if s.strip()}
    return str(tg_id) in norm


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
            # مجوز ادمین: یا در .env لیست شده باشد یا در DB نقش ADMIN داشته باشد
            user = await crud.get_user_by_telegram_id(session, user_tg_id)
            if _is_admin_tg(user_tg_id) or (user and user.role == ROLE_ADMIN):
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
                await cb.message.answer("ورود مشتری موفق بود.")
                await cb.message.answer("پنل مشتری:", reply_markup=customer_main_kb())
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
