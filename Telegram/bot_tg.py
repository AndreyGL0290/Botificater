import logging  # Логирование 
# Telegram 
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text

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

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

mess = {}  #Тут будем хранить время последнего обращения к боту от пользователя
# так делать плохо и лучше БД использовать, но сейчас пойдёт

# клавиатура из обной кнопки
keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
buttons = ["Хочу сертификат"]
keyboard.add(*buttons)

template_message_start = Template("Привет, $name!\n👋🏼😀\nЯ Квантоша, бот, созданный проектной группой в IT Квантуме, "\
		"для отправки сертификата о посещении дня открытых дверей\nНапиши мне свои ФИО и я отправлю тебе твой сертификат")

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

@dp.message_handler()
async def main_function(message: types.Message):
	global mess  # время последнего обращения к боту от пользователя (словарь)
	
	#  "генийальный" анти DDoS
	can_receive_message = 1
	# if message.from_user.id not in mess: #Если пользователь не писал ещё сообщения, то добавляем его ID в словарь и присваиваем время
	# 	mess[message.from_user.id] = datetime.datetime.now()
	# elif (datetime.datetime.now() - mess[message.from_user.id]).total_seconds() < 15:  # Ставим ограничения на время последовательных сообщений боту
	# 	await message.answer('Мне можно писать не чаще чем раз в 15 секунд\nಥ_ಥ\nТебе придётся подождать')
	# 	can_receive_message = 0
	if can_receive_message:
		mess[message.from_user.id] = datetime.datetime.now()  # обновляем время последнего обращения от пользователя
		await message.answer("Твой сертификат создаётся, подожди немного")
		# формируем дату: дд-мм-гггг
		today_date = "{:02d}".format(datetime.date.today().day)  # форматирование строки - всегда из двух числе  
		today_date += "-" + "{:02d}".format(datetime.date.today().month)
		today_date += "-" + str(datetime.date.today().year)
		UID = uuid.uuid4().hex #уникальный идентификатор для ID сертификата
		user_name = name_change(message.text)

		file = await sync_to_async(PPTX_GENERATOR)(user_name, UID, today_date)  # формирование pptx документа из шаблона (ФИО, ID, дата)
		# file - ФИО+ID:  Кастрюлев Евлампий Спиридонович_ID 
		pptx_to_pdf(file, today_date)
		doc = open('./GENERATED_PDF/' + today_date + '/' + file + ".pdf", 'rb')  # берём файл
		await message.reply_document(doc)  # и отправляем его пользователю

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

if __name__ == '__main__':
	while True:
		try:
			executor.start_polling(dp, skip_updates=True)
		except Exception as e:
			print(e)
    