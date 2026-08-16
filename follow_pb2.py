import os
import re
import json
import time
import requests
import threading
from flask import Flask
import telebot
from google.protobuf.json_format import MessageToDict
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import follow_pb2

# ==================== WEB SERVER (Render Fix) ====================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# सर्वर को बैकग्राउंड में चालू करें
threading.Thread(target=run_flask, daemon=True).start()

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8976574521:AAHjW9VvjWg2qtY6Tf-hRkW0LxWlsgO6qxI"
bot = telebot.TeleBot(BOT_TOKEN)

KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

JWT_API = "https://ff-jwt-gen-api.lovable.app/api/public/token"
FOLLOW_URL = "https://client.ind.freefiremobile.com/Follow"
UNFOLLOW_URL = "https://client.ind.freefiremobile.com/Unfollow"

# Colors
C_RESET = "\033[0m"
C_WHITE = "\033[97m"
SG_GREEN = "\033[92m"
SG_CYAN = "\033[96m"
SG_RED = "\033[91m"
SG_YELLOW = "\033[93m"
SG_NEON = "\033[92m"
SG_GOLD = "\033[38;2;255;215;0m"
SG_PURPLE = "\033[38;2;147;112;219m"

# ==================== HELPER FUNCTIONS ====================
def encrypt_payload(data: bytes) -> bytes:
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    return cipher.encrypt(pad(data, AES.block_size))

def extract_account_data(obj):
    if not isinstance(obj, dict):
        return None
    uid, password, jwt_token = None, None, None
    for key in ['uid', 'UID', 'userId', 'user_id', 'userid', 'id', 'account_id']:
        if key in obj and obj[key]:
            uid = str(obj[key])
            break
    for key in ['password', 'pass', 'pwd', 'Password', 'PASSWORD']:
        if key in obj and obj[key]:
            password = str(obj[key])
            break
    for key in ['jwt_token', 'jwt', 'token', 'JWT', 'access_token', 'accessToken']:
        if key in obj and obj[key]:
            jwt_token = str(obj[key])
            break
    if uid:
        acc = {'uid': uid}
        if password: acc['password'] = password
        if jwt_token: acc['jwt_token'] = jwt_token
        return acc
    return None

def extract_accounts_regex(content):
    accounts = []
    pattern = r'["\']?uid["\']?\s*:\s*["\']?(\d+)["\']?.*?["\']?password["\']?\s*:\s*["\']([^"\']+)["\']'
    matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
    for uid, pwd in matches:
        accounts.append({'uid': uid, 'password': pwd})
    return accounts

def get_jwt_token(uid, password):
    url = f"{JWT_API}?uid={uid}&password={password}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "live" and data.get("token"):
                return data.get("token")
            elif data.get("token"):
                return data.get("token")
            elif data.get("jwt"):
                return data.get("jwt")
            elif data.get("data") and isinstance(data.get("data"), dict):
                return data["data"].get("token")
        return None
    except Exception as e:
        print(f"JWT Error: {e}")
        return None

def send_follow(target_id, jwt):
    try:
        req = follow_pb2.CSFollowReq()
        req.target_id = int(target_id)
        encrypted_data = encrypt_payload(req.SerializeToString())

        headers = {
            "User-Agent": "UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
            "Accept": "*/*",
            "Accept-Encoding": "deflate, gzip",
            "Authorization": f"Bearer {jwt}",
            "X-Ga": "v1 1",
            "Releaseversion": "OB54",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Unity-Version": "2022.3.47f1",
        }
        response = requests.post(FOLLOW_URL, headers=headers, data=encrypted_data, timeout=20)
        return response.status_code == 200
    except Exception as e:
        print(f"Follow Error: {e}")
        return False

def send_unfollow(target_id, jwt):
    try:
        try:
            req = follow_pb2.CSFollowReq()
            req.target_id = int(target_id)
            encrypted_data = encrypt_payload(req.SerializeToString())
        except:
            req = follow_pb2.CSUnfollowReq()
            req.target_id = int(target_id)
            encrypted_data = encrypt_payload(req.SerializeToString())

        headers = {
            "User-Agent": "UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
            "Accept": "*/*",
            "Accept-Encoding": "deflate, gzip",
            "Authorization": f"Bearer {jwt}",
            "X-Ga": "v1 1",
            "Releaseversion": "OB54",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Unity-Version": "2022.3.47f1",
        }
        response = requests.post(UNFOLLOW_URL, headers=headers, data=encrypted_data, timeout=20)
        return response.status_code == 200
    except Exception as e:
        print(f"Unfollow Error: {e}")
        return False

# ==================== TELEGRAM BOT COMMANDS ====================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🔥 **SGCODEX FREE FIRE BOT ONLINE** 🔥\n\nCommands:\n/follow `<Target_UID>` `<JWT_Token>`\n/unfollow `<Target_UID>` `<JWT_Token>`")

@bot.message_handler(commands=['follow'])
def handle_follow(message):
    try:
        args = message.text.split()
        if len(args) < 3:
            bot.reply_to(message, "❌ **Usage:** `/follow <Target_UID> <JWT_Token>`", parse_mode="Markdown")
            return
        
        target_uid, jwt = args[1], args[2]
        bot.reply_to(message, f"⏳ Sending Follow request to `{target_uid}`...")
        
        if send_follow(target_uid, jwt):
            bot.send_message(message.chat.id, f"✅ Successfully followed `{target_uid}`!")
        else:
            bot.send_message(message.chat.id, f"❌ Follow failed for `{target_uid}`.")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {e}")

@bot.message_handler(commands=['unfollow'])
def handle_unfollow(message):
    try:
        args = message.text.split()
        if len(args) < 3:
            bot.reply_to(message, "❌ **Usage:** `/unfollow <Target_UID> <JWT_Token>`", parse_mode="Markdown")
            return
        
        target_uid, jwt = args[1], args[2]
        bot.reply_to(message, f"⏳ Sending Unfollow request to `{target_uid}`...")
        
        if send_unfollow(target_uid, jwt):
            bot.send_message(message.chat.id, f"✅ Successfully unfollowed `{target_uid}`!")
        else:
            bot.send_message(message.chat.id, f"❌ Unfollow failed for `{target_uid}`.")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {e}")

# ==================== MAIN EXECUTION ====================
if __name__ == "__main__":
    print(f"{SG_GREEN}SGCODEX Bot Service Started Successfully!{C_RESET}")
    bot.infinity_polling(none_stop=True)
    
