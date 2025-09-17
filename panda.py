import json
import requests
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import time
import secrets
from flask import Flask

# ──────────────────────────────────────────────────────────────
# USERS – add up to 10 refresh tokens here
# ──────────────────────────────────────────────────────────────
USERS = [
    {"username": "user1", "refresh_token": "REFRESH_TOKEN_1"},
    {"username": "user2", "refresh_token": "REFRESH_TOKEN_2"},
    {"username": "user3", "refresh_token": "AMf-vBwEQUVsiklkrQs7efyS4YdIwWoGhTgVS-WbEUMLDWLf2dJyEC7_gP5Cwp_kQ4RQNtAAWKD_V7CYsA4CVWSXxm4hKwBzrQhr0Tmoph1NLfqB21ulzutYzc4H6RzLpRBD61ljZn20ICwbl6aoguyaQ9215KIe3dsF9JUl_11DmSbB3EEN7yfnrUETmzSLdRE-rKTaFDC3rZGbgff4P-FnrT_-Lz5vjL6I_zl764UAdvAQFQrlEC72J8ztaLYUconr2J9NOW2G7tcq7vpdXXkhwkrOPJrV8hwfGgMiD8UIXQJ84nXSFSQSya7_3TT_3Z4wTPkAOlajRTRXABP_fltC0tsi6zJQgoaEmw7ldXthDEePq2SpZdflhumehwwv0BhV2efxovIw6IAatjVdMSML_4CnWkDUSyuwGXRBsFhEb84DwrEBFRcXhJ34tddWAO4RK_b-CoHW"},
]

# ──────────────────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────────────────
PRE_COMPUTED_HASH = "72e08b10b491d84ebe82e6186e7bcea6b638f3f2cae16b257126f9a7bc334192"
PROJECT_ID = "cash-panda-76893"
COIN_LIMIT = 60000

# ──────────────────────────────────────────────────────────────
# FUNCTIONS
# ──────────────────────────────────────────────────────────────
def refresh_id_token(refresh_token):
    """Exchange refresh token for a new id_token + user_id"""
    url = "https://securetoken.googleapis.com/v1/token?key=AIzaSyAMQu13Wg_7UnuwSstH6JKfh37VIEZ4bGg"
    headers = {"Content-Type": "application/json"}
    data = {"grantType": "refresh_token", "refreshToken": refresh_token}
    resp = requests.post(url, headers=headers, json=data)
    resp.raise_for_status()
    j = resp.json()
    return j["id_token"], j["user_id"], int(time.time()) + int(j.get("expires_in", 3600))

def fetch_pending_offers(id_token, user_id):
    """Get all PENDING offers for a user"""
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/users/{user_id}:runQuery"
    query = {
        "structuredQuery": {
            "from": [{"collectionId": "readEarn"}],
            "where": {
                "fieldFilter": {
                    "field": {"fieldPath": "status"},
                    "op": "EQUAL",
                    "value": {"stringValue": "PENDING"}
                }
            }
        }
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {id_token}"}
    resp = requests.post(url, headers=headers, json=query)
    resp.raise_for_status()
    return resp.json()

def generate_refid(aes_key_hex, uid, project_id, offer_id):
    """AES encrypt offer payload → base64 refid"""
    aes_key = bytes.fromhex(aes_key_hex)
    payload = {"uid": uid, "project_id": project_id, "offer_id": offer_id}
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode("utf-8")
    cipher = AES.new(aes_key, AES.MODE_ECB)
    ciphertext = cipher.encrypt(pad(payload_bytes, AES.block_size))
    return base64.b64encode(ciphertext).decode("utf-8")

def finish_reading(refid):
    """Send refid to finish-reading API"""
    url = "https://backend.rtechnology.in/api/finish-reading/"
    nonce = ''.join(secrets.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(12))
    payload = {"refid": refid, "timestamp": int(time.time() * 1000), "nonce": nonce}
    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json=payload)
    print(f"Sent to finish-reading: {payload}")
    print(f"Finish API response: {resp.status_code} {resp.text}")
    return resp.status_code, resp.text

def process_user(user):
    """Main logic per user"""
    now = int(time.time())
    if "jwt" not in user or now >= user.get("jwt_expiry", 0):
        try:
            jwt, uid, expiry = refresh_id_token(user["refresh_token"])
            user["jwt"] = jwt
            user["uid"] = uid
            user["jwt_expiry"] = expiry
            print(f"[{user['username']}] Refreshed token, uid={uid}")
        except Exception as e:
            print(f"[{user['username']}] Refresh failed: {e}")
            return

    if "total_coins" not in user:
        user["total_coins"] = 0

    if user["total_coins"] >= COIN_LIMIT:
        print(f"[{user['username']}] Reached coin limit.")
        return

    try:
        offers = fetch_pending_offers(user["jwt"], user["uid"])
    except Exception as e:
        print(f"[{user['username']}] Fetch offers failed: {e}")
        return

    for offer in offers:
        doc = offer.get("document")
        if not doc:
            continue
        fields = doc.get("fields", {})
        offer_id_field = fields.get("offerId")
        reward_field = fields.get("rewardAmount")
        if not offer_id_field or not reward_field:
            continue
        offer_id = offer_id_field.get("stringValue")
        reward_amount = reward_field.get("integerValue") or reward_field.get("stringValue")
        if not offer_id or not reward_amount:
            continue
        reward_amount = int(reward_amount)
        if user["total_coins"] + reward_amount > COIN_LIMIT:
            reward_amount = COIN_LIMIT - user["total_coins"]
        user["total_coins"] += reward_amount
        print(f"[{user['username']}] Offer {offer_id} with reward {reward_amount}")
        refid = generate_refid(PRE_COMPUTED_HASH, user["uid"], PROJECT_ID, offer_id)
        try:
            finish_reading(refid)
        except Exception as e:
            print(f"[{user['username']}] Finish reading failed: {e}")
            continue

# ──────────────────────────────────────────────────────────────
# FLASK APP for Render healthcheck
# ──────────────────────────────────────────────────────────────
app = Flask(__name__)

@app.route("/")
def home():
    return "Offer bot running ✅"

# ──────────────────────────────────────────────────────────────
# MAIN LOOP
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import threading

    def worker():
        counter = 0
        while True:
            counter += 1
            print(f"\n=== Run {counter} at {time.ctime()} ===")
            for user in USERS:
                process_user(user)
            time.sleep(60)  # run every 1 minute

    threading.Thread(target=worker, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
