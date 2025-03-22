import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

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
    backtest_end_date = st.date_input("Select backtesting end date", datetime.today())
    backtest_start_date = st.date_input("Select backtesting start date", backtest_end_date - timedelta(days=365))
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

                # Format the Date column to show only YYYY-MM-DD
                aligned_data['Date'] = aligned_data['Date'].dt.strftime('%Y-%m-%d')

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
                        holding_period = (pd.to_datetime(exit_date) - pd.to_datetime(entry_date)).days

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

                # Calculate Trade Summary Metrics
                total_trades = len(trades_df)
                winning_trades = trades_df[trades_df['Profit %'] > 0]
                losing_trades = trades_df[trades_df['Profit %'] <= 0]
                win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
                lose_rate = len(losing_trades) / total_trades * 100 if total_trades > 0 else 0

                long_trades = trades_df[trades_df['Trade Type'] == "Long Ratio"]
                total_long_trades = len(long_trades)
                long_win_rate = len(long_trades[long_trades['Profit %'] > 0]) / total_long_trades * 100 if total_long_trades > 0 else 0
                long_lose_rate = len(long_trades[long_trades['Profit %'] <= 0]) / total_long_trades * 100 if total_long_trades > 0 else 0

                short_trades = trades_df[trades_df['Trade Type'] == "Short Ratio"]
                total_short_trades = len(short_trades)
                short_win_rate = len(short_trades[short_trades['Profit %'] > 0]) / total_short_trades * 100 if total_short_trades > 0 else 0
                short_lose_rate = len(short_trades[short_trades['Profit %'] <= 0]) / total_short_trades * 100 if total_short_trades > 0 else 0

                max_drawdown = trades_df['Max Loss'].min() if not trades_df.empty else 0
                profit_factor = winning_trades['Profit %'].sum() / abs(losing_trades['Profit %'].sum()) if not losing_trades.empty else 0

                # Create Trade Summary DataFrame
                trade_summary = pd.DataFrame({
                    'Metric': [
                        'Total Trades', 'Win Rate (%)', 'Lose Rate (%)',
                        'Total Long Trades', 'Long Win Rate (%)', 'Long Lose Rate (%)',
                        'Total Short Trades', 'Short Win Rate (%)', 'Short Lose Rate (%)',
                        'Max Drawdown ($)', 'Profit Factor'
                    ],
                    'Value': [
                        total_trades, win_rate, lose_rate,
                        total_long_trades, long_win_rate, long_lose_rate,
                        total_short_trades, short_win_rate, short_lose_rate,
                        max_drawdown, profit_factor
                    ]
                })

                # Display the stock price, z-score, and RSI table
                st.subheader("Stock Prices, Z-Score, and RSI")
                st.dataframe(aligned_data[['Date', f'{ticker1}_Close', f'{ticker2}_Close', 'Ratio', 'Z-Score', 'RSI']].reset_index(drop=True))

                # Display the trades table
                st.subheader("Trades Table")
                st.dataframe(trades_df.reset_index(drop=True))

                # Display the trade summary
                st.subheader("Trade Summary")
                st.dataframe(trade_summary.reset_index(drop=True))

                # Plot the Z-Score and trades
                st.subheader("Z-Score and Trades")
                st.line_chart(aligned_data.set_index('Date')[['Z-Score']])

        except Exception as e:
            st.exception(f"An error occurred: {e}")
