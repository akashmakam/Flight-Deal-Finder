# data_manager.py
import requests
import json


class DataManager:
    """
    A DataManager that accepts either:
      - full prices endpoint (endswith /prices)
      - or a base endpoint (without /prices) — it appends /prices when needed
    """

    def __init__(self, endpoint, token=None):
        if not endpoint:
            raise ValueError("Sheety endpoint must be provided to DataManager")

        self.endpoint = endpoint.rstrip("/")  # normalize
        self.bearer_token = token
        # prepare headers: if token available, add Authorization, else send only content-type
        if self.bearer_token:
            self.header = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.bearer_token}"
            }
        else:
            self.header = {"Content-Type": "application/json"}

    def _prices_url(self):
        # If the endpoint already appears to point to prices resource, use it.
        if self.endpoint.endswith("/prices"):
            return self.endpoint
        # If endpoint is the full api root that includes the project and resource
        # allow both endpoint that ends with /flightDeals or /flightDeals/prices
        if self.endpoint.endswith("/flightDeals"):
            # append prices
            return f"{self.endpoint}/prices"
        # fallback
        return f"{self.endpoint}/prices"

    def get_flight_data(self):
        url = self._prices_url()
        response = requests.get(url=url, headers=self.header)
        response.raise_for_status()
        result = response.json()
        # Sheety responses usually return a key 'prices' containing list
        # but in some exported sheets it may differ. Be defensive:
        if isinstance(result, dict):
            for k in ("prices", "Prices", "data"):
                if k in result:
                    return result[k]
        # if it's directly a list:
        if isinstance(result, list):
            return result
        # otherwise return raw result
        return result

    def update_flight_data(self, row_id, payload):
        url = f"{self._prices_url()}/{row_id}"
        # Sheety expects the payload structure to match sheet name (usually 'price')
        body = {"price": payload}
        response = requests.put(url=url, json=body, headers=self.header)
        response.raise_for_status()
        return response.json()

    def add_user(self, user):
        url = self.endpoint.rstrip("/") + "/users"
        body = {
            "user": {
                "firstName": user.first_name,
                "lastName": user.last_name,
                "email": user.email
            }
        }
        response = requests.post(url=url, json=body, headers=self.header)
        response.raise_for_status()
        return response.json()

    def get_users(self):
        url = self.endpoint.rstrip("/") + "/users"
        try:
            response = requests.get(url=url, headers=self.header)
            response.raise_for_status()
            result = response.json()
            # common key 'users'
            if isinstance(result, dict) and "users" in result:
                return result["users"]
            # fallback detect list
            if isinstance(result, list):
                return result
            return []
        except Exception:
            # if no users sheet, return empty list
            return []
