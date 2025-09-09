import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import streamlit as st
from technical_indicators import analyze_tickers

class PortfolioAnalyzer:
    def __init__(self, portfolio_df):
        """
        Initialize the Portfolio Analyzer with portfolio data
        
        Args:
            portfolio_df (pd.DataFrame): DataFrame containing portfolio holdings
        """
        self.portfolio_df = portfolio_df.copy()
        self.validate_portfolio_data()
        
    def validate_portfolio_data(self):
        """Validate and standardize portfolio data format"""
        # Remove summary rows first (like "Total" rows)
        if 'Slice' in self.portfolio_df.columns:
            # Filter out summary rows where Slice contains "Total" or similar
            self.portfolio_df = self.portfolio_df[
                ~self.portfolio_df['Slice'].astype(str).str.contains('Total|TOTAL|total|Summary|SUMMARY|summary', na=False)
            ]
        
        # Ensure we have required columns
        if 'Symbol' not in self.portfolio_df.columns:
            # Try common variations including user's format
            symbol_columns = ['symbol', 'ticker', 'Ticker', 'SYMBOL', 'Stock', 'stock', 'Slice']
            for col in symbol_columns:
                if col in self.portfolio_df.columns:
                    self.portfolio_df['Symbol'] = self.portfolio_df[col]
                    break
            else:
                raise ValueError("No symbol column found. Please include a 'Symbol' or 'Slice' column with stock tickers.")
        
        # Clean up symbol column
        self.portfolio_df['Symbol'] = self.portfolio_df['Symbol'].astype(str).str.strip().str.upper()
        
        # Handle company names if available
        if 'Name' in self.portfolio_df.columns and 'Company Name' not in self.portfolio_df.columns:
            self.portfolio_df['Company Name'] = self.portfolio_df['Name']
        
        # Handle shares and weights
        if 'Shares' not in self.portfolio_df.columns and 'Weight' not in self.portfolio_df.columns:
            # Try common variations including user's format
            shares_columns = ['shares', 'quantity', 'Quantity', 'SHARES', 'Amount', 'amount', 'Owned quantity']
            weight_columns = ['weight', 'Weight', 'WEIGHT', 'Allocation', 'allocation', '%']
            
            for col in shares_columns:
                if col in self.portfolio_df.columns:
                    self.portfolio_df['Shares'] = pd.to_numeric(self.portfolio_df[col], errors='coerce')
                    break
            else:
                for col in weight_columns:
                    if col in self.portfolio_df.columns:
                        weights = pd.to_numeric(self.portfolio_df[col], errors='coerce')
                        # Normalize weights if they appear to be percentages
                        if weights.notna().any() and weights.max() > 1:
                            weights = weights / 100
                        self.portfolio_df['Weight'] = weights
                        break
                else:
                    # If no shares or weights, assume equal weights
                    self.portfolio_df['Weight'] = 1.0 / len(self.portfolio_df)
        
        # Handle current value if available
        if 'Value' in self.portfolio_df.columns and 'Current Value' not in self.portfolio_df.columns:
            self.portfolio_df['Current Value'] = pd.to_numeric(self.portfolio_df['Value'], errors='coerce')

        # add extra columns from csv
        self.portfolio_df['Cost (£)'] = pd.to_numeric(self.portfolio_df['Invested value'], errors='coerce')
        self.portfolio_df['Value (£)'] = pd.to_numeric(self.portfolio_df['Value'], errors='coerce')
        self.portfolio_df['P&L (£)'] = pd.to_numeric(self.portfolio_df['Result'], errors='coerce')
        
        # Remove rows with invalid symbols
        self.portfolio_df = self.portfolio_df.dropna(subset=['Symbol'])
        self.portfolio_df = self.portfolio_df[self.portfolio_df['Symbol'] != '']
        
    def fetch_stock_data(self, symbols):
        """
        Fetch current stock data for given symbols
        
        Args:
            symbols (list): List of stock symbols
            
        Returns:
            dict: Dictionary with symbol as key and stock info as value
        """
        stock_data = {}
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(interval="1d")
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    stock_data[symbol] = {
                        'Current Price': current_price,
                        'Previous Close': info.get('previousClose', current_price),
                        'Market Cap': info.get('marketCap', 0),
                        'Company Name': info.get('longName', symbol),
                        'Sector': info.get('sector', 'Unknown'),
                        'Industry': info.get('industry', 'Unknown'),
                        'Currency': info.get('currency', 'Unknown')
                    }
                else:
                    # Fallback for symbols without recent data
                    stock_data[symbol] = {
                        'Current Price': 0,
                        'Previous Close': 0,
                        'Market Cap': 0,
                        'Company Name': symbol,
                        'Sector': 'Unknown',
                        'Industry': 'Unknown',
                        'Currency': 'Unknown'
                    }
                    
            except Exception as e:
                st.warning(f"Could not fetch data for {symbol}: {str(e)}")
                stock_data[symbol] = {
                    'Current Price': 0,
                    'Previous Close': 0,
                    'Market Cap': 0,
                    'Company Name': symbol,
                    'Sector': 'Unknown',
                    'Industry': 'Unknown',
                    'Currency': 'Unknown'
                }
                
        return stock_data
    
    def get_portfolio_summary(self):
        """
        Generate comprehensive portfolio summary with current market data
        
        Returns:
            pd.DataFrame: Enhanced portfolio summary with current prices and metrics
        """
        try:
            symbols = self.portfolio_df['Symbol'].tolist()
            
            # Fetch current market data
            stock_data = self.fetch_stock_data(symbols)
            
            # Create summary DataFrame
            summary_data = []
            
            for _, row in self.portfolio_df.iterrows():
                symbol = row['Symbol']
                stock_info = stock_data.get(symbol, {})
                
                # Basic information
                summary_row = {
                    'Symbol': symbol,
                    'Company Name': stock_info.get('Company Name', symbol),
                    'Sector': stock_info.get('Sector', 'Unknown'),
                    'Current Price': stock_info.get('Current Price', 0),
                    'Currency': stock_info.get('Currency', 0),
                    'Previous Close': stock_info.get('Previous Close', 0)
                }
                
                # Add shares if available
                if 'Shares' in row and pd.notna(row['Shares']):
                    shares = float(row['Shares'])
                    cost_gbp = float(row['Cost (£)'])
                    mv_gbp = float(row['Value (£)'])
                    summary_row['Shares'] = shares
                    summary_row['Market Value'] = shares * stock_info.get('Current Price', 0)
                    summary_row['Cost (£)'] = cost_gbp
                    summary_row['Value (£)'] = mv_gbp
                    summary_row['P&L (£)'] = float(row['P&L (£)'])
                    summary_row['P&L %'] = ((mv_gbp-cost_gbp) / cost_gbp) * 100
                else:
                    summary_row['Shares'] = 0
                    summary_row['Market Value'] = 0
                
                # Add or calculate weights
                if 'Weight' in row and pd.notna(row['Weight']):
                    summary_row['Weight'] = float(row['Weight'])
                else:
                    # Will calculate after we have all market values
                    summary_row['Weight'] = 0
                
                # Calculate daily change
                current_price = stock_info.get('Current Price', 0)
                previous_close = stock_info.get('Previous Close', 0)
                if previous_close > 0:
                    daily_change = ((current_price - previous_close) / previous_close) * 100
                    summary_row['Daily Change (%)'] = daily_change
                else:
                    summary_row['Daily Change (%)'] = 0
                
                summary_data.append(summary_row)
            
            summary_df = pd.DataFrame(summary_data)
            
            # Calculate weights if not provided
            if 'Weight' in summary_df.columns and summary_df['Weight'].sum() == 0:
                total_value = summary_df['Market Value'].sum()
                if total_value > 0:
                    summary_df['Weight'] = summary_df['Market Value'] / total_value
                else:
                    # Equal weights if no market value available
                    summary_df['Weight'] = 1.0 / len(summary_df)
            
            # Format numeric columns
            if 'Current Price' in summary_df.columns:
                summary_df['Current Price'] = summary_df['Current Price'].round(2)
            if 'Previous Close' in summary_df.columns:
                summary_df['Previous Close'] = summary_df['Previous Close'].round(2)
            if 'Market Value' in summary_df.columns:
                summary_df['Market Value'] = summary_df['Market Value'].round(2)
            if 'Weight' in summary_df.columns:
                summary_df['Weight (%)'] = (summary_df['Weight'] * 100).round(2)
            if 'Daily Change (%)' in summary_df.columns:
                summary_df['Daily Change (%)'] = summary_df['Daily Change (%)'].round(2)
            if 'P&L %' in summary_df.columns:
                summary_df['P&L %'] = summary_df['P&L %'].round(2)
            if 'P&L (£)' in summary_df.columns:
                summary_df['P&L (£)'] = summary_df['P&L (£)'].round(2)
                
            return summary_df
            
        except Exception as e:
            st.error(f"Error generating portfolio summary: {str(e)}")
            return None
    
    def get_portfolio_metrics(self, summary_df):
        """
        Calculate key portfolio metrics
        
        Args:
            summary_df (pd.DataFrame): Portfolio summary DataFrame
            
        Returns:
            dict: Dictionary of portfolio metrics
        """
        try:
            metrics = {}
            
            # Basic metrics
            metrics['Total Holdings'] = len(summary_df)
            metrics['Total Market Value'] = summary_df['Market Value'].sum() if 'Market Value' in summary_df.columns else 0
            
            # Concentration metrics
            if 'Weight' in summary_df.columns:
                weights = summary_df['Weight']
                metrics['Largest Position'] = weights.max()
                metrics['Smallest Position'] = weights.min()
                metrics['Concentration Ratio (Top 3)'] = weights.nlargest(3).sum()
                
                # Diversification metrics (Herfindahl Index)
                metrics['Herfindahl Index'] = (weights ** 2).sum()
                metrics['Effective Number of Holdings'] = 1 / metrics['Herfindahl Index'] if metrics['Herfindahl Index'] > 0 else 0
            
            # Performance metrics
            if 'Daily Change (%)' in summary_df.columns and 'Weight' in summary_df.columns:
                weighted_return = (summary_df['Daily Change (%)'] * summary_df['Weight']).sum()
                metrics['Portfolio Daily Return (%)'] = weighted_return
            
            # Sector diversification
            if 'Sector' in summary_df.columns:
                sector_counts = summary_df['Sector'].value_counts()
                metrics['Number of Sectors'] = len(sector_counts)
                metrics['Most Common Sector'] = sector_counts.index[0] if len(sector_counts) > 0 else 'Unknown'
            
            return metrics
            
        except Exception as e:
            st.error(f"Error calculating portfolio metrics: {str(e)}")
            return {}
