import telebot
import sqlite3
import qrcode
import code128
from reportlab.pdfgen.canvas import Canvas
import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from telebot import types

db_name = 'business.db'
productIsOutText = 'Товар закончился '
typeProductText = 'Выбери тип товара'
typeModelText = 'Выбери фирму'
typeModelSettingText = 'Выбери модель'
cancelText = 'Отмена ↩'
pikupText = '🏃‍♂️ САМОВЫВОЗ 🏃‍♀️'
deliveryText = '📦 ДОСТАВКА 📦'
specialText = 'nvjklfhahpoqeu79801845ioewsdf'
data = {}

bot = telebot.TeleBot(bot_id)


def clearData(message):
    data['delivery_name' + str(message.chat.id)] = ""
    data['delivery_type' + str(message.chat.id)] = ""
    data['delivery_cod' + str(message.chat.id)] = ""
    data['menu' + str(message.chat.id)] = "-"
    data['type_sale' + str(message.chat.id)] = "-"
    data['group' + str(message.chat.id)] = "-"
    data['name' + str(message.chat.id)] = "-"
    data['model' + str(message.chat.id)] = "-"
    data['size' + str(message.chat.id)] = "-"
    data['statistics' + str(message.chat.id)] = "-"
    data['id_messages' + str(message.chat.id)] = []


def getPermission(id):
    #return True
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute('SELECT id_telegram FROM users')
    dataEl = cur.fetchall()
    cur.close()
    conn.close()
    for el in dataEl:
        if id == el[0]:
            return True
    return False


@bot.message_handler(commands=['start'])
def main(message):
    if getPermission(message.from_user.id):
        start(message)
    else:
        bot.send_message(message.chat.id,
                         f'Привет {message.from_user.first_name}, у тебя нет доступа к данному боту 🖕🖕🖕')


def start(message):
    global data
    clearData(message)
    bot.clear_step_handler_by_chat_id(message.chat.id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton('🗄 Наличие 🗄', callback_data='availability'))
    markup.add(types.InlineKeyboardButton('💰 Продажа 💰', callback_data='sale'))
    markup.add(types.InlineKeyboardButton('💳 Номер карты 💳', callback_data='karta'))
    markup.add(types.InlineKeyboardButton('📊 Статистика 📊', callback_data='statistics'))
    markup.add(types.InlineKeyboardButton('💸 Возврат 💸', callback_data='refund'))
    markup.add(types.InlineKeyboardButton('⚙ Администрирование ⚙', callback_data='admin'))
    bot.send_message(message.chat.id, f'Привет {message.from_user.first_name}! Что тебе подсказать?',
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    if not getPermission(call.from_user.id):
        bot.send_message(call.message.chat.id,
                         f'Привет {call.message.from_user.first_name}, у тебя больше нет доступа к данному боту 🖕🖕🖕')
        return
    global data
    if call.data == 'availability':
        clearData(call.message)
        data['menu' + str(call.message.chat.id)] = 1
        choice_product(call.message)
    elif call.data == 'sale':
        clearData(call.message)
        data['menu' + str(call.message.chat.id)] = 2
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton(pikupText))
        markup.add(types.KeyboardButton(deliveryText))
        markup.add(types.KeyboardButton(cancelText))
        msg = bot.send_message(call.message.chat.id, 'Выбери тип продажи', reply_markup=markup)
        data['id_messages' + str(call.message.chat.id)].append(msg.message_id)
        bot.register_next_step_handler(call.message, setDelivery)
    elif call.data == 'karta':
        getCards(call.message)
    elif call.data == 'refund':
        clearData(call.message)
        data['menu' + str(call.message.chat.id)] = 3
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton(pikupText))
        markup.add(types.KeyboardButton(deliveryText))
        markup.add(types.KeyboardButton(cancelText))
        msg = bot.send_message(call.message.chat.id, 'Выбери тип продажи', reply_markup=markup)
        data['id_messages' + str(call.message.chat.id)].append(msg.message_id)
        bot.register_next_step_handler(call.message, setDelivery)

    elif call.data == 'statistics':
        clearData(call.message)
        data['menu' + str(call.message.chat.id)] = 4
        markup = types.InlineKeyboardMarkup()
        btnAllStatistics = types.InlineKeyboardButton('🌐 ЗА ВСЕ ВРЕМЯ 🌐', callback_data='all_time')
        btnCurStatistics = types.InlineKeyboardButton('📅 СЕГОДНЯ 📅', callback_data='cur_time')
        btnAllMonthStatistics = types.InlineKeyboardButton('🌐📈 ЗА ВСЕ ВРЕМЯ ПО МЕСЯЦАМ 📉🌐', callback_data='all_month')
        btnCurMonthStatistics = types.InlineKeyboardButton('📅📈 ЗА ТЕКУЩИЙ МЕСЯЦ 📉📅', callback_data='cur_month')
        markup.add(btnAllStatistics)
        markup.add(btnCurStatistics)
        markup.add(btnAllMonthStatistics)
        markup.add(btnCurMonthStatistics)
        msg = bot.send_message(call.message.chat.id, 'Выбери период', reply_markup=markup)
        data['id_messages' + str(call.message.chat.id)].append(msg.message_id)
    elif call.data == 'admin':
        clearData(call.message)
        data['menu' + str(call.message.chat.id)] = 5
        markup = types.InlineKeyboardMarkup()
        btnAddCard = types.InlineKeyboardButton('💳 Добавить номер карты ✅', callback_data='add_card')
        btnDelCard = types.InlineKeyboardButton('💳 Удалить номер карты ❌', callback_data='del_card')
        btnSearchUser = types.InlineKeyboardButton('🧐 Узнать ID пользователя 🔍', callback_data='search_user')
        btnChangeUser = types.InlineKeyboardButton('👨‍💻 Изменить кладовщика ✅', callback_data='change_user')
        btnAddUser = types.InlineKeyboardButton('👨‍🔧 Добавить пользователя ✅', callback_data='add_user')
        btnDelUser = types.InlineKeyboardButton('🙅 Удалить пользователя ❌️', callback_data='del_user')
        btnChangePrice = types.InlineKeyboardButton('💵 Изменить стоимость товара 💶', callback_data='change_price')
        btnChangePrDelivery = types.InlineKeyboardButton('🚛 Изменить процент за доставку товара 📦',
                                                         callback_data='change_pr_delivery')
        btnChangeActivate = types.InlineKeyboardButton('🗑 Снять товар с продажи 🗑', callback_data='change_activate')
        markup.add(btnChangeActivate)
        markup.add(btnAddCard)
        markup.add(btnDelCard)
        markup.add(btnSearchUser)
        markup.add(btnChangeUser)
        markup.add(btnAddUser)
        markup.add(btnDelUser)
        markup.add(btnChangePrice)
        markup.add(btnChangePrDelivery)
        msg = bot.send_message(call.message.chat.id, 'Что ты хочешь сделать?', reply_markup=markup)
        data['id_messages' + str(call.message.chat.id)].append(msg.message_id)
    elif call.data == 'all_time':
        data['statistics' + str(call.message.chat.id)] = 1
        statisticsAll(call.message)
    elif call.data == 'cur_time':
        data['statistics' + str(call.message.chat.id)] = 2
        statisticsCur(call.message)
    elif call.data == 'all_month':
        data['statistics' + str(call.message.chat.id)] = 3
        statisticsAllMonth(call.message)
    elif call.data == 'cur_month':
        data['statistics' + str(call.message.chat.id)] = 4
        statisticsCurMonth(call.message)
    elif call.data == 'add_card':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton(cancelText))
        msg = bot.send_message(call.message.chat.id, 'Введи номер карты', reply_markup=markup)
        data['id_messages' + str(call.message.chat.id)].append(msg.message_id)
        bot.register_next_step_handler(call.message, setCard)
    elif call.data == 'search_user':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton(cancelText))
        msg = bot.send_message(call.message.chat.id,
                               'Перешли в этот чат сообщение пользователя, чей ID ты хочешь узнать.',
                               reply_markup=markup)
        data['id_messages' + str(call.message.chat.id)].append(msg.message_id)
        bot.register_next_step_handler(call.message, searchUser)
    elif call.data == 'del_card':
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()
        cur.execute("SELECT number_card FROM cards")
        dataEl = cur.fetchall()
        cur.close()
        conn.close()
        if len(dataEl) == 0:
            bot.send_message(call.message.chat.id, 'В базе отсутствуют номера карт.')
            clearMessage(call.message)
            return
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for el in dataEl:
            markup.add(types.KeyboardButton(el[0]))
        markup.add(types.KeyboardButton(cancelText))
        msg = bot.send_message(call.message.chat.id, 'Выбери какой номер карты удалить', reply_markup=markup)
        data['id_messages' + str(call.message.chat.id)].append(msg.message_id)
        bot.register_next_step_handler(call.message, delCard)
    elif call.data == 'change_user':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton(cancelText))
        msg = bot.send_message(call.message.chat.id, 'Введи id номер пользователя телеграм', reply_markup=markup)
        data['id_messages' + str(call.message.chat.id)].append(msg.message_id)
        bot.register_next_step_handler(call.message, changeUser)
    elif call.data == 'add_user':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton(cancelText))
        msg = bot.send_message(call.message.chat.id, 'Введи id номер пользователя телеграм', reply_markup=markup)
        data['id_messages' + str(call.message.chat.id)].append(msg.message_id)
        bot.register_next_step_handler(call.message, addUser)
    elif call.data == 'del_user':
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()
        cur.execute("SELECT id_telegram FROM users")
        dataEl = cur.fetchall()
        cur.close()
        conn.close()
        if len(dataEl) == 0:
            bot.send_message(call.message.chat.id, 'В базе отсутствуют пользователи.')
            clearMessage(call.message)
            return
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for el in dataEl:
            markup.add(types.KeyboardButton(el[0]))
        markup.add(types.KeyboardButton(cancelText))
        msg = bot.send_message(call.message.chat.id, 'Выбери какого пользователя удалить', reply_markup=markup)
        data['id_messages' + str(call.message.chat.id)].append(msg.message_id)
        bot.register_next_step_handler(call.message, delUser)
    elif call.data == 'change_price':
        # clearData(call.message)
        data['menu' + str(call.message.chat.id)] = 6
        choice_product(call.message)
    elif call.data == 'change_activate':
        # clearData(call.message)
        data['menu' + str(call.message.chat.id)] = 7
        choice_product(call.message)
    elif call.data == 'change_pr_delivery':
        # clearData(call.message)
        data['menu' + str(call.message.chat.id)] = 8
        choice_product(call.message)


def returnStart(message):
    clearMessage(message)
    start(message)


def cancelMessage(message, seek):
    markup = types.ReplyKeyboardRemove()
    msg = bot.send_message(message.chat.id, '.', reply_markup=markup)
    bot.delete_message(message.chat.id, msg.message_id)
    data['id_messages' + str(message.chat.id)].sort(reverse=True)
    for i in range(seek + 2):
        bot.delete_message(message.chat.id, data['id_messages' + str(message.chat.id)][i])
    for i in range(seek + 2):
        data['id_messages' + str(message.chat.id)].remove(data['id_messages' + str(message.chat.id)][0])


def clearMessage(message):
    markup = types.ReplyKeyboardRemove()
    msg = bot.send_message(message.chat.id, '.', reply_markup=markup)
    bot.delete_message(message.chat.id, msg.message_id)
    data['id_messages' + str(message.chat.id)].sort(reverse=True)
    for el in data['id_messages' + str(message.chat.id)]:
        bot.delete_message(message.chat.id, el)
    data['id_messages' + str(message.chat.id)].clear()


def searchUser(message):
    if message.text == '/start':
        returnStart(message)
        return
    data['id_messages' + str(message.chat.id)].append(message.message_id)
    if message.text == cancelText:
        cancelMessage(message, 0)
        return
    try:
        idNumber = message.forward_from.id
        clearMessage(message)
        bot.send_message(message.chat.id, 'ID номер пользователя:')
        bot.send_message(message.chat.id, idNumber)
    except:
        cancelMessage(message, 0)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton(cancelText))
        msg = bot.send_message(message.chat.id, 'Ты что-то не то ввел 😊, перешли сообщение пользователя!',
                               reply_markup=markup)
        data['id_messages' + str(message.chat.id)].append(msg.message_id)
        bot.register_next_step_handler(message, searchUser)


def setCard(message):
    if message.text == '/start':
        returnStart(message)
        return
    data['id_messages' + str(message.chat.id)].append(message.message_id)
    if message.text == cancelText:
        cancelMessage(message, 0)
        return
    if len(message.text) == 16:
        try:
            z = int(message.text)
            conn = sqlite3.connect(db_name)
            cur = conn.cursor()
            cur.execute("INSERT INTO cards(number_card) VALUES('%s')" % (message.text))
            conn.commit()
            cur.close()
            conn.close()
            clearMessage(message)
            bot.send_message(message.chat.id, f'Ты добавил новую карту.\n{message.text}')
        except:
            cancelMessage(message, 0)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add(types.KeyboardButton(cancelText))
            msg = bot.send_message(message.chat.id, 'Ты что-то не то ввел 😊, номер карты должен состоять из 16 цифр',
                                   reply_markup=markup)
            data['id_messages' + str(message.chat.id)].append(msg.message_id)
            bot.register_next_step_handler(message, setCard)
    else:
        cancelMessage(message, 0)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton(cancelText))
        msg = bot.send_message(message.chat.id, 'Номер карты должен состоять из 16 цифр', reply_markup=markup)
        data['id_messages' + str(message.chat.id)].append(msg.message_id)
        bot.register_next_step_handler(message, setCard)


def delCard(message):
    if message.text == '/start':
        returnStart(message)
        return
    data['id_messages' + str(message.chat.id)].append(message.message_id)
    if message.text == cancelText:
        cancelMessage(message, 0)
        return
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute("DELETE FROM cards WHERE number_card='%s'" % (message.text))
    conn.commit()
    cur.close()
    conn.close()
    clearMessage(message)
    bot.send_message(message.chat.id, f'Ты удалил карту.\n{message.text}')


def changeUser(message):
    if message.text == '/start':
        returnStart(message)
        return
    data['id_messages' + str(message.chat.id)].append(message.message_id)
    if message.text == cancelText:
        cancelMessage(message, 0)
        return
    try:
        z = int(message.text)
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()
        cur.execute("UPDATE stock_users SET id_telegram='%s'" % (message.text))
        conn.commit()
        cur.close()
        conn.close()
        clearMessage(message)
        bot.send_message(message.chat.id, f'Ты изменил id кладовщика.\n{message.text}')
    except:
        cancelMessage(message, 0)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton(cancelText))
        msg = bot.send_message(message.chat.id, 'Ты что-то не то ввел 😊, ID должен состоять из цифр',
                               reply_markup=markup)
        data['id_messages' + str(message.chat.id)].append(msg.message_id)
        bot.register_next_step_handler(message, changeUser)

def addUser(message):
    if message.text == '/start':
        returnStart(message)
        return
    data['id_messages' + str(message.chat.id)].append(message.message_id)
    if message.text == cancelText:
        cancelMessage(message, 0)
        return
    try:
        z = int(message.text)
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()
        cur.execute("INSERT INTO users(id_telegram) VALUES('%s')" % (message.text))
        conn.commit()
        cur.close()
        conn.close()
        clearMessage(message)
        bot.send_message(message.chat.id, f'Ты добавил пользователя с id номером.\n{message.text}')
    except:
        cancelMessage(message, 0)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton(cancelText))
        msg = bot.send_message(message.chat.id, 'Ты что-то не то ввел 😊, ID должен состоять из цифр',
                               reply_markup=markup)
        data['id_messages' + str(message.chat.id)].append(msg.message_id)
        bot.register_next_step_handler(message, addUser)


def delUser(message):
    if message.text == '/start':
        returnStart(message)
        return
    data['id_messages' + str(message.chat.id)].append(message.message_id)
    if message.text == cancelText:
        cancelMessage(message, 0)
        return
    if message.text == str(message.from_user.id):
        cancelMessage(message, 0)
        bot.send_message(message.chat.id, f'Нельзя удалять себя.')
        return
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id_telegram='%s'" % (message.text))
    conn.commit()
    cur.close()
    conn.close()
    clearMessage(message)
    bot.send_message(message.chat.id, f'Ты удалил пользователя с id номером.\n{message.text}')


def getCards(message):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute('SELECT number_card FROM cards')

    dataEl = cur.fetchall()
    cur.close()
    conn.close()
    if len(dataEl) == 0:
        bot.send_message(message.chat.id,
                         'В базе отсутствуют номера карт. Добавьте через Администрирование новую карту.')
    else:
        for el in dataEl:
            bot.send_message(message.chat.id, el[0])


def statisticsCur(message):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    date = datetime.fromtimestamp(message.date).strftime("%Y-%m-%d")
    cur.execute("SELECT SUM(cash) FROM process WHERE status=2 AND date(date_time)='%s'" % (date))
    dataEl = cur.fetchone()
    if dataEl[0] != None:
        cash = dataEl[0]
    else:
        cash = 0
    cur.execute("SELECT SUM(cash) FROM process WHERE status=3 AND date(date_time)='%s'" % (date))
    dataEl = cur.fetchone()
    if dataEl[0] != None:
        cash = round(cash - dataEl[0], 2)
    else:
        cash = round(cash, 2)

    cur.execute("SELECT SUM(price) FROM process WHERE status=2 AND date(date_time)='%s'" % (date))
    dataEl = cur.fetchone()
    if dataEl[0] != None:
        price = dataEl[0]
    else:
        price = 0

    cur.execute("SELECT SUM(price) FROM process WHERE status=3 AND date(date_time)='%s'" % (date))
    dataEl = cur.fetchone()
    if dataEl[0] != None:
        price = round(price - dataEl[0], 2)
    else:
        price = round(price, 2)
    cur.close()
    conn.close()
    clearMessage(message)
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, f'Общая чистая прибыль за сегодня - {cash}\nОбщий приход за сегодня - {price}',
                     reply_markup=markup)


def statisticsAll(message):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute("SELECT SUM(cash) FROM process WHERE status=2")
    dataEl = cur.fetchone()
    if dataEl[0] != None:
        cash = dataEl[0]
    else:
        cash = 0

    cur.execute("SELECT SUM(cash) FROM process WHERE status=3")
    dataEl = cur.fetchone()
    if dataEl[0] != None:
        cash = round(cash - dataEl[0], 2)
    else:
        cash = round(cash, 2)
    # +790000

    cur.execute("SELECT SUM(price) FROM process WHERE status=2")
    dataEl = cur.fetchone()
    if dataEl[0] != None:
        price = dataEl[0]
    else:
        price = 0

    cur.execute("SELECT SUM(price) FROM process WHERE status=3")
    dataEl = cur.fetchone()
    if dataEl[0] != None:
        price = round(price - dataEl[0], 2)
    else:
        price = round(price, 2)

    cur.execute("SELECT SUM(count*cost_price) FROM store")
    dataEl = cur.fetchone()
    if dataEl[0] != None:
        costPrice = round(dataEl[0], 2)
    else:
        costPrice = 0

    cur.execute("SELECT SUM(store.count*product.price) FROM store INNER JOIN product on product.id=store.id_product")
    dataEl = cur.fetchone()
    if dataEl[0] != None:
        priceProduct = round(dataEl[0], 2)
    else:
        priceProduct = 0

    cur.close()
    conn.close()
    clearMessage(message)
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id,
                     f'Общая чистая прибыль - {cash}\nОбщий приход - {price}\nВ товар вложено - {costPrice}\nВ товаре при продаже - {priceProduct}',
                     reply_markup=markup)


def statisticsAllMonth(message):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute(
        "select sum(cash* (CASE WHEN status = 2 THEN 1 ELSE -1 END)),strftime('%Y-%m', date_time) from process GROUP by strftime('%Y-%m', date_time)")

    dataEl = cur.fetchall()
    cur.close()
    conn.close()
    textOut = ""
    if len(dataEl) == 0:
        bot.send_message(message.chat.id,
                         'У Вас еще не было продаж...')
    else:
        for el in dataEl:
            textOut = f'Чистая прибыль {round(el[0], 2)} рублей за {el[1]}\n' + textOut

    clearMessage(message)
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, textOut, reply_markup=markup)


def statisticsCurMonth(message):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute(
        "select product_group.name, sum(CASE WHEN status = 2 THEN 1 ELSE -1 END),sum(cash* (CASE WHEN status = 2 THEN 1 ELSE -1 END)) from process INNER JOIN product on process.id_product=product.id AND strftime('%m-%Y', process.date_time)=strftime('%m-%Y', DATE()) INNER JOIN product_group on product_group.id=product.id_product_group GROUP by product.id_product_group")

    dataEl = cur.fetchall()
    cur.close()
    conn.close()
    textOut = ""
    allCash = 0
    if len(dataEl) == 0:
        bot.send_message(message.chat.id,
                         'У Вас еще не было продаж...')
    else:
        for el in dataEl:
            textOut = textOut + f'В категории {el[0]} продано {el[1]} шт. доход {round(el[2], 2)} рублей\n'
            allCash = allCash + el[2]
        textOut = textOut + f'Общий доход за месяц {round(allCash, 2)} рублей.'

    clearMessage(message)
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, textOut, reply_markup=markup)


def setDelivery(message):
    global data
    data['id_messages' + str(message.chat.id)].append(message.message_id)
    if message.text == '/start':
        returnStart(message)
        return
    if message.text == cancelText:
        cancelMessage(message, 0)
        start(message)
        return
    if message.text == pikupText:
        data['type_sale' + str(message.chat.id)] = 1
        choice_product(message)
    elif message.text == deliveryText:
        data['type_sale' + str(message.chat.id)] = 2
        if data['menu' + str(message.chat.id)] == 3:
            choice_product(message)
        else:
            choice_delivery(message)
    else:
        bot.delete_message(message.chat.id, message.message_id)
        data['id_messages' + str(message.chat.id)].remove(message.message_id)
        bot.register_next_step_handler(message, setDelivery)
        return


def choice_delivery(message):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute('SELECT name FROM tc_delivery')
    dataEl = cur.fetchall()
    cur.close()
    conn.close()
    if len(dataEl) == 0:
        markup = types.ReplyKeyboardRemove()
        clearMessage(message)
        bot.send_message(message.chat.id, 'В базе отсутствуют транспортные компании.', reply_markup=markup)
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for el in dataEl:
        markup.add(types.KeyboardButton(el[0]))
    markup.add(types.KeyboardButton(cancelText))
    msg = bot.send_message(message.chat.id, 'Выбери транспортную компанию', reply_markup=markup)
    data['id_messages' + str(message.chat.id)].append(msg.message_id)
    bot.register_next_step_handler(message, setDeliveryGetNumber)


def setDeliveryGetNumber(message):
    global data
    data['id_messages' + str(message.chat.id)].append(message.message_id)
    if message.text == '/start':
        returnStart(message)
        return
    if message.text == cancelText:
        clearMessage(message)
        start(message)
        return

    if message.text != specialText:
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()
        cur.execute("SELECT type FROM tc_delivery WHERE name='%s'" % (message.text))

        dataEl = cur.fetchall()
        cur.close()
        conn.close()
        if len(dataEl) == 0:
            bot.delete_message(message.chat.id, message.message_id)
            data['id_messages' + str(message.chat.id)].remove(message.message_id)
            bot.register_next_step_handler(message, setDeliveryGetNumber)
            return
        data['delivery_name' + str(message.chat.id)] = message.text
        for el in dataEl:
            data['delivery_type' + str(message.chat.id)] = el[0]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton(cancelText))
        msg = bot.send_message(message.chat.id, 'Введи код отправления', reply_markup=markup)
        data['id_messages' + str(message.chat.id)].append(msg.message_id)
        bot.register_next_step_handler(message, setNumberGetGroup)
    else:
        bot.delete_message(message.chat.id, message.message_id)
        data['id_messages' + str(message.chat.id)].remove(message.message_id)
        bot.register_next_step_handler(message, setDeliveryGetNumber)


def generate_barcode(message, text1, text2, text3):
    imageName = data['delivery_cod' + str(message.chat.id)] + '.png'
    image = code128.image(data['delivery_cod' + str(message.chat.id)], height=100)

    w, h = image.size
    new_w = w  # the same
    margin = 20
    new_h = h + (3 * margin)
    new_image = Image.new('RGB', (new_w, new_h), (255, 255, 255))
    new_image.paste(image, (0, margin))
    font = ImageFont.truetype("arial.ttf", 18)
    drawer = ImageDraw.Draw(new_image)
    drawer.text((5, 0), text1, font=font, fill='black')
    drawer.text((5, 120), text2, font=font, fill='black')
    drawer.text((5, 140), text3, font=font, fill='black')

    new_image.save(imageName)


def generate_qr_code(message, text1, text2, text3):
    imageName = data['delivery_cod' + str(message.chat.id)] + '.png'
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=20,
        border=4,
    )

    qr.add_data(data['delivery_cod' + str(message.chat.id)])
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")

    font = ImageFont.truetype("arial.ttf", 40)
    drawer = ImageDraw.Draw(image)
    drawer.text((10, 10), text1, font=font, fill='black')

    drawer.text((15, 500), text2, font=font, fill='black')
    drawer.text((15, 535), text3, font=font, fill='black')
    image.save(imageName)


def createBarcodeA(message, text1, text2, text3):
    delivery_cod = data['delivery_cod' + str(message.chat.id)]
    imageName = delivery_cod + '.png'
    pdfName = delivery_cod + '.pdf'
    if data['delivery_type' + str(message.chat.id)] == 'QR_CODE':
        generate_qr_code(message, text1, text2, text3)
    else:
        generate_barcode(message, text1, text2, text3)

    c = Canvas(pdfName)
    c.drawImage(imageName, 0, 440, width=600, height=400)
    c.save()
    document = open(pdfName, 'rb')
    bot.send_document(message.chat.id, document)
    document.close()
    document = open(pdfName, 'rb')

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute("SELECT id_telegram FROM stock_users")
    dataEl = cur.fetchall()
    cur.close()
    conn.close()
    if len(dataEl) == 0:
        bot.send_message(message.chat.id, 'В базе отсутствуют id кладовщика.')
        clearMessage(message)
        return
    bot.send_document(dataEl[0], document)
    document.close()
    os.remove(imageName)
    os.remove(pdfName)


def setNumberGetGroup(message):
    global data
    data['id_messages' + str(message.chat.id)].append(message.message_id)
    if message.text == '/start':
        returnStart(message)
        return
    if message.text == cancelText:
        clearMessage(message)
        start(message)
        return

    if message.text != specialText:
        data['delivery_cod' + str(message.chat.id)] = message.text
        choice_product(message)
    else:
        bot.delete_message(message.chat.id, message.message_id)
        data['id_messages' + str(message.chat.id)].remove(message.message_id)
        bot.register_next_step_handler(message, setDeliveryGetNumber)


def choice_product(message):
    # выводит список групп товаров ПЕРЧАТКИ СУМКИ И Т.Д.
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    if data['menu' + str(message.chat.id)] == 2:
        cur.execute(
            'SELECT DISTINCT product_group.name FROM product_group INNER JOIN product on product.activate=1 AND product.id_product_group=product_group.id INNER JOIN store on product.id=store.id_product WHERE store.count<>0 order by product_group.id')
    else:
        cur.execute(
            'SELECT DISTINCT product_group.name FROM product_group INNER JOIN product on product.activate=1 AND product.id_product_group=product_group.id order by product_group.id')
    dataEl = cur.fetchall()
    cur.close()
    conn.close()
    if len(dataEl) == 0:
        markup = types.ReplyKeyboardRemove()
        clearMessage(message)
        bot.send_message(message.chat.id, 'В базе отсутствуют товары.', reply_markup=markup)
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for el in dataEl:
        markup.add(types.KeyboardButton(el[0]))
    markup.add(types.KeyboardButton(cancelText))
    msg = bot.send_message(message.chat.id, typeProductText, reply_markup=markup)
    data['id_messages' + str(message.chat.id)].append(msg.message_id)
    bot.register_next_step_handler(message, setGroupGetName)


def setGroupGetName(message):
    global data
    data['id_messages' + str(message.chat.id)].append(message.message_id)
    if message.text == '/start':
        returnStart(message)
        return
    if message.text == cancelText:
        """if data['menu' + str(message.chat.id)] == 1 or data['menu' + str(message.chat.id)] == 6 or data['menu' + str(message.chat.id)] == 7:
            cancelMessage(message,0)
        else:
            cancelMessage(message, 2)"""
        clearMessage(message)
        start(message)
        return

    if message.text != specialText:
        data['group' + str(message.chat.id)] = message.text
    else:
        data['id_messages' + str(message.chat.id)].remove(message.message_id)

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    if data['menu' + str(message.chat.id)] == 2:
        cur.execute(
            "SELECT DISTINCT product.name FROM product_group INNER JOIN product on product.activate=1 AND product.id_product_group=product_group.id INNER JOIN store on product.id=store.id_product WHERE store.count<>0 AND product_group.name='%s'" % (
            data['group' + str(message.chat.id)]))
    else:
        cur.execute(
            "SELECT DISTINCT product.name FROM product_group INNER JOIN product on product.activate=1 AND product.id_product_group=product_group.id WHERE product_group.name='%s'" % (
            data['group' + str(message.chat.id)]))
    dataEl = cur.fetchall()
    cur.close()
    conn.close()
    if len(dataEl) == 0:
        bot.delete_message(message.chat.id, message.message_id)
        data['id_messages' + str(message.chat.id)].remove(message.message_id)
        bot.register_next_step_handler(message, setGroupGetName)
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for el in dataEl:
        markup.add(types.KeyboardButton(el[0]))
    markup.add(types.KeyboardButton(cancelText))
    msg = bot.send_message(message.chat.id, typeModelText, reply_markup=markup)
    data['id_messages' + str(message.chat.id)].append(msg.message_id)
    bot.register_next_step_handler(message, setNameGetModel)


def setNameGetModel(message):
    global data
    data['id_messages' + str(message.chat.id)].append(message.message_id)
    if message.text == '/start':
        returnStart(message)
        return
    if message.text == cancelText:
        cancelMessage(message, 2)
        choice_product(message)
        return

    if message.text != specialText:
        data['name' + str(message.chat.id)] = message.text
    else:
        data['id_messages' + str(message.chat.id)].remove(message.message_id)

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    if data['menu' + str(message.chat.id)] == 2:
        cur.execute(
            "SELECT DISTINCT product.model FROM product_group INNER JOIN product on product.activate=1 AND product.id_product_group=product_group.id INNER JOIN store on product.id=store.id_product WHERE store.count<>0 AND product_group.name='%s' AND product.name='%s' ORDER BY product.model" % (
                data['group' + str(message.chat.id)], data['name' + str(message.chat.id)]))
    else:
        cur.execute(
            "SELECT DISTINCT product.model FROM product_group INNER JOIN product on product.activate=1 AND product.id_product_group=product_group.id WHERE product_group.name='%s' AND product.name='%s' ORDER BY product.model" % (
                data['group' + str(message.chat.id)], data['name' + str(message.chat.id)]))

    dataEl = cur.fetchall()
    cur.close()
    conn.close()
    if len(dataEl) == 0:
        bot.delete_message(message.chat.id, message.message_id)
        data['id_messages' + str(message.chat.id)].remove(message.message_id)
        bot.register_next_step_handler(message, setNameGetModel)
        return
    if data['menu' + str(message.chat.id)] == 1:
        getAvailability(message)
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for el in dataEl:
        markup.add(types.KeyboardButton(el[0]))
    markup.add(types.KeyboardButton(cancelText))
    msg = bot.send_message(message.chat.id, typeModelSettingText, reply_markup=markup)
    data['id_messages' + str(message.chat.id)].append(msg.message_id)
    bot.register_next_step_handler(message, setModelGetSize)


def setModelGetSize(message):
    global data
    data['id_messages' + str(message.chat.id)].append(message.message_id)
    if message.text == '/start':
        returnStart(message)
        return
    if message.text == cancelText:
        cancelMessage(message, 2)
        message.text = specialText
        setGroupGetName(message)
        return
    if message.text != specialText:
        data['model' + str(message.chat.id)] = message.text
    else:
        data['id_messages' + str(message.chat.id)].remove(message.message_id)

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    if data['menu' + str(message.chat.id)] == 2:
        cur.execute(
            "SELECT DISTINCT product.size FROM product_group INNER JOIN product on product.activate=1 AND product.id_product_group=product_group.id INNER JOIN store on product.id=store.id_product WHERE store.count<>0 AND product_group.name='%s' AND product.name='%s' AND product.model='%s' ORDER BY product.id" % (
            data['group' + str(message.chat.id)], data['name' + str(message.chat.id)],
            data['model' + str(message.chat.id)]))
    else:
        cur.execute(
            "SELECT DISTINCT product.size FROM product_group INNER JOIN product on product.activate=1 AND product.id_product_group=product_group.id WHERE product_group.name='%s' AND product.name='%s' AND product.model='%s' ORDER BY product.model" % (
                data['group' + str(message.chat.id)], data['name' + str(message.chat.id)],
                data['model' + str(message.chat.id)]))
    dataEl = cur.fetchall()
    cur.close()
    conn.close()
    if len(dataEl) == 0:
        bot.delete_message(message.chat.id, message.message_id)
        data['id_messages' + str(message.chat.id)].remove(message.message_id)
        bot.register_next_step_handler(message, setModelGetSize)
        return
    if data['menu' + str(message.chat.id)] == 6:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton(cancelText))
        msg = bot.send_message(message.chat.id, 'Напиши новую стоимость товара', reply_markup=markup)
        data['id_messages' + str(message.chat.id)].append(msg.message_id)
        bot.register_next_step_handler(message, changePrice)
        return
    if data['menu' + str(message.chat.id)] == 8:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton(cancelText))
        msg = bot.send_message(message.chat.id, 'Напиши новый процент за доставку товара', reply_markup=markup)
        data['id_messages' + str(message.chat.id)].append(msg.message_id)
        bot.register_next_step_handler(message, changePrDelivery)
        return
    if dataEl[0][0] == "-":  # нет размера у товара
        # data['id_messages' + str(message.chat.id)].remove(message.message_id)
        message.text = "-"
        setSizeGetPrice(message)
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for el in dataEl:
        markup.add(types.KeyboardButton(el[0]))
    markup.add(types.KeyboardButton(cancelText))
    msg = bot.send_message(message.chat.id, 'Выбери размер', reply_markup=markup)
    data['id_messages' + str(message.chat.id)].append(msg.message_id)
    bot.register_next_step_handler(message, setSizeGetPrice)


def setSizeGetPrice(message):
    global data
    data['id_messages' + str(message.chat.id)].append(message.message_id)
    if message.text == '/start':
        returnStart(message)
        return
    if message.text == cancelText:
        cancelMessage(message, 2)
        message.text = specialText
        setNameGetModel(message)
        return

    if message.text != specialText and message.text != '-':
        data['size' + str(message.chat.id)] = message.text
    else:
        data['id_messages' + str(message.chat.id)].remove(message.message_id)

    if data['menu' + str(message.chat.id)] == 7:
        changeActivate(message)
        return
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute(
        "SELECT product.price FROM product_group INNER JOIN product on product.activate=1 AND product.id_product_group=product_group.id WHERE product_group.name='%s' AND product.name='%s' AND product.model='%s' AND product.size='%s'" % (
            data['group' + str(message.chat.id)], data['name' + str(message.chat.id)],
            data['model' + str(message.chat.id)], data['size' + str(message.chat.id)]))
    dataEl = cur.fetchall()
    cur.close()
    conn.close()
    if len(dataEl) == 0:
        bot.delete_message(message.chat.id, message.message_id)
        data['id_messages' + str(message.chat.id)].remove(message.message_id)
        bot.register_next_step_handler(message, setSizeGetPrice)
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for el in dataEl:
        markup.add(types.KeyboardButton(el[0]))
    markup.add(types.KeyboardButton(cancelText))
    msg = bot.send_message(message.chat.id, 'Выбери стоимость продажи или введи другую', reply_markup=markup)
    data['id_messages' + str(message.chat.id)].append(msg.message_id)
    bot.register_next_step_handler(message, setPrice)


def setPrice(message):
    global data
    data['id_messages' + str(message.chat.id)].append(message.message_id)
    if message.text == '/start':
        returnStart(message)
        return
    if message.text == cancelText:
        if data['size' + str(message.chat.id)] == '-':
            cancelMessage(message, 2)
            message.text = specialText
            setNameGetModel(message)
        else:
            cancelMessage(message, 2)
            message.text = specialText
            setModelGetSize(message)
        return
    price = message.text
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute(
        "SELECT product.id, product.percent FROM product_group INNER JOIN product on product.activate=1 AND product.id_product_group=product_group.id WHERE product_group.name='%s' AND product.name='%s' AND product.model='%s' AND product.size='%s'" % (
            data['group' + str(message.chat.id)], data['name' + str(message.chat.id)],
            data['model' + str(message.chat.id)], data['size' + str(message.chat.id)]))
    dataEl = cur.fetchone()
    cur.close()
    conn.close()
    if data['menu' + str(message.chat.id)] == 3:
        setRefund(message, dataEl[0], price, dataEl[1])
    else:
        setSale(message, dataEl[0], price, dataEl[1])


def changeActivate(message):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute(
        "UPDATE product SET activate ='0' WHERE id in (SELECT product.id FROM product_group INNER JOIN product on product.id_product_group=product_group.id WHERE product_group.name='%s' AND product.name='%s' AND product.model='%s'  AND product.size='%s')" % (
            data['group' + str(message.chat.id)], data['name' + str(message.chat.id)],
            data['model' + str(message.chat.id)], data['size' + str(message.chat.id)]))

    conn.commit()
    cur.close()
    conn.close()
    clearMessage(message)
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id,
                     f"💥Ты удалил товар: 💥\n{data['group' + str(message.chat.id)]}\n{data['name' + str(message.chat.id)]}\n{data['model' + str(message.chat.id)]}\n{data['size' + str(message.chat.id)]}",
                     reply_markup=markup)


def changePrice(message):
    global data
    data['id_messages' + str(message.chat.id)].append(message.message_id)
    if message.text == '/start':
        returnStart(message)
        return
    if message.text == cancelText:
        cancelMessage(message, 2)
        message.text = specialText
        setNameGetModel(message)
        return
    price = 0
    if is_number(message.text):
        price = message.text
    else:
        bot.delete_message(message.chat.id, message.message_id)
        data['id_messages' + str(message.chat.id)].remove(message.message_id)
        bot.register_next_step_handler(message, changePrice)
        return

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute(
        "UPDATE product SET price='%s' WHERE id in (SELECT product.id FROM product_group INNER JOIN product on product.id_product_group=product_group.id WHERE product_group.name='%s' AND product.name='%s' AND product.model='%s')" % (
            price, data['group' + str(message.chat.id)], data['name' + str(message.chat.id)],
            data['model' + str(message.chat.id)]))

    conn.commit()
    cur.close()
    conn.close()
    clearMessage(message)
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id,
                     f"💥Ты изменил стоимость 💥\n{data['group' + str(message.chat.id)]}\n{data['name' + str(message.chat.id)]}\n{data['model' + str(message.chat.id)]}\nНовая цена: <b>{price}</b>",
                     reply_markup=markup, parse_mode="HTML")


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def changePrDelivery(message):
    global data
    data['id_messages' + str(message.chat.id)].append(message.message_id)
    if message.text == '/start':
        returnStart(message)
        return
    prDelivery = 0
    if is_number(message.text):
        prDelivery = message.text
    else:
        bot.delete_message(message.chat.id, message.message_id)
        data['id_messages' + str(message.chat.id)].remove(message.message_id)
        bot.register_next_step_handler(message, changePrDelivery)
        return
    if message.text == cancelText:
        cancelMessage(message, 2)
        message.text = specialText
        setNameGetModel(message)
        return

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute(
        "UPDATE product SET percent='%s' WHERE id in (SELECT product.id FROM product_group INNER JOIN product on product.id_product_group=product_group.id WHERE product_group.name='%s' AND product.name='%s' AND product.model='%s')" % (
            prDelivery, data['group' + str(message.chat.id)], data['name' + str(message.chat.id)],
            data['model' + str(message.chat.id)]))

    conn.commit()
    cur.close()
    conn.close()
    clearMessage(message)
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id,
                     f"💥Ты изменил процент за доставку  💥\n{data['group' + str(message.chat.id)]}\n{data['name' + str(message.chat.id)]}\n{data['model' + str(message.chat.id)]}\nНовый процент: <b>{prDelivery}</b>",
                     reply_markup=markup, parse_mode="HTML")


def setRefund(message, id, price, percent):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, count, cost_price FROM store WHERE id_product='%s' order by date(date_time) DESC" % (id))
    dataEl = cur.fetchone()
    count = dataEl[1] + 1
    cur.execute("UPDATE store SET count='%s' WHERE id='%s'" % (count, dataEl[0]))
    status = data['menu' + str(message.chat.id)]
    priceDelivery = 0
    if data['type_sale' + str(message.chat.id)] == 2:
        priceDelivery = float(price) * (float(percent)) / 100
        price = float(price) * (100 - float(percent)) / 100

    cash = float(price) - float(dataEl[2])
    cash = round(cash, 2)
    date = datetime.fromtimestamp(message.date).strftime("%Y-%m-%d %H:%M:%S")
    cur.execute(
        "INSERT INTO process(id_product,status,price,date_time,cash,delivery) VALUES('%s','%s','%s','%s','%s','%s')" % (
        id, status, price, date, cash, priceDelivery))
    conn.commit()
    cur.close()
    conn.close()
    markup = types.ReplyKeyboardRemove()
    clearMessage(message)
    typeSale = 'доставкой'
    if data['type_sale' + str(message.chat.id)] == 1:
        typeSale = 'самовывозом'
    bot.send_message(message.chat.id,
                     f"🤧 Не грусти 🥺\nТебе вернули {typeSale}\n {data['group' + str(message.chat.id)]} {data['name' + str(message.chat.id)]} {data['model' + str(message.chat.id)]} {data['size' + str(message.chat.id)]}\nминус из дохода <b>{cash}</b>",
                     reply_markup=markup, parse_mode="HTML")


def setSale(message, id, price, percent):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, count, cost_price FROM store WHERE id_product='%s' AND count<>0 order by date(date_time)" % (id))
    dataEl = cur.fetchone()
    count = dataEl[1] - 1
    cur.execute("UPDATE store SET count='%s' WHERE id='%s'" % (count, dataEl[0]))
    status = data['menu' + str(message.chat.id)]
    priceDelivery = 0
    if data['type_sale' + str(message.chat.id)] == 2:
        priceDelivery = float(price) * (float(percent)) / 100
        price = float(price) * (100 - float(percent)) / 100
    cash = float(price) - float(dataEl[2])
    cash = round(cash, 2)
    date = datetime.fromtimestamp(message.date).strftime("%Y-%m-%d %H:%M:%S")
    cur.execute(
        "INSERT INTO process(id_product,status,price,date_time,cash,delivery) VALUES('%s','%s','%s','%s','%s','%s')" % (
        id, status, price, date, cash, priceDelivery))
    conn.commit()
    cur.close()
    conn.close()
    markup = types.ReplyKeyboardRemove()
    clearMessage(message)
    typeSale = 'самовывозом'

    if data['type_sale' + str(message.chat.id)] == 2:
        typeSale = 'доставкой ' + data['delivery_name' + str(message.chat.id)]
        # createqr(message, f"{data['delivery_name' + str(message.chat.id)]} {data['delivery_cod' + str(message.chat.id)]} {data['group' + str(message.chat.id)]}\n{data['name' + str(message.chat.id)]} {data['model' + str(message.chat.id)]} {data['size' + str(message.chat.id)]}")
        createBarcodeA(message,
                       f"{data['delivery_name' + str(message.chat.id)]} {data['delivery_cod' + str(message.chat.id)]}",
                       f"{data['group' + str(message.chat.id)]} {data['name' + str(message.chat.id)]}",
                       f"{data['model' + str(message.chat.id)]} {data['size' + str(message.chat.id)]}")
    bot.send_message(message.chat.id,
                     f"💥Поздравляю с продажей🥳\nТы продал(а) {typeSale}\n {data['group' + str(message.chat.id)]} {data['name' + str(message.chat.id)]} {data['model' + str(message.chat.id)]} {data['size' + str(message.chat.id)]}\nСтоимость доставки {priceDelivery}({percent}%)\nЧистая прибыль <b>{cash}</b>",
                     reply_markup=markup, parse_mode="HTML")


def getAvailability(message):
    nameProduct = data['name' + str(message.chat.id)]
    group = data['group' + str(message.chat.id)]
    text = ""
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute(
        "SELECT product.id FROM product_group INNER JOIN product on product.activate=1 AND product.id_product_group=product_group.id WHERE product_group.name='%s' AND product.name='%s' ORDER BY product.model" % (
        group, nameProduct))
    dataEl = cur.fetchall()
    for el in dataEl:
        cur.execute("SELECT name, model, size FROM product WHERE id='%s'" % (el[0]))
        dataEl_ = cur.fetchone()
        text = text + dataEl_[0] + " <i>" + dataEl_[1] + "</i> <b>" + dataEl_[2] + "</b> "
        cur.execute("SELECT SUM(count) FROM store WHERE id_product='%s'" % (el[0]))
        dataEl__ = cur.fetchone()
        text = text + "<b>" + str(dataEl__[0]) + "</b> шт.\n"
    cur.close()
    conn.close()
    markup = types.ReplyKeyboardRemove()
    clearMessage(message)
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")


bot.infinity_polling(timeout=10, long_polling_timeout=5)
