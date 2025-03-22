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
                trades = []
                in_position = False
                entry_price_stock1 = None
                entry_price_stock2 = None
                entry_date = None
                trade_type = None
                max_loss = 0

                for i in range(len(aligned_data)):
                    if not in_position and aligned_data['Z-Score'].iloc[i] > entry_deviation:
                        # Enter Short Ratio trade
                        trade_type = "Short Ratio"
                        entry_price_stock1 = aligned_data[f'{ticker1}_Close'].iloc[i]
                        entry_price_stock2 = aligned_data[f'{ticker2}_Close'].iloc[i]
                        entry_date = aligned_data['Date'].iloc[i]
                        in_position = True
                        max_loss = 0
                    elif not in_position and aligned_data['Z-Score'].iloc[i] < -entry_deviation:
                        # Enter Long Ratio trade
                        trade_type = "Long Ratio"
                        entry_price_stock1 = aligned_data[f'{ticker1}_Close'].iloc[i]
                        entry_price_stock2 = aligned_data[f'{ticker2}_Close'].iloc[i]
                        entry_date = aligned_data['Date'].iloc[i]
                        in_position = True
                        max_loss = 0
                    elif in_position and abs(aligned_data['Z-Score'].iloc[i]) < exit_deviation:
                        # Exit trade
                        exit_price_stock1 = aligned_data[f'{ticker1}_Close'].iloc[i]
                        exit_price_stock2 = aligned_data[f'{ticker2}_Close'].iloc[i]
                        exit_date = aligned_data['Date'].iloc[i]

                        # Calculate profit percentage
                        if trade_type == "Long Ratio":
                            profit_pct = ((exit_price_stock1 - entry_price_stock1) / entry_price_stock1) - \
                                         ((exit_price_stock2 - entry_price_stock2) / entry_price_stock2)
                        elif trade_type == "Short Ratio":
                            profit_pct = ((entry_price_stock2 - exit_price_stock2) / entry_price_stock2) - \
                                         ((entry_price_stock1 - exit_price_stock1) / entry_price_stock1)

                        # Calculate holding period
                        holding_period = (exit_date - entry_date).days

                        # Add trade to trades list
                        trades.append({
                            'Entry Date': entry_date,
                            'Exit Date': exit_date,
                            'Trade Type': trade_type,
                            'Profit %': profit_pct * 100,
                            'Holding Period': holding_period,
                            'Max Loss': max_loss * 100
                        })

                        # Reset trade variables
                        in_position = False
                        entry_price_stock1 = None
                        entry_price_stock2 = None
                        entry_date = None
                        trade_type = None
                        max_loss = 0

                    # Update max loss during the trade
                    if in_position:
                        current_profit = 0
                        if trade_type == "Long Ratio":
                            current_profit = ((aligned_data[f'{ticker1}_Close'].iloc[i] - entry_price_stock1) / entry_price_stock1) - \
                                             ((aligned_data[f'{ticker2}_Close'].iloc[i] - entry_price_stock2) / entry_price_stock2)
                        elif trade_type == "Short Ratio":
                            current_profit = ((entry_price_stock2 - aligned_data[f'{ticker2}_Close'].iloc[i]) / entry_price_stock2) - \
                                             ((entry_price_stock1 - aligned_data[f'{ticker1}_Close'].iloc[i]) / entry_price_stock1)
                        if current_profit < max_loss:
                            max_loss = current_profit

                # Convert trades list to a DataFrame
                trades_df = pd.DataFrame(trades)

                # Display the stock price, z-score, and RSI table
                st.subheader("Stock Prices, Z-Score, and RSI")
                st.dataframe(aligned_data[['Date', f'{ticker1}_Close', f'{ticker2}_Close', 'Ratio', 'Z-Score', 'RSI']])

                # Display the trades table
                st.subheader("Trades Table")
                st.dataframe(trades_df)

                # Plot the Z-Score and trades
                st.subheader("Z-Score and Trades")
                st.line_chart(aligned_data.set_index('Date')[['Z-Score']])

        except Exception as e:
            st.exception(f"An error occurred: {e}")
