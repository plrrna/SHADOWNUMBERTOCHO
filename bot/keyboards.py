from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict
from .prices import get_price

MAIN_KB = ReplyKeyboardMarkup(
        keyboard=[
                [KeyboardButton(text="📱 Номера"), KeyboardButton(text="👤 Профиль")],
                [KeyboardButton(text="ℹ️ Помощь")],
        ],
        resize_keyboard=True,
)

RED_CIRCLE = "🔴"
GREEN_CIRCLE = "🟢"


def category_keyboard() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📱 eSIM", callback_data="cat:esim")],
                [InlineKeyboardButton(text="📞 Физические номера", callback_data="cat:physical")],
        ])


def numbers_inline_keyboard(numbers: List[Dict]) -> InlineKeyboardMarkup:
        rows = []
        for item in numbers:
                price_str = f" — ${item.get('price', '?')}/мес"
                label = f"{RED_CIRCLE if item['status']=='busy' else GREEN_CIRCLE} {item['number']}{price_str}"
                rows.append([
                        InlineKeyboardButton(text=label, callback_data=f"num:{item['number']}")
                ])
        return InlineKeyboardMarkup(inline_keyboard=rows)


def durations_keyboard(number: str, monthly_price: int = 25) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
                [
                        InlineKeyboardButton(text=f"1 мес — ${monthly_price * 1}", callback_data=f"dur:1:{number}"),
                        InlineKeyboardButton(text=f"3 мес — ${monthly_price * 3}", callback_data=f"dur:3:{number}"),
                ],
                [
                        InlineKeyboardButton(text=f"6 мес — ${monthly_price * 6}", callback_data=f"dur:6:{number}"),
                        InlineKeyboardButton(text=f"12 мес — ${monthly_price * 12}", callback_data=f"dur:12:{number}"),
                ],
        ])


def payment_keyboard(payment_id: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
                [
                        InlineKeyboardButton(text="Я оплатил", callback_data=f"paid:{payment_id}")
                ]
        ])


def promo_choice_keyboard() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
                [
                        InlineKeyboardButton(text="🎁 Ввести промокод", callback_data="enter_promo")
                ],
                [
                        InlineKeyboardButton(text="❌ Пропустить", callback_data="skip_promo")
                ]
        ])


def profile_keyboard() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
                [
                        InlineKeyboardButton(text="📋 Мои аренды", callback_data="my_rentals")
                ]
        ])
