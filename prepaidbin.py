from random import randint as r
from random import choice as c
from requests import Session as s
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Generate a random BIN based on card types
def gen_bin():
    visa = "4" + "".join(str(r(0, 9)) for _ in range(5))
    mastercard = "5" + "".join(str(r(0, 9)) for _ in range(5))
    amex = "3" + "".join(str(r(0, 9)) for _ in range(5))
    discover = "6" + "".join(str(r(0, 9)) for _ in range(5))
    diners = "36" + "".join(str(r(0, 9)) for _ in range(4))
    bins = [visa, mastercard, amex, discover, diners]
    return c(bins)

# Validate BIN length
def validate_bin_length(bin):
    return len(bin) == 6

# Generate multiple BINs
def generate_multiple_bins(count):
    return [gen_bin() for _ in range(count)]

# Lookup BIN details from the API
def bin_lookup(bin):
    api = f"https://bins.antipublic.cc/bins/{bin}"
    try:
        response = s().get(api).json()
        if not is_valid_response(response):
            return {"error": "Invalid or incomplete data from API"}
        return response
    except Exception as e:
        return {"error": str(e)}

# Check if a response is valid (avoid Unknown results)
def is_valid_response(response):
    required_keys = ["bin", "type", "level", "country_name", "bank"]
    return all(response.get(key) for key in required_keys)

# Check if the BIN is prepaid or not
def check_prepaid(response):
    try:
        return response.get("prepaid", False)  # Returns True if prepaid, else False
    except:
        return False

# Format response for Telegram
def format_response(response):
    try:
        prepaid_status = "✅ Prepaid" if check_prepaid(response) else "❌ Non-Prepaid"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""
━━━━━━━━━━━━━━━━━━━━━━━
<b>🔍 BIN Lookup Result</b>
━━━━━━━━━━━━━━━━━━━━━━━
<b>💳 BIN » </b><code>{response["bin"]}</code>
<b>📋 Type » </b>{response["type"]}
<b>⭐ Level » </b>{response["level"]}
<b>💡 Prepaid Status » </b>{prepaid_status}
<b>🌍 Country » </b>{response["country_name"]} {response.get("country_flag", "")}
<b>🏦 Bank » </b>{response["bank"]}
━━━━━━━━━━━━━━━━━━━━━━━
<b>⏱️ Checked On » </b>{now}
<b>📢 By » @WerewolfDemonInfo</b>
━━━━━━━━━━━━━━━━━━━━━━━
"""
    except Exception as e:
        return f"⚠️ Error formatting response: {str(e)}"

# Send the message to Telegram (only for prepaid BINs)
def send_message(token, chat_id, bin):
    response = bin_lookup(bin)
    if "error" in response:
        log_error(response["error"])
        return  # Skip invalid responses

    # Check if the BIN is prepaid
    if check_prepaid(response):
        try:
            text = format_response(response)
            api = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={text}&parse_mode=HTML"
            s().get(api)
            log_activity(response["bin"], "Prepaid BIN Found - Message Sent")
        except Exception as e:
            log_error(f"Error sending message: {e}")
    else:
        log_activity(bin, "Non-Prepaid BIN - Skipped")

# Log successful activity
def log_activity(bin, status):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] Checked BIN: {bin} | Status: {status}")

# Log errors
def log_error(message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] ERROR: {message}")

# Save results to a file
def save_to_file(bin, response):
    with open("bin_results.txt", "a") as file:
        file.write(f"BIN: {bin}\n")
        file.write(f"Response: {response}\n\n")

# Handle API rate limits
def handle_rate_limits(api_call, max_retries=3):
    retries = 0
    while retries < max_retries:
        response = api_call()
        if response.status_code != 429:  # 429 is the status code for too many requests
            return response
        retries += 1
        time.sleep(2 ** retries)  # Exponential backoff
    return {"error": "Max retries reached"}

# Send bulk messages (only for prepaid BINs)
def send_bulk_messages(token, chat_id, bins):
    for bin in bins:
        send_message(token, chat_id, bin)

# Log activity to a file
def log_activity_to_file(bin, status):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("activity_logs.txt", "a") as file:
        file.write(f"[{now}] Checked BIN: {bin} | Status: {status}\n")

# Handle exceptions
def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_error(f"Exception in {func.__name__}: {e}")
    return wrapper

# Main program with ThreadPoolExecutor
if __name__ == "__main__":
    token = "6708572604:AAEH9547KB_QOr-P0-W1Tbl6-T6gcjBP2HM"
    chat_id = "-1002311212181"
    max_workers = 10  # Reduce the number of threads for stability
    
    start = ThreadPoolExecutor(max_workers=max_workers)
    while True:
        bin = gen_bin()
        log_activity(bin, "Processing")
        start.submit(send_message, token, chat_id, bin)