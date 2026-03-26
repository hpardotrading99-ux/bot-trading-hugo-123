import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Bot Trading IA PRO", layout="wide")

st.title("🚀 Bot Trading IA PRO FINAL (XAUUSD)")

# =========================
# DESCARGAR DATOS
# =========================
data = yf.download("GC=F", period="1d", interval="1m")

# =========================
# 🔥 ARREGLAR MULTIINDEX
# =========================
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

# =========================
# LIMPIEZA
# =========================
data = data.dropna()

# =========================
# CREAR FUTURE (SIN ERRORES)
# =========================
data["Future"] = data["Close"].shift(-1)

# IMPORTANTE: quitar NaN después del shift
data = data.dropna()

# =========================
# TARGET IA
# =========================
data["Target"] = (data["Future"] > data["Close"]).astype(int)

# =========================
# INDICADORES
# =========================
data["SMA20"] = data["Close"].rolling(20).mean()
data["SMA50"] = data["Close"].rolling(50).mean()

# =========================
# SEÑAL SIMPLE
# =========================
last = data.iloc[-1]

if last["SMA20"] > last["SMA50"]:
    signal = "🟢 COMPRA"
else:
    signal = "🔴 VENTA"

# =========================
# UI
# =========================
st.subheader("📊 Precio actual")
st.write(last["Close"])

st.subheader("📈 Señal IA")
st.write(signal)

st.subheader("📋 Datos")
st.dataframe(data.tail(50))
