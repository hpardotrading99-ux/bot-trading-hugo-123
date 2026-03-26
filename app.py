import streamlit as st
import yfinance as yf
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

st.title("🚀 Bot Trading IA PRO FINAL (XAUUSD)")

# Descargar datos
data = yf.download("GC=F", period="7d", interval="5m")

# Validar datos
if data.empty:
    st.error("❌ No hay datos")
    st.stop()

# Ver columnas
st.write("Columnas:", data.columns)

# Asegurar Close
if "Close" not in data.columns:
    if "Adj Close" in data.columns:
        data["Close"] = data["Adj Close"]
    else:
        st.error("❌ No existe Close")
        st.stop()

# Crear Future
data["Future"] = data["Close"].shift(-1)

# Eliminar NaN correctamente (SIN subset)
data = data.dropna()

# Crear target
data["Target"] = (data["Future"] > data["Close"]).astype(int)

# Features
X = data[["Close"]]
y = data["Target"]

# Modelo
model = RandomForestClassifier()
model.fit(X, y)

# Predicción
pred = model.predict(X.tail(1))[0]

# Resultado
if pred == 1:
    st.success("📈 COMPRA")
else:
    st.error("📉 VENTA")

# Mostrar datos
st.subheader("Últimos datos")
st.write(data.tail())
