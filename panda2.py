import json
import requests
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import time
import secrets
import threading
from flask import Flask

app = Flask(__name__)

# --- Users with refresh tokens ---
USERS = [
    {"username": "user1", "refresh_token": "AMf-vBxENXHLQNNnkNtx5KOOTtCPO-5RzROUfaqSAarRXY3mt9uIBrkvGtt-2_9I9qfC43NiJCYp2REnXAjIg3NScPANDfmz3wUF90TA1Cxbs-rxyAz2WGfk0LV67H0nCzzwv763jJcknFZYO2O5R-ImsJLFAj74fy74tIaUprAoljJs0R_JB-BDgETo05gtSbLShNksTLR8WHlC3SE4xK0oaasWouU30ZFJ7EHL1e1s7Jer9RvBb7pjf_2qfo3FwzDH2O5nY1bE7KaZky29azBK8_JpWNDUUy_zM6VaK7LwjE6whGIOYYK-SLChLkr_WQ5lsAMoc_SBFfQQFOKC83eWEzNUtT3jXW5kKSoUC3e1h17twtwdO57ULcuZLvRYuIG7kLYL1Fs0eEOM9L1shtpm0gMAAiLPOrcfOSK0Zld8_ownixbjL1d6LkugALvxfD5Opr-eeRMZ"},
    {"username": "user2", "refresh_token": "AMf-vBw-Mor88zX9XkaN0ezhtc6BM5c62_dZRVydWwFXCDPUINXx6z61YTujyKK5kucQu8EYeqrl11Xoyx5SJ2Yap58rzfqKhgeg-IAywDm1g_wlHwW7v-3XslVPH_9uZq-1OsLhxaHLCnFcEUj9zetOn3vlPvq5Bq1VYAIv5dPVuPEIKwh39B-i0kykQbBfM2ChKx7cmrlEvi9pjO5444CpGvJDIYqVpiu-bW92IyI3UgHJD_nOHQ4cNZ4fLYcP4V53q0kehZbHC5j5Rl6PlrxSFx-8fWyR9GcuPnv3GjQBPxYncgA6E5iDh_Oq_UTYUhLHhXu_DLc-YXljR2hEiDLRwSb5IIldhfLFI-oGz69-dhbQvgqeRtKkjQ_VJko8Rgk82HqzmSMGfKYlCWGZ-5MP7lKAj0Cz2Vr572bJxbVibhvPwvAtzcS0miAa6xloVrtOgY7JCdDi"},
    {"username": "user3", "refresh_token": "AMf-vBwD3-EFQpBbVMvGpp6Gi1aZas9LIXOMADRCBoBtjCn568ssBsAVvsWreLXHA-fimmoBe2472c0mvb2IOd9XHwTd9Lg9c3Mwj-enqivwQWDQSV5JWQmOiDwVUm8Ali49oTLmUnZuWPPOFKvhcBhf9AyrSfWfblQKGRRKpjIlB0wv8oHyxWZNNL7Y_04SAelLYyidx20ZcVB1B_YZ-1D-qHvds_N22BcM-w-Xi5WyJxGSPu7cbFBjC189tkFZXg2lQyQ9aCUwleKWhRFphzUQCaoq64rJfbq4mXkv15yycHEjd3j8HQ_1OOmzkG9oJaaOnSmUW2R9EFuJKp040frrsQtsU-o_-JIv2OXljwUxxmNJ__Kq2KuhpEr6VA0l0rcp83IwaAT1RBpWow6nR6Nkf3wzqUYrSVXV86eNs67vOLy9vbk-qUFNhj3aqmR28E6XTCbBtLhG"}
]

# --- Config ---
PRE_COMPUTED_HASH = "72e08b10b491d84ebe82e6186e7bcea6b638f3f2cae16b257126f9a7bc334192"
PROJECT_ID = "cash-panda-76893"
COIN_LIMIT = 200000

# --- Helpers ---
def refresh_id_token(refresh_token):
    url = "https://securetoken.googleapis.com/v1/token?key=AIzaSyAMQu13Wg_7UnuwSstH6JKfh37VIEZ4bGg"
    data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    resp = requests.post(url, data=data)
    resp.raise_for_status()
    j = resp.json()
    return j["id_token"], j["user_id"], int(time.time()) + int(j.get("expires_in", 3600))

def fetch_pending_offers(id_token, user_id):
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
    aes_key = bytes.fromhex(aes_key_hex)
    payload = {"uid": uid, "project_id": project_id, "offer_id": offer_id}
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode("utf-8")
    cipher = AES.new(aes_key, AES.MODE_ECB)
    ciphertext = cipher.encrypt(pad(payload_bytes, AES.block_size))
    return base64.b64encode(ciphertext).decode("utf-8")

def finish_reading(refid):
    url = "https://backend.rtechnology.in/api/finish-reading/"
    nonce = ''.join(secrets.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(12))
    payload = {"refid": refid, "timestamp": int(time.time() * 1000), "nonce": nonce}
    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json=payload)
    print(f"Sent to finish-reading: {payload}")
    print(f"Finish API response: {resp.status_code} {resp.text}")
    return resp.status_code, resp.text

def process_user(user):
    refresh_token = user["refresh_token"]
    id_token, uid, expiry = refresh_id_token(refresh_token)
    offers = fetch_pending_offers(id_token, uid)

    for offer in offers:
        doc = offer.get("document")
        if not doc:
            continue
        fields = doc["fields"]
        offer_id = fields["offerId"]["stringValue"]
        refid = generate_refid(PRE_COMPUTED_HASH, uid, PROJECT_ID, offer_id)
        finish_reading(refid)
        time.sleep(60)  # run every 1 min

def worker():
    while True:
        for user in USERS:
            try:
                process_user(user)
            except Exception as e:
                print(f"Error processing {user['username']}: {e}")
        time.sleep(5)

@app.route('/')
def home():
    return "Bot running with 3 users."

if __name__ == '__main__':
    threading.Thread(target=worker, daemon=True).start()
    app.run(host='0.0.0.0', port=10000)
