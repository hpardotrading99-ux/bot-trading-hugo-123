import streamlit as st
import yfinance as yf
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="Bot Trading IA PRO", layout="wide")

st.title("🚀 Bot Trading IA PRO FINAL (XAUUSD)")

# ==============================
# DATOS
# ==============================
@st.cache_data
def load_data():
    data = yf.download("GC=F", period="7d", interval="5m")
    return data

data = load_data()

# ==============================
# FEATURE ENGINEERING
# ==============================

# 🎯 FIX DEFINITIVO DEL ERROR
data["Future"] = data["Close"].shift(-1)

# 🔥 CLAVE: limpiar antes de comparar
data = data.dropna(subset=["Future", "Close"])

data["Target"] = (data["Future"] > data["Close"]).astype(int)

# Indicadores
data["Return"] = data["Close"].pct_change()
data["MA5"] = data["Close"].rolling(5).mean()
data["MA20"] = data["Close"].rolling(20).mean()

# Limpiar NaNs finales
data = data.dropna()

# ==============================
# MODELO IA
# ==============================
features = ["Return", "MA5", "MA20"]

X = data[features]
y = data["Target"]

model = RandomForestClassifier(n_estimators=100)
model.fit(X, y)

# ==============================
# PREDICCIÓN
# ==============================
last_data = X.iloc[-1:]
prediction = model.predict(last_data)[0]

# ==============================
# INTERFAZ
# ==============================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Precio actual")
    st.metric("XAUUSD", round(data["Close"].iloc[-1], 2))

with col2:
    st.subheader("🤖 Señal IA")

    if prediction == 1:
        st.success("📈 COMPRAR (BUY)")
    else:
        st.error("📉 VENDER (SELL)")

# ==============================
# GRÁFICO
# ==============================
st.subheader("📉 Gráfico")

st.line_chart(data["Close"])

# ==============================
# DEBUG (opcional)
# ==============================
with st.expander("🔍 Ver datos"):
    st.write(data.tail())
