import time
import requests
import random
import re

# --- API endpoints ---
LIST_OFFERS_API = "https://server.offerpro.io/api/tasks/list_article_offers/?ordering=-cpc&no_pagination=false&page=1"
API_A = "https://backend.rtechnology.in/api/finish-reading/"
API_B = "https://rfitness.rayolesoftware.com/api/finish-reading/"

HEADERS = {
    "Content-Type": "application/json"
}

# --- Updated enc and payload ---
OFFERS_PAYLOAD = {
    "enc": "1ShOOaT2pwmlLYnB6QqWGuz7K_bhD1BclNDS_y9ZU5ubJQDcvQ4wgwnZ8e5yuouHA40w5PJSGK0i7Y7Hs3h9yX1nmDTMOTMzF0vFMsoupJnTjDld0fF6XaZ08E5bByh4oHFqadIw8lRSVUzL7borVpsR_JHvFc6lgQwE_1A84PRmz0tcwBpPlTd8T9AKyL33Zt0zZDxYhU1h06LGiorwmW3PJz2y0MLmmvaxSwUi623FyDBFaUmIgfHZudZKTaKOMDN2deo1bcZ21W_TQlr-n3JXXvVO7FSnJTekwEFaVJU",
    "app_id": 14,
    "device_id": "43b3046d6d839eb9dc3719328dbcdafcae1c773e6f293b7cef98d133fba228dc"
}

# --- Cooldowns ---
cooldown_a_until = 0
cooldown_b_until = 0

# --- Track used refids to avoid duplicates ---
used_refids = set()

# --- Fetch latest offers and extract new refids ---
def fetch_refids():
    try:
        r = requests.post(LIST_OFFERS_API, headers=HEADERS, json=OFFERS_PAYLOAD, timeout=10)
        offers = r.json()
    except Exception as e:
        print(f"[OFFERS] Error fetching offers: {e}")
        return []

    new_refids = []
    for offer in offers:
        offer_link = offer.get("offer_link")
        if not offer_link:
            continue
        # Extract refid from URL
        match = re.search(r"refid=([^&]+)", offer_link)
        if match:
            refid = match.group(1)
            if refid not in used_refids:
                used_refids.add(refid)
                new_refids.append(refid)
    return new_refids

# --- API calls ---
def try_api_a(refid):
    global cooldown_a_until
    payload = {"refid": refid}
    try:
        r = requests.post(API_A, headers=HEADERS, json=payload, timeout=10)
        resp = r.json()
    except Exception as e:
        print(f"[API A] Error: {e}")
        return False

    if resp.get("message") == "ok":
        print(f"[API A] ✅ Success for refid")
        return True
    elif resp.get("message") == "Failure":
        cooldown_a_until = time.time() + 120
        print(f"[API A] ⏳ Cooldown 120s")
    elif resp.get("message") == "Invalid request":
        print(f"[API A] ❌ Invalid refid")
    else:
        print(f"[API A] ⚠️ Unknown response: {resp}")
    return False

def try_api_b(refid):
    global cooldown_b_until
    payload = {
        "refid": refid,
        "timestamp": int(time.time() * 1000),
        "nonce": ''.join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=12))
    }
    try:
        r = requests.post(API_B, headers=HEADERS, json=payload, timeout=10)
        resp = r.json()
    except Exception as e:
        print(f"[API B] Error: {e}")
        return False

    if resp.get("message") == "ok":
        print(f"[API B] ✅ Success for refid")
        return True
    elif resp.get("message", "").startswith("Please try again"):
        wait_ms = resp.get("wait_ms", 120000)
        cooldown_b_until = time.time() + (wait_ms / 1000)
        print(f"[API B] ⏳ Cooldown {wait_ms/1000:.1f}s")
    elif resp.get("message") == "Invalid request":
        print(f"[API B] ❌ Invalid refid")
    else:
        print(f"[API B] ⚠️ Unknown response: {resp}")
    return False

# --- Main loop ---
def main_loop():
    global cooldown_a_until, cooldown_b_until
    refids_queue = []

    while True:
        now = time.time()

        # Refill queue if empty or no offers
        if not refids_queue:
            refids_queue = fetch_refids()
            if not refids_queue:
                # Wait 60s only if no new refids at all
                wait_time = 60
                print(f"[INFO] No new refids, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue

        refid = refids_queue.pop(0)

        # Determine which API is free
        use_a = now >= cooldown_a_until
        use_b = now >= cooldown_b_until

        if use_a and use_b:
            api_choice = random.choice(['A', 'B'])
        elif use_a:
            api_choice = 'A'
        elif use_b:
            api_choice = 'B'
        else:
            # Both cooling -> wait shortest remaining
            wait_time = min(cooldown_a_until, cooldown_b_until) - now
            print(f"⏸️ Both APIs cooling, waiting {wait_time:.1f}s")
            refids_queue.insert(0, refid)  # put back
            time.sleep(wait_time)
            continue

        # Send to the chosen API
        if api_choice == 'A':
            print(f"[INFO] Sending refid to API A")
            success = try_api_a(refid)
        else:
            print(f"[INFO] Sending refid to API B")
            success = try_api_b(refid)

        # If refid was finished (success), fetch new refids immediately
        if success:
            print("[INFO] Offer finished, fetching new refids immediately...")
            refids_queue = fetch_refids()

        # Short delay before next iteration
        time.sleep(1)

if __name__ == "__main__":
    main_loop()
