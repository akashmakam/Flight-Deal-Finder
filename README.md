# ✈️ Flight Deal Finder

A Python automation project that searches for cheap flight deals using the **Amadeus API**, stores and retrieves data via **Google Sheets (Sheety API)**, and sends instant **WhatsApp alerts through Twilio** when prices drop below your preferred threshold.

---

## 🧠 Overview

The Flight Deal Finder automates the process of checking flight prices daily so you don’t have to!  
It looks up the cheapest available flights from **Singapore (SIN)** to your selected destinations and alerts you via **WhatsApp or SMS** when it finds a better deal than your set price.

---

## ⚙️ Tech Stack

| Component | Purpose |
|------------|----------|
| **Python 3.12+** | Main programming language |
| **Amadeus API** | Fetches flight data and prices |
| **Sheety API** | Connects to Google Sheets for storing destinations and price limits |
| **Twilio API** | Sends WhatsApp/SMS alerts for low-price deals |
| **dotenv** | Loads API keys securely from `.env` |

---

## 🗂️ Project Structure

python_flight_deal_finder/
│
├── main.py # Controls the overall workflow
├── data_manager.py # Handles Sheety (Google Sheets) integration
├── flight_search.py # Connects to Amadeus API for flight data
├── notification_manager.py # Sends WhatsApp/SMS alerts using Twilio
├── flight_data.py # (Optional) Defines a simple data class for flights
├── .env # Stores all API keys and endpoints (not shared publicly)
└── README.md # Project documentation


---

## 🔐 Environment Setup

1. Create a file named `.env` in your project root.
2. Replace sensitive values as needed in .env file

## 🚀 How to Run

1. Install dependencies
pip install requests python-dotenv twilio


2. Run the main script
python main.py

The program will:
Fetch destination data from Google Sheets via Sheety.
Search for flights from your departure location to each destination.
Compare prices against your preset lowest price.
Send a WhatsApp alert if a cheaper deal is found.
