import binascii
import os
import random
import sys
import urllib3
import re
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from flask import Flask, jsonify, request, render_template_string
import requests
from requests.adapters import HTTPAdapter

# ---------- SSL Warnings & Connection Pool Setup ----------
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

OAUTH_EAT_URL = "https://100067.connect.garena.com/oauth/token/grant"
INSPECT_TOKEN_URL = "https://prod-api.reward.ff.garena.com/redemption/api/auth/inspect_token/"

http_session = requests.Session()
adapter = HTTPAdapter(pool_connections=50, pool_maxsize=50)
http_session.mount("http://", adapter)
http_session.mount("https://", adapter)
http_session.verify = False

def extract_eat_token(input_str):
    if not input_str:
        return None
    input_str = input_str.strip()
    if "eat=" in input_str:
        match = re.search(r'eat=([a-zA-Z0-9_\-]+)', input_str)
        if match:
            return match.group(1)
    return input_str

def perform_eat_login(eat_token):
    # আপনার কোডের ক্লায়েন্ট আইডি ও সিক্রেট লিস্ট[span_1](start_span)[span_1](end_span)
    clients = [
        {
            "client_id": "100067",
            "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        },
        {"client_id": "100067", "client_secret": "fd4f9c1186e2469a8b191c0e3e2d63f0"},
        {"client_id": "100011", "client_secret": "fd4f9c1186e2469a8b191c0e3e2d63f0"},
    ]

    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; SM-G998B Build/TP1A.220624.014)",
        "Content-Type": "application/x-www-form-urlencoded",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
    }

    for cred in clients:
        payload = {
            "grant_type": "eat",
            "eat": eat_token,
            "client_id": cred["client_id"],
            "client_secret": cred["client_secret"],
        }
        try:
            resp = http_session.post(
                OAUTH_EAT_URL, data=payload, headers=headers, timeout=6
            )
            data = resp.json()
            if "access_token" in data:
                return data["access_token"], data.get("open_id")
        except Exception:
            continue

    return None, None

def get_name_region_from_reward(access_token):
    try:
        headers = {
            "accept": "application/json, text/plain, */*",
            "access-token": access_token,
            "user-agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36",
        }
        resp = http_session.get(INSPECT_TOKEN_URL, headers=headers, timeout=5)
        data = resp.json()
        return data.get("uid"), data.get("name"), data.get("region")
    except:
        return None, None, None

@app.route("/", methods=["GET"])
def index():
    html_file = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_file):
        with open(html_file, "r", encoding="utf-8") as f:
            return render_template_string(f.read())
    return jsonify({"status": "EAT Generator API Running ✅"})

@app.route("/generate", methods=["POST"])
def generate():
    req_data = request.get_json(silent=True) or {}
    raw_input = req_data.get("eat") or req_data.get("url") or request.args.get("eat")
    
    if not raw_input:
        return jsonify({"success": False, "error": "Please paste URL or EAT token!"}), 400
        
    eat_token = extract_eat_token(raw_input)
    if not eat_token:
        return jsonify({"success": False, "error": "Invalid EAT Token format!"}), 400

    # Get Access Token using EAT
    access_token, open_id = perform_eat_login(eat_token)
    if not access_token:
        return jsonify({"success": False, "error": "Invalid or Expired EAT Token!"}), 400

    # Get Player Info (UID, Nickname, Region)
    uid, name, region = get_name_region_from_reward(access_token)

    return jsonify({
        "success": True,
        "nickname": name if name else "—",
        "region": region if region else "—",
        "uid": str(uid) if uid else "—",
        "level": "—",
        "access_token": access_token,
        "jwt_token": f"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.{access_token}"
    })

app = app
