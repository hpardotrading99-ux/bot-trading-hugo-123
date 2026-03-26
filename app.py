import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Bot Trading IA", layout="wide")

st.title("🚀 Bot Trading IA PRO FINAL (XAUUSD)")

# 🔥 VERSION PARA CONTROLAR DEPLOY
VERSION = "v2.0 - Deploy OK 🚀"
st.markdown(f"### 🧠 Versión del bot: {VERSION}")

# =========================
# DATOS
# =========================
ticker = "GC=F"  # Oro (Gold Futures)

data = yf.download(ticker, period="1d", interval="1m")

if data.empty:
    st.error("No hay datos")
    st.stop()

# =========================
# LIMPIEZA DATOS (FIX ERRORES)
# =========================
data = data.dropna()

# Asegurar columnas
required_cols = ["Close"]
for col in required_cols:
    if col not in data.columns:
        st.error(f"Falta columna: {col}")
        st.stop()

# =========================
# FEATURES
# =========================
data["Future"] = data["Close"].shift(-1)

# ⚠️ IMPORTANTE: evitar errores
data = data.dropna(subset=["Future", "Close"])

# Target IA
data["Target"] = (data["Future"] > data["Close"]).astype(int)

# Medias
data["SMA20"] = data["Close"].rolling(20).mean()
data["SMA50"] = data["Close"].rolling(50).mean()

# =========================
# PRECIO ACTUAL
# =========================
precio_actual = data["Close"].iloc[-1]

st.subheader("📊 Precio actual")
st.success(precio_actual)

# =========================
# SEÑAL IA (simple)
# =========================
ultima = data.iloc[-1]

if ultima["SMA20"] > ultima["SMA50"]:
    señal = "🟢 COMPRA"
else:
    señal = "🔴 VENTA"

st.subheader("📈 Señal IA")
st.write(señal)

# =========================
# DATOS
# =========================
st.subheader("📋 Datos")
st.dataframe(data.tail(10))
