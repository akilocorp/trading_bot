import streamlit as st
import os
from dotenv import load_dotenv
import requests
import hmac
import hashlib
import time
import pandas as pd
from balance import get_balance
# --- Load Environment Variables ---
# This ensures all imported modules also have access
load_dotenv()

# Get environment variables
ROOSTOO_API_KEY = os.getenv('ROOSTOO_API_KEY')
ROOSTOO_API_SECRET = os.getenv('ROOSTOO_API_SECRET')
BASE_URL = os.getenv('BASE_URL')

# --- Import from your existing files ---
# Assumes utilities.py and trades.py are in the same directory
try:
    from utilities import get_server_timestamp, get_exchange_info
    from trades import query_order
except ImportError:
    st.error("Could not find 'utilities.py' or 'trades.py'. Make sure they are in the same directory.")
    st.stop()



# --- Data Loading Functions with Caching ---
# Cache data for 60 seconds to avoid hitting the API on every refresh
@st.cache_data(ttl=60)
def load_api_status():
    """Loads exchange info."""
    return get_exchange_info()

@st.cache_data(ttl=60)
def load_balance_data():
    """Loads account balance."""
    return get_balance()

@st.cache_data(ttl=60)
def load_open_orders():
    """Loads all pending orders."""
    # Query for all pairs, pending only
    return query_order(pair=None, pending_only=True)


# --- Streamlit UI ---

st.set_page_config(page_title="Roostoo Dashboard", layout="wide")
st.title("📈 Roostoo Trading Dashboard")

# Check for API keys
if not ROOSTOO_API_KEY or not ROOSTOO_API_SECRET or not BASE_URL:
    st.error("Missing environment variables (ROOSTOO_API_KEY, ROOSTOO_API_SECRET, BASE_URL). Please check your .env file.")
    st.stop()

# Manual refresh button
if st.button("Refresh Data"):
    st.cache_data.clear()

# --- 1. Load Data ---
api_info = load_api_status()
balance_data = load_balance_data()
open_orders_data = load_open_orders()

# --- 2. Process Data ---

# API Status
api_status_str = "Offline"
api_color = "🔴"
if api_info and api_info.get('IsRunning'):
    api_status_str = "Online"
    api_color = "🟢"

# Balance
balance_df = pd.DataFrame()
assets_held_count = 0

# Open Orders ("Coins we are trading")
open_orders_list = []
trading_pairs_count = 0
if open_orders_data and open_orders_data.get('Success'):
    open_orders_list = open_orders_data.get('OrderMatched', [])
    # Find unique pairs we are trading
    trading_pairs = set(order['Pair'] for order in open_orders_list)
    trading_pairs_count = len(trading_pairs)


# --- 3. Display Metrics ---
st.header("Key Metrics")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="API Status", value=f"{api_color} {api_status_str}")

with col2:
    st.metric(label="Assets Held", value=assets_held_count, help="Number of assets with a non-zero balance.")

with col3:
    st.metric(label="Active Trading Pairs", value=trading_pairs_count, help="Number of unique pairs with open orders.")


# --- 4. Display Details ---
st.divider()

# Account Balance
st.subheader("💰 Account Balance")
if balance_data:
    st.dataframe(balance_data, use_container_width=True)
else:
    st.info("No assets with a balance found.")

# Open Orders
st.subheader("📊 Open Orders")  
if open_orders_list:
    st.dataframe(open_orders_list, use_container_width=True)
elif open_orders_data and not open_orders_data.get('Success'):
    st.error(f"Error loading orders: {open_orders_data.get('ErrMsg')}")
else:
    st.info("No open orders found.")