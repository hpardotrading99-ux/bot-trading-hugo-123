import streamlit as st
import yfinance as yf
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

st.title("🚀 Bot Trading IA PRO FINAL (XAUUSD)")

# Descargar datos
data = yf.download("GC=F", period="7d", interval="5m")

# Verificar si hay datos
if data.empty:
    st.error("No hay datos disponibles")
    st.stop()

# Asegurar columna Close
if "Close" not in data.columns:
    if "Adj Close" in data.columns:
        data["Close"] = data["Adj Close"]
    else:
        st.error("No existe columna Close")
        st.write(data.columns)
        st.stop()

# Crear variables
data["Future"] = data["Close"].shift(-1)

# Eliminar NaN
data = data.dropna()

# Crear target
data["Target"] = (data["Future"] > data["Close"]).astype(int)

# Features
X = data[["Close"]]
y = data["Target"]

# Modelo IA
model = RandomForestClassifier()
model.fit(X, y)

# Predicción
pred = model.predict(X.tail(1))[0]

# Resultado
if pred == 1:
    st.success("📈 Señal: COMPRA")
else:
    st.error("📉 Señal: VENTA")

# Mostrar datos
st.subheader("Datos recientes")
st.write(data.tail())
