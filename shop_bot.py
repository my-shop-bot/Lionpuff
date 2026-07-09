import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "").strip()  # твой Telegram ID, куда придут заказы

if not BOT_TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN")
if not ADMIN_CHAT_ID:
    raise RuntimeError("Не задан ADMIN_CHAT_ID")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ==== Каталог товаров: отредактируй под себя ====
# Разбито на 2 серии, как в твоём списке. Просто отредактируй строки при необходимости.
CATEGORIES = {
    "s1": {
        "title": "Vozol STAR 40k",
        "items": [
            "Watermelon Gum — Арбузная Жвачка 🍉🟢",
            "Tiger Blood — Кровь Тигра 🐅❤️",
            "Watermelon Ice — Арбузный Лёд 🍉❄️",
            "Peach Mango Watermelon — Персик Манго Арбуз 🍑🥭🍉",
            "Watermelon Melon — Арбуз Дыня 🍉🍈",
            "Blackberry Pomegranate Cherry — Ежевика Гранат Вишня 🫐🍒",
            "Melon Bubblegum — Дынная Жвачка 🍈🟢",
            "Strawberry Raspberry Cherry — Клубника Малина Вишня 🍓🍒",
            "Tropical Fruit Storm — Тропический Фруктовый Шторм 🌴🍍",
            "Grape Ice — Виноградный Лёд 🍇❄️",
            "Strawberry Kiwi — Клубника Киви 🍓🥝",
            "Spearmint — Мятный Спрей 🌿❄️",
            "Date Shake Molasses — Финиковый Шейк 🌴🥤",
            "Blueberry Energy — Черничная Энергия 🫐⚡",
            "Dragonfruit Banana Cherry — Питахайя Банан Вишня 🐉🍌🍒",
            "Blue Razz Ice — Голубая Малина Лёд 🔵❄️",
            "Strawberry Gum — Клубничная Жвачка 🍓🟢",
            "Love 777 — Любовь 777 ❤️✨",
            "Raspberry Watermelon — Малина Арбуз 🍓🍉",
            "Mixed Berry — Ягодный Микс 🫐🍓",
        ],
    },
    "s2": {
        "title": "Vozol STAR 50k",
        "items": [
            "Cool Mint — Холодная Мята ❄️🌿",
            "Watermelon Sour Peach — Арбуз Кислый Персик 🍉🍑",
            "Watermelon Grape Boysenberry — Арбуз Виноград Бойзенберри 🍉🍇",
            "Blue Razz Ice — Голубая Малина Лёд 🔵❄️",
            "Cherimoya Grapefruit Berries — Черимойя Грейпфрут Ягоды 🍈🍊",
            "Strawmelon Peach — Клубарбуз Персик 🍓🍉🍑",
            "Strawberry Ice — Клубничный Лёд 🍓❄️",
            "Strawberry Watermelon — Клубника Арбуз 🍓🍉",
            "Vzbull — Vzbull ⚡🐂",
            "Sour Apple Ice — Кислое Яблоко Лёд 🍏❄️",
            "White Peach Raspberry — Белый Персик Малина 🍑🍓",
            "Strawberry Kiwi — Клубника Киви 🍓🥝",
            "Blueberry Ice — Черничный Лёд 🫐❄️",
            "Blueberry Mint — Черника Мята 🫐🌿",
            "Mango Ice — Манго Лёд 🥭❄️",
            "Peach Ice — Персиковый Лёд 🍑❄️",
            "Mango Peach — Манго Персик 🥭🍑",
            "Melon Ice — Дынный Лёд 🍈❄️",
            "Melon Gum — Дынная Жвачка 🍈🟢",
        ],
    },
}

# плоский словарь id -> название, чтобы обращаться к товару по короткому ключу в callback_data
PRODUCTS = {}
for cat_id, cat in CATEGORIES.items():
    for i, name in enumerate(cat["items"]):
        PRODUCTS[f"{cat_id}_{i}"] = name


class Order(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_place = State()


def age_gate_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Мне есть 18 лет", callback_data="age_ok")]]
    )


def categories_keyboard() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=cat["title"], callback_data=f"cat_{cid}")] for cid, cat in CATEGORIES.items()]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def items_keyboard(cat_id: str) -> InlineKeyboardMarkup:
    cat = CATEGORIES[cat_id]
    rows = [[InlineKeyboardButton(text=name, callback_data=f"item_{cat_id}_{i}")] for i, name in enumerate(cat["items"])]
    rows.append([InlineKeyboardButton(text="⬅️ Назад к сериям", callback_data="back_cats")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def order_keyboard(pid: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🛒 Заказать", callback_data=f"order_{pid}")]]
    )


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Этот каталог предназначен только для совершеннолетних (18+).",
        reply_markup=age_gate_keyboard(),
    )


@dp.callback_query(F.data == "age_ok")
async def confirm_age(callback: CallbackQuery):
    await callback.message.edit_text("Выберите серию:", reply_markup=categories_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "back_cats")
async def back_to_categories(callback: CallbackQuery):
    await callback.message.edit_text("Выберите серию:", reply_markup=categories_keyboard())
    await callback.answer()


@dp.callback_query(F.data.startswith("cat_"))
async def show_category(callback: CallbackQuery):
    cat_id = callback.data.split("_", 1)[1]
    cat = CATEGORIES.get(cat_id)
    if not cat:
        await callback.answer("Серия не найдена", show_alert=True)
        return
    await callback.message.edit_text(f"{cat['title']}:", reply_markup=items_keyboard(cat_id))
    await callback.answer()


@dp.callback_query(F.data.startswith("item_"))
async def show_item(callback: CallbackQuery):
    pid = callback.data.split("_", 1)[1]
    name = PRODUCTS.get(pid)
    if not name:
        await callback.answer("Товар не найден", show_alert=True)
        return

    await callback.message.answer(name, reply_markup=order_keyboard(pid))
    await callback.answer()


@dp.callback_query(F.data.startswith("order_"))
async def start_order(callback: CallbackQuery, state: FSMContext):
    pid = callback.data.split("_", 1)[1]
    name = PRODUCTS.get(pid)
    if not name:
        await callback.answer("Товар не найден", show_alert=True)
        return

    await state.update_data(product_name=name)
    await state.set_state(Order.waiting_name)
    await callback.message.answer("Как к вам обращаться? Напишите имя:")
    await callback.answer()


@dp.message(Order.waiting_name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(customer_name=message.text)
    await state.set_state(Order.waiting_phone)
    await message.answer("Укажите номер телефона для связи:")


@dp.message(Order.waiting_phone)
async def get_phone(message: Message, state: FSMContext):
    await state.update_data(customer_phone=message.text)
    await state.set_state(Order.waiting_place)
    await message.answer("Где и когда удобно встретиться для передачи товара и оплаты?")


@dp.message(Order.waiting_place)
async def get_place(message: Message, state: FSMContext):
    data = await state.get_data()
    data["meeting_place"] = message.text

    order_text = (
        "🆕 Новый заказ (оплата наличными при встрече)\n\n"
        f"Товар: {data['product_name']}\n"
        f"Имя: {data['customer_name']}\n"
        f"Телефон: {data['customer_phone']}\n"
        f"Место/время встречи: {data['meeting_place']}\n"
        f"Telegram покупателя: @{message.from_user.username or 'нет username'} (id {message.from_user.id})"
    )

    await bot.send_message(ADMIN_CHAT_ID, order_text)
    await message.answer("Спасибо! Заказ принят, с вами свяжутся для подтверждения встречи.")
    await state.clear()


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
