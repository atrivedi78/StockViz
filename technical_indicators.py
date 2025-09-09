import pandas as pd
import numpy as np
import yfinance as yf
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

def analyze_macd(macd, signal, hist, price, label):
    notes = []
    score = 0

    macd_last, macd_prev = macd.iloc[-1], macd.iloc[-2]
    signal_last, signal_prev = signal.iloc[-1], signal.iloc[-2]
    hist_last, hist_prev = hist.iloc[-1], hist.iloc[-2]

    # Basic position
    if macd_last > signal_last and macd_last > 0:
        notes.append("MACD above Signal and zero (bullish)")
        score += 2
    elif macd_last < signal_last and macd_last < 0:
        notes.append("MACD below Signal and zero (bearish)")
        score -= 2
    else:
        notes.append("MACD in mixed territory")

    # Fresh crossovers
    if macd_prev < signal_prev and macd_last > signal_last:
        notes.append("Fresh bullish crossover")
        score += 2
    elif macd_prev > signal_prev and macd_last < signal_last:
        notes.append("Fresh bearish crossover")
        score -= 2

    # Histogram momentum
    if hist_last > hist_prev:
        notes.append("Momentum strengthening")
        score += 1
    elif hist_last < hist_prev:
        notes.append("Momentum weakening")
        score -= 1

    # Divergence check (simplified)
    price_high = price.iloc[-20:].max()
    price_low = price.iloc[-20:].min()
    macd_high = macd.iloc[-20:].max()
    macd_low = macd.iloc[-20:].min()

    if price.iloc[-1] > price_high and macd_last < macd_high:
        notes.append("Bearish divergence (price high not confirmed by MACD)")
        score -= 2
    if price.iloc[-1] < price_low and macd_last > macd_low:
        notes.append("Bullish divergence (price low not confirmed by MACD)")
        score += 2

    # Translate score into ranked outlook
    if score >= 3:
        outlook = "Strong Bullish"
    elif score >= 1:
        outlook = "Weak Bullish"
    elif score <= -3:
        outlook = "Strong Bearish"
    elif score <= -1:
        outlook = "Weak Bearish"
    else:
        outlook = "Neutral"

    return {"Outlook": outlook, "Score": score, "Notes": notes, "Label": label}

def compute_macd(prices, fast=12, slow=26, signal=9):
    """Compute MACD and return separate series (used by analyze_tickers)"""
    try:
        if len(prices) < slow:
            return pd.Series(), pd.Series(), pd.Series()
        
        # Calculate EMAs
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        
        # MACD line
        macd_line = ema_fast - ema_slow
        
        # Signal line
        signal_line = macd_line.ewm(span=signal).mean()
        
        # Histogram
        histogram = macd_line - signal_line
        
        return macd_line.dropna(), signal_line.dropna(), histogram.dropna()
    
    except Exception as e:
        print(f"Error in compute_macd: {e}")
        return pd.Series(), pd.Series(), pd.Series()

def interpret_macd(price_df):
    """Interpret weekly and monthly MACD with ranking and confidence scoring."""
    try:
        if price_df is None or price_df.empty or len(price_df) < 50:
            return None
            
        weekly = price_df['Close'].resample('W').last()
        monthly = price_df['Close'].resample('ME').last()
        
        # Make sure we have enough data points
        if len(weekly) < 10 or len(monthly) < 5:
            return None

        macd_w, sig_w, hist_w = compute_macd(weekly)
        macd_m, sig_m, hist_m = compute_macd(monthly)
        
        # Check if MACD calculation was successful
        if macd_w.empty or sig_w.empty or hist_w.empty or macd_m.empty or sig_m.empty or hist_m.empty:
            return None

        weekly_view = analyze_macd(macd_w, sig_w, hist_w, weekly, "Weekly")
        monthly_view = analyze_macd(macd_m, sig_m, hist_m, monthly, "Monthly")
    except Exception as e:
        print(f"Error in interpret_macd: {e}")
        return None

    overall_score = (weekly_view["Score"] + monthly_view["Score"]) / 2

    if overall_score >= 3:
        overall = "Strong Bullish"
    elif overall_score >= 1:
        overall = "Weak Bullish"
    elif overall_score <= -3:
        overall = "Strong Bearish"
    elif overall_score <= -1:
        overall = "Weak Bearish"
    else:
        overall = "Neutral"

    max_score = 6
    confidence = int(round(((overall_score + max_score) / (2 * max_score)) * 100, 0))

    return {
        "Outlook": overall,
        "Confidence": confidence,
        "Weekly": weekly_view["Outlook"],
        "Monthly": monthly_view["Outlook"],
        "Weekly Notes": "; ".join(weekly_view["Notes"]),
        "Monthly Notes": "; ".join(monthly_view["Notes"])
    }

# --- Multi-ticker wrapper ---
def analyze_tickers(tickers, start="2020-01-01"):
    results = []
    for ticker in tickers:
        try:
            df = yf.download(ticker, start=start, progress=False)
            if df is None or df.empty:
                continue
            
            # Check if we have enough data
            if len(df) < 50:  # Need at least 50 days for meaningful analysis
                continue
                
            res = interpret_macd(df)
            if res is not None:
                res["Ticker"] = ticker
                results.append(res)
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            continue

    ranked = pd.DataFrame(results).sort_values(by="Confidence", ascending=False)
    return ranked.reset_index(drop=True)