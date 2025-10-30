# customer.py
import os
from dotenv import load_dotenv
from data_manager import DataManager

load_dotenv()

class Customer:
    def __init__(self):
        self.first_name = ""
        self.last_name = ""
        self.email = ""

    def register(self):
        print("Welcome to Nicole's Flight Club.")
        print("We find the best flight deals and email you.")
        self.first_name = input("What is your first name? \n")
        self.last_name = input("What is your last name? \n")
        email = ""
        confirm_email = ""
        while email != confirm_email:
            email = input("What is your email address? \n")
            confirm_email = input("Type your email address again for confirmation: \n")
            if email != confirm_email:
                print("Please provide your email address again!")
        self.email = email
        print("Welcome to the club!")

# if you want to run registration standalone:
if __name__ == "__main__":
    SHEETY_ENDPOINT = os.getenv("SHEETY_PRICES_ENDPOINT")
    SHEETY_BEARER_TOKEN = os.getenv("SHEETY_BEARER_TOKEN")
    data_manager = DataManager(SHEETY_ENDPOINT, SHEETY_BEARER_TOKEN)

    new_customer = Customer()
    new_customer.register()
    result = data_manager.add_user(new_customer)
    print("Added user:", result)
