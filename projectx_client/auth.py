import requests


class Auth:
    def __init__(self, base_url, username, api_key):
        self.base_url = base_url
        self.username = username
        self.api_key = api_key
        self.jwt_token = None

    def login(self):
        url = f"{self.base_url}/api/Auth/loginKey"

        payload = {"userName": self.username, "apiKey": self.api_key}

        response = requests.post(url, json=payload)
        response.raise_for_status()

        self.jwt_token = response.json()["token"]

        return self.jwt_token
