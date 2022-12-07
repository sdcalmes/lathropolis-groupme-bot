import json
import requests
import datetime
from apscheduler.schedulers.background import BlockingScheduler
from revChatGPT.revChatGPT import Chatbot



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


def get_latest_message():
    url = CONFIG['API_URL'] + "groups/" + BOT['group_id'] + "/messages?token=" + CONFIG['TOKEN']
    newMessage = False
    latest_messages = requests.get(url).json()['response']['messages']
    if latest_messages[0]['id'] != CONFIG['LAST_CHECKED_MSG_ID']:
        newMessage = True
        write_last_checked_msg_id(latest_messages[0]['id'])
    return newMessage, latest_messages[0]


def write_message(message):
    url = CONFIG['API_URL'] + "/bots/post"
    params = dict()
    params["token"] = CONFIG['TOKEN']
    params["bot_id"] = BOT['bot_id']
    params["text"] = message
    resp_js = requests.post(url, params=params)


def check_messages():
    new_message, message = get_latest_message()
    if new_message and message['text'] is not None:
        print("[" + str(datetime.datetime.fromtimestamp(message['created_at'])) + "] [" + message['name'] + "]: " + message['text'])
        if str.startswith(message['text'], '@testicles'):
            write_message(message['text'].split('@testicles', 1)[1])
        if str.startswith(message['text'], '@chatGPT'):
            msg = GPT.get_chat_response(message['text'].split('@chatGPT', 1)[1])['message']
            write_message(msg)


def setup_gpt():
    global GPT
    cfg = {
        "email": CONFIG['GPT_EMAIL'],
        "password": CONFIG['GPT_PASSWORD']
    }
    GPT = Chatbot(cfg, conversation_id=None)

if __name__ == '__main__':
    import_config()
    setup_gpt()
    get_bot_by_bot_name(CONFIG['GROUPME_BOT_NAME'])
    scheduler = BlockingScheduler()
    scheduler.add_job(check_messages, 'interval', seconds=1)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass


# See PyCharm help at https://www.jetbrains.com/help/pycharm/



