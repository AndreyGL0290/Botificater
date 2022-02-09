# pip install aiofiles

import datetime
import uuid
import os
from sqlite3.dbapi2 import Cursor

from vkbottle.tools.dev_tools import keyboard
from PPTX_GENERATOR import PPTX_GENERATOR 
import sqlite3

import logging
from vkbottle.bot import Bot, Message
from vkbottle.tools import DocMessagesUploader
from settings import TOKEN

from morphy_using import name_change

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)

keyboard = '{"buttons":[[{"action":{"type":"text","label":"Хочу сертификат","payload":""},"color":"positive"}]]}'
empty_keyboard = '{"buttons":[]}'
mess = {}  #Тут будем хранить время последнего обращения к боту от пользователя
# так делать плохо и лучше БД использовать, но сейчас пойдёт

@bot.on.message(text="Начать")
async def hi_handler(message: Message):
    users_info = await bot.api.users.get(message.from_id)
    S = "Привет, " + users_info[0].first_name
    S += "\n👋🏼😀\nЯ Квантоша, бот, созданный для отправки сертификата о посещении дня открытых дверей\
        \nНапиши мне своё имя и я отправлю тебе твой сертификат"
    
    await message.answer(S, keyboard=keyboard)

@bot.on.message(text="Хочу сертификат")
async def what_is_name(message: Message):
    await message.answer("Напиши мне свои ФИО", keyboard=empty_keyboard)

@bot.on.message()
async def certificate(message: Message):
    global mess  # время последнего обращения к боту от пользователя (словарь)
    users_info = await bot.api.users.get(message.from_id)
    #  "генийальный" анти DDoS
    can_receive_message = 1
    if users_info[0].id not in mess: #Если пользователь не писал ещё сообщения, то добавляем его ID в словарь и присваиваем время
        mess[users_info[0].id] = datetime.datetime.now()
    elif (datetime.datetime.now() - mess[users_info[0].id]).total_seconds() < 15:  # Ставим ограничения на время последовательных сообщений боту
        await message.answer('Мне можно писать не чаще чем раз в 15 секунд\nಥ_ಥ\nТебе придётся подождать')
        can_receive_message = 0
    if can_receive_message:
        await message.answer("Твой сертификат создаётся, подожди немного", keyboard=keyboard)
        now = str(datetime.date.today().day)
        now += "-" + str(datetime.date.today().month)
        now += "-" + str(datetime.date.today().year)
        UID = uuid.uuid4().hex #уникальный идентификатор
        user_name = name_change(message.text)
        file = PPTX_GENERATOR(user_name, UID, now)
        #print("GENERATOR OK")
        file = file.replace(" ", "©")
        command = "python PPTX_to_PDF.py " + file + " " + now
        res = os.system(command)  # открываем скрипт для форматирования
        file = file.replace("©", " ")
        #print("PDF OK")
        doc = await DocMessagesUploader(bot.api).upload(
            file + ".pdf", './GENERATED_PDF/' + now + '/' + file + ".pdf", peer_id=message.peer_id
        )
        await message.answer(attachment=doc, reply_to=message.id)

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
        users_list = [UID, message.text, now, now_time.strftime("%H:%M:%S"), "VK", users_info[0].first_name + " " + users_info[0].last_name, users_info[0].id]
        cursor.execute("INSERT INTO users VALUES(?,?,?,?,?,?,?);", users_list)
        connect.commit()

bot.run_forever()


