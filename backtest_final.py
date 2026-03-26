import pandas as pd
import numpy as np
import yfinance as yf

print("📥 Descargando datos...")

df = yf.download("GC=F", period="60d", interval="15m")

if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

df = df.dropna()

# =========================
# 📊 INDICADORES
# =========================
df["ema20"] = df["Close"].ewm(span=20).mean()
df["ema50"] = df["Close"].ewm(span=50).mean()

delta = df["Close"].diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)

avg_gain = gain.rolling(14).mean()
avg_loss = loss.rolling(14).mean()

rs = avg_gain / avg_loss
df["rsi"] = 100 - (100 / (1 + rs))

df = df.dropna()

# =========================
# 🤖 BACKTEST SIMPLE
# =========================
balance = 10000
risk_per_trade = 0.01

position = None
trades = []

for i in range(len(df)):

    close = float(df["Close"].iloc[i])
    ema20 = float(df["ema20"].iloc[i])
    ema50 = float(df["ema50"].iloc[i])
    rsi = float(df["rsi"].iloc[i])

    # =====================
    # ENTRADA
    # =====================
    if position is None:

        if ema20 > ema50 and rsi < 40:
            entry = close
            sl = entry - 10
            tp = entry + 20
            position = ("BUY", entry, sl, tp)

        elif ema20 < ema50 and rsi > 60:
            entry = close
            sl = entry + 10
            tp = entry - 20
            position = ("SELL", entry, sl, tp)

    # =====================
    # GESTIÓN
    # =====================
    else:
        side, entry, sl, tp = position

        if side == "BUY":
            if close <= sl:
                loss = -(balance * risk_per_trade)
                balance += loss
                trades.append(loss)
                position = None

            elif close >= tp:
                profit = (balance * risk_per_trade * 2)
                balance += profit
                trades.append(profit)
                position = None

        elif side == "SELL":
            if close >= sl:
                loss = -(balance * risk_per_trade)
                balance += loss
                trades.append(loss)
                position = None

            elif close <= tp:
                profit = (balance * risk_per_trade * 2)
                balance += profit
                trades.append(profit)
                position = None

# =========================
# 📊 RESULTADOS
# =========================
total_profit = sum(trades)
total_trades = len(trades)
wins = len([t for t in trades if t > 0])
win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

print("\n📊 RESULTADOS BACKTEST SIMPLE\n")
print(f"Balance final: ${round(balance,2)}")
print(f"Beneficio total: ${round(total_profit,2)}")
print(f"Trades: {total_trades}")
print(f"Win rate: {round(win_rate,2)}%")
