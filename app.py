import streamlit as st
import yfinance as yf
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="Bot IA Trading", layout="wide")

st.title("🧠 Bot Trading IA (Oro XAUUSD)")

SYMBOL = "GC=F"

# --- DATOS ---
data = yf.download(SYMBOL, period="5d", interval="5m")

if data.empty:
    st.error("Error cargando datos")
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

# Momentum
data["Momentum"] = data["Close"].diff()

# --- TARGET (futuro) ---
data["Future"] = data["Close"].shift(-3)
data["Target"] = (data["Future"] > data["Close"]).astype(int)

# Limpiar
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

prediction = model.predict(X_last)[0]

# --- FILTRO IA ---
signal = "NO TRADE"

if prediction == 1:
    signal = "BUY"
elif prediction == 0:
    signal = "SELL"

# --- DATOS ---
price = float(last["Close"])

# SL / TP
atr = float(last["ATR"])

if signal == "BUY":
    sl = price - atr * 2
    tp = price + atr * 3
elif signal == "SELL":
    sl = price + atr * 2
    tp = price - atr * 3
else:
    sl, tp = None, None

# --- UI ---
st.subheader("📍 Señal IA")

if signal == "BUY":
    st.success("🟢 IA: COMPRA")
elif signal == "SELL":
    st.error("🔴 IA: VENTA")
else:
    st.warning("⚪ IA: NO OPERAR")

st.write(f"Precio: {price}")
st.write(f"Stop Loss: {sl}")
st.write(f"Take Profit: {tp}")

st.subheader("📊 Gráfico")
st.line_chart(data[["Close", "EMA20", "EMA50"]])
