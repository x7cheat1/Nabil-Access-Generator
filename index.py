import os
import re
import requests
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

# Garena Official API Endpoints
OAUTH_EAT_URL = "https://100067.connect.garena.com/oauth/token/grant"
INSPECT_TOKEN_URL = "https://prod-api.reward.ff.garena.com/redemption/api/auth/inspect_token/"

def extract_eat_token(input_str):
    if not input_str:
        return None
    input_str = input_str.strip()
    if "eat=" in input_str:
        match = re.search(r'eat=([a-zA-Z0-9_\-]+)', input_str)
        if match:
            return match.group(1)
    return input_str

def get_access_token_from_eat(eat_token):
    # গ্যারেনার বিভিন্ন ক্লায়েন্ট আইডি ও সিক্রেট কম্বিনেশন যা টোকেন গ্র্যান্ট করতে ব্যবহৃত হয়
    credentials = [
        {
            "client_id": "100067",
            "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
            "client_type": "2"
        },
        {
            "client_id": "100067",
            "client_secret": "fd4f9c1186e2469a8b191c0e3e2d63f0",
            "client_type": "2"
        },
        {
            "client_id": "100011",
            "client_secret": "fd4f9c1186e2469a8b191c0e3e2d63f0",
            "client_type": "1"
        }
    ]
    
    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; SM-G998B Build/TP1A.220624.014)",
        "Content-Type": "application/x-www-form-urlencoded",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
    }
    
    for cred in credentials:
        payload = {
            "grant_type": "eat",
            "eat": eat_token,
            "client_id": cred["client_id"],
            "client_secret": cred["client_secret"],
            "client_type": cred["client_type"]
        }
        try:
            resp = requests.post(OAUTH_EAT_URL, data=payload, headers=headers, timeout=8)
            data = resp.json()
            if "access_token" in data:
                return data["access_token"]
        except Exception:
            continue
            
    return None

def inspect_player_info(access_token):
    headers = {
        "accept": "application/json, text/plain, */*",
        "access-token": access_token,
        "user-agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36",
    }
    try:
        resp = requests.get(INSPECT_TOKEN_URL, headers=headers, timeout=8)
        data = resp.json()
        if "uid" in data or "name" in data:
            return {
                "uid": str(data.get("uid", "—")),
                "nickname": data.get("name", "—"),
                "region": data.get("region", "—")
            }
    except Exception:
        pass
    return {"uid": "—", "nickname": "—", "region": "—"}

@app.route("/", methods=["GET"])
def home():
    html_file = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_file):
        with open(html_file, "r", encoding="utf-8") as f:
            return render_template_string(f.read())
    return jsonify({"status": "Online ✅"})

@app.route("/generate", methods=["POST"])
def generate():
    req_data = request.get_json(silent=True) or {}
    raw_input = req_data.get("eat") or request.args.get("eat")
    
    if not raw_input:
        return jsonify({"success": False, "error": "Please paste URL or EAT token!"}), 400
        
    eat_token = extract_eat_token(raw_input)
    access_token = get_access_token_from_eat(eat_token)
    
    if not access_token:
        return jsonify({"success": False, "error": "Invalid or Expired EAT Token!"}), 400

    player_data = inspect_player_info(access_token)
    
    return jsonify({
        "success": True,
        "nickname": player_data["nickname"],
        "region": player_data["region"],
        "uid": player_data["uid"],
        "level": "—",
        "access_token": access_token,
        "jwt_token": f"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.{access_token}"
    })

app = app
