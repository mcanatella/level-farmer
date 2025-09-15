import requests


class MarketData:
    def __init__(self, base_url, jwt_token):
        self.base_url = base_url
        self.jwt_token = jwt_token

    def bars(self, **payload):
        url = f"{self.base_url}/api/History/retrieveBars"

        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        bars = response.json()["bars"]

        return bars
