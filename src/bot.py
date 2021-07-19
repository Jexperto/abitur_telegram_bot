import hashlib
import io
import telebot
from threading import Timer

from applicants_data import ApplicantsData
from network import get_file

token = open("../token.txt", "r").read()

interval = 3600
download_timer = 60
commands = [['help', 'start'], ['get'], ['subscribe', 'sub'], ['unsubscribe', 'unsub'], ["amount"],
            ['point_summary', 'psum', 'opossum'], ['amount_applicants_higher_than', 'higher']]
subscribers = {}
bot = telebot.TeleBot(token=token)
should_notify = True
last_file_hash = None
file_handle = None
raw_file = None
can_download = True


def reset_download():
    global can_download
    can_download = True


def download_file():
    global can_download
    global file_handle
    global raw_file
    if can_download:
        raw_file = get_file()
        can_download = False
        file_handle = open('../../abitur_bot/table.xls', 'wb').write(raw_file)
        t = Timer(interval=download_timer, function=reset_download)
        t.start()


def send_update():
    global last_file_hash

    download_file()
    md5 = hashlib.md5(raw_file).hexdigest()
    updated = False if md5 == last_file_hash else True

    if raw_file is None:
        for key in subscribers:
            bot.send_message(key, "Something went wrong with getting the file")
    else:

        if updated:
            print("current md5: ", md5, "last md5:", last_file_hash)
            last_file_hash = md5
            for key in subscribers:
                doc = io.BytesIO(raw_file)
                doc.name = "table.xls"
                bot.send_document(key, doc)
                subscribers[key] = True
        else:
            for key in subscribers:
                if subscribers[key]:
                    bot.send_message(key, "Пока ничего не менялось")
                else:
                    doc = io.BytesIO(raw_file)
                    doc.name = "table.xls"
                    bot.send_document(key, doc)
                    subscribers[key] = True

    t = Timer(interval=interval, function=send_update)
    t.start()


@bot.message_handler(commands=['help', 'start'])
def get_commands(message):
    res = 'Here is the list of all commands\n'
    for command in commands:
        for subcommand in command:
            res += '/' + subcommand + ',\t'
    bot.send_message(message.chat.id, res)


@bot.message_handler(commands=['get'])
def send_table(message):
    global raw_file
    global can_download

    download_file()
    if raw_file is None:
        bot.send_message(message.chat.id, "Что-то пошло не так... Файла нет. \U0001F633")
    else:
        if message.chat.id in subscribers:
            subscribers[message.chat.id] = True
            if subscribers[message.chat.id]:
                bot.send_message(message.chat.id, "Ничего не поменялось, но забирай \U0001F605")
        doc = io.BytesIO(raw_file)
        doc.name = "table.xls"
        bot.send_document(message.chat.id, doc)


@bot.message_handler(commands=['subscribe', 'sub'])
def sub(message):
    subscribers[message.chat.id] = False
    bot.send_message(message.chat.id, "Буду писать \U0001F609")
    print('subscribers: ', subscribers)


@bot.message_handler(commands=['unsubscribe', 'unsub'])
def unsub(message):
    subscribers.pop(message.chat.id)
    bot.send_message(message.chat.id, 'Ты меня бросаешь? \U0001F62D')
    print('subscribers: ', subscribers)


def parse_command(command):
    return command.split()[1:]


def give_help(message, available_args):
    rs = "Доступные аргументы:\n"
    for index in range(len(available_args)):
        rs += str(index + 1) + ")\t" + str(available_args[index]) + "\n"
    bot.send_message(message.chat.id, rs)
    return


@bot.message_handler(commands=['amount'])
def amount(message):
    args = parse_command(message.text)
    available_args = [['c', 'с', 'согл', 'consent', 'согласие']]
    if len(args) > 0 and args[0] == 'help':
        give_help(message, available_args)
        return
    if not file_handle:
        download_file()
    a = ApplicantsData("table.xls", "09.04.01 Информатика и вычислительная техника")
    rs = a.amount(any(x in available_args[0] for x in args))
    bot.send_message(message.chat.id, rs)


@bot.message_handler(commands=['point_summary', 'psum', 'opossum'])
def point_summary(message):
    args = parse_command(message.text)
    available_args = [['c', 'с', 'согл', 'consent', 'согласие'],
                      [["г=", "группировка=", "группа=", "g=", "group=", "b=", "bins="]],
                      ['sort', 'сорт', 'сортировка'],
                      ['asc', 'ascending', 'возрастание', 'возр']
                      ]
    if len(args) > 0 and args[0] == 'help':
        give_help(message, available_args)
        return
    if not file_handle:
        download_file()
    a = ApplicantsData("table.xls", "09.04.01 Информатика и вычислительная техника")
    bins = 10
    bins_commands = ["г", "группировка", "группа", "g", "group", "b", "bins"]
    for ar in args:
        for b in bins_commands:
            if ar.startswith(b + "="):
                bins = int(ar[len(b) + 1:])

    rs = a.point_summary(any(x in available_args[0] for x in args), bins,
                         any(x in available_args[2] for x in args),
                         any(x in available_args[3] for x in args))
    bot.send_message(message.chat.id, str(rs))


@bot.message_handler(commands=['amount_applicants_higher_than', 'higher'])
def amount_applicants_higher_than(message):
    args = parse_command(message.text)
    available_args = [["з=", "ч=", "число=", "значение=", "v=", "value="],
                      ['c', 'с', 'согл', 'consent', 'согласие']
                      ]
    if len(args) > 0 and args[0] == 'help':
        give_help(message, available_args)
        return

    if not file_handle:
        download_file()
    a = ApplicantsData("table.xls", "09.04.01 Информатика и вычислительная техника")
    value = 1
    value_commands = ["з", "ч", "число", "значение", "v", "value"]
    for ar in args:
        for b in value_commands:
            if ar.startswith(b + "="):
                value = int(ar[len(b) + 1:])
    rs = a.amount_applicants_higher_than(value, any(x in available_args[1] for x in args))
    bot.send_message(message.chat.id, str(rs))


@bot.message_handler(commands=['test'])
def test(message):
    bot.send_message(message.chat.id, b"\xf0\x9f\x8d\x95")
    print(message)


timer = Timer(interval=interval, function=send_update)
timer.start()
bot.polling()