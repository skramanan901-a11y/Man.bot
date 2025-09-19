import json
import requests
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import time
import secrets

# ──────────────────────────────────────────────────────────────
# USERS – added your new refresh token here
# ──────────────────────────────────────────────────────────────
USERS = [
    {"username": "user1", "refresh_token": "AMf-vBw5AtK28JUdzYfg-28XKbOdzf8d6g0_8c6K2chDqA5qXYAaUEZ6LEOdhC1WOHl1wNbX4dRvcRs4mg5uaP7yva0YD3MABP9aGPphXCHiGENvQMiadJvogAZ6TT1EsDffro4B4Pl-fsJjb4HNKSZA2BwCG-yToIGXgZilJ5bzceHkmaEbqz3jnPiQtI3SXBoxzpOK17USlQrlU9bYuPp6ULa9RRDz1cO4vDjEf6UIVVtF-MFMpYvh5ZU-xXcYvI2yPFH9sDCtusW0ISU4xKKEF0acqEvbi-gOK_mmtdc4hR2UDQRRUEs__TFX3cx15voY2Tm8CMPlsuZyXpPuFNRfilpy1bjwyBsNsRkl1eWFimg4ydquQVh2v9E6VvM4QlGi_eTpfoOMuLT5-Q8lCvl-P0tAVGgirgNzoJo1-eOhfUFMuDUC4jTWBR9FL7J4Pn0bsb8qJ_U0"},
    {"username": "user2", "refresh_token": "AMf-vBxLEUc94mUMt_G15-xFrtxNGFVI_OT8X2jOgnQv3SwK2ank2e0hGonbVMJ3r4KsG3Ld1zxquAF2Z41dSxCyR0xWDrgs8B7Uvf2C1X5NcCIeGab01g_12eLnRYO6U_WMB7Gt4yGbeSFAKr0YO2ItmahKLoVyo3tD-yf-SCB_qZWnpVT9b4-cJa1-CVsSTEECioWuiU7QYtylH1Cesjbm6KzmtA1s9kPl2OMj_upPDoU3eCl3Vx3gKvwQuHYLOgS1UbuZ8FZv7WICGMO2gnMTyYut36v7BV3Poqi8MPC0Dzhu4OaevjgMb_0vRlykxVCA1X8ywnT-1bIxA3Y1Xh1r4KldUohPbSVPvAbHfn5Z_93QFXLfolgrodPk_4dLgvMpfFbNQbDBVi0GP_STFDJWUmzPfhia7GbD7wEHfXXK_Gs0knkbrLVi-_sOXgiojtQaO6Za4n0f"},
    {"username": "user3", "refresh_token": "AMf-vByNt1LcTZWHG99tYOmYLgIwams1cV_DuCjSL44W8qt2sxOnYKfLJryzoQM2sOapwL63ldieKufdtJeLA-h4FSoDKMeNp5Y2CQyk3TE24s-nS66kgEbmmItv0ZCc-Z5401AUPJ8xRZ0HMDYXYzGrLCtotfriDeMuZcvltFwLfD2NadQurWTEkOBRwnbQiXnNKp0YEtMgwlpwRqllsnJa5l9hCsmvhs3r8DEFTBKVnPg4y-AEdXywNRCP_8Y9r4qVr1L5o3rWqJcd0xty0925yFzZ9s1yq_PeR7aP2T9-T4yq8HCPn1BXI1urvumI2OKepCu_11e7XUomLjCSbUiyRVlSjfLinzS29Eu4at7G-YgSPIhZp7YbJ5LfOEn8p5uCUbS29LBgRiX82t3VXzSsR84EeaZ6qp-BhARjaq8XPGJEiwEHZEFSg-YKi7zp7K7mAIQlJrCS"},
]

PRE_COMPUTED_HASH = "72e08b10b491d84ebe82e6186e7bcea6b638f3f2cae16b257126f9a7bc334192"
PROJECT_ID = "puzzle-master-51426"
COIN_LIMIT = 100000


# ──────────────────────────────────────────────────────────────
def refresh_id_token(refresh_token):
    """
    Use form-encoded fields required by Google Secure Token endpoint.
    Returns: (id_token, user_id, expiry_timestamp)
    """
    url = "https://securetoken.googleapis.com/v1/token?key=AIzaSyCF-M9WFi6IsTIn7G3hzG_nIi3rWA3XD6o"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    resp = requests.post(url, data=data)
    resp.raise_for_status()
    j = resp.json()
    # expires_in is seconds from now
    expiry = int(time.time()) + int(j.get("expires_in", 3600))
    return j["id_token"], j.get("user_id") or j.get("user_id"), expiry


def fetch_pending_offers(id_token, user_id):
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/users/{user_id}:runQuery"
    query = {
        "structuredQuery": {
            "from": [{"collectionId": "readEarn"}],
            "where": {
                "fieldFilter": {
                    "field": {"fieldPath": "status"},
                    "op": "EQUAL",
                    "value": {"stringValue": "PENDING"},
                }
            },
        }
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {id_token}"}
    resp = requests.post(url, headers=headers, json=query)
    resp.raise_for_status()
    return resp.json()


def generate_refid(aes_key_hex, uid, project_id, offer_id):
    # validate hex key length
    try:
        aes_key = bytes.fromhex(aes_key_hex)
    except Exception as e:
        raise ValueError("AES key hex is invalid: " + str(e))
    if len(aes_key) not in (16, 24, 32):
        raise ValueError("AES key must be 16/24/32 bytes long (hex length 32/48/64).")

    payload = {"uid": uid, "project_id": project_id, "offer_id": offer_id}
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    cipher = AES.new(aes_key, AES.MODE_ECB)
    ciphertext = cipher.encrypt(pad(payload_bytes, AES.block_size))
    return base64.b64encode(ciphertext).decode("utf-8")


def finish_reading(refid):
    url = "https://backend.rtechnology.in/api/finish-reading/"
    nonce = "".join(secrets.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(12))
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

    # Firestore runQuery returns a list of results; iterate safely
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
        # reward field may be integerValue (string) or stringValue
        reward_amount = None
        if "integerValue" in reward_field:
            try:
                reward_amount = int(reward_field["integerValue"])
            except Exception:
                reward_amount = None
        elif "stringValue" in reward_field:
            try:
                reward_amount = int(reward_field["stringValue"])
            except Exception:
                reward_amount = None

        if not offer_id or reward_amount is None:
            continue

        if user["total_coins"] + reward_amount > COIN_LIMIT:
            reward_amount = COIN_LIMIT - user["total_coins"]
            if reward_amount <= 0:
                print(f"[{user['username']}] No remaining coin space for offer {offer_id}.")
                continue

        user["total_coins"] += reward_amount
        print(f"[{user['username']}] Offer {offer_id} with reward {reward_amount}")

        try:
            refid = generate_refid(PRE_COMPUTED_HASH, user["uid"], PROJECT_ID, offer_id)
        except Exception as e:
            print(f"[{user['username']}] Refid generation failed: {e}")
            continue

        try:
            finish_reading(refid)
        except Exception as e:
            print(f"[{user['username']}] Finish reading failed: {e}")
            continue


# ──────────────────────────────────────────────────────────────
# MAIN LOOP
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    while True:
        for user in USERS:
            process_user(user)
        # small sleep to avoid a busy spin; adjust or remove if you deliberately want no sleep
        time.sleep(5)
