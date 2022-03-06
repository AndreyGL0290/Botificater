# Логирование
import logging

# Telegram 
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext

# Работа со временем
import datetime

# Генерация уникальных идентификаторов для сертификатов
import uuid

# Токен для бота в файле settings.py (нужно создать)
from settings import TOKEN

# Наши пакеты
from PPTX_GENERATOR import PPTX_GENERATOR
from morphy_using import name_change
from PPTX_to_PDF import pptx_to_pdf

# БД sqlite (рекомендую DB Browser) 
import sqlite3

# Работа со строками
from string import Template

# Работа с асинхронностью
from asgiref.sync import sync_to_async

# Токен, который берется из settings.py (дается при создании бота в BotFather)
API_TOKEN = TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

mess = {}  # Тут будем хранить время последнего обращения к боту от пользователя
# Так делать плохо и лучше БД использовать, но сейчас пойдёт

# Клавиатура из одной кнопки
keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
buttons = ["Хочу сертификат"]
keyboard.add(*buttons)

template_message_start = Template("Привет, $name!\n👋🏼😀\nЯ Квантоша, бот, созданный проектной группой в IT Квантуме, "\
		"для отправки сертификата о посещении дня открытых дверей\nНапиши мне свои ФИО и я отправлю тебе твой сертификат")

# Создаем класс с возможными состояниями
class Form(StatesGroup):
	waiting_for_your_name = State()

@dp.message_handler(commands=['start', 'help', 'начать', 'сертификат'])
async def send_welcome(message: types.Message):
	message_start = template_message_start.substitute(name=message.from_user.first_name)
	await message.reply(message_start, reply_markup=keyboard)

# На всякий случай
@dp.message_handler(Text(equals=['start', 'help', 'начать', 'сертификат']))
async def send_welcome(message: types.Message):
	message_start = template_message_start.substitute(name=message.from_user.first_name)
	await message.reply(message_start, reply_markup=keyboard)

@dp.message_handler(Text(equals="Хочу сертификат"))
async def certificate(message: types.Message, state: FSMContext):
	await message.answer("Напиши мне свои ФИО", reply_markup=keyboard)
	await state.update_data(cased=False)
	await Form.waiting_for_your_name.set()

# Отреагирует на введенное ФИО пользователя
@dp.message_handler(state=Form.waiting_for_your_name)
async def enter_your_name(message: types.Message, state: FSMContext):
	cased_user_name = message.text
	# Если имя человека просклонялось неправильно и он нажал НЕТ
	data = await state.get_data()
	is_cased = data['cased']
	if not is_cased:
		cased_user_name = name_change(message.text)
	
	# Заносим склоненное имя в переменную этого состояния
	await state.update_data(name=cased_user_name)
	inline_btn_yes = InlineKeyboardButton('Да', callback_data='Да')
	inline_btn_no = InlineKeyboardButton('Нет', callback_data='Нет')
	inline_kb = InlineKeyboardMarkup().add(inline_btn_yes, inline_btn_no)
	await message.answer(f"Сертификат будет выдан {cased_user_name}\nВсё ли правильно?", reply_markup=inline_kb)

# Если человек скажет что фамилия просклонялась правильно
@dp.callback_query_handler(lambda c: c.data == "Да", state=Form.waiting_for_your_name)
async def user_answered_yes(callback_query: types.CallbackQuery, state: FSMContext):
	# Сделать анти DDOS
	await bot.answer_callback_query(callback_query.id)
	await main_algorithm(state, callback_query)

# Если человек скажет, что фамилия просклонялась не правильно
@dp.callback_query_handler(lambda c: c.data == "Нет", state=Form.waiting_for_your_name)
async def user_answered_no(callback_query: types.CallbackQuery, state: FSMContext):
	await bot.answer_callback_query(callback_query.id)
	await bot.send_message(callback_query.from_user.id, "Как будет правильно?")
	await state.update_data(cased=True)
	await Form.waiting_for_your_name.set()

async def main_algorithm(state, instance):
	# Если перешли в алгоритм из ветки ДА
	try:
		data = await state.get_data()
		user_name = data["name"]
	# Если перешли в алгоритм из ветки НЕТ
	except KeyError:
		user_name = instance.text

	today_date = "{:02d}".format(datetime.date.today().day)  # Форматирование строки - всегда из двух числе  
	today_date += "-" + "{:02d}".format(datetime.date.today().month)
	today_date += "-" + str(datetime.date.today().year)

	UID = uuid.uuid4().hex # Уникальный идентификатор для ID сертификата

	file = await sync_to_async(PPTX_GENERATOR)(user_name, UID, today_date)  # Фрмирование pptx документа из шаблона (ФИО, ID, дата)

	pptx_to_pdf(file, today_date)

	with open('./GENERATED_PDF/' + today_date + '/' + file + ".pdf", 'rb') as doc: # Берём файл
		# Отправка файла из ветки ДА
		if type(instance) == types.CallbackQuery:
			await bot.answer_callback_query(instance.id)
			await bot.send_document(instance.from_user.id, doc) # Отправляем его пользователю
		# Отправка файла из ветки НЕТ
		else:
			await instance.answer_document(document=doc) # Отправляем его пользователю

	# Работа с БД
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
	users_list = [UID, user_name, today_date, now_time.strftime("%H:%M:%S"), "Telegram", instance.from_user.username, instance.from_user.id]
	cursor.execute("INSERT INTO users VALUES(?,?,?,?,?,?,?);", users_list)
	connect.commit()

	# Заканчиваем диалог с пользователем
	await state.finish()

if __name__ == '__main__':
	while True:
		try:
			executor.start_polling(dp, skip_updates=True)
		except Exception as e:
			print(e)
    