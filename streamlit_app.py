import streamlit as st
import yfinance as yf
import pandas as pd

# Streamlit app details
st.set_page_config(page_title="Historical Stock Prices", layout="wide")
with st.sidebar:
    st.title("Historical Stock Prices")
    ticker = st.text_input("Enter a stock ticker (e.g. AAPL)", "AAPL")
    period = st.selectbox("Enter a time frame", ("1D", "5D", "1M", "6M", "YTD", "1Y", "5Y"), index=2)
    button = st.button("Submit")

# If Submit button is clicked
if button:
    if not ticker.strip():
        st.error("Please provide a valid stock ticker.")
    else:
        try:
            with st.spinner('Please wait...'):
                # Retrieve stock data
                stock = yf.Ticker(ticker)
                info = stock.info

                st.subheader(f"{ticker} - {info.get('longName', 'N/A')}")

                # Plot historical stock price data
                period_map = {
                    "1D": ("1d", "1h"),
                    "5D": ("5d", "1d"),
                    "1M": ("1mo", "1d"),
                    "6M": ("6mo", "1wk"),
                    "YTD": ("ytd", "1mo"),
                    "1Y": ("1y", "1mo"),
                    "5Y": ("5y", "3mo"),
                }
                selected_period, interval = period_map.get(period, ("1mo", "1d"))
                history = stock.history(period=selected_period, interval=interval)

                # Plot the historical closing prices
                chart_data = pd.DataFrame(history["Close"])
                st.line_chart(chart_data)

                # Format the Date column to show only YYYY-MM-DD
                history.reset_index(inplace=True)  # Convert the index (Date) to a column
                history["Date"] = history["Date"].dt.strftime("%Y-%m-%d")  # Format the date

                # Display historical data in a table
                st.subheader("Historical Data")
                st.dataframe(history[["Date", "Open", "High", "Low", "Close", "Volume"]])  # Show only relevant columns

        except Exception as e:
            st.exception(f"An error occurred: {e}")
