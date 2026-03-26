import pandas as pd
import numpy as np
import yfinance as yf
from itertools import product

print("📥 Descargando datos...")

# ⚠️ CORREGIDO: 15m solo permite ~60 días
df = yf.download("GC=F", period="60d", interval="15m")

# Arreglar columnas si vienen raras
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

df["tr"] = np.maximum(
    df["High"] - df["Low"],
    np.maximum(
        abs(df["High"] - df["Close"].shift()),
        abs(df["Low"] - df["Close"].shift())
    )
)
df["atr"] = df["tr"].rolling(14).mean()

df = df.dropna()

print("🚀 Empezando optimización...")

# =========================
# ⚙️ PARÁMETROS (AJUSTADOS)
# =========================
risk_list = [0.005, 0.01]
rsi_buy_list = [30, 35, 40]
rsi_sell_list = [60, 65, 70]
atr_sl_list = [1.0, 1.2]
atr_tp_list = [2.0, 2.5]
trend_filter_list = [0.2, 0.5]

results = []

# =========================
# 🔁 LOOP DE OPTIMIZACIÓN
# =========================
for risk, rsi_buy, rsi_sell, atr_sl, atr_tp, trend_filter in product(
    risk_list, rsi_buy_list, rsi_sell_list, atr_sl_list, atr_tp_list, trend_filter_list
):

    balance = 10000
    position = None
    trades = []
    peak = balance
    max_dd = 0

    for i in range(len(df)):

        close = float(df["Close"].iloc[i])
        ema20 = float(df["ema20"].iloc[i])
        ema50 = float(df["ema50"].iloc[i])
        rsi = float(df["rsi"].iloc[i])
        atr = float(df["atr"].iloc[i])

        trend = abs(ema20 - ema50)

        # 🔥 NO bloqueamos trades (solo informativo)
        if trend < trend_filter:
            pass

        # =====================
        # 🟢 ENTRADA
        # =====================
        if position is None:

            if ema20 > ema50 and rsi < rsi_buy:
                position = ("BUY", close, close - atr * atr_sl, close + atr * atr_tp)

            elif ema20 < ema50 and rsi > rsi_sell:
                position = ("SELL", close, close + atr * atr_sl, close - atr * atr_tp)

        # =====================
        # 🔴 GESTIÓN
        # =====================
        else:
            side, entry, sl, tp = position

            if side == "BUY":
                if close <= sl:
                    loss = -(balance * risk)
                    balance += loss
                    trades.append(loss)
                    position = None

                elif close >= tp:
                    profit = (balance * risk * atr_tp)
                    balance += profit
                    trades.append(profit)
                    position = None

            elif side == "SELL":
                if close >= sl:
                    loss = -(balance * risk)
                    balance += loss
                    trades.append(loss)
                    position = None

                elif close <= tp:
                    profit = (balance * risk * atr_tp)
                    balance += profit
                    trades.append(profit)
                    position = None

        # 📉 DRAWNDOWN
        if balance > peak:
            peak = balance

        dd = (peak - balance) / peak
        if dd > max_dd:
            max_dd = dd

    total_profit = sum(trades)
    total_trades = len(trades)
    wins = len([t for t in trades if t > 0])
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

    results.append({
        "profit": total_profit,
        "balance": balance,
        "trades": total_trades,
        "win_rate": win_rate,
        "drawdown": max_dd,
        "risk": risk,
        "rsi_buy": rsi_buy,
        "rsi_sell": rsi_sell,
        "atr_sl": atr_sl,
        "atr_tp": atr_tp,
        "trend_filter": trend_filter
    })

# =========================
# 🏆 RESULTADOS
# =========================
results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    by=["profit", "drawdown"],
    ascending=[False, True]
)

print("\n🏆 TOP 10 CONFIGURACIONES:\n")
print(results_df.head(10))
