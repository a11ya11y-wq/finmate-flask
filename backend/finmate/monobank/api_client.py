import requests
from  cryptography.fernet import Fernet
from flask import current_app



BASE_URL = "https://api.monobank.ua"

class MonoAPI:
    def __init__(self, encrypted_token_bytes):
        if not encrypted_token_bytes:
            raise ValueError("API token is required")

        try:
            key = current_app.config['ENCRYPTION_KEY']
            cipher_suite = Fernet(key)
            decrypted_token_bytes = cipher_suite.decrypt(encrypted_token_bytes)
            self.api_token = decrypted_token_bytes.decode()
        except Exception as e:
            print(f"Failed to decrypt token: {e}")
            raise ValueError("Invalid or corrupted API token")


        self.headers = {
            'X-Token': self.api_token
        }


    def _make_request(self, endpoint):
        try:
            response = requests.get(f'{BASE_URL}{endpoint}', headers=self.headers)
            return response.json()
        except Exception as e:
            print(f'Error: {e}')
            raise requests.RequestException(f"API Request failed: {e}")

    def get_client_info(self):
        return self._make_request("/personal/client-info")


    def get_transactions(self, account_id, from_date_timestamp):
        endpoint = f"/personal/statement/{account_id}/{from_date_timestamp}"
        return self._make_request(endpoint)


