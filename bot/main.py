import os
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
# removed config import to avoid .env RuntimeError
from .keyboards import MAIN_KB, numbers_inline_keyboard, durations_keyboard, RED_CIRCLE, GREEN_CIRCLE, payment_keyboard, promo_choice_keyboard, profile_keyboard, category_keyboard
from . import storage
from .prices import PRICES
from .crypto import CryptoPay
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set. Please add it to your environment variables.")

CRYPTO_PAY_TOKEN = os.getenv("CRYPTO_PAY_TOKEN", "")
try:
        ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
except Exception:
        ADMIN_ID = 0

router = Router()

crypto_client = CryptoPay(CRYPTO_PAY_TOKEN) if CRYPTO_PAY_TOKEN else None

# Temporary storage for users waiting to enter promo code
# Format: {user_id: {"number": str, "months": int, "price": float}}
pending_promo_state = {}


def _format_until(until_iso: str) -> str:
        try:
                return datetime.strptime(until_iso, "%Y-%m-%dT%H:%M:%S").strftime("%d.%m.%Y %H:%M UTC")
        except Exception:
                return until_iso


@router.message(CommandStart())
async def start(message: Message):
        # Register user
        username = message.from_user.username
        storage.register_user(message.from_user.id, username)
        
        await message.answer(
                "Добро пожаловать в Shadow Numbers!\nВыберите действие ниже.",
                reply_markup=MAIN_KB,
        )


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def help_cmd(message: Message):
        text = (
                "Shadow Numbers — сервис аренды анонимных номеров Telegram.\n\n"
                "Возможности:\n"
                f"- Номера: наглядный список со статусами ({RED_CIRCLE} — занято, {GREEN_CIRCLE} — свободно).\n"
		"- Две категории: 📱 eSIM ($10-$30/мес) и 📞 Физические номера ($4-$10/мес).\n"
		"- Аренда: доступные сроки — 1, 3, 6 или 12 месяцев.\n"
		"- Тарифы: итоговая стоимость = цена номера × количество месяцев.\n"
		"- Управление: раздел '👤 Профиль' → '📋 Мои аренды' — просмотр активных аренд.\n"
		"- Оплата: безопасные платежи в USDT через Crypto Pay.\n"
		"- Промокоды: скидки на аренду (вводятся при оплате).\n\n"
		"Порядок действий:\n"
		"1) Откройте раздел '📱 Номера' и выберите категорию.\n"
		"2) Выберите свободный номер (цена указана рядом).\n"
		"3) Укажите срок аренды и введите промокод (опционально).\n"
		"4) Оплатите счёт (USDT) по сгенерированной ссылке.\n"
		"5) Нажмите 'Я оплатил' — бот автоматически подтвердит оплату.\n\n"
        )
        await message.answer(text)


@router.message(F.text == "📱 Номера")
async def list_numbers(message: Message):
        await message.answer("Выберите категорию номеров:", reply_markup=category_keyboard())


@router.callback_query(F.data.startswith("cat:"))
async def select_category(callback: CallbackQuery):
        category = callback.data.split(":", 1)[1]
        numbers = storage.list_numbers(category=category)
        
        category_name = "eSIM" if category == "esim" else "Физические номера"
        if not numbers:
                await callback.answer(f"В категории '{category_name}' пока нет номеров", show_alert=True)
                return
        
        await callback.message.edit_text(
                f"📱 {category_name}\n\nВыберите номер:",
                reply_markup=numbers_inline_keyboard(numbers)
        )
        await callback.answer()


@router.callback_query(F.data.startswith("num:"))
async def pick_number(callback: CallbackQuery):
        number = callback.data.split(":", 1)[1]
        item = storage.get_number(number)
        if not item:
                await callback.answer("Номер не найден", show_alert=True)
                return
        if item["status"] == "busy":
                await callback.message.edit_text(
                        f"{RED_CIRCLE} {number} — занят. Выберите другой номер.",
                        reply_markup=numbers_inline_keyboard(storage.list_numbers()),
                )
                await callback.answer()
                return
        
        monthly_price = item.get("price", 25)
        await callback.message.edit_text(
                f"Вы выбрали {GREEN_CIRCLE} {number}\n"
                f"Цена: ${monthly_price}/мес\n\n"
                "Выберите срок аренды:",
                reply_markup=durations_keyboard(number, monthly_price),
        )
        await callback.answer()


@router.callback_query(F.data.startswith("dur:"))
async def rent_duration(callback: CallbackQuery):
        _, months_str, number = callback.data.split(":", 2)
        months = int(months_str)
        
        # Get number info to retrieve individual price
        num_info = storage.get_number(number)
        if not num_info:
                await callback.answer("Номер не найден", show_alert=True)
                return
        
        # Calculate price: monthly price * months
        monthly_price = num_info.get("price", PRICES.get(1, 25))
        total_price = monthly_price * months
        
        # Save pending state for promo code entry
        pending_promo_state[callback.from_user.id] = {
                "number": number,
                "months": months,
                "price": total_price,
        }
        
        # Ask for promo code
        await callback.message.edit_text(
                f"Вы выбрали номер {number} на {months} мес.\n"
                f"Цена: ${total_price} (${monthly_price}/мес)\n\n"
                "🎁 Хотите использовать промокод для получения скидки?",
                reply_markup=promo_choice_keyboard(),
        )
        await callback.answer()


@router.callback_query(F.data == "enter_promo")
async def enter_promo(callback: CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in pending_promo_state:
                await callback.answer("Сессия истекла. Начните заново.", show_alert=True)
                return
        
        state = pending_promo_state[user_id]
        await callback.message.edit_text(
                f"🎁 Введите промокод для получения скидки:\n\n"
                f"Номер: {state['number']}\n"
                f"Срок: {state['months']} мес\n"
                f"Цена: ${state['price']}"
        )
        await callback.answer()


@router.callback_query(F.data == "skip_promo")
async def skip_promo(callback: CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in pending_promo_state:
                await callback.answer("Сессия истекла. Начните заново.", show_alert=True)
                return
        
        state = pending_promo_state.pop(user_id)
        await process_payment(callback, state["number"], state["months"], state["price"], None, None)


@router.message(F.text)
async def handle_promo_code(message: Message):
        user_id = message.from_user.id
        if user_id not in pending_promo_state:
                return
        
        promo_code = message.text.strip()
        state = pending_promo_state[user_id]
        
        # Validate promo code
        promo = storage.get_promocode(promo_code)
        if not promo:
                await message.answer(
                        f"❌ Промокод '{promo_code}' не найден или неактивен.\n"
                        "Попробуйте ещё раз или нажмите \"Пропустить\".",
                        reply_markup=promo_choice_keyboard(),
                )
                return
        
        # Calculate discount
        original_price = state["price"]
        discount_percent = promo["percent"]
        final_price = max(1, round(original_price * (100 - discount_percent) / 100, 2))
        
        # Remove from pending state
        pending_promo_state.pop(user_id)
        
        await message.answer(
                f"✅ Промокод {promo['code']} применён!\n"
                f"Скидка: {discount_percent}%\n"
                f"Цена без скидки: ${original_price}\n"
                f"Цена со скидкой: ${final_price}\n\n"
                "Создаю счёт для оплаты..."
        )
        
        await process_payment_from_message(message, state["number"], state["months"], final_price, promo_code, discount_percent)


async def process_payment(callback, number: str, months: int, final_price: float, promo_code: str = None, discount_percent: int = None):
        """Create invoice and process payment from callback with optional promo code."""
        if not crypto_client:
                # Fallback without crypto: instantly rent (dev/test)
                rental = storage.add_rental(callback.from_user.id, number, months)
                if rental is None:
                        await callback.answer("Номер уже занят", show_alert=True)
                        return
                until_h = _format_until(rental["until"])
                msg_text = f"Готово! {number} арендован до {until_h}."
                if promo_code:
                        msg_text = f"✅ Промокод {promo_code} применён (-{discount_percent}%)!\n\n" + msg_text
                
                await callback.message.edit_text(msg_text)
                await callback.answer()
                return
        
        # Create Crypto Pay invoice
        payment_id = f"{callback.from_user.id}:{number}:{months}:{int(time.time())}"
        description = f"Аренда {number} на {months} мес"
        if promo_code:
                description += f" (промокод {promo_code})"
        
        invoice = await crypto_client.create_invoice(amount=final_price, asset="USDT", description=description, payload=payment_id)
        if not invoice:
                await callback.answer("Не удалось создать счёт. Повторите позже.", show_alert=True)
                return
        
        payment_data = {
                "user_id": callback.from_user.id,
                "number": number,
                "months": months,
                "price": final_price,
                "invoice_id": invoice.get("invoice_id"),
                "status": "pending",
        }
        if promo_code:
                payment_data["promo_code"] = promo_code
                payment_data["discount_percent"] = discount_percent
        
        storage.create_pending_payment(payment_id, payment_data)
        pay_url = invoice.get("pay_url") or invoice.get("bot_invoice_url")
        
        msg_text = f"Оплатите {final_price}$ USDT за {months} мес аренды номера {number}.\n\n"
        if promo_code:
                msg_text = f"✅ Промокод {promo_code} применён! Скидка {discount_percent}%\n\n" + msg_text
        msg_text += f"Ссылка на оплату: {pay_url}\n\n"
        msg_text += "После оплаты нажмите 'Я оплатил' для проверки."
        
        await callback.message.edit_text(msg_text, reply_markup=payment_keyboard(payment_id))
        await callback.answer()


async def process_payment_from_message(message: Message, number: str, months: int, final_price: float, promo_code: str = None, discount_percent: int = None):
        """Create invoice and process payment from user message with promo code."""
        user_id = message.from_user.id
        
        if not crypto_client:
                # Fallback without crypto: instantly rent (dev/test)
                rental = storage.add_rental(user_id, number, months)
                if rental is None:
                        await message.answer("❌ Номер уже занят")
                        return
                until_h = _format_until(rental["until"])
                msg_text = f"✅ Готово! {number} арендован до {until_h}."
                await message.answer(msg_text)
                return
        
        # Create Crypto Pay invoice
        payment_id = f"{user_id}:{number}:{months}:{int(time.time())}"
        description = f"Аренда {number} на {months} мес (промокод {promo_code})"
        
        invoice = await crypto_client.create_invoice(amount=final_price, asset="USDT", description=description, payload=payment_id)
        if not invoice:
                await message.answer("❌ Не удалось создать счёт. Повторите позже.")
                return
        
        payment_data = {
                "user_id": user_id,
                "number": number,
                "months": months,
                "price": final_price,
                "invoice_id": invoice.get("invoice_id"),
                "status": "pending",
                "promo_code": promo_code,
                "discount_percent": discount_percent,
        }
        
        storage.create_pending_payment(payment_id, payment_data)
        pay_url = invoice.get("pay_url") or invoice.get("bot_invoice_url")
        
        msg_text = f"💳 Оплатите {final_price}$ USDT за {months} мес аренды номера {number}.\n\n"
        msg_text += f"Ссылка на оплату: {pay_url}\n\n"
        msg_text += "После оплаты нажмите 'Я оплатил' для проверки."
        
        await message.answer(msg_text, reply_markup=payment_keyboard(payment_id))


@router.callback_query(F.data.startswith("paid:"))
async def paid_check(callback: CallbackQuery):
        if not crypto_client:
                await callback.answer("Крипто-оплата не настроена", show_alert=True)
                return
        payment_id = callback.data.split(":", 1)[1]
        p = storage.get_payment(payment_id)
        if not p or not p.get("invoice_id"):
                await callback.answer("Платёж не найден", show_alert=True)
                return
        invoice = await crypto_client.get_invoice(int(p["invoice_id"]))
        if not invoice:
                await callback.answer("Счёт не найден", show_alert=True)
                return
        status = invoice.get("status")
        if status != "paid":
                await callback.answer("Платёж ещё не подтверждён", show_alert=True)
                return
        # Activate rental
        rental = storage.add_rental(callback.from_user.id, p["number"], int(p["months"]))
        if rental is None:
                await callback.answer("Номер уже занят", show_alert=True)
                return
        storage.set_payment_status(payment_id, "paid")
        until_h = _format_until(rental["until"])
        await callback.message.edit_text(
                f"Оплата подтверждена. {p['number']} арендован до {until_h}.")
        await callback.answer()


@router.message(F.text == "👤 Профиль")
async def profile(message: Message):
        user_id = message.from_user.id
        username = message.from_user.username or "Не указан"
        
        # Get or register user
        user_data = storage.get_user(user_id)
        if not user_data:
                user_data = storage.register_user(user_id, message.from_user.username)
        
        # Calculate days in bot
        first_seen = datetime.strptime(user_data["first_seen"], "%Y-%m-%dT%H:%M:%S")
        days_in_bot = (datetime.utcnow() - first_seen).days
        
        # Get bot info for referral link
        bot = await message.bot.me()
        bot_username = bot.username
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        
        profile_text = (
                f"👤 Ваш профиль\n\n"
                f"📝 Username: @{username}\n"
                f"🆔 ID: {user_id}\n"
                f"📅 Дней в боте: {days_in_bot}\n"
                f"🔗 Реферальная ссылка:\n{ref_link}"
        )
        
        await message.answer(profile_text, reply_markup=profile_keyboard())


@router.callback_query(F.data == "my_rentals")
async def my_rentals_callback(callback: CallbackQuery):
        rentals = storage.list_rentals(callback.from_user.id)
        if not rentals:
                await callback.answer("У вас нет активных аренд", show_alert=True)
                return
        
        lines = ["📋 Ваши аренды:\n"]
        for r in rentals:
                lines.append(f"• {r['number']} — до {_format_until(r['until'])}")
        lines.append("\n💡 Чтобы продлить: /extend <номер> <месяцев>")
        
        await callback.message.edit_text("\n".join(lines))
        await callback.answer()


@router.message(Command("extend"))
async def extend_cmd(message: Message):
        # Format: /extend <number> <months>
        parts = message.text.strip().split()
        if len(parts) < 3:
                await message.answer("Использование: /extend <номер> <месяцев>")
                return
        number = " ".join(parts[1:-1])
        try:
                months = int(parts[-1])
        except ValueError:
                await message.answer("Месяцы должны быть числом (1/3/6/12)")
                return
        updated = storage.extend_rental(message.from_user.id, number, months)
        if not updated:
                await message.answer("Аренда не найдена для указанного номера.")
                return
        await message.answer(f"Продлено до {_format_until(updated['until'])}.")


@router.message(Command("admin_rent"))
async def admin_rent_cmd(message: Message):
        if message.from_user.id != ADMIN_ID:
                await message.answer("Команда доступна только владельцу.")
                return
        parts = message.text.strip().split()
        if len(parts) < 3:
                await message.answer("Использование: /admin_rent <номер> <месяцев>")
                return
        number = " ".join(parts[1:-1])
        try:
                months = int(parts[-1])
        except ValueError:
                await message.answer("Месяцы должны быть числом.")
                return
        rental = storage.force_rental(message.from_user.id, number, months)
        if not rental:
                await message.answer("Номер не найден.")
                return
        await message.answer(f"Оформлено владельцем. Аренда {number} до {_format_until(rental['until'])}.")


@router.message(Command("promo_add"))
async def promo_add_cmd(message: Message):
        if message.from_user.id != ADMIN_ID:
                await message.answer("Команда доступна только владельцу.")
                return
        parts = message.text.strip().split()
        if len(parts) != 3:
                await message.answer("Использование: /promo_add <КОД> <ПРОЦЕНТ>\nПример: /promo_add SALE20 20")
                return
        code = parts[1]
        try:
                percent = int(parts[2])
        except ValueError:
                await message.answer("Процент должен быть числом от 1 до 100.")
                return
        
        promo = storage.add_promocode(code, percent, message.from_user.id)
        if not promo:
                await message.answer("Ошибка: промокод уже существует или процент указан неверно (1-100).")
                return
        
        await message.answer(f"✅ Промокод создан:\nКод: {promo['code']}\nСкидка: {promo['percent']}%")


@router.message(Command("promo_list"))
async def promo_list_cmd(message: Message):
        if message.from_user.id != ADMIN_ID:
                await message.answer("Команда доступна только владельцу.")
                return
        
        promos = storage.list_promocodes()
        if not promos:
                await message.answer("Промокодов пока нет.")
                return
        
        lines = ["📋 Список промокодов:"]
        for p in promos:
                status = "✅ активен" if p.get("active", True) else "❌ отключен"
                lines.append(f"\n• {p['code']} — {p['percent']}% ({status})")
        
        await message.answer("\n".join(lines))


@router.message(Command("promo_disable"))
async def promo_disable_cmd(message: Message):
        if message.from_user.id != ADMIN_ID:
                await message.answer("Команда доступна только владельцу.")
                return
        parts = message.text.strip().split()
        if len(parts) != 2:
                await message.answer("Использование: /promo_disable <КОД>")
                return
        
        code = parts[1]
        if storage.deactivate_promocode(code):
                await message.answer(f"✅ Промокод {code.upper()} отключен.")
        else:
                await message.answer(f"❌ Промокод {code.upper()} не найден.")


async def expiry_worker():
        while True:
                try:
                        released = storage.release_if_expired()
                        # Optionally, could log released count
                except Exception:
                        pass
                await asyncio.sleep(60)


async def main():
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher()
        dp.include_router(router)
        asyncio.create_task(expiry_worker())
        # Drop pending updates to avoid conflicts with other instances
        await dp.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":
        asyncio.run(main())
