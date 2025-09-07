import pandas as pd
import numpy as np
from typing import Optional, Tuple

def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average (EMA)
    
    Args:
        prices (pd.Series): Price series
        period (int): EMA period
        
    Returns:
        pd.Series: EMA values
    """
    return prices.ewm(span=period, adjust=False).mean()

def calculate_macd(prices: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Optional[pd.DataFrame]:
    """
    Calculate MACD (Moving Average Convergence Divergence) indicator
    
    Args:
        prices (pd.Series): Price series (typically closing prices)
        fast_period (int): Fast EMA period (default: 12)
        slow_period (int): Slow EMA period (default: 26)
        signal_period (int): Signal line EMA period (default: 9)
        
    Returns:
        pd.DataFrame: DataFrame with MACD, Signal, and Histogram columns
        None: If calculation fails
    """
    try:
        if len(prices) < slow_period:
            return None
        
        # Calculate EMAs
        ema_fast = calculate_ema(prices, fast_period)
        ema_slow = calculate_ema(prices, slow_period)
        
        # Calculate MACD line
        macd_line = ema_fast - ema_slow
        
        # Calculate Signal line (EMA of MACD line)
        signal_line = calculate_ema(macd_line, signal_period)
        
        # Calculate MACD histogram
        histogram = macd_line - signal_line
        
        # Create result DataFrame
        macd_df = pd.DataFrame({
            'MACD': macd_line,
            'Signal': signal_line,
            'Histogram': histogram
        }, index=prices.index)
        
        # Remove NaN values
        macd_df = macd_df.dropna()
        
        return macd_df
        
    except Exception as e:
        print(f"Error calculating MACD: {str(e)}")
        return None

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI)
    
    Args:
        prices (pd.Series): Price series
        period (int): RSI period (default: 14)
        
    Returns:
        pd.Series: RSI values
    """
    try:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
        
    except Exception as e:
        print(f"Error calculating RSI: {str(e)}")
        return pd.Series(index=prices.index, dtype=float)

def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2) -> pd.DataFrame:
    """
    Calculate Bollinger Bands
    
    Args:
        prices (pd.Series): Price series
        period (int): Moving average period (default: 20)
        std_dev (float): Standard deviation multiplier (default: 2)
        
    Returns:
        pd.DataFrame: DataFrame with Middle Band (SMA), Upper Band, and Lower Band
    """
    try:
        sma = prices.rolling(window=period).mean()
        rolling_std = prices.rolling(window=period).std()
        
        upper_band = sma + (rolling_std * std_dev)
        lower_band = sma - (rolling_std * std_dev)
        
        bb_df = pd.DataFrame({
            'Middle Band': sma,
            'Upper Band': upper_band,
            'Lower Band': lower_band
        }, index=prices.index)
        
        return bb_df
        
    except Exception as e:
        print(f"Error calculating Bollinger Bands: {str(e)}")
        return pd.DataFrame(index=prices.index)

def calculate_moving_averages(prices: pd.Series, periods: list = [20, 50, 200]) -> pd.DataFrame:
    """
    Calculate multiple Simple Moving Averages
    
    Args:
        prices (pd.Series): Price series
        periods (list): List of periods for moving averages
        
    Returns:
        pd.DataFrame: DataFrame with moving averages
    """
    try:
        ma_df = pd.DataFrame(index=prices.index)
        
        for period in periods:
            ma_df[f'SMA_{period}'] = prices.rolling(window=period).mean()
            
        return ma_df
        
    except Exception as e:
        print(f"Error calculating moving averages: {str(e)}")
        return pd.DataFrame(index=prices.index)

def detect_macd_signals(macd_df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect MACD trading signals
    
    Args:
        macd_df (pd.DataFrame): MACD DataFrame with MACD, Signal, and Histogram columns
        
    Returns:
        pd.DataFrame: DataFrame with additional signal columns
    """
    try:
        signals_df = macd_df.copy()
        
        # MACD line crossovers with signal line
        signals_df['MACD_Above_Signal'] = signals_df['MACD'] > signals_df['Signal']
        signals_df['Signal_Change'] = signals_df['MACD_Above_Signal'].astype(int).diff()
        
        # Buy signals (MACD crosses above signal line)
        signals_df['Buy_Signal'] = signals_df['Signal_Change'] == 1
        
        # Sell signals (MACD crosses below signal line)
        signals_df['Sell_Signal'] = signals_df['Signal_Change'] == -1
        
        # Zero line crossovers
        signals_df['MACD_Above_Zero'] = signals_df['MACD'] > 0
        signals_df['Zero_Line_Change'] = signals_df['MACD_Above_Zero'].astype(int).diff()
        
        # Bullish momentum (MACD crosses above zero)
        signals_df['Bullish_Momentum'] = signals_df['Zero_Line_Change'] == 1
        
        # Bearish momentum (MACD crosses below zero)
        signals_df['Bearish_Momentum'] = signals_df['Zero_Line_Change'] == -1
        
        # Histogram analysis
        signals_df['Histogram_Positive'] = signals_df['Histogram'] > 0
        signals_df['Histogram_Increasing'] = signals_df['Histogram'].diff() > 0
        
        return signals_df
        
    except Exception as e:
        print(f"Error detecting MACD signals: {str(e)}")
        return macd_df

def get_macd_interpretation(latest_macd: pd.Series) -> dict:
    """
    Provide interpretation of current MACD values
    
    Args:
        latest_macd (pd.Series): Latest MACD values
        
    Returns:
        dict: Interpretation of MACD signals
    """
    try:
        interpretation = {
            'trend': 'Neutral',
            'signal_strength': 'Weak',
            'recommendation': 'Hold',
            'details': []
        }
        
        macd_value = latest_macd.get('MACD', 0)
        signal_value = latest_macd.get('Signal', 0)
        histogram_value = latest_macd.get('Histogram', 0)
        
        # Trend analysis
        if macd_value > signal_value:
            if macd_value > 0:
                interpretation['trend'] = 'Strong Bullish'
                interpretation['recommendation'] = 'Buy'
            else:
                interpretation['trend'] = 'Weak Bullish'
                interpretation['recommendation'] = 'Hold/Buy'
        else:
            if macd_value < 0:
                interpretation['trend'] = 'Strong Bearish'
                interpretation['recommendation'] = 'Sell'
            else:
                interpretation['trend'] = 'Weak Bearish'
                interpretation['recommendation'] = 'Hold/Sell'
        
        # Signal strength
        macd_signal_diff = abs(macd_value - signal_value)
        if macd_signal_diff > 0.5:
            interpretation['signal_strength'] = 'Strong'
        elif macd_signal_diff > 0.2:
            interpretation['signal_strength'] = 'Medium'
        else:
            interpretation['signal_strength'] = 'Weak'
        
        # Add details
        if histogram_value > 0:
            interpretation['details'].append("MACD histogram is positive, indicating strengthening bullish momentum")
        else:
            interpretation['details'].append("MACD histogram is negative, indicating strengthening bearish momentum")
        
        if macd_value > 0:
            interpretation['details'].append("MACD is above zero line, suggesting overall bullish trend")
        else:
            interpretation['details'].append("MACD is below zero line, suggesting overall bearish trend")
        
        return interpretation
        
    except Exception as e:
        print(f"Error interpreting MACD: {str(e)}")
        return {
            'trend': 'Unknown',
            'signal_strength': 'Unknown',
            'recommendation': 'Hold',
            'details': ['Error in analysis']
        }
