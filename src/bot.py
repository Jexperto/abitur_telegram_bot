import hashlib
import io
import os
import shelve
import sys
import telebot
from threading import Timer
from applicants_data import ApplicantsData
from network import get_file

wd = os.path.dirname(sys.modules['__main__'].__file__) + "/"
with open(wd + "../resources/secret.txt", "a+"):
    pass
with open(wd + "../resources/token.txt", "a+"):
    pass
table_path = wd + '../resources/table.xls'
token = open(wd + "../resources/token.txt", "r").read().replace("\n", "").replace("\r", "")
subs_file = shelve.open(wd + "../resources/subscribers")
admins_file = shelve.open(wd + "../resources/admins")
subscribers = list(subs_file.keys())

args = []
for i, arg in enumerate(sys.argv):
    if i > 0:
        args.append(int(arg))
interval = args[0] if len(args) > 0 else 3600
download_timer = args[1] if len(args) > 1 else 60

commands = [['help', 'start'], ['get'], ['subscribe', 'sub'], ['unsubscribe', 'unsub'], ["amount"],
            ['point_summary', 'psum', 'opossum'], ['amount_applicants_higher_than', 'higher']]
bot = telebot.TeleBot(token=token)
should_notify = True
last_file_hash = None
file_handle = None
raw_file = None
can_download = True


def add_subscriber(sub_id):
    global subscribers
    global subs_file
    if str(sub_id) in subscribers:
        return -1
    subs_file[str(sub_id)] = {"int": -1, "current_int": 0, "notified": False}  # interval
    subscribers.append(str(sub_id))
    return 0


def remove_subscriber(sub_id):
    global subscribers
    global subs_file
    if str(sub_id) in subs_file:
        del subs_file[str(sub_id)]
        subscribers.remove(str(sub_id))
        return True
    return False


def reset_download():
    global can_download
    can_download = True


def download_file():
    global can_download
    global file_handle
    if can_download:
        file = get_file()
        can_download = False
        file_handle = open(table_path, 'wb').write(file)
        t = Timer(interval=download_timer, function=reset_download)
        t.start()
        return file
    return False


def set_nested_object(top_level_obj, top_level_key, nested_key, value):
    nested = top_level_obj[top_level_key]
    nested[nested_key] = value
    top_level_obj[top_level_key] = nested


def start_timed_downloads():
    global last_file_hash
    global raw_file
    file = download_file()
    if not file:
        return
    if file is None:
        for key in admins_file.keys():
            bot.send_message(key, "Something went wrong with getting the file")
    md5 = hashlib.md5(file).hexdigest()
    raw_file = file
    file_updated = False if md5 == last_file_hash else True
    if file_updated:
        for key in subscribers:
            set_nested_object(subs_file, key, "notified", False)
    last_file_hash = md5
    d_timer = Timer(interval=download_timer, function=start_timed_downloads)
    d_timer.start()


def notify_user(user_id, doc):
    print(subs_file[user_id]["notified"])
    if not subs_file[user_id]["notified"]:
        set_nested_object(subs_file, user_id, "notified", True)
        bot.send_message(user_id, "Полундра, файл проапдейтился")
        bot.send_document(user_id, doc)
        set_nested_object(subs_file, user_id, "current_int", 0)
        return
    current_int = int(subs_file[user_id]["current_int"])
    user_total_interval = int(subs_file[user_id]["int"])
    if user_total_interval < 0:
        return
    if current_int + interval > user_total_interval:
        set_nested_object(subs_file, user_id, "current_int", 0)
        bot.send_message(user_id, "Пока ничего не менялось")
    else:
        set_nested_object(subs_file, user_id, "current_int", current_int + interval)


def send_updates():
    doc = io.BytesIO(raw_file)
    doc.name = "table.xls"
    for key in subscribers:
        notify_user(key, doc)
    t = Timer(interval=interval, function=send_updates)
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
    file = download_file()
    user_id = str(message.chat.id)
    if file is None:
        bot.send_message(message.chat.id, "Что-то пошло не так... Файла нет. \U0001F633")
    else:
        if file:
            raw_file = file
        if user_id in subscribers:
            if subs_file[user_id]["notified"]:
                bot.send_message(message.chat.id, "Ничего не поменялось, но забирай \U0001F605")
            else:
                bot.send_message(message.chat.id, "Лови")
        doc = io.BytesIO(raw_file)
        doc.name = "table.xls"
        bot.send_document(message.chat.id, doc)


@bot.message_handler(commands=['subscribe', 'sub'])
def sub(message):
    code = add_subscriber(message.chat.id)
    if code == -1:
        bot.send_message(message.chat.id, "Ты дебил, ты и так подписался на меня \U0001F633")
    else:
        bot.send_message(message.chat.id, "Буду писать \U0001F609")


@bot.message_handler(commands=['unsubscribe', 'unsub'])
def unsub(message):
    if remove_subscriber(message.chat.id):
        bot.send_message(message.chat.id, 'Ты меня бросаешь? \U0001F62D')
    else:
        bot.send_message(message.chat.id, 'Ты и так на меня не подписн')


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
    a = ApplicantsData(table_path, "09.04.01 Информатика и вычислительная техника")
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
    a = ApplicantsData(table_path, "09.04.01 Информатика и вычислительная техника")
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
    a = ApplicantsData(table_path, "09.04.01 Информатика и вычислительная техника")
    value = 1
    value_commands = ["з", "ч", "число", "значение", "v", "value"]
    for ar in args:
        for b in value_commands:
            if ar.startswith(b + "="):
                value = int(ar[len(b) + 1:])
    rs = a.amount_applicants_higher_than(value, any(x in available_args[1] for x in args))
    bot.send_message(message.chat.id, str(rs))


@bot.message_handler(commands=['interval'])
def set_personal_interval(message):
    args = parse_command(message.text)
    user_id = str(message.chat.id)
    if len(args) > 0:
        try:
            i = int(args[0])
            if i <= 0:
                set_nested_object(subs_file, user_id, "int", -1)
                bot.send_message(message.chat.id, "Окей, не буду беспокоить")
                return
            set_nested_object(subs_file, user_id, "int", i * 60)
            last_digit = int(repr(i)[-1])
            number = str(i)
            if i == 1:
                bot.send_message(message.chat.id,
                                 "Буду писать тебе каждую минуту")
            else:
                bot.send_message(message.chat.id,
                                 "Буду писать тебе " + ("каждую " + number + " минуту" if last_digit == 1 else (
                                     "каждые " + number + " минуты" if (
                                             1 < last_digit < 4) else "каждые " + number + " минут")))
        except ValueError:
            bot.send_message(message.chat.id, "Число, Карл, мне нужно число...")


@bot.message_handler(commands=['debug'])
def add_admin(message):
    global admins_file
    user_id = str(message.chat.id)
    args = parse_command(message.text)
    if len(args) > 0:
        if str(args[0]).lower() == "true" or str(args[0]).lower() == "1":
            admins_file[user_id] = True
            bot.send_message(message.chat.id, "Debug enabled")

        elif str(args[0]).lower() == "false" or str(args[0]).lower() == "0":
            if str(message.chat.id) in admins_file:
                del admins_file[user_id]
            bot.send_message(message.chat.id, "Debug disabled")


@bot.message_handler(commands=['test'])
def test(message):
    bot.send_message(message.chat.id, b"\xf0\x9f\x8d\x95")


@bot.message_handler(commands=['stop'])
def stop(message):
    args = parse_command(message.text)
    secret = open(wd + '../resources/secret.txt', "r").readline().replace("\n", "")
    print(secret)
    if len(args) > 0 and args[0] == secret:
        bot.stop_polling()
        bot.send_message(message.chat.id, "Pausing polling...")
    else:
        bot.send_message(message.chat.id, "Ага, бегу и падаю \U0001F64A")


file = download_file()
if file:
    raw_file = file
else:
    with open(wd + "../resources/table.xls", "r+") as f:
        raw_file = f.read()

timer = Timer(interval=download_timer, function=start_timed_downloads)
user_interval_timer = Timer(interval=interval, function=send_updates)
user_interval_timer.start()
timer.start()
bot.polling()
