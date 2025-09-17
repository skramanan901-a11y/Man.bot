from flask import Flask
import threading
import time
import requests
from datetime import datetime

app = Flask(__name__)

# --- API endpoints ---
LIST_OFFERS_API = "https://server.offerpro.io/api/tasks/list_article_offers/?ordering=-cpc&no_pagination=false&page=1"
API_A = "https://backend.rtechnology.in/api/finish-reading/"
API_B = "https://rfitness.rayolesoftware.com/api/finish-reading/"

HEADERS = {
    "Content-Type": "application/json"
}

# --- User configuration (10 slots with enc + app_id + placeholder device_id) ---
USERS = {
    "user1": {
        "enc": "Y-G196gbwELXW9JwJVz4ZVOID9pR0wgZznEbZgqWgTPasHoQBHqvLayJI1wR2lJDxBMTHplGE2Mph-1XHwhBVhwoKssAwOHEjcOhtbE-bLdmX1gwEDU3hhxe0wt90UqS_BF_s6GpUnYFe7lCqXhUY1D3rRNsU-y0YbhblLJ2fDibizAsXwH8EqwgZWikl4L_lItaoPGzOtw3AVzuJ0xsXnIMii80vz65Y4Z-qoyy8DJiUOGy3i1bFXAwYuNV6KcbgFwYJ_iaHNr5yRyrLdo4HHBZZMszhBmVynO2XeSBj0M=",
        "app_id": 14,
        "device_id": "user1_device"
    },
    "user2": {
        "enc": "VK2aRg9jpjqhhYZLHT0l5tIVfH3cjtuaZxVo15Y_2AuxyaMzDnStQeyC6VpzCH4_LEoxHZLJ82pfjiLsWVnJFLDUHTyeLViiNOscR5wk-aizeGf_a3lShqlJNCgsYVDiRS0GUQ6Z66Td4YVLCcQKoswcq0kCRrp7-MAmmEeo_OWV_Hq9LPg9patd4VlkRa9oZxV139LK1bdOYmJH6uxU3NPUe7roxyYF1_Uaif7bfDW_YwbP6HKBCX82deo8JPhsRr8oJeuF5CBMfQQePxrVBJAF3WUbLgtxA5fLWeRZP6U=",
        "app_id": 16,
        "device_id": "user2_device"
    },
    "user3": {
        "enc": "y6mHV25ZdatA9y9lLbTckQ6j69tM9ytHHbAMIASccTG8mDbLCmriPJF6An5Fwcmp-p5c6Oma3E0eCkcEMWL9CQWGfxUbB0_XdckALgIVaKKZFNtNk_qbLejTEaZSLhftMj_OPimex7XKHRUJMpSwcstjAz3bdJVO6g6PJavuSi1_4hKQXoCzAshmS9M8jWeWUjcMcFyLHFAC5rJffIkw5w2dx93DMWelAoSVYW6o_lwm_BCZJ1mWstc9AJ6tNhsD6q_sCLjcbJH77AE_Fsv6QeBW3uyRN7MIGqPa7usDWp0=",
        "app_id": 15,
        "device_id": "user3_device"
    },
    "user4": {
        "enc": "LpmETUP1laHCLAX-NdxwUeeXRPqevc0DjjAZwgUZ0DMBKK6_yxbh3hKDZMr8_dC8SEEEiC5IrWiwHiR5urykzDE-ONpncTG8RWVWwD6eI-OZceaJHQbD335FwDnUlBTtrFc5zS-kqcW1virnjne2-10HFT6jnvRNoHHVHewBdqIClkXNMeeDfrtyaNGfV5x3vAFRxzEw-g4Zw8nEybdQI4Zhkr0zXq6IpUcJiH-1XecMLAET-6kSgDvzq1WFQIpyHHomFUtOW4Dw1rAzFfVdhUZj1gLUTTNlD20oDfXfV60=",
        "app_id": 17,
        "device_id": "user4_device"
    },
    "user5": {
        "enc": "gH-RZAKZAZKdEOV8pMqMsTKl0BWvIf7HWQUIV0MWR0_As_IKKs32X2vHhMg3TGSkUlpAhACyqXPASrTQm-wm9_ZeeL6Eub_bc9TlKPHy32mLIcs5_6VrfxzVMuECdznT0fWRdMYPsTonOUCwzk1unHeH6RvYvfN1yEf5Ek9m-h8WPYkEdvqg3UAkvTympO3SQHHtVcYxdrDtJu6YfMLxzwwDTe9n_Yoq1KhhtGR1Beo2JxK2teMFc3eHXt4HFndXYNPyPb63e9Je26xiGw9YOhwpL-aJ6EENpT6yCllQqZY=",
        "app_id": 24,
        "device_id": "user5_device"
    },
    "user6": {
        "enc": "GbFALlR7a7CsHNn7pbcHzKhX8P_34GTjoPvIwkK7_buvVI4y2smYEiEnEt6yvx_WyRu7tedP06zWAstKhsJOsAZEYSjoBW_g0lqW0-Rfk5LdTzotsA2NAb6XjmDm6GeET8dcMvWUTWHht7o9gqZt9ERejq3N14R75iG1xNJDtoKL02rECWylmXp2Wamjgq31zjoNeSHRTjM2-E7hsDvQgIJglOeCpTnAA9M7axILRfTMfQ7woDY-vztMgslHQIEuHF87cSNZp6hCIWGFIBc-SC83nvZkKn5PdNdOJ5kZPCY=",
        "app_id": 4,
        "device_id": "user6_device"
    },
    "user7": {
        "enc": "iVBWZ9FQ1t0GrrnRr3EyVxVqb0p9qthFXvpqHXyjh_ulW9xqvQcC4LJ2MAI2c1FA0p4P2SgAuhgCeD3K7JWw3gjVJEW8sAWldL0GTdYQQ_mQdeKcEIyQL9xrnjLjnvIOXC0E9Dp80fmVdVMgiL9uRI-vt2Q-HSrrUED8eWz7VR9UDBzFGvR1fy_hZXT4cTr-qzaollYlOnzrIjgKbOn3MBy62Uv3fpN5icQW3SvduafbTLt2C0Aa4hWSCTxN-QxlB9_TyfMBdvZqZdJ-XAKNeg2CPGWxW6qMilxirE09kJU=",
        "app_id": 24,
        "device_id": "user7_device"
    },
    "user8": {
        "enc": "nlqq8-1RD2iHKhbYA3ktZt_25BYFrJ5SIrpKKKqEu0QOxPDKURyUXOTTteizJ_kdnUoIX7Q5eGNbsUlJpKJKyopj3i9XAwincWEjV8ZzIeQ8XPGiffrD1ZGHvuoS1JDj2T2QtHNnnLiiXo6GLUjbgeFbeUP63gPyW1YfmCxV90sTB8tB2MOtV0z2cfjVYyYoa2MQAxGTT_YHZB5VJPKfeVcyWk-XcDsfyCwnG-r8t2eO0xF0hcgONieMws1tceuCl48eFuAqshtMXzH3MiGw8ZEEiFt5xaIRbfw-2yJvi4s=",
        "app_id": 24,
        "device_id": "user8_device"
    },
    "user9": {
        "enc": "e8GhHsJKPjIKoyB1-vm4KxpewCnJrlffr9oydgqgsMJvU6jGxIfmglSTg5dKlS5PAQ1UcsnAgS8DZnMyP8BuxKSVLReRN9G-Rd-0Y-3d0055fhZ_nr1e7Z4Q_EuNhXgDWJVlLPUcEqZ2ha491Sz57TqWvY1A3PemQNEt6iDz5jkjEELCLapgD7NFdneTEZdxJT1ivX3h3JY8lQJ1rNjZdeHjzx7_lfL4y4m5DNxKF5dX9vsE5wvWr2QT84p7Hf6-oaJd6mIChhTBiIzvYNkmkvKRPlkF78LJ-VT5j8w_huQ=",
        "app_id": 24,
        "device_id": "user9_device"
    },
    "user10": {
        "enc": "-m6WR24xzCUmdFxB94p_FBDybrWO5qqnNMQHJzZVomGehSNZ3_yGX9F4OaUU_SWA2of7QuJXcO5bnPjKJmvQBqHKsaJSS9E70kZDTkuK2QyvOf65UKxGPK3e90KHeeVsjBIERdFo6iXWb_PLP_Ujgt-uLEivb58a5CsXywS2Jptp8rvfb_6CssJ-RjnrN3PHNBSC-ZIECfBhbAmFh1eUWf-xLdjPVgf9L1iDdhGpiJlFrR9M4-p9zYy9HHj4rgF028rSDcD9osoNYrOQX0R9TcjyovTpeZuPRGiUX3h7BcI=",
        "app_id": 16,
        "device_id": "user10_device"
    },
}

# --- Example function for making API request ---
def finish_reading(user, offer_id):
    payload = {
        "enc": USERS[user]["enc"],
        "app_id": USERS[user]["app_id"],
        "device_id": USERS[user]["device_id"],
        "offer_id": offer_id
    }
    try:
        response = requests.post(API_A, json=payload, headers=HEADERS)
        print(f"[{datetime.now()}] {user} → Offer {offer_id} → {response.status_code}")
    except Exception as e:
        print(f"Error for {user}: {e}")

# --- Background worker thread ---
def worker():
    counter = 0
    while True:
        counter += 1
        print(f"=== Run {counter} at {datetime.now()} ===")
        
        for user in USERS:
            if USERS[user]["enc"]:  # only if slot is filled
                finish_reading(user, offer_id="YOUR_OFFER_ID_HERE")
        
        time.sleep(60)  # wait exactly 1 minute

# --- Start worker in background ---
threading.Thread(target=worker, daemon=True).start()

# --- Flask endpoint for health check ---
@app.route("/")
def home():
    return "OfferPro bot is running."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
