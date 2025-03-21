import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# Function to calculate RSI
def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Streamlit app details
st.set_page_config(page_title="Pair Trading Backtesting", layout="wide")

with st.sidebar:
    st.title("Pair Trading Backtesting")
    # Input for two stock tickers
    ticker1 = st.text_input("Enter the first stock ticker (e.g. AAPL)", "AAPL")
    ticker2 = st.text_input("Enter the second stock ticker (e.g. MSFT)", "MSFT")
    # Input for lookback period
    lookback_period = st.number_input("Enter lookback period for z-score calculation", min_value=1, value=30)
    # Input for RSI period
    rsi_period = st.number_input("Enter RSI period", min_value=1, value=14)
    # Input for backtesting period
    backtest_start_date = st.date_input("Select backtesting start date")
    backtest_end_date = st.date_input("Select backtesting end date")
    # Input for trade entry and exit deviations
    entry_deviation = st.number_input("Enter trade entry deviation (e.g., 2.5)", value=2.5)
    exit_deviation = st.number_input("Enter trade exit deviation (e.g., 1.5)", value=1.5)
    button = st.button("Run Backtest")

# If Run Backtest button is clicked
if button:
    if not ticker1.strip() or not ticker2.strip():
        st.error("Please provide valid stock tickers for both fields.")
    elif backtest_start_date > backtest_end_date:
        st.error("Backtesting start date must be before end date.")
    else:
        try:
            with st.spinner('Fetching data and running backtest...'):
                # Fetch data for both tickers
                stock1 = yf.Ticker(ticker1)
                stock2 = yf.Ticker(ticker2)

                # Fetch historical data for the backtesting period
                history1 = stock1.history(start=backtest_start_date, end=backtest_end_date, interval="1d")
                history2 = stock2.history(start=backtest_start_date, end=backtest_end_date, interval="1d")

                # Align the data by date
                aligned_data = pd.DataFrame({
                    'Date': history1.index,
                    f'{ticker1}_Close': history1['Close'],
                    f'{ticker2}_Close': history2['Close']
                }).dropna()

                # Calculate the ratio between the two stocks
                aligned_data['Ratio'] = aligned_data[f'{ticker1}_Close'] / aligned_data[f'{ticker2}_Close']

                # Calculate the z-score of the ratio
                aligned_data['Ratio_Mean'] = aligned_data['Ratio'].rolling(window=lookback_period).mean()
                aligned_data['Ratio_Std'] = aligned_data['Ratio'].rolling(window=lookback_period).std()
                aligned_data['Z-Score'] = (aligned_data['Ratio'] - aligned_data['Ratio_Mean']) / aligned_data['Ratio_Std']

                # Calculate RSI of the spread
                aligned_data['RSI'] = calculate_rsi(aligned_data['Z-Score'], period=rsi_period)

                # Backtesting logic
                aligned_data['Position'] = 0
                aligned_data['Trade'] = 0
                in_position = False

                for i in range(len(aligned_data)):
                    if not in_position and aligned_data['Z-Score'].iloc[i] > entry_deviation:
                        aligned_data['Position'].iloc[i] = -1  # Short the spread
                        aligned_data['Trade'].iloc[i] = 1  # Trade entry
                        in_position = True
                    elif not in_position and aligned_data['Z-Score'].iloc[i] < -entry_deviation:
                        aligned_data['Position'].iloc[i] = 1  # Long the spread
                        aligned_data['Trade'].iloc[i] = 1  # Trade entry
                        in_position = True
                    elif in_position and abs(aligned_data['Z-Score'].iloc[i]) < exit_deviation:
                        aligned_data['Position'].iloc[i] = 0  # Exit the trade
                        aligned_data['Trade'].iloc[i] = -1  # Trade exit
                        in_position = False

                # Display results
                st.subheader("Backtesting Results")
                st.dataframe(aligned_data[['Date', f'{ticker1}_Close', f'{ticker2}_Close', 'Ratio', 'Z-Score', 'RSI', 'Position', 'Trade']])

                # Plot the Z-Score and trades
                st.subheader("Z-Score and Trades")
                st.line_chart(aligned_data.set_index('Date')[['Z-Score']])
                st.write("Trades:")
                st.write(aligned_data[aligned_data['Trade'] != 0][['Date', 'Trade']])

        except Exception as e:
            st.exception(f"An error occurred: {e}")
