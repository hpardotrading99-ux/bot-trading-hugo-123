import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="Bot IA PRO FINAL", layout="wide")

st.title("🚀 Bot Trading IA PRO FINAL (XAUUSD)")

SYMBOL = "GC=F"

# --- TELEGRAM CONFIG ---
TELEGRAM_TOKEN = "8733507632:AAF5NKhoL4gVm_Fjlg50LgS7bKM4cGhKoGw"
CHAT_ID = "867927346"

def enviar_alerta(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": mensaje})

# --- DATOS ---
data = yf.download(SYMBOL, period="5d", interval="5m")

if data.empty:
    st.error("❌ Error cargando datos")
    st.stop()

# --- INDICADORES ---
data["EMA20"] = data["Close"].ewm(span=20).mean()
data["EMA50"] = data["Close"].ewm(span=50).mean()

delta = data["Close"].diff()
gain = (delta.where(delta > 0, 0)).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss
data["RSI"] = 100 - (100 / (1 + rs))

data["ATR"] = (data["High"] - data["Low"]).rolling(14).mean()
data["Momentum"] = data["Close"].diff()

# --- TARGET ---
data["Future"] = data["Close"].shift(-3)
data["Target"] = (data["Future"] > data["Close"]).astype(int)

data = data.dropna()

# --- IA ---
features = ["EMA20", "EMA50", "RSI", "ATR", "Momentum"]

X = data[features]
y = data["Target"]

model = RandomForestClassifier(n_estimators=50)
model.fit(X, y)

# --- PREDICCIÓN ---
last = data.iloc[-1]
X_last = last[features].values.reshape(1, -1)

proba = model.predict_proba(X_last)[0]

prob_sell = proba[0]
prob_buy = proba[1]

confidence = max(prob_buy, prob_sell)

signal = "NO TRADE"

if prob_buy > 0.6:
    signal = "BUY"
elif prob_sell > 0.6:
    signal = "SELL"

if confidence < 0.6:
    signal = "NO TRADE"

# --- DATOS ---
price = float(last["Close"])
atr = float(last["ATR"])

# --- SL / TP ---
sl = None
tp = None

if signal == "BUY":
    sl = price - atr * 2
    tp = price + atr * 3

elif signal == "SELL":
    sl = price + atr * 2
    tp = price - atr * 3

# --- ALERTA TELEGRAM ---
mensaje = f"""
🚨 Señal IA

Activo: XAUUSD
Señal: {signal}
Precio: {round(price,2)}
SL: {round(sl,2) if sl else None}
TP: {round(tp,2) if tp else None}
Confianza: {round(confidence,2)}
"""

if signal != "NO TRADE":
    enviar_alerta(mensaje)

# --- UI ---
col1, col2, col3 = st.columns(3)

col1.metric("💰 Precio", round(price, 2))
col2.metric("📊 ATR", round(atr, 2))
col3.metric("🧠 Confianza", round(confidence, 2))

st.subheader("📍 Señal IA")

if signal == "BUY":
    st.success("🟢 IA: COMPRA")
elif signal == "SELL":
    st.error("🔴 IA: VENTA")
else:
    st.warning("⚪ IA: NO OPERAR")

st.subheader("🧠 Probabilidades")
st.write(f"BUY: {round(prob_buy,2)}")
st.write(f"SELL: {round(prob_sell,2)}")

st.subheader("🎯 Gestión de riesgo")
st.write(f"Stop Loss: {round(sl,2) if sl else None}")
st.write(f"Take Profit: {round(tp,2) if tp else None}")

# --- BACKTEST ---
capital = 1000
balance = capital
trades = []

for i in range(len(data)-10):
    row = data.iloc[i]
    future_price = data.iloc[i+3]["Close"]

    X_test = row[features].values.reshape(1, -1)
    proba_bt = model.predict_proba(X_test)[0]

    prob_sell_bt = proba_bt[0]
    prob_buy_bt = proba_bt[1]

    if prob_buy_bt > 0.6:
        profit = future_price - row["Close"]
        balance += profit
        trades.append(profit)

    elif prob_sell_bt > 0.6:
        profit = row["Close"] - future_price
        balance += profit
        trades.append(profit)

st.subheader("📊 Backtest IA")

st.write(f"Balance inicial: {capital}")
st.write(f"Balance final: {round(balance,2)}")
st.write(f"Beneficio: {round(balance-capital,2)}")
st.write(f"Trades: {len(trades)}")

if trades:
    winrate = sum(1 for t in trades if t > 0) / len(trades)
    st.write(f"Winrate: {round(winrate*100,2)}%")

# --- GRÁFICO ---
st.subheader("📈 Gráfico")
st.line_chart(data[["Close", "EMA20", "EMA50"]])

with st.expander("📋 Ver datos"):
    st.dataframe(data.tail(20))
