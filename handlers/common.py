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
from keyboards.customer import customer_main_kb
from config import ADMIN_TELEGRAM_IDS
from utils.ui import edit_or_send

router = Router()

def _is_admin_tg(tg_id: int) -> bool:
    ids = ADMIN_TELEGRAM_IDS
    if isinstance(ids, (list, tuple, set)):
        norm = {str(x).strip() for x in ids if str(x).strip()}
    else:
        norm = {s.strip() for s in str(ids).split(",") if s.strip()}
    return str(tg_id) in norm

@router.message(Command("start"))
async def start(msg: types.Message, state: FSMContext):
    await state.clear()
    await edit_or_send(msg, "به بات مدیریت مارکتینگ فراز خوش آمدید.\nنوع پنل را انتخاب کنید:", entry_menu_kb())

@router.callback_query(F.data.in_({"enter_admin", "enter_staff", "enter_customer"}))
async def entry_choose_role(cb: types.CallbackQuery, state: FSMContext):
    user_tg_id = cb.from_user.id
    choice = cb.data

    async with AsyncSessionLocal() as session:
        if choice == "enter_admin":
            user = await crud.get_user_by_telegram_id(session, user_tg_id)
            if _is_admin_tg(user_tg_id) or (user and user.role == ROLE_ADMIN):
                await edit_or_send(cb, "ورود مدیر موفق بود.\n\nپنل مدیر:", admin_main_kb())
            else:
                await edit_or_send(cb, "⚠️ شما دسترسی به پنل مدیر ندارید.", entry_menu_kb(), force_new=True)
            return

        if choice == "enter_staff":
            user = await crud.get_user_by_telegram_id(session, user_tg_id)
            if user and user.role == ROLE_STAFF:
                await edit_or_send(cb, "ورود نیروی مارکتینگ موفق بود.\n\nپنل نیرو:", staff_main_kb())
            else:
                await edit_or_send(cb, "⚠️ شما دسترسی به پنل نیرو ندارید.", entry_menu_kb(), force_new=True)
            return

        if choice == "enter_customer":
            client = await crud.get_client_by_telegram_id(session, user_tg_id)
            if client:
                await edit_or_send(cb, "ورود مشتری موفق بود.\n\nپنل مشتری:", customer_main_kb())
            else:
                await edit_or_send(cb, "⚠️ شما به عنوان مشتری ثبت نشده‌اید.", entry_menu_kb(), force_new=True)
            return

@router.callback_query(F.data == "back_to_entry")
async def back_to_entry_cb(cb: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await edit_or_send(cb, "بازگشت به منوی شروع.\nنوع پنل را انتخاب کنید:", entry_menu_kb())

@router.message(F.text == BACK_TEXT)
async def back_to_entry_msg(msg: types.Message, state: FSMContext):
    await state.clear()
    await edit_or_send(msg, "بازگشت به منوی شروع.\nنوع پنل را انتخاب کنید:", entry_menu_kb())
