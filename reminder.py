import requests


def send_test_message():
    url = "https://api.fonnte.com/send"
    payload = {
        "target": "62895616199398",  # Nomor tujuan dalam format internasional
        "message": "Tes pengiriman pesan WhatsApp dari Fonnte.",
    }
    headers = {
        "Authorization": "wsyuepP_Up4gtgdYYmT4",  # Masukkan API Key Fonnte yang valid
    }

    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        print(f"Pesan terkirim: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")


send_test_message()
