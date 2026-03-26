import pandas as pd
import numpy as np
import yfinance as yf

print("📥 Descargando datos...")

# =========================
# ⚙️ CONFIG GENERAL
# =========================
risk_per_trade = 0.01
rsi_buy = 35
rsi_sell = 65
atr_sl = 1.2
atr_tp = 3.0

balance_inicial = 10000

# =========================
# 🌍 ACTIVO (CAMBIA AQUÍ)
# =========================
symbol = "^IXIC"   # prueba también "GC=F" o "^GSPC"

period = "30d"

# =========================
# 🔥 FILTRO POR MERCADO
# =========================
if symbol == "GC=F":
    trend_strength_min = 1.0
elif symbol == "^IXIC":
    trend_strength_min = 0.1
elif symbol == "^GSPC":
    trend_strength_min = 0.7
else:
    trend_strength_min = 0.5

# =========================
# 📥 DATOS
# =========================
df = yf.download(symbol, period=period, interval="15m")

if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

df = df.dropna()

# =========================
# 📊 INDICADORES (DINÁMICOS)
# =========================

# 💥 EMAs diferentes según mercado
if symbol == "^IXIC":
    df["ema_fast"] = df["Close"].ewm(span=10).mean()
    df["ema_slow"] = df["Close"].ewm(span=30).mean()
else:
    df["ema_fast"] = df["Close"].ewm(span=20).mean()
    df["ema_slow"] = df["Close"].ewm(span=50).mean()

# RSI
delta = df["Close"].diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)

avg_gain = gain.rolling(14).mean()
avg_loss = loss.rolling(14).mean()

rs = avg_gain / avg_loss
df["rsi"] = 100 - (100 / (1 + rs))

# ATR
df["tr"] = np.maximum(
    df["High"] - df["Low"],
    np.maximum(
        abs(df["High"] - df["Close"].shift()),
        abs(df["Low"] - df["Close"].shift())
    )
)

df["atr"] = df["tr"].rolling(14).mean()

df = df.dropna()

# =========================
# 🤖 BACKTEST
# =========================
balance = balance_inicial
position = None
trades = []
peak = balance
max_dd = 0

for i in range(len(df)):

    close = float(df["Close"].iloc[i])
    ema_fast = float(df["ema_fast"].iloc[i])
    ema_slow = float(df["ema_slow"].iloc[i])
    rsi = float(df["rsi"].iloc[i])
    atr = float(df["atr"].iloc[i])

    trend_strength = abs(ema_fast - ema_slow)

    # =====================
    # ENTRADA
    # =====================
    if position is None and trend_strength > trend_strength_min:

        if ema_fast > ema_slow and rsi < rsi_buy:
            position = ("BUY", close, close - atr * atr_sl, close + atr * atr_tp)

        elif ema_fast < ema_slow and rsi > rsi_sell:
            position = ("SELL", close, close + atr * atr_sl, close - atr * atr_tp)

    # =====================
    # GESTIÓN
    # =====================
    elif position is not None:

        side, entry, sl, tp = position

        if side == "BUY":
            if close <= sl:
                loss = -(balance * risk_per_trade)
                balance += loss
                trades.append(loss)
                position = None

            elif close >= tp:
                profit = (balance * risk_per_trade * atr_tp)
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
                profit = (balance * risk_per_trade * atr_tp)
                balance += profit
                trades.append(profit)
                position = None

    # =====================
    # 📉 DRAWDOWN
    # =====================
    if balance > peak:
        peak = balance

    dd = (peak - balance) / peak
    if dd > max_dd:
        max_dd = dd

# =========================
# 📊 RESULTADOS
# =========================
total_profit = sum(trades)
total_trades = len(trades)
wins = len([t for t in trades if t > 0])
win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

print("\n📊 RESULTADOS FINAL PRO (ADAPTATIVO)\n")
print(f"Activo: {symbol}")
print(f"Balance final: ${round(balance,2)}")
print(f"Beneficio: ${round(total_profit,2)}")
print(f"Trades: {total_trades}")
print(f"Win rate: {round(win_rate,2)}%")
print(f"Max Drawdown: {round(max_dd*100,2)}%")
