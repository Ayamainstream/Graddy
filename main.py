import api_calls
import bot_messages
import config
import logging
import moodle_login

from telegram.ext import Filters
from aiogram.bot import api
from aiogram import *

logging.basicConfig(level=logging.INFO)

PATCHED_URL = "https://telegg.ru/orig/bot{token}/{method}"
setattr(api, 'API_URL', PATCHED_URL)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot=bot)


def log_text(debug_text):
    print(debug_text)


async def start(message: types.Message):
    await message.reply(text=bot_messages.start_command_response, reply=False)


async def help(message: types.Message):
    await message.reply(text=bot_messages.help_command_response, reply=False)


async def unknown_command(message: types.Message):
    await message.reply(text=bot_messages.unknown_command_response, reply=False)


async def set_username(message: types.Message):
    await message.reply(text=bot_messages.set_username_response, reply=False)


async def set_password(message: types.Message):
    await message.reply(text=bot_messages.set_password_response, reply=False)
    new_username = message.text.lower()
    api_calls.update_username(new_username)


async def notify_grades(message: types.Message):
    chat_id = message.message_id
    await message.reply(text=bot_messages.checking_data_response)
    current_grades = moodle_login.get_all_grades()
    if len(current_grades.keys()) == 0:
        await message.reply(text=bot_messages.wrong_moodle_data_response)
    else:
        await message.reply(text=bot_messages.successful_moodle_login_response)
        set_grades_for_chat(chat_id, current_grades)


def set_grades_for_chat(chat_id, new_grades):
    api_calls.update_grades_for_chat(chat_id, new_grades)


async def my_grades(message: types.Message):
    course_names = moodle_login.get_course_names()
    markup = types.InlineKeyboardMarkup()
    for key in course_names:
        markup.add(types.InlineKeyboardButton(text=key, callback_data=key))

        @dp.callback_query_handler()
        async def process_callback(call: types.CallbackQuery):
            await bot.edit_message_text(text=moodle_login.get_grades(call.data), chat_id=call.message.chat.id,
                                        message_id=call.message.message_id)

    await message.reply(text="Выбери предмет: ", reply_markup=markup, reply=False)

#
# async def feedback_choice(message: types.Message):
#     await message.reply(bot_messages.feedback_command_response)
#     feedback_username, feedback_text = message.chat.username, message.text
#     final_feedback = '@{} has left feedback 📝\n\n{}'.format(feedback_username, feedback_text)
#     await message.reply(chat_id='-389544616', text=final_feedback)
#     await message.reply(text=bot_messages.feedback_sent_response)


def main():
    dp.register_message_handler(start, commands=['start'])
    dp.register_message_handler(help, commands=['help'])
    # dp.register_message_handler(help, commands=['set_username'])
    # dp.register_message_handler(help, commands=['set_password'])
    dp.register_message_handler(notify_grades, commands=['notify_grades'])
    dp.register_message_handler(my_grades, commands=['my_grades'])
    dp.register_message_handler(unknown_command, Filters.command)
    executor.start_polling(dispatcher=dp)


if __name__ == '__main__':
    main()
