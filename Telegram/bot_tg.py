from email import message
import logging
from subprocess import call  # Логирование 
# Telegram 
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
import datetime
from datetime import timedelta
# генерация уникальных идентификаторов для сертификатов
import uuid

import os
# токен для бота в файле settings.py (нужно создать)
from settings import TOKEN
#
from PPTX_GENERATOR import PPTX_GENERATOR
from PPTX_to_PDF import pptx_to_pdf
# БД sqlite (рекомендую DB Browser) 
import sqlite3
from sqlite3.dbapi2 import Cursor

from string import Template

from morphy_using import name_change

from asgiref.sync import sync_to_async

API_TOKEN = TOKEN
user_name = ''
# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

mess = {}  #Тут будем хранить время последнего обращения к боту от пользователя
# так делать плохо и лучше БД использовать, но сейчас пойдёт

# клавиатура из обной кнопки
keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
buttons = ["Хочу сертификат"]
keyboard.add(*buttons)

template_message_start = Template("Привет, $name!\n👋🏼😀\nЯ Квантоша, бот, созданный проектной группой в IT Квантуме, "\
		"для отправки сертификата о посещении дня открытых дверей\nНапиши мне свои ФИО и я отправлю тебе твой сертификат")

class Form(StatesGroup):
	waiting_for_your_name = State()
	waiting_for_your_correct_name = State()

@dp.message_handler(commands=['start', 'help', 'начать', 'сертификат'])
async def send_welcome(message: types.Message):
	message_start = template_message_start.substitute(name=message.from_user.first_name)
	await message.reply(message_start, reply_markup=keyboard)

# на всякий случай
@dp.message_handler(Text(equals=['start', 'help', 'начать', 'сертификат']))
async def send_welcome(message: types.Message):
	message_start = template_message_start.substitute(name=message.from_user.first_name)
	await message.reply(message_start, reply_markup=keyboard)

@dp.message_handler(Text(equals="Хочу сертификат"))
async def certificate(message: types.Message):
	await message.answer("Напиши мне свои ФИО", reply_markup=keyboard)
	await Form.waiting_for_your_name.set()
	@dp.message_handler(state=Form.waiting_for_your_name)
	async def main_function(message: types.Message, state: FSMContext):
		await state.update_data(name=message.text)
		await message.answer("Твой сертификат создаётся, подожди немного")
		user_name = name_change(message.text)
		inline_btn_yes = InlineKeyboardButton('Да', callback_data='Да')
		inline_btn_no = InlineKeyboardButton('Нет', callback_data='Нет')
		inline_kb = InlineKeyboardMarkup().add(inline_btn_yes, inline_btn_no)
		await message.reply(Template("Сертификат будет выдан $cased_name\nВсе ли правильно?").substitute(cased_name=user_name), reply_markup=inline_kb)
		await state.finish()
		@dp.callback_query_handler(lambda c: c.data == 'Да')
		async def create(callback_query: types.CallbackQuery):
			#  "гениальный" анти DDoS
			can_receive_message = 1
			# if message.from_user.id not in mess: #Если пользователь не писал ещё сообщения, то добавляем его ID в словарь и присваиваем время
			# 	mess[message.from_user.id] = datetime.datetime.now()
			# elif (datetime.datetime.now() - mess[message.from_user.id]).total_seconds() < 15:  # Ставим ограничения на время последовательных сообщений боту
			# 	await message.answer('Мне можно писать не чаще чем раз в 15 секунд\nಥ_ಥ\nТебе придётся подождать')
			# 	can_receive_message = 0
			if can_receive_message:
				user_name = name_change(message.text)
				# формируем дату: дд-мм-гггг
				today_date = "{:02d}".format(datetime.date.today().day)  # форматирование строки - всегда из двух числе  
				today_date += "-" + "{:02d}".format(datetime.date.today().month)
				today_date += "-" + str(datetime.date.today().year)
				UID = uuid.uuid4().hex #уникальный идентификатор для ID сертификата
				file = await sync_to_async(PPTX_GENERATOR)(user_name, UID, today_date)  # формирование pptx документа из шаблона (ФИО, ID, дата)
				# file - ФИО+ID:  Кастрюлев Евлампий Спиридонович_ID 
				pptx_to_pdf(file, today_date)

				doc = open('./GENERATED_PDF/' + today_date + '/' + file + ".pdf", 'rb')  # берём файл
				await bot.answer_callback_query(callback_query.id)
				await bot.send_document(callback_query.from_user.id, doc)  # и отправляем его пользователю
				doc.close() # Закрываем файл

				# работа с SQLLite
				connect = sqlite3.connect('users.db')
				cursor = connect.cursor()
				cursor.execute("""CREATE TABLE IF NOT EXISTS users(
						user_id TEXT PRIMARY KEY,
						user_name TEXT,
						date TEXT,
						time TEXT,
						source TEXT,
						uname_source TEXT,
						uid_source TEXT
						)
						""")	

				now_time = datetime.datetime.now()
				users_list = [UID, user_name, today_date, now_time.strftime("%H:%M:%S"), "Telegram", callback_query.from_user.username, callback_query.from_user.id]
				cursor.execute("INSERT INTO users VALUES(?,?,?,?,?,?,?);", users_list)
				connect.commit()

		@dp.callback_query_handler(lambda c: c.data == 'Нет')
		async def create_with_user_name(callback_query: types.CallbackQuery, state: FSMContext):
			await bot.answer_callback_query(callback_query.id)
			await bot.send_message(callback_query.from_user.id, "Как будет правильно?")
			await Form.waiting_for_your_correct_name.set()
			@dp.message_handler(state=Form.waiting_for_your_correct_name)
			async def another_main_function(message_1: types.Message):
				global mess  # время последнего обращения к боту от пользователя (словарь)
				await state.update_data(correct_name=message_1.text)
				#  "генийальный" анти DDoS
				can_receive_message = 1
				# if message.from_user.id not in mess: #Если пользователь не писал ещё сообщения, то добавляем его ID в словарь и присваиваем время
				# 	mess[message.from_user.id] = datetime.datetime.now()
				# elif (datetime.datetime.now() - mess[message.from_user.id]).total_seconds() < 15:  # Ставим ограничения на время последовательных сообщений боту
				# 	await message.answer('Мне можно писать не чаще чем раз в 15 секунд\nಥ_ಥ\nТебе придётся подождать')
				# 	can_receive_message = 0
				if can_receive_message:
					# формируем дату: дд-мм-гггг
					today_date = "{:02d}".format(datetime.date.today().day)  # форматирование строки - всегда из двух числе  
					today_date += "-" + "{:02d}".format(datetime.date.today().month)
					today_date += "-" + str(datetime.date.today().year)
					UID = uuid.uuid4().hex #уникальный идентификатор для ID сертификата
					file = await sync_to_async(PPTX_GENERATOR)(message_1.text, UID, today_date)  # формирование pptx документа из шаблона (ФИО, ID, дата)
					# file - ФИО+ID:  Кастрюлев Евлампий Спиридонович_ID 
					pptx_to_pdf(file, today_date)

					doc = open('./GENERATED_PDF/' + today_date + '/' + file + ".pdf", 'rb')  # берём файл
					await message_1.answer_document(document=doc)  # и отправляем его пользователю

					# работа с SQLLite
					connect = sqlite3.connect('users.db')
					cursor = connect.cursor()
					cursor.execute("""CREATE TABLE IF NOT EXISTS users(
							user_id TEXT PRIMARY KEY,
							user_name TEXT,
							date TEXT,
							time TEXT,
							source TEXT,
							uname_source TEXT,
							uid_source TEXT
							)
							""")	

					now_time = datetime.datetime.now()
					users_list = [UID, user_name, today_date, now_time.strftime("%H:%M:%S"), "Telegram", message.from_user.username, message.from_user.id]
					cursor.execute("INSERT INTO users VALUES(?,?,?,?,?,?,?);", users_list)
					connect.commit()
					await state.finish()

if __name__ == '__main__':
	while True:
		try:
			executor.start_polling(dp, skip_updates=True)
		except Exception as e:
			print(e)
    