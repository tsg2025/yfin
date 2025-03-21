import streamlit as st
import yfinance as yf
import pandas as pd

# Streamlit app details
st.set_page_config(page_title="Daily Historical Stock Prices", layout="wide")

with st.sidebar:
    st.title("Daily Historical Stock Prices")
    # Input for two stock tickers
    ticker1 = st.text_input("Enter the first stock ticker (e.g. AAPL)", "AAPL")
    ticker2 = st.text_input("Enter the second stock ticker (e.g. MSFT)", "MSFT")
    # Single date range for both stocks
    start_date = st.date_input("Select start date")
    end_date = st.date_input("Select end date")
    button = st.button("Submit")

# If Submit button is clicked
if button:
    if not ticker1.strip() or not ticker2.strip():
        st.error("Please provide valid stock tickers for both fields.")
    elif start_date > end_date:
        st.error("Start date must be before end date.")
    else:
        try:
            with st.spinner('Fetching data...'):
                # Fetch data for both tickers
                stock1 = yf.Ticker(ticker1)
                stock2 = yf.Ticker(ticker2)

                # Get stock info
                info1 = stock1.info
                info2 = stock2.info

                # Display stock names
                st.subheader(f"{ticker1} - {info1.get('longName', 'N/A')}")
                st.subheader(f"{ticker2} - {info2.get('longName', 'N/A')}")

                # Fetch historical data for both stocks
                history1 = stock1.history(start=start_date, end=end_date, interval="1d")
                history2 = stock2.history(start=start_date, end=end_date, interval="1d")

                # Reset index and ensure the Date column is in datetime format
                history1.reset_index(inplace=True)
                history1["Date"] = pd.to_datetime(history1["Date"]).dt.strftime("%Y-%m-%d")
                history2.reset_index(inplace=True)
                history2["Date"] = pd.to_datetime(history2["Date"]).dt.strftime("%Y-%m-%d")

                # Display historical data side by side
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader(f"{ticker1} Daily Historical Data")
                    st.dataframe(history1[["Date", "Open", "High", "Low", "Close", "Volume"]])
                with col2:
                    st.subheader(f"{ticker2} Daily Historical Data")
                    st.dataframe(history2[["Date", "Open", "High", "Low", "Close", "Volume"]])

        except Exception as e:
            st.exception(f"An error occurred: {e}")
