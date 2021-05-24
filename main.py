import api_calls
import bot_messages
import config
import logging
import moodle_login
import asyncio

from telegram.ext import Filters
from aiogram.bot import api
from aiogram import *

logging.basicConfig(level=logging.INFO)

PATCHED_URL = "https://telegg.ru/orig/bot{token}/{method}"
setattr(api, 'API_URL', PATCHED_URL)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot=bot)


async def log_text(debug_text):
    print(debug_text)


async def start(message: types.Message):
    await message.reply(text=bot_messages.start_command_response, reply=False)


async def help(message: types.Message):
    await message.reply(text=bot_messages.help_command_response, reply=False)


async def unknown_command(message: types.Message):
    await message.reply(text=bot_messages.unknown_command_response, reply=False)


def get_all_chats_info():
    return api_calls.get_all_chats_info()



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


def notifying_grades_process(message: types.Message):
    grade_cycles = 0
    while True:
        grade_cycles += 1
        log_text('Starting to check for new grades.. {}'.format(grade_cycles))
        chats = get_all_chats_info()
        total_number = len(chats)
        current_number = 0
        for chat in chats:
            if not 'notify_grades' in chat or not chat['notify_grades']:
                continue
            try:
                current_number += 1
                chat_id = chat['chat_id']
                username = chat['username']
                log_text('Checking {} grades.. {}/{}'.format(username, current_number, total_number))
                current_grades = moodle_login.get_all_grades()
                if len(current_grades.keys()) == 0:
                    await message.reply(text=bot_messages.password_changed_response)
                    api_calls.disable_notify_grades_for_chat(chat_id)
                    continue
                old_grades = chat['grades']
                for course_name, course_grades in current_grades.items():
                    if not course_name in old_grades:
                        old_grades[course_name] = []
                    for course_grade in course_grades:
                        name = course_grade['name']
                        grade = course_grade['grade']
                        unique_grade = True
                        for old_grade in old_grades[course_name]:
                            old_name = old_grade['name']
                            old_grade = old_grade['grade']
                            if old_name == name and old_grade == grade:
                                unique_grade = False
                        if unique_grade and course_name.lower() != 'error' and name.lower() != 'error' and grade.lower() != 'error':
                            await message.reply(text='Новая оценка!\n\n')
                            info = '{} - <b>{}</b>\n'.format('Course name', course_name)
                            info += '{} - <b>{}</b>\n'.format('Grade name', name)
                            info += '{} - <b>{}</b>\n'.format('Grade', grade)
                            if 'range' in course_grade and course_grade['range'].lower() != 'error':
                                info += '{} - <b>{}</b>\n'.format('Range', course_grade['range'])
                            if 'percentage' in course_grade and course_grade['percentage'].lower() != 'error':
                                info += '{} - <b>{}</b>\n'.format('Percentage', course_grade['percentage'])
                            await message.reply(text=info)
                            log_text('{} got a new grade'.format(username))
                            log_text('{} - {} - {}'.format(course_name, name, grade))
            except:
                log_text('Grades exception occured but still running..')
                pass



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
