# flight_data.py
class FlightData:
    def __init__(self, departure_city, dep_code, destination, dest_code, price, outbound_date, return_date, stop_overs=0, via_cities=None):
        self.departure_city = departure_city
        self.departure_airport_code = dep_code
        self.destination = destination
        self.destination_airport_code = dest_code
        self.price = price
        self.outbound_date = outbound_date
        self.return_date = return_date
        self.stop_overs = stop_overs
        self.via_cities = via_cities or []
