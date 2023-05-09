import asyncio
import logging
import random
import string

from aiogram import Bot, Dispatcher, types

from aiogram import Router
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command, Text

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from aiogram import F

import user_settings
from config import API_TOKEN
from states import Settings

from tickers import Tickers

router = Router()

ticker = Tickers()
u_settings = user_settings.Settings()
u_settings.rate = 100
u_settings.limit = 1000000


@router.message(Command('start'))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Это димка. Отправь команду /rate чтобы получить актуальный курс рубля к доллару)")


@router.message(Command(commands=["cancel"]))
@router.message(Text(text="отмена", ignore_case=True))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text="Действие отменено",
    )


def make_string(data):
    result_s = ""
    for i in range(len(data)):
        result_s += f"Методы оплаты: <b>{', '.join(data[i]['payment_methods'])}</b>\n"
        result_s += f"Курс: <b>{data[i]['rate']}₽</b>\n"
        result_s += f"Лимит: <b>{data[i]['limit']}₽</b>\n"
        result_s += f"Доступно: <b>{data[i]['available_money']} USDT</b>\n"
        result_s += "\n"
        result_s += "-" * 10 + "\n"
    if len(result_s) > 0:
        return result_s
    return "Ничего не найдено по заданным параметрам ((("


@router.message(Command(commands=["rate"]))
async def get_currency_data(message: types.Message):
    data1 = ticker.get_tickers_data(page=1, max_limit=u_settings.limit, rate=u_settings.rate)
    data2 = ticker.get_tickers_data(page=2, max_limit=u_settings.limit, rate=u_settings.rate)[:3]

    if data1 and data1[0] and len(data1[0]['payment_methods']) != 0:
        await message.answer("<b>Страница 1</b>")
        await message.answer(make_string(data1))
    else:
        await message.answer(
            "Ничего не найдено по заданным параметрам (((\n\nЧтобы изменить параметры отправь команду /change_settings")
    if data2:
        await message.answer("<b>Страница 2</b>")
        await message.answer(make_string(data2))
    else:
        await message.answer(
            "Ничего не найдено по заданным параметрам (((\n\nЧтобы изменить параметры отправь команду /change_settings")


@router.message(Command(commands=["set_notify"]))
async def set_notify(message: types.Message):
    loop = asyncio.get_event_loop()
    loop.create_task(notify(message))
    await message.answer(f"Уведомления успешны установлены, "
                         f"когда курс будет меньше <b>{u_settings.rate}₽</b>, вам придет уведомление ;)\n\n"
                         f"<i>*Проверка курса производится каждые 5 минут</i>")


# @router.message(Command(commands=["cancel_notify"]))
# async def cancel_notify(message: types.Message):
#   global loop
#
#   await message.answer(f"Уведомления успешно отключены")


@router.message(Command(commands=["settings"]))
async def get_params(message: types.Message):
    await message.answer(
        f"Текущие параметры:\n\nКурс: <b>{u_settings.rate}₽</b>\nРазмер депозита: <b>{u_settings.limit}₽</b>\n"
        f"Валюта <b>RUB --> USDT</b>\n\n"
        "Чтобы изменить параметры отправь команду /change_settings")


@router.message(Command('change_settings'))
async def cmd_settings(message: types.Message, state: FSMContext):
    await message.answer('Укажите <b>максимальный размер депозита</b>:\n\n Отправьте /cancel чтобы выйти')
    await state.set_state(Settings.choosing_max_limit)


@router.message(Settings.choosing_max_limit, F.text.regexp(r"[+-]?([0-9]*[.])?[0-9]+").as_("digits"))
async def set_settings(message: types.Message, state: FSMContext):
    await state.update_data(chosen_limit=int(message.text.lower()))
    await message.answer(
        text="Спасибо. Теперь, пожалуйста, укажите <b>максимально допустимый курс</b>:\n\n Отправьте /cancel чтобы "
             "выйти",
    )
    await state.set_state(Settings.choosing_rate)


@router.message(Settings.choosing_max_limit)
async def set_settings_incorrectly(message: types.Message):
    await message.answer(
        text="<b>Некорректное значение!</b>\n\n"
             "Пожалуйста, введите просто число:\n\n Отправьте /cancel чтобы выйти'",
    )


@router.message(Settings.choosing_rate, F.text.regexp(r"[+-]?([0-9]*[.])?[0-9]+").as_("digits"))
async def limit_chosen(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    await message.answer(
        text=f"Выбраны следующие параметры:\nКурс: <b>{message.text}₽</b>\nРазмер депозита: <b>{user_data['chosen_limit']}₽</b>.\n\n"
             f"Перейти к просмотру котировок /rate",
    )
    u_settings.rate = float(message.text)
    u_settings.limit = float(user_data['chosen_limit'])

    await state.clear()


@router.message(Settings.choosing_rate)
async def limit_chosen_incorrectly(message: types.Message):
    await message.answer(
        text="<b>Некорректное значение!</b>\n\n"
             "Пожалуйста, введите просто число:\n\n Отправьте /cancel чтобы выйти'",
    )


async def notify(message: types.Message):
    while True:
        data = ticker.get_tickers_data(page=1, max_limit=u_settings.limit, rate=u_settings.rate - 0.01)
        if data:
            await message.answer(f"<b>Уведомление!!!!</b>\n\n{make_string(data)}")

        await asyncio.sleep(300)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    dp = Dispatcher(storage=MemoryStorage())
    bot = Bot(token=API_TOKEN, parse_mode="HTML")
    dp.include_router(router)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
