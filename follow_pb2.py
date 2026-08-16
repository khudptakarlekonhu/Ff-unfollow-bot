import json
import requests
import os
import re
import telebot
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from google.protobuf.json_format import MessageToDict
from datetime import datetime

import follow_pb2


# ================= CONFIGURATION =================
# BotFather से मिला अपना Telegram Bot Token यहाँ डालें
BOT_TOKEN = "8976574521:AAEGsZ7CiUm1SdVrqsVfc7RHVP-18rM6CAY"
bot = telebot.TeleBot(BOT_TOKEN)

# ================= SGCODEX THEME COLORS =================
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_BLUE = "\033[94m"
C_MAGENTA = "\033[95m"
C_CYAN = "\033[96m"
C_WHITE = "\033[97m"
C_BLACK = "\033[30m"
C_BOLD = "\033[1m"
C_DIM = "\033[2m"
C_ITALIC = "\033[3m"
C_UNDERLINE = "\033[4m"
C_BLINK = "\033[5m"
C_REVERSE = "\033[7m"
C_HIDDEN = "\033[8m"
BG_BLACK = "\033[40m"
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"
BG_WHITE = "\033[47m"
C_RESET = "\033[0m"

# SGCODEX Theme Colors
SG_GOLD = "\033[38;2;255;215;0m"
SG_PURPLE = "\033[38;2;147;112;219m"
SG_BLUE = "\033[38;2;0;191;255m"
SG_PINK = "\033[38;2;255;20;147m"
SG_GREEN = "\033[38;2;0;255;127m"
SG_ORANGE = "\033[38;2;255;165;0m"
SG_RED = "\033[38;2;255;69;0m"
SG_CYAN = "\033[38;2;0;255;255m"
SG_VIOLET = "\033[38;2;138;43;226m"
SG_NEON = "\033[38;2;57;255;20m"
SG_YELLOW = "\033[38;2;255;255;0m"

# ================= CONFIG =================
KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

JWT_API = "https://ff-jwt-gen-api.lovable.app/api/public/token"
FOLLOW_URL = "https://client.ind.freefiremobile.com/Follow"
UNFOLLOW_URL = "https://client.ind.freefiremobile.com/Unfollow"  # Added unfollow endpoint

# Statistics
stats = {
    "total": 0,
    "success": 0,
    "failed": 0,
    "jwt_failed": 0,
    "used_existing_tokens": 0,
    "expired_tokens": 0
}

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    banner = f"""
{C_RESET}{SG_NEON}╔══════════════════════════════════════════════════════════════════════╗{C_RESET}
{C_RESET}{SG_NEON}║{C_RESET}{SG_GOLD}          ███████╗ ██████╗ ██████╗  ██████╗ ██████╗ ███████╗██╗  ██╗{C_RESET}{SG_NEON}║{C_RESET}
{C_RESET}{SG_NEON}║{C_RESET}{SG_GOLD}          ██╔════╝██╔════╝██╔═══██╗██╔════╝██╔═══██╗██╔════╝╚██╗██╔╝{C_RESET}{SG_NEON}║{C_RESET}
{C_RESET}{SG_NEON}║{C_RESET}{SG_GOLD}          ███████╗██║     ██║   ██║██║     ██║   ██║█████╗   ╚███╔╝ {C_RESET}{SG_NEON}║{C_RESET}
{C_RESET}{SG_NEON}║{C_RESET}{SG_GOLD}          ╚════██║██║     ██║   ██║██║     ██║   ██║██╔══╝   ██╔██╗ {C_RESET}{SG_NEON}║{C_RESET}
{C_RESET}{SG_NEON}║{C_RESET}{SG_GOLD}          ███████║╚██████╗╚██████╔╝╚██████╗╚██████╔╝███████╗██╔╝ ██╗{C_RESET}{SG_NEON}║{C_RESET}
{C_RESET}{SG_NEON}║{C_RESET}{SG_GOLD}          ╚══════╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝{C_RESET}{SG_NEON}║{C_RESET}
{C_RESET}{SG_NEON}╠══════════════════════════════════════════════════════════════════════╣{C_RESET}
{C_RESET}{SG_NEON}║{C_RESET}{SG_PINK}          🔥 FREE FIRE FOLLOW/UNFOLLOW BOT - SGCODEX EDITION 🔥   {C_RESET}{SG_NEON}║{C_RESET}
{C_RESET}{SG_NEON}║{C_RESET}{SG_VIOLET}                    👑 CREATED BY SR 👑                       {C_RESET}{SG_NEON}║{C_RESET}
{C_RESET}{SG_NEON}╚══════════════════════════════════════════════════════════════════════╝{C_RESET}
    """
    print(banner)

def print_progress_bar(current, total, status=""):
    width = 60
    progress = current / total
    filled = int(width * progress)
    
    bar = ""
    for i in range(width):
        if i < filled:
            bar += f"{SG_NEON}█{C_RESET}"
        else:
            bar += f"{C_DIM}░{C_RESET}"
    
    percentage = int(progress * 100)
    print(f"\r{C_RESET}{SG_CYAN}[{bar}] {C_RESET}{C_BOLD}{percentage}%{C_RESET} {C_DIM}({current}/{total}){C_RESET} {status}", end="")

def encrypt_payload(data: bytes) -> bytes:
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    return cipher.encrypt(pad(data, AES.block_size))

def load_accounts(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = re.sub(r',\s*}', '}', content)
    content = re.sub(r',\s*]', ']', content)
    
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return extract_accounts_regex(content)
    
    accounts = []
    if isinstance(data, list):
        for item in data:
            acc = extract_account_data(item)
            if acc:
                accounts.append(acc)
    elif isinstance(data, dict):
        for key in ['accounts', 'users', 'data', 'list']:
            if key in data and isinstance(data[key], list):
                for item in data[key]:
                    acc = extract_account_data(item)
                    if acc:
                        accounts.append(acc)
                if accounts:
                    return accounts
        acc = extract_account_data(data)
        if acc:
            accounts.append(acc)
    
    if not accounts:
        accounts = extract_accounts_regex(content)
    
    return accounts

def extract_account_data(obj):
    if not isinstance(obj, dict):
        return None
    
    uid = None
    password = None
    jwt_token = None
    
    uid_keys = ['uid', 'UID', 'userId', 'user_id', 'userid', 'id', 'account_id']
    for key in uid_keys:
        if key in obj and obj[key]:
            uid = str(obj[key])
            break
    
    pwd_keys = ['password', 'pass', 'pwd', 'Password', 'PASSWORD']
    for key in pwd_keys:
        if key in obj and obj[key]:
            password = str(obj[key])
            break
    
    token_keys = ['jwt_token', 'jwt', 'token', 'JWT', 'access_token', 'accessToken']
    for key in token_keys:
        if key in obj and obj[key]:
            jwt_token = str(obj[key])
            break
    
    if uid:
        account = {'uid': uid}
        if password:
            account['password'] = password
        if jwt_token:
            account['jwt_token'] = jwt_token
        return account
    
    return None

def extract_accounts_regex(content):
    accounts = []
    pattern = r'["\']?uid["\']?\s*:\s*["\']?(\d+)["\']?.*?["\']?password["\']?\s*:\s*["\']([^"\']+)["\']'
    matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
    for uid, pwd in matches:
        accounts.append({'uid': uid, 'password': pwd})
    return accounts

def get_jwt_token(uid, password):
    """Get JWT from API"""
    url = f"{JWT_API}?uid={uid}&password={password}"
    
    try:
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("status") == "live" and data.get("token"):
                token = data.get("token")
                account_id = data.get("account_id", "N/A")
                region = data.get("region", "N/A")
                print(f"    {SG_GREEN}✓ Account ID: {C_WHITE}{account_id}{C_RESET} | {SG_CYAN}Region: {C_WHITE}{region}{C_RESET}")
                return token
            elif data.get("token"):
                return data.get("token")
            elif data.get("jwt"):
                return data.get("jwt")
            elif data.get("data") and isinstance(data.get("data"), dict):
                if data["data"].get("token"):
                    return data["data"]["token"]
            else:
                print(f"    {SG_RED}✗ Invalid response format{C_RESET}")
                return None
        else:
            print(f"    {SG_RED}✗ API error: {response.status_code}{C_RESET}")
            return None
            
    except Exception as e:
        print(f"    {SG_RED}✗ Exception: {e}{C_RESET}")
        return None

def send_follow(target_id, jwt):
    """Send follow request to Free Fire"""
    req = follow_pb2.CSFollowReq()
    req.target_id = target_id
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

    if response.status_code == 200:
        print(f"    {SG_GREEN}✓ Status: {C_WHITE}{response.status_code}{C_RESET} {SG_NEON}✅{C_RESET}")
        try:
            res = follow_pb2.CSFollowRes()
            res.ParseFromString(response.content)
            res_dict = MessageToDict(res, preserving_proto_field_name=True)
            follower_count = res_dict.get('creator_stats', {}).get('follower_count', 'N/A')
            print(f"    {SG_CYAN}📊 Follower Count: {C_WHITE}{follower_count}{C_RESET}")
        except Exception as e:
            print(f"    {SG_YELLOW}⚠ Response received but could not decode: {e}{C_RESET}")
        return True
    elif response.status_code == 401:
        print(f"    {SG_RED}✗ Status: {response.status_code} - Token Expired or Invalid ❌{C_RESET}")
        try:
            print(f"    {SG_YELLOW}Server Response: {response.text[:200]}{C_RESET}")
        except:
            pass
        return False
    else:
        print(f"    {SG_RED}✗ Status: {response.status_code} ❌{C_RESET}")
        try:
            print(f"    {SG_YELLOW}Server Response: {response.text[:200]}{C_RESET}")
        except Exception:
            print(f"    {SG_YELLOW}Raw Bytes: {response.content[:200]}{C_RESET}")
        return False

def send_unfollow(target_id, jwt):
    """Send unfollow request to Free Fire"""
    # Note: Unfollow might use a different protobuf message type
    # If CSUnfollowReq exists, use it; otherwise try CSFollowReq with different action
    try:
        # Try using CSFollowReq (some APIs use same request with different endpoint)
        req = follow_pb2.CSFollowReq()
        req.target_id = target_id
        encrypted_data = encrypt_payload(req.SerializeToString())
    except:
        # If CSUnfollowReq exists, use it instead
        try:
            req = follow_pb2.CSUnfollowReq()
            req.target_id = target_id
            encrypted_data = encrypt_payload(req.SerializeToString())
        except:
            print(f"    {SG_RED}✗ Unfollow protobuf not available{C_RESET}")
            return False

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

    if response.status_code == 200:
        print(f"    {SG_GREEN}✓ Status: {C_WHITE}{response.status_code}{C_RESET} {SG_NEON}✅{C_RESET}")
        try:
            res = follow_pb2.CSFollowRes()
            res.ParseFromString(response.content)
            res_dict = MessageToDict(res, preserving_proto_field_name=True)
            print(f"    {SG_CYAN}📊 Response: {C_WHITE}{json.dumps(res_dict, indent=4)}{C_RESET}")
        except Exception as e:
            print(f"    {SG_YELLOW}⚠ Response received but could not decode: {e}{C_RESET}")
        return True
    elif response.status_code == 401:
        print(f"    {SG_RED}✗ Status: {response.status_code} - Token Expired or Invalid ❌{C_RESET}")
        try:
            print(f"    {SG_YELLOW}Server Response: {response.text[:200]}{C_RESET}")
        except:
            pass
        return False
    else:
        print(f"    {SG_RED}✗ Status: {response.status_code} ❌{C_RESET}")
        try:
            print(f"    {SG_YELLOW}Server Response: {response.text[:200]}{C_RESET}")
        except Exception:
            print(f"    {SG_YELLOW}Raw Bytes: {response.content[:200]}{C_RESET}")
        return False

def print_stats():
    total = stats["total"]
    success = stats["success"]
    failed = stats["failed"]
    jwt_failed = stats["jwt_failed"]
    existing = stats["used_existing_tokens"]
    expired = stats["expired_tokens"]
    
    print(f"""
{C_RESET}{SG_NEON}╔══════════════════════════════════════════════════════════════════════╗{C_RESET}
{C_RESET}{SG_NEON}║{C_RESET}{SG_GOLD}                        📊 STATISTICS                            {C_RESET}{SG_NEON}║{C_RESET}
{C_RESET}{SG_NEON}╠══════════════════════════════════════════════════════════════════════╣{C_RESET}
{C_RESET}{SG_NEON}║{C_RESET}{SG_GREEN}  ✅ Successful: {C_WHITE}{success:^7}{C_RESET}                               {C_RESET}{SG_NEON}║{C_RESET}
{C_RESET}{SG_NEON}║{C_RESET}{SG_RED}  ❌ Failed:     {C_WHITE}{failed:^7}{C_RESET}                               {C_RESET}{SG_NEON}║{C_RESET}
{C_RESET}{SG_NEON}║{C_RESET}{SG_ORANGE}  ⚠️  JWT Failed:  {C_WHITE}{jwt_failed:^7}{C_RESET}                               {C_RESET}{SG_NEON}║{C_RESET}
{C_RESET}{SG_NEON}║{C_RESET}{SG_CYAN}  📊 Total:      {C_WHITE}{total:^7}{C_RESET}                               {C_RESET}{SG_NEON}║{C_RESET}
{C_RESET}{SG_NEON}║{C_RESET}{SG_PURPLE}  🔑 Existing:   {C_WHITE}{existing:^7}{C_RESET}                               {C_RESET}{SG_NEON}║{C_RESET}
{C_RESET}{SG_NEON}║{C_RESET}{SG_YELLOW}  ⏰ Renewed:    {C_WHITE}{expired:^7}{C_RESET}                               {C_RESET}{SG_NEON}║{C_RESET}
{C_RESET}{SG_NEON}╚══════════════════════════════════════════════════════════════════════╝{C_RESET}
    """)

def main():
    clear_screen()
    print_banner()
    print()
    
    # Get action (Follow or Unfollow)
    print(f"{C_RESET}{SG_PURPLE}╔══════════════════════════════════════════════════════════════════════╗{C_RESET}")
    print(f"{C_RESET}{SG_PURPLE}║{C_RESET}{SG_GOLD}                    🎯 ACTION SELECT                        {C_RESET}{SG_PURPLE}║{C_RESET}")
    print(f"{C_RESET}{SG_PURPLE}╚══════════════════════════════════════════════════════════════════════╝{C_RESET}")
    print()
    
    print(f"  {SG_CYAN}[1]{C_RESET} {C_WHITE}Follow{C_RESET}")
    print(f"  {SG_CYAN}[2]{C_RESET} {C_WHITE}Unfollow{C_RESET}")
    print()
    
    while True:
        try:
            action_choice = int(input(f"  {SG_CYAN}[?]{C_RESET} {C_WHITE}Choose action (1 or 2): {C_RESET}"))
            if action_choice in [1, 2]:
                break
            print(f"  {SG_RED}[!]{C_RESET} {C_WHITE}Please enter 1 or 2.{C_RESET}")
        except:
            print(f"  {SG_RED}[!]{C_RESET} {C_WHITE}Please enter a valid number.{C_RESET}")
    
    action_name = "Follow" if action_choice == 1 else "Unfollow"
    action_func = send_follow if action_choice == 1 else send_unfollow
    
    print()
    
    # Get target ID
    print(f"{C_RESET}{SG_PURPLE}╔══════════════════════════════════════════════════════════════════════╗{C_RESET}")
    print(f"{C_RESET}{SG_PURPLE}║{C_RESET}{SG_GOLD}                    🎯 TARGET SETUP                         {C_RESET}{SG_PURPLE}║{C_RESET}")
    print(f"{C_RESET}{SG_PURPLE}╚══════════════════════════════════════════════════════════════════════╝{C_RESET}")
    print()
    
    while True:
        try:
            TARGET_ID = int(input(f"  {SG_CYAN}[?]{C_RESET} {C_WHITE}Enter Target UID to {action_name}: {C_RESET}"))
            break
        except:
            print(f"  {SG_RED}[!]{C_RESET} {C_WHITE}Please enter a valid UID (numbers only).{C_RESET}")
    
    print()
    
    # Get accounts file
    print(f"{C_RESET}{SG_PURPLE}╔══════════════════════════════════════════════════════════════════════╗{C_RESET}")
    print(f"{C_RESET}{SG_PURPLE}║{C_RESET}{SG_GOLD}                    📁 ACCOUNTS SETUP                      {C_RESET}{SG_PURPLE}║{C_RESET}")
    print(f"{C_RESET}{SG_PURPLE}╚══════════════════════════════════════════════════════════════════════╝{C_RESET}")
    print()
    
    while True:
        filepath = input(f"  {SG_CYAN}[?]{C_RESET} {C_WHITE}Enter path of UID file: {C_RESET}").strip()
        filepath = filepath.replace('"', '').replace("'", "")
        if os.path.exists(filepath):
            break
        print(f"  {SG_RED}[!]{C_RESET} {C_WHITE}File not found.{C_RESET}")
    
    # Load accounts
    try:
        accounts = load_accounts(filepath)
        if not accounts:
            print(f"  {SG_RED}[!]{C_RESET} {C_WHITE}No valid accounts found.{C_RESET}")
            return
        
        accounts_with_token = sum(1 for acc in accounts if acc.get('jwt_token'))
        print(f"  {SG_GREEN}[+]{C_RESET} {C_WHITE}Loaded {SG_GREEN}{len(accounts)}{C_RESET} {C_WHITE}Accounts")
        print(f"  {SG_CYAN}[+]{C_RESET} {C_WHITE}{accounts_with_token} accounts have existing JWT tokens{C_RESET}")
    except Exception as e:
        print(f"  {SG_RED}[!]{C_RESET} {C_WHITE}Error loading accounts: {e}{C_RESET}")
        return
    
    print()
    print(f"{C_RESET}{SG_NEON}╔══════════════════════════════════════════════════════════════════════╗{C_RESET}")
    print(f"{C_RESET}{SG_NEON}║{C_RESET}{SG_GOLD}                    🚀 PROCESSING                            {C_RESET}{SG_NEON}║{C_RESET}")
    print(f"{C_RESET}{SG_NEON}╚══════════════════════════════════════════════════════════════════════╝{C_RESET}")
    print()
    
    # Process each account
    stats["total"] = len(accounts)
    
    for i, acc in enumerate(accounts, 1):
        uid = str(acc.get("uid", "Unknown"))
        
        print(f"\n{C_RESET}{SG_CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C_RESET}")
        print(f"  {SG_GOLD}[{i}/{len(accounts)}]{C_RESET} {C_WHITE}Processing UID: {SG_NEON}{uid}{C_RESET}")
        print(f"{C_RESET}{SG_CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C_RESET}")
        
        jwt = acc.get('jwt_token')
        
        if jwt:
        print(f"  {SG_GREEN}✓{C_RESET} {C_WHITE}Using existing JWT token{C_RESET}")
            stats["used_existing_tokens"] += 1
            
         print(f"  {SG_BLUE}→{C_RESET} {C_WHITE}Sending {action_name} request to {SG_GOLD}{TARGET_ID}{C_RESET}...")
          success = action_func(TARGET_ID, jwt)
          
           if success:
                stats["success"] += 1
            else:
               stats["failed"] += 1
                password = acc.get("password", "")
                if password:
                    print(f"  {SG_YELLOW}→{C_RESET} {C_WHITE}Token may be expired. Trying to get new JWT...{C_RESET}")
                    new_jwt = get_jwt_token(uid, password)
                    if new_jwt:
                        print(f"  {SG_GREEN}✓{C_RESET} {C_WHITE}New JWT obtained, retrying...{C_RESET}")
                        retry_success = action_func(TARGET_ID, new_jwt)
                        if retry_success:
                            stats["success"] += 1
                            stats["failed"] -= 1
                            stats["expired_tokens"] += 1
                        else:
                            stats["expired_tokens"] += 1
                    else:
                        print(f"  {SG_RED}✗{C_RESET} {C_WHITE}Failed to get new JWT{C_RESET}")
                        stats["jwt_failed"] += 1
        else:
            password = acc.get("password", "")
            
            if not password:
                print(f"  {SG_RED}✗{C_RESET} {C_WHITE}No password or JWT token found for UID: {uid}{C_RESET}")
                stats["failed"] += 1
                stats["jwt_failed"] += 1
                continue
            
            print(f"  {SG_BLUE}→{C_RESET} {C_WHITE}Getting JWT token from API...{C_RESET}")
                    jwt = acc.get('jwt_token')
        
        if jwt:
            print(f"  {SG_GREEN}✓{C_RESET} {C_WHITE}Using existing JWT token{C_RESET}")
            stats["used_existing_tokens"] += 1
            
            print(f"  {SG_BLUE}→{C_RESET} {C_WHITE}Sending {action_name} request to {SG_GOLD}{TARGET_ID}{C_RESET}...")
            success = action_func(TARGET_ID, jwt)
            
            if success:
                stats["success"] += 1
            else:
                stats["failed"] += 1
                password = acc.get("password", "")
                if password:
                    print(f"  {SG_YELLOW}→{C_RESET} {C_WHITE}Token may be expired. Trying to get new JWT...{C_RESET}")
                    new_jwt = get_jwt_token(uid, password)
                    if new_jwt:
                        print(f"  {SG_GREEN}✓{C_RESET} {C_WHITE}New JWT obtained, retrying...{C_RESET}")
                        retry_success = action_func(TARGET_ID, new_jwt)
                        if retry_success:
                            stats["success"] += 1
                            stats["failed"] -= 1
                            stats["expired_tokens"] += 1
                        else:
                            stats["expired_tokens"] += 1
                    else:
                        print(f"  {SG_RED}✗{C_RESET} {C_WHITE}Failed to get new JWT{C_RESET}")
                        stats["jwt_failed"] += 1
        else:
            password = acc.get("password", "")
            
            if not password:
                print(f"  {SG_RED}✗{C_RESET} {C_WHITE}No password or JWT token found for UID: {uid}{C_RESET}")
                stats["failed"] += 1
                stats["jwt_failed"] += 1
                continue
            
            print(f"  {SG_BLUE}→{C_RESET} {C_WHITE}Getting JWT token from API...{C_RESET}")
            jwt = get_jwt_token(uid, password)
            
            if not jwt:
                print(f"  {SG_RED}✗{C_RESET} {C_WHITE}Failed to get JWT for UID: {uid}{C_RESET}")
                stats["jwt_failed"] += 1
                stats["failed"] += 1
                continue
            
            print(f"  {SG_GREEN}✓{C_RESET} {C_WHITE}JWT obtained successfully{C_RESET}")
            
            print(f"  {SG_BLUE}→{C_RESET} {C_WHITE}Sending {action_name} request to {SG_GOLD}{TARGET_ID}{C_RESET}...")
            success = action_func(TARGET_ID, jwt)
            
            if success:
                stats["success"] += 1
            else:
                stats["failed"] += 1
        
        print_progress_bar(i, len(accounts), f"{SG_GREEN}✓ {i}/{len(accounts)}{C_RESET}")
        
        if i < len(accounts):
            time.sleep(2)
    
    print("\n")
    print_stats()
    
    print(f"""
{C_RESET}{SG_VIOLET}╔══════════════════════════════════════════════════════════════════════╗{C_RESET}
{C_RESET}{SG_VIOLET}║{C_RESET}{SG_PINK}          ✨ THANK YOU FOR USING SGCODEX BOT ✨                {C_RESET}{SG_VIOLET}║{C_RESET}
{C_RESET}{SG_VIOLET}║{C_RESET}{SG_GOLD}                    🔥 STAY CONNECTED 🔥                       {C_RESET}{SG_VIOLET}║{C_RESET}
{C_RESET}{SG_VIOLET}╚══════════════════════════════════════════════════════════════════════╝{C_RESET}
    """)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{C_RESET}{SG_RED}╔══════════════════════════════════════════════════════════════════════╗{C_RESET}")
        print(f"{C_RESET}{SG_RED}║{C_RESET}{SG_WHITE}                    ⛔ STOPPED BY USER                          {C_RESET}{SG_RED}║{C_RESET}")
        print(f"{C_RESET}{SG_RED}╚══════════════════════════════════════════════════════════════════════╝{C_RESET}")
