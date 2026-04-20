import requests
from django.conf import settings

class NovaPoshtaClient:
    API_URL = "https://api.novaposhta.ua/v2.0/json/"

    def __init__(self, api_key):
        self.api_key = api_key

    def get_settlements(self, search_text):
        """Пошук міст/населених пунктів"""
        payload = {
            "apiKey": self.api_key,
            "modelName": "Address",
            "calledMethod": "searchSettlements",
            "methodProperties": {
                "CityName": search_text,
                "Limit": 10
            }
        }
        response = requests.post(self.API_URL, json=payload)
        data = response.json()
        
        # Повертаємо список адрес (вони лежать у data['data'][0]['Addresses'])
        if data.get('success'):
            return data['data'][0]['Addresses']
        return []

# Створюємо об'єкт для використання в коді
# В settings.py запишіть NP_API_KEY = "ваш_ключ"
np_client = NovaPoshtaClient(settings.NP_API_KEY)