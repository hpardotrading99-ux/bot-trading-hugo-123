import streamlit as st
import yfinance as yf
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="Bot IA PRO", layout="wide")

st.title("🧠 Bot Trading IA PRO (Oro XAUUSD)")

SYMBOL = "GC=F"

# --- DATOS ---
data = yf.download(SYMBOL, period="5d", interval="5m")

if data.empty:
    st.error("❌ Error cargando datos")
    st.stop()

# --- FEATURES ---
data["EMA20"] = data["Close"].ewm(span=20).mean()
data["EMA50"] = data["Close"].ewm(span=50).mean()

delta = data["Close"].diff()
gain = (delta.where(delta > 0, 0)).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss
data["RSI"] = 100 - (100 / (1 + rs))

data["ATR"] = (data["High"] - data["Low"]).rolling(14).mean()
data["Momentum"] = data["Close"].diff()

# --- TARGET (futuro) ---
data["Future"] = data["Close"].shift(-3)
data["Target"] = (data["Future"] > data["Close"]).astype(int)

data = data.dropna()

# --- ENTRENAMIENTO IA ---
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

# Filtro extra
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

st.write(f"Probabilidad BUY: {round(prob_buy,2)}")
st.write(f"Probabilidad SELL: {round(prob_sell,2)}")

st.subheader("🎯 Gestión de riesgo")

st.write(f"Stop Loss: {round(sl,2) if sl else None}")
st.write(f"Take Profit: {round(tp,2) if tp else None}")

st.subheader("📊 Gráfico")

st.line_chart(data[["Close", "EMA20", "EMA50"]])

with st.expander("📋 Ver datos"):
    st.dataframe(data.tail(20))
