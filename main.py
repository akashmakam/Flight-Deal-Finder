# main.py
# Orchestrates DataManager, FlightSearch, NotificationManager

import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

from data_manager import DataManager
from flight_search import FlightSearch
from notification_manager import NotificationManager

# Use the exact names you have in your .env
SHEETY_ENDPOINT = os.getenv("SHEETY_PRICES_ENDPOINT")
SHEETY_BEARER_TOKEN = os.getenv("SHEETY_BEARER_TOKEN")

if not SHEETY_ENDPOINT:
    raise RuntimeError("SHEETY_PRICES_ENDPOINT not found in environment. Add it to your .env")

data_manager = DataManager(SHEETY_ENDPOINT, SHEETY_BEARER_TOKEN)

# Initialize FlightSearch with Amadeus settings from .env
AM_TOKEN_ENDPOINT = os.getenv("TOKEN_ENDPOINT")
AM_API_KEY = os.getenv("API_KEY")
AM_API_SECRET = os.getenv("API_SECRET")
AM_IATA_ENDPOINT = os.getenv("IATA_ENDPOINT")
AM_FLIGHT_ENDPOINT = os.getenv("FLIGHT_ENDPOINT")

flight_search = FlightSearch(
    token_endpoint=AM_TOKEN_ENDPOINT,
    client_id=AM_API_KEY,
    client_secret=AM_API_SECRET,
    iata_endpoint=AM_IATA_ENDPOINT,
    flight_endpoint=AM_FLIGHT_ENDPOINT
)

# NotificationManager — email via SMTP (optional). If not set, we just print alerts.
notification_manager = NotificationManager(
    from_email=os.getenv("FROM_EMAIL"),
    password=os.getenv("EMAIL_PASSWORD"),
    smtp=os.getenv("SMTP")
)

# Fetch data from Sheety
flight_data = data_manager.get_flight_data()
users = data_manager.get_users()

if not flight_data:
    print("No flight rows found in Sheety. Exiting.")
    exit()

# Example origin — change to your origin if needed
ORIGIN_IATA = os.getenv("ORIGIN_CITY_IATA", "SIN")  # default BLR if not set

for entry in flight_data:
    # Some sheets use blank string - normalize key names
    city = entry.get("city") or entry.get("City") or entry.get("cityName")
    iata_code = entry.get("iataCode") or entry.get("IATA") or entry.get("iata")

    # If iata missing, query Amadeus
    if not iata_code:
        print(f"Fetching IATA code for {city} ...")
        code = flight_search.get_iata_code(city)
        if code:
            iata_code = code
            entry["iataCode"] = iata_code
            # Update sheet with the new code (some spreadsheets expect a specific structure)
            try:
                data_manager.update_flight_data(entry.get("id"), entry)
            except Exception as e:
                print("Warning: could not update Sheety with IATA code:", e)
        else:
            print(f"Could not find IATA code for {city}, skipping.")
            continue

    # Search flights from ORIGIN_IATA to iata_code
    print(f"Searching flights: {ORIGIN_IATA} -> {iata_code} for {city}")
    flight = flight_search.search_flights(
        origin=ORIGIN_IATA,
        destination=iata_code,
        date_from=datetime.now(),
        date_to=datetime.now() + timedelta(weeks=26),
        max_stops=0
    )

    if not flight:
        print(f"No flights found for {city} ({iata_code}).")
        continue

    lowest_price = entry.get("lowestPrice") or entry.get("lowest_price") or entry.get("price")
    if lowest_price is None:
        print(f"No lowestPrice set for {city}; skipping price comparison.")
        continue

    # Compare prices (Amadeus returns numeric price)
    try:
        if float(flight.price) <= float(lowest_price):
            google_flight_link = f"https://www.google.com/flights?hl=en#flt={flight.departure_airport_code}.{flight.destination_airport_code}.{flight.outbound_date}*{flight.destination_airport_code}.{flight.departure_airport_code}.{flight.return_date}"

            email_msg = f"Subject: Low price alert! \n\n" \
                        f"Low price alert! Only {flight.price} to fly from " \
                        f"{flight.departure_city}-{flight.departure_airport_code} to " \
                        f"{flight.destination}-{flight.destination_airport_code}, from " \
                        f"{flight.outbound_date} to {flight.return_date}. \n"

            if flight.stop_overs == 0:
                email_msg += "Direct flight. \n"
            else:
                email_msg += f"Flight with {flight.stop_overs} stop over(s), via {', '.join(flight.via_cities)}. \n"

            email_msg += f"{google_flight_link}"
            print(email_msg)

            # send email to all users (if NotificationManager configured), else print
            for user in users:
                to_email = user.get("email") or user.get("Email")
                if notification_manager.can_send():
                    notification_manager.send_email(message=email_msg, to_email=to_email)
                else:
                    print(f"[DRY-RUN] Would email {to_email}:")
                    print(email_msg)
        else:
            print(f"Price {flight.price} higher than threshold {lowest_price} for {city}.")
    except Exception as e:
        print("Error during price comparison or sending notifications:", e)
