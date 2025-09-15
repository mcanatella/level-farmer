import json
import logging
import requests

logger = logging.getLogger(__name__)


class Orders:
    def __init__(self, base_url, jwt_token):
        self.base_url = base_url
        self.jwt_token = jwt_token

    def place(self, **payload):
        url = f"{self.base_url}/api/Order/place"

        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
        }

        logger.info(json.dumps({"event": "place_request", "args": payload}))

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        order_id = response.json()["orderId"]

        return order_id

    def search_open(self, **payload):
        url = f"{self.base_url}/api/Order/searchOpen"

        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
        }

        logger.debug(json.dumps({"event": "search_open_request", "args": payload}))

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        orders = response.json()["orders"]

        return orders

    def cancel(self, **payload):
        url = f"{self.base_url}/api/Order/cancel"

        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
        }

        logger.info(json.dumps({"event": "cancel_request", "args": payload}))

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
