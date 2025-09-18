import json
import requests
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import time
import secrets
from flask import Flask
import threading

# ──────────────────────────────────────────────────────────────
# USERS – refresh tokens (10 slots)
# ──────────────────────────────────────────────────────────────
USERS = [
    {"username": "user1", "refresh_token": "AMf-vBwMSKybJCADjLPzq1rZIVQczxWLTIrbggRu49JIIT8AXH-v4DS9HLrP_NoP5kdh0xN4Bm86tvStVPjfNj6mU9ulYmpXXvJkknnHGjKZWbopYV5m0tazKVNLY4r2GOj25p68lpY9LiwAi63VQKPZDPOrDBAyA0GgPlmtUH1SyqgpteTfQ_ZqVnDE6U1bLUUX6yhzHrvzN23l0QnnYrDK7KviHffNAOhWUpcIOjvomNdn_NoyiT4pwac95gmF2h1Ku0polVoeyDS-IgCd2sCAZEUNxsiFOLOvrxWa7BG1ewiORn-6KVwOkYF7B8dPGU1PcyG3V78cWVVrVt29Y33Zl-jko8K0_Cu8Bqpr71E3P2Au-1b3vv1o0VTgb23p4OP-n_gdlS7iS9SDp2o1-69AK9Mgjqdx5m9UAMKjdI5TPZqavaRuq8Yo0k0xh1eH8pgEIxx9bZV8"},
    {"username": "user2", "refresh_token": "AMf-vBzQh5o-S8HPImfmOOFJUdKdLCwbWgkKD1p39jzBLWcrL8Fch1LI-st4zb7eXJAb3ixuFrl4C2A5l9jzSs6oTyUhYxZOhn9Lq0PehdllO-PxYKmBLwjXLuXa3Ur-HnNq2cHMfvGSHbyh_pmnYJ8dWnXQ9xjZ3GkUsXfwsLgnhlQ_NFL-XZxK50Fa4RYsZ0UhL9lZCCdBUfvM8h3elA2V3M3-zzYjxoOFaM2tVcyH6XOwLAEGexwwmzNKW8rGYDc7HL4q1TGP1udgJxS3h3oqCBVtRgmAYZuczfQ6W-5wWA5GDOnX1WV7DtumdSXe46xt1_LxBs2nVZHepwbS8_-eDErNVcHsr3fiTDa7HYkuA_q3OOZnCfHeFitKDW95SuuSWWRnJV8q-uCtuqpdhfTS_h4TjqUuMJq1jRuXCa-LaIDme2uX7McE6U1-yKMKUXmsK5aEuX7K"},
    {"username": "user3", "refresh_token": "AMf-vBwEQUVsiklkrQs7efyS4YdIwWoGhTgVS-WbEUMLDWLf2dJyEC7_gP5Cwp_kQ4RQNtAAWKD_V7CYsA4CVWSXxm4hKwBzrQhr0Tmoph1NLfqB21ulzutYzc4H6RzLpRBD61ljZn20ICwbl6aoguyaQ9215KIe3dsF9JUl_11DmSbB3EEN7yfnrUETmzSLdRE-rKTaFDC3rZGbgff4P-FnrT_-Lz5vjL6I_zl764UAdvAQFQrlEC72J8ztaLYUconr2J9NOW2G7tcq7vpdXXkhwkrOPJrV8hwfGgMiD8UIXQJ84nXSFSQSya7_3TT_3Z4wTPkAOlajRTRXABP_fltC0tsi6zJQgoaEmw7ldXthDEePq2SpZdflhumehwwv0BhV2efxovIw6IAatjVdMSML_4CnWkDUSyuwGXRBsFhEb84DwrEBFRcXhJ34tddWAO4RK_b-CoHW"},
    {"username": "user4", "refresh_token": "AMf-vBxENXHLQNNnkNtx5KOOTtCPO-5RzROUfaqSAarRXY3mt9uIBrkvGtt-2_9I9qfC43NiJCYp2REnXAjIg3NScPANDfmz3wUF90TA1Cxbs-rxyAz2WGfk0LV67H0nCzzwv763jJcknFZYO2O5R-ImsJLFAj74fy74tIaUprAoljJs0R_JB-BDgETo05gtSbLShNksTLR8WHlC3SE4xK0oaasWouU30ZFJ7EHL1e1s7Jer9RvBb7pjf_2qfo3FwzDH2O5nY1bE7KaZky29azBK8_JpWNDUUy_zM6VaK7LwjE6whGIOYYK-SLChLkr_WQ5lsAMoc_SBFfQQFOKC83eWEzNUtT3jXW5kKSoUC3e1h17twtwdO57ULcuZLvRYuIG7kLYL1Fs0eEOM9L1shtpm0gMAAiLPOrcfOSK0Zld8_ownixbjL1d6LkugALvxfD5Opr-eeRMZ"},
    {"username": "user5", "refresh_token": "AMf-vBw-Mor88zX9XkaN0ezhtc6BM5c62_dZRVydWwFXCDPUINXx6z61YTujyKK5kucQu8EYeqrl11Xoyx5SJ2Yap58rzfqKhgeg-IAywDm1g_wlHwW7v-3XslVPH_9uZq-1OsLhxaHLCnFcEUj9zetOn3vlPvq5Bq1VYAIv5dPVuPEIKwh39B-i0kykQbBfM2ChKx7cmrlEvi9pjO5444CpGvJDIYqVpiu-bW92IyI3UgHJD_nOHQ4cNZ4fLYcP4V53q0kehZbHC5j5Rl6PlrxSFx-8fWyR9GcuPnv3GjQBPxYncgA6E5iDh_Oq_UTYUhLHhXu_DLc-YXljR2hEiDLRwSb5IIldhfLFI-oGz69-dhbQvgqeRtKkjQ_VJko8Rgk82HqzmSMGfKYlCWGZ-5MP7lKAj0Cz2Vr572bJxbVibhvPwvAtzcS0miAa6xloVrtOgY7JCdDi"},
    {"username": "user6", "refresh_token": "AMf-vBwD3-EFQpBbVMvGpp6Gi1aZas9LIXOMADRCBoBtjCn568ssBsAVvsWreLXHA-fimmoBe2472c0mvb2IOd9XHwTd9Lg9c3Mwj-enqivwQWDQSV5JWQmOiDwVUm8Ali49oTLmUnZuWPPOFKvhcBhf9AyrSfWfblQKGRRKpjIlB0wv8oHyxWZNNL7Y_04SAelLYyidx20ZcVB1B_YZ-1D-qHvds_N22BcM-w-Xi5WyJxGSPu7cbFBjC189tkFZXg2lQyQ9aCUwleKWhRFphzUQCaoq64rJfbq4mXkv15yycHEjd3j8HQ_1OOmzkG9oJaaOnSmUW2R9EFuJKp040frrsQtsU-o_-JIv2OXljwUxxmNJ__Kq2KuhpEr6VA0l0rcp83IwaAT1RBpWow6nR6Nkf3wzqUYrSVXV86eNs67vOLy9vbk-qUFNhj3aqmR28E6XTCbBtLhG"},
    {"username": "user7", "refresh_token": "AMf-vBzixcsZBcq8L9izZrvmUT5f_XOLl0LnjPccSMsnTBLrepn9GVSFpHFYAgZZHxve456IQX8Mn8Jfv6BnHms8E6jlRkUC1uzoP_RtMSjHwCOju3wo3i9ipednVJX_qqAwl53ZSqvvDM0nmzseZnI12_XANe8YI41YZ5a8QIXWP_epyP0aYMeYCo4A5WQURWZt5_6DmUf2oi6gk9YSNJXh2r-QlVXOqBcgX4k1stg9jWaYt-OaA5kKmyP0g4Mip8axKUpxPDe569U3xE4h1esfjThrShVEJjbz4rXGY5in1AGYin-_u_T0TBYGp6BEMD0ZVoU6wqXnhsfWiaKOJ5H7vBJjF3xgJy6raE8_K8AqnoZgvlkD-p_1JW0zDznl1XGLrjq4hIL0Aqk8AW-SArNVAuXDwjhZZNkJwzvSTee60ilZ0H1l8tlv9JsX7T-6ZCWq3c2H0Ez3"},
    {"username": "user8", "refresh_token": "AMf-vBzNE51qrhNXhrX1LcG4IKCGGA_vpclp0VElqQeCqMvggLbuPEwS37CrCZCMBD4B-nWGdb5YJmJ_qTov4AAoV3ZiSGv0x31HioP7HsuqWEjJw1eit7J62ikcbYVOjKEprFPyPLBs4-2Btoxf3eSibDi5SE-CRhh05ID7xa_RCjQh0ZP6pODATS16wR94HhmmwxGUQfQGQIsOrUjwkZC0auPYlKDM3tvETcJemVtbGg2uq0kuduj11O4EB5ZoNAqc_GvuZMKj9mUwWIMo7bn-OOSAl1MiwOq8fQKg-7u4wzR5D7oaYWndIhWLYlguiihkn22y8Q0WRCKjp75SIn1f5SZmasTZGqjjeotGsnNfWjUXB6ocX1qbOKvzru8TWq6lhdYDCU6Au9ooJw3d8xthWmg_92ZGRgnVthbmBTKcZ1SsCNnY-dI"},
    {"username": "user9", "refresh_token": "AMf-vBw423NPl5IfIgcrruVoLVMn35V_aBYlbh7_zsmJ-ResJvwWEZiLwYPEthLgN59IoKt8h0sIF6IjGfUdZaX58HeGXcxuE8P0wEGGToOzVMCPDQlbxqsE3dRen_hoyqWkhn4Vbi_U9DffOMQqG0oUnmLvZW-_Dw-LNB87zPvIw96jIIBpUdKX-mb1WjsAIetkVXC8fVLkXF7R1EAfADVQdUyM9R37b5rW3o1LGK4Kwg39kSXXJAD2qpp_nHz_CuDOnJ37vj1RkShtpYJjht3DpsR-UGqbq3JDwW1wGx7U9257AL6PCcv6l8RBKwEY6khUOA6RZA0_1ljHqOP_ZCdaYxpS_yF4KT7jBhw4U0JmkA_IC3k7HoGW2iIavxafOBB97IH4AWXAs91XwDRg9viZKxwv0_ggstOTGV0Pu3XHDS35CK59mnDuzZY4x7oiBP6qE1Xq0KRw"},
    {"username": "user10", "refresh_token": "AMf-vBzvS9IuT-NAEhqpqrERtptgXOcNTf0vi8KB-wm83suw77BuV3XZOWlLNc23xceATHd9MTt9OF3wrsjjtKDHJ-sxoXwakdIojJFPiIevn5Aw4ET3nkpleyFnxzd-L6erA9jYlByULDXw3kzjjn1OO3IikqsMmf8h2I6rD-oLleOBj-KbCthQIJF0v3RKtvMuFzbv8w-7J8MrgvcJVBT9YUmt31cHs69SimWZwfd7oeieqJHc519aVN-yIBF410_27taILIcoSM1i3uo0bHH9557st-wFFT-x5-g2SyAT5nficGq9O-uNboel9LJqu_HvBCqiRz32F4cTrPkuY8A73QLkbLc09PtndLOwyrSi9j4DgMUS0Y6eKCDkzC-2VnELyW0MJh-_a0WHY5vhoeBFuIePhlfcdRNSR77zdJ7kpgy4k-_zBLca-B1bL90PqMTZeI6D7SO"},
]

PRE_COMPUTED_HASH = "72e08b10b491d84ebe82e6186e7bcea6b638f3f2cae16b257126f9a7bc334192"
PROJECT_ID = "cash-panda-76893"
COIN_LIMIT = 200000

# ──────────────────────────────────────────────────────────────
# FUNCTIONS
# ──────────────────────────────────────────────────────────────
def refresh_id_token(refresh_token):
    url = "https://securetoken.googleapis.com/v1/token?key=AIzaSyAMQu13Wg_7UnuwSstH6JKfh37VIEZ4bGg"
    headers = {"Content-Type": "application/json"}
    data = {"grantType": "refresh_token", "refreshToken": refresh_token}
    resp = requests.post(url, headers=headers, json=data)
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
# FLASK APP (for Render healthcheck)
# ──────────────────────────────────────────────────────────────
app = Flask(__name__)

@app.route("/")
def home():
    return "Offer bot running ✅"

# ──────────────────────────────────────────────────────────────
# MAIN LOOP in background thread
# ──────────────────────────────────────────────────────────────
def worker():
    counter = 0
    while True:
        counter += 1
        print(f"\n=== Run {counter} at {time.ctime()} ===")
        for user in USERS:
            process_user(user)
        time.sleep(60)  # run every 1 minute

if __name__ == "__main__":
    threading.Thread(target=worker, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
        
