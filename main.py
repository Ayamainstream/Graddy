import logging
import ast
import bot_messages
import config
import moodle_login
import asyncio

from aiogram import *
from aiogram.bot import api
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from telegram.ext import Filters
from SQLighter import SQLighter

logging.basicConfig(level=logging.INFO)

PATCHED_URL = "https://telegg.ru/orig/bot{token}/{method}"
setattr(api, 'API_URL', PATCHED_URL)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot=bot, storage=MemoryStorage())
db = SQLighter('sql.db')


class Form(StatesGroup):
    username = State()
    password = State()
    feedback = State()


async def log_text(debug_text):
    print(debug_text)


async def start(message: types.Message):
    user_id = message.from_user.id
    config.user_id = user_id
    await message.reply(text=bot_messages.start_command_response, reply=False)
    if not db.subscriber_exists(user_id):
        db.add_subscriber(user_id)


async def help(message: types.Message):
    await message.reply(text=bot_messages.help_command_response, reply=False)


async def unknown_command(message: types.Message):
    await message.reply(text=bot_messages.unknown_command_response, reply=False)


async def username_choice(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['username'] = message.text
    new_username = data['username']
    user_id = message.from_user.id
    await log_text('{} wants to join Graddy community'.format(new_username))
    await message.reply(bot_messages.updated_login_response, reply=False)
    await state.finish()
    db.update_username(user_id, new_username)


async def set_username(message: types.Message):
    await Form.username.set()
    await message.reply(text=bot_messages.set_username_response, reply=False)


async def password_choice(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['password'] = message.text
    new_password = data['password']
    user_id = message.from_user.id
    await message.reply(bot_messages.updated_password_response, reply=False)
    await state.finish()
    db.update_password(user_id, new_password)


async def set_password(message: types.Message):
    await Form.password.set()
    await message.reply(text=bot_messages.set_password_response, reply=False)


async def notify_grades(message: types.Message):
    try:
        user_id = message.from_user.id
        username = db.get_username(user_id)
        password = db.get_password(user_id)
        status = db.get_subscription(user_id)
        await message.reply(text=bot_messages.checking_data_response, reply=False)
        current_grades = moodle_login.get_all_grades(username, password)
        if len(current_grades.keys()) == 0:
            await message.reply(text=bot_messages.wrong_moodle_data_response, reply=False)
        elif status:
            await message.reply(text=bot_messages.already_notifying_response, reply=False)
        else:
            db.update_subscription(user_id, True)
            db.save_grades(username, str(current_grades))
            await message.reply(text=bot_messages.successful_moodle_login_response, reply=False)
    except:
        await message.reply(text=bot_messages.no_login_or_password_response, reply=False)


async def disable_notify(message: types.Message):
    user_id = message.from_user.id
    status = db.get_subscription(user_id)
    if status:
        await message.reply(text=bot_messages.already_not_notifying_response, reply=False)
    else:
        await message.reply(text=bot_messages.checking_data_response, reply=False)
        db.update_subscription(user_id, False)
        await message.reply(text=bot_messages.disable_notifying_response, reply=False)


async def notifying_grades_process(wait_for):
    grade_cycles = 0
    while True:
        await asyncio.sleep(wait_for)
        grade_cycles += 1
        await log_text('Starting to check for new grades.. {}'.format(grade_cycles))
        chats = db.get_all_chats_info()
        total_number = len(chats)
        current_number = 0
        for chat in chats:
            try:
                current_number += 1
                user_id = chat[0]
                username = chat[1]
                password = chat[2]
                await log_text('Checking {} grades.. {}/{}'.format(username, current_number, total_number))
                current_grades = moodle_login.get_all_grades(username, password)
                if len(current_grades.keys()) == 0:
                    await bot.send_message(user_id, text=bot_messages.password_changed_response)
                    continue
                old_grades = ast.literal_eval(db.get_grades_for_chat(user_id))
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
                        if unique_grade and course_name.lower() != 'error' and name.lower() != 'error' \
                                and grade.lower() != 'error':
                            await bot.send_message(user_id, text='Новая оценка!\n\n')
                            info = '{} - {}\n'.format('Course name', course_name)
                            info += '{} - {}\n'.format('Grade name', name)
                            info += '{} - {}\n'.format('Grade', grade)
                            if 'range' in course_grade and course_grade['range'].lower() != 'error':
                                info += '{} - {}\n'.format('Range', course_grade['range'])
                            if 'percentage' in course_grade and course_grade['percentage'].lower() != 'error':
                                info += '{} - {}\n'.format('Percentage', course_grade['percentage'])
                            await bot.send_message(user_id, text=info)
                            await log_text('{} got a new grade'.format(username))
                            await log_text('{} - {} - {}'.format(course_name, name, grade))
                    db.save_grades(username, str(current_grades))
            except:
                await log_text('Grades exception occurred but still running..')
                pass


async def my_grades(message: types.Message):
    await message.reply(text=bot_messages.checking_data_response, reply=False)
    user_id = message.from_user.id
    username = db.get_username(user_id)
    password = db.get_password(user_id)
    if str(username) == "None" or str(password) == "None":
        await message.reply(text=bot_messages.no_login_or_password_response, reply=False)
    else:
        try:
            course_names = moodle_login.get_course_names(username, password)
            markup = types.InlineKeyboardMarkup()
            for key in course_names:
                markup.add(types.InlineKeyboardButton(text=key, callback_data=key))

                @dp.callback_query_handler()
                async def process_callback(call: types.CallbackQuery):
                    await bot.edit_message_text(text=moodle_login.get_grades(username, password, call.data),
                                                chat_id=call.message.chat.id, message_id=call.message.message_id)

            await message.reply(text="Выбери предмет: ", reply_markup=markup, reply=False)
        except:
            await message.reply(text=bot_messages.wrong_moodle_data_response)


async def feedback(message: types.Message):
    await Form.feedback.set()
    await message.reply(bot_messages.feedback_command_response)


async def feedback_choice(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['feedback'] = message.text
    feedback_text = data['feedback']
    feedback_username = message.chat.username
    final_feedback = '@{} has left feedback 📝\n\n{}'.format(feedback_username, feedback_text)
    await bot.send_message(chat_id='648374421', text=final_feedback)
    await message.reply(text=bot_messages.feedback_sent_response)
    await state.finish()


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.finish()
    await message.reply(bot_messages.command_cancel_response)


def main():
    dp.register_message_handler(start, commands=['start'])
    dp.register_message_handler(help, commands=['help'])
    dp.register_message_handler(set_username, commands=['set_username'])
    dp.register_message_handler(username_choice, state=Form.username)
    dp.register_message_handler(set_password, commands=['set_password'])
    dp.register_message_handler(password_choice, state=Form.password)
    dp.register_message_handler(notify_grades, commands=['notify_grades'])
    dp.register_message_handler(disable_notify, commands=['disable_notify'])
    dp.register_message_handler(my_grades, commands=['my_grades'])
    dp.register_message_handler(feedback, commands=['feedback'])
    dp.register_message_handler(feedback_choice, state=Form.feedback)
    dp.register_message_handler(unknown_command, Filters.command)

    loop = asyncio.get_event_loop()
    loop.create_task(notifying_grades_process(100))
    executor.start_polling(dispatcher=dp)


if __name__ == '__main__':
    main()
