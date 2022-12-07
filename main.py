import json
import requests
import datetime
from apscheduler.schedulers.background import BlockingScheduler
from revChatGPT.revChatGPT import Chatbot
import sys
import keyboard
import os



CONFIG = {}
BOT = None
GPT: Chatbot = None


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


def import_config():
    global CONFIG
    with open('resources/config.json') as config_file:
        CONFIG = json.load(config_file)


def write_last_checked_msg_id(last_checked_msg_id):
    with open('resources/config.json', 'w', encoding='utf-8') as config_file:
        CONFIG['LAST_CHECKED_MSG_ID'] = last_checked_msg_id
        json.dump(CONFIG, config_file, ensure_ascii=False, indent=4)


def pprint(printable_str):
    print(json.dumps(printable_str, indent=2))


def get_bot_by_bot_name(name):
    global BOT
    url = CONFIG['API_URL'] + "bots?token=" + CONFIG['TOKEN']
    resp_j = requests.get(url).json()
    for bot in resp_j['response']:
        if bot['name'] == name:
            BOT = bot


def get_group_members(group_id):
    group_id = BOT['group_id']
    url = CONFIG['API_URL'] + "groups/" + group_id + "?token=" + CONFIG['TOKEN']
    members = requests.get(url).json()['response']['members']
    member_id_list = list()
    for member in members:
        mem = {
            'user_id': member['user_id'],
            'length': len(member['nickname']),
            'nick': member['nickname']
        }
        member_id_list.append(mem)
    return member_id_list



def get_latest_message():
    url = CONFIG['API_URL'] + "groups/" + BOT['group_id'] + "/messages?token=" + CONFIG['TOKEN']
    newMessage = False
    latest_messages = requests.get(url).json()['response']['messages']
    if latest_messages[0]['id'] != CONFIG['LAST_CHECKED_MSG_ID']:
        newMessage = True
        write_last_checked_msg_id(latest_messages[0]['id'])
    return newMessage, latest_messages[0]


def write_message(message, data=None):
    url = CONFIG['API_URL'] + "/bots/post?token=" + CONFIG['TOKEN']
    params = dict()
    datas = {
        'bot_id': BOT['bot_id'],
        'text': message
    }
    if data is not None:
        datas['attachments']: data['attachments']
    params = json.dumps(datas).encode('utf8')
    resp_js = requests.post(url, data=params, headers={'content-type': 'application/json'})



def check_messages():
    new_message, message = get_latest_message()
    if new_message and message['text'] is not None:
        print("[" + str(datetime.datetime.fromtimestamp(message['created_at'])) + "] [" + message['name'] + "]: " + message['text'])
        if str.startswith(message['text'], '@testicles'):
            write_message(message['text'].split('@testicles', 1)[1])
        if str.startswith(message['text'], '@chatGPT'):
            print("Getting chat response for string \"" + message['text'].split('@chatGPT', 1)[1] + "\"")
            try:
                msg = GPT.get_chat_response(message['text'].split('@chatGPT', 1)[1])['message']
                write_message(msg)
            except Exception as exc:
                write_message("ChatGPT hit an error. Please try again shortly.")
        if str.startswith(message['text'], '@Pam'):
            print("Pam!")
            write_message("Hello, I'm Pam. How may I help you today?")
        if str.startswith(message['text'], '@housepic2'):
            member_id_list = get_group_members('')
            message_to_send = {
                "attachments": [{'loci': [], 'type': 'mentions', 'user_ids': []}]
            }
            index = 0
            for member_id in member_id_list:
                message_to_send['attachments'][0]['loci'].append([index, member_id['length']])
                message_to_send['attachments'][0]['user_ids'].append(member_id['user_id'])
                index += member_id['length']+2
            write_message(message['text'].split('@housepic2', 1)[1], message_to_send)
        if str.startswith(message['text'], '@sidebet'):
            print("Lets do something for this sidebet.")


def setup_gpt():
    global GPT
    cfg = {
        "email": CONFIG['GPT_EMAIL'],
        "password": CONFIG['GPT_PASSWORD']
    }
    write_message("ChatGPT is running.")
    try:
        GPT = Chatbot(cfg, conversation_id=None)
    except Exception as exc:
        write_message("ChatGPT failed to login. It is not currently running.")


def check_quit():
    isStopped = False
    # This is here to simulate application activity (which keeps the main thread alive).
    if keyboard.is_pressed('Esc'):
        print("Esc pressed")
        if not isStopped:
            write_message("Chat GPT has been shutdown.")
            isStopped = True
            scheduler.shutdown()
            print('Exiting on Esc...')
            sys.exit(0)

if __name__ == '__main__':
    import_config()
    get_bot_by_bot_name(CONFIG['GROUPME_BOT_NAME'])
    setup_gpt()
    # get_group_members('f')
    check_messages()
    scheduler = BlockingScheduler()
    scheduler.add_job(check_messages, 'interval', seconds=2)

    # HOLD THE ESCAPE KEY TO EXIT THIS BOT GRACEFULLY
    scheduler.add_job(check_quit, 'interval', seconds=2)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)


    # See PyCharm help at https://www.jetbrains.com/help/pycharm/



