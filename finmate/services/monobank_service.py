import requests

BASE_URL = "https://api.monobank.ua"

class MonoAPI:
    def __init__(self, api_token):
        self.headers = {
            'X-Token': api_token
        }


    def _make_request(self, endpoint):
        try:
            response = requests.get(f'{BASE_URL}{endpoint}', headers=self.headers)
            return response.json()
        except Exception as e:
            print(f'Error: {e}')
            return None


    def get_client_info(self):
        return self._make_request("/personal/client-info")


    def get_transactions(self, account_id, from_date_timestamp):
        endpoint = f"/personal/statement/{account_id}/{from_date_timestamp}"
        return self._make_request(endpoint)

client = MonoAPI(api_token='u-qhw2Pd8FudBP7D6Kse8Ce7gZab9nKfB9AD6UScl47Q')
