import json
import config
import requests
from cryptography.fernet import Fernet

key = Fernet.generate_key()
cipher = Fernet(key)

HEADERS = {
    'content-type': 'application/json; charset=utf-8'
}


def encrypt(content):
    return cipher.encrypt(content.encode()).decode()


def decrypt(content):
    return cipher.decrypt(content.encode()).decode()


def update_username(chat_id, new_username):
    payload = {
        'username': encrypt(new_username),
    }
    requests.post(
        '{}/chat/update_username/{}'.format(config.BOT_TOKEN, chat_id),
        data=json.dumps(payload),
        headers=HEADERS
    )


def update_password(chat_id, new_password):
    payload = {
        'main_password': encrypt(new_password),
    }
    requests.post(
        '{}/chat/update_password/{}'.format(config.BOT_TOKEN, chat_id),
        data=json.dumps(payload),
        headers=HEADERS
    )


def process_chat(chat):
    encrypted_fields = {
        'username': False,
        'main_password': False,
        'grades': True
    }
    for field, require_loads in encrypted_fields.items():
        if field in chat:
            chat[field] = decrypt(chat[field])
            if require_loads:
                chat[field] = json.loads(chat[field])
    return chat


def get_chat_info(chat_id):
    chat_info = requests.get(
        '{}/chat/{}'.format(config.BOT_TOKEN, chat_id)
    )
    chat_info = json.loads(chat_info.text)
    return process_chat(chat_info)


def update_grades_for_chat(chat_id, new_grades):
    payload = {
        'new_grades': encrypt(json.dumps(new_grades))
    }
    requests.put(
        '{}/chat/update_grades/{}'.format(config.BOT_TOKEN, chat_id),
        data=json.dumps(payload),
        headers=HEADERS
    )
