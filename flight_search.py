# flight_search.py hi
import requests
import time
from flight_data import FlightData


class FlightSearch:
    """
    Minimal Amadeus integration:
      - get_access_token() : obtains Bearer token using client_id & client_secret
      - get_iata_code(city) : uses Amadeus reference-data locations endpoint to find city code
      - search_flights(...) : queries flight-offers endpoint for cheapest option and builds FlightData
    """

    def __init__(self, token_endpoint, client_id, client_secret, iata_endpoint, flight_endpoint):
        self.token_endpoint = token_endpoint
        self.client_id = client_id
        self.client_secret = client_secret
        self.iata_endpoint = iata_endpoint
        self.flight_endpoint = flight_endpoint
        self._token = None
        self._token_expiry = 0

    def get_access_token(self):
        # cache token until expiry
        now = time.time()
        if self._token and now < self._token_expiry - 10:
            return self._token

        if not self.token_endpoint or not self.client_id or not self.client_secret:
            raise RuntimeError("Amadeus credentials missing in environment")

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        resp = requests.post(self.token_endpoint, data=data)
        resp.raise_for_status()
        j = resp.json()
        self._token = j.get("access_token")
        expires_in = j.get("expires_in", 1800)
        self._token_expiry = now + int(expires_in)
        return self._token

    def _auth_header(self):
        token = self.get_access_token()
        return {"Authorization": f"Bearer {token}"}

    def get_iata_code(self, city_name):
        """
        Query Amadeus reference-data locations endpoint for a city code.
        city_name: str or dict {"term": "Paris"}
        """
        if isinstance(city_name, dict):
            term = city_name.get("term")
        else:
            term = city_name

        if not term:
            return None

        params = {"keyword": term, "subType": "CITY", "page[limit]": 10}
        resp = requests.get(self.iata_endpoint, headers=self._auth_header(), params=params)
        resp.raise_for_status()
        j = resp.json()
        data = j.get("data") or []
        if not data:
            return None
        # Choose first entry's iataCode or 'iataCode' in 'iataCode' field
        first = data[0]
        # Amadeus returns IATA in 'iataCode' sometimes under 'iataCode'
        code = first.get("iataCode") or first.get("address", {}).get("iataCode")
        # as fallback check 'iataCode' inside 'iataCode' nested
        if not code and isinstance(first.get("iataCodes"), list):
            code = first["iataCodes"][0]
        return code

    def search_flights(self, origin, destination, date_from, date_to, max_stops=0):
        """
        Uses Amadeus /v2/shopping/flight-offers
        We will request the cheapest available within date range.
        Returns FlightData or None.
        """
        # Amadeus expects dates in YYYY-MM-DD
        dep_from = date_from.strftime("%Y-%m-%d")
        dep_to = date_to.strftime("%Y-%m-%d")

        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": dep_from,
            "returnDate": (date_from + (date_to - date_from) / 2).strftime("%Y-%m-%d"),  # pick a reasonable return date midpoint
            "adults": 1,
            "nonStop": "true" if max_stops == 0 else "false",
            "currencyCode": "EUR",
            "max": 5
        }

        resp = requests.get(self.flight_endpoint, headers=self._auth_header(), params=params)
        # If Amadeus returns 401 or similar, raise for debug
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            # Print response to help debug
            print("Amadeus flight search failed:", resp.status_code, resp.text)
            return None

        j = resp.json()
        # Data structure may vary. Amadeus returns 'data' list
        items = j.get("data") or []
        if not items:
            return None

        # Choose the first offer and attempt to extract price and route info
        offer = items[0]
        # price lives under offer['price']['total']
        price = None
        try:
            price = float(offer.get("price", {}).get("total"))
        except Exception:
            # fallback: if it is string with decimals
            try:
                price = float(offer.get("price", {}).get("total", "0"))
            except Exception:
                price = None

        # route parsing: Amadeus v2 flightOffers has itineraries -> segments with departure/arrival
        try:
            itineraries = offer.get("itineraries", [])
            # outbound = itineraries[0], inbound = itineraries[1] (if round-trip)
            outbound = itineraries[0] if len(itineraries) > 0 else None
            inbound = itineraries[1] if len(itineraries) > 1 else None

            # get dates and airports from first/last segments
            def extract_trip_info(itin):
                if not itin:
                    return None, None, []
                segments = itin.get("segments", [])
                dep_seg = segments[0]
                arr_seg = segments[-1]
                dep_airport = dep_seg.get("departure", {}).get("iataCode")
                arr_airport = arr_seg.get("arrival", {}).get("iataCode")
                dep_city = dep_seg.get("departure", {}).get("iataCode")  # Amadeus doesn't always provide city name; keep code
                arr_city = arr_seg.get("arrival", {}).get("iataCode")
                dep_date = dep_seg.get("departure", {}).get("at", "").split("T")[0]
                arr_date = arr_seg.get("arrival", {}).get("at", "").split("T")[0]
                via = []
                # collect intermediate airports (excluding origin/destination)
                if len(segments) > 1:
                    for seg in segments[1:-1]:
                        via.append(seg.get("arrival", {}).get("iataCode"))
                return dep_airport, arr_airport, dep_date, arr_date, via

            dep_airport, dest_airport, outbound_date, _, via_out = extract_trip_info(outbound)
            _, _, _, return_date, via_in = extract_trip_info(inbound)

            # Compose FlightData (some fields may be same due to missing city name)
            flight = FlightData(
                departure_city=dep_airport or origin,
                dep_code=dep_airport or origin,
                destination=dest_airport or destination,
                dest_code=dest_airport or destination,
                price=price,
                outbound_date=outbound_date or dep_from,
                return_date=return_date or dep_from,
                stop_overs=len(via_out) + len(via_in),
                via_cities=(via_out + via_in)
            )
            print(f"{flight.destination}: €{flight.price}")
            return flight
        except Exception as e:
            print("Error parsing Amadeus response:", e)
            return None
