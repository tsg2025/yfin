import streamlit as st
import yfinance as yf
import pandas as pd

# Streamlit app details
st.set_page_config(page_title="Daily Historical Stock Prices", layout="wide")
with st.sidebar:
    st.title("Daily Historical Stock Prices")
    ticker = st.text_input("Enter a stock ticker (e.g. AAPL)", "AAPL")
    start_date = st.date_input("Select start date")  # User selects start date
    end_date = st.date_input("Select end date")  # User selects end date
    button = st.button("Submit")

# If Submit button is clicked
if button:
    if not ticker.strip():
        st.error("Please provide a valid stock ticker.")
    elif start_date > end_date:
        st.error("Start date must be before end date.")
    else:
        try:
            with st.spinner('Fetching data...'):
                # Retrieve stock data
                stock = yf.Ticker(ticker)
                info = stock.info

                st.subheader(f"{ticker} - {info.get('longName', 'N/A')}")

                # Fetch daily historical data for the selected date range
                history = stock.history(start=start_date, end=end_date, interval="1d")

                # Format the Date column to show only YYYY-MM-DD
                history.reset_index(inplace=True)  # Convert the index (Date) to a column
                history["Date"] = history["Date"].dt.strftime("%Y-%m-%d")  # Format the date

                # Display historical data in a table
                st.subheader("Daily Historical Data")
                st.dataframe(history[["Date", "Open", "High", "Low", "Close", "Volume"]])  # Show only relevant columns

        except Exception as e:
            st.exception(f"An error occurred: {e}")
