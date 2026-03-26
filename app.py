import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests
from streamlit_autorefresh import st_autorefresh

# =========================
# CONFIG
# =========================
st.set_page_config(layout="wide")
st.title("🤖 Bot Trading PRO - MODO AGRESIVO")

st_autorefresh(interval=3000, key="refresh")

# =========================
# TELEGRAM
# =========================
TELEGRAM_TOKEN = "8733507632:AAF5NKhoL4gVm_Fjlg50LgS7bKM4cGhKoGw"
TELEGRAM_CHAT_ID = "867927346"

last_update_id = None

def get_telegram_updates():
    global last_update_id
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    response = requests.get(url).json()

    if not response["result"]:
        return None

    last = response["result"][-1]

    if last_update_id == last["update_id"]:
        return None

    last_update_id = last["update_id"]

    return last["message"]["text"]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg
    })

# =========================
# SESSION STATE
# =========================
if "bot_active" not in st.session_state:
    st.session_state.bot_active = True

if "position" not in st.session_state:
    st.session_state.position = None

if "trades" not in st.session_state:
    st.session_state.trades = []

if "balance" not in st.session_state:
    st.session_state.balance = 150  # 👈 capital inicial agresivo

if "equity" not in st.session_state:
    st.session_state.equity = [150]

# =========================
# CONTROL TELEGRAM
# =========================
cmd = get_telegram_updates()

if cmd:
    if cmd == "/startbot":
        st.session_state.bot_active = True
        send_telegram("🟢 Bot ACTIVADO")

    elif cmd == "/stopbot":
        st.session_state.bot_active = False
        send_telegram("🔴 Bot PARADO")

    elif cmd == "/balance":
        send_telegram(f"💰 Balance: {round(st.session_state.balance,2)}€")

    elif cmd == "/status":
        estado = "ACTIVO" if st.session_state.bot_active else "PARADO"
        send_telegram(f"🤖 Estado: {estado}")

# =========================
# MERCADO
# =========================
symbol = st.selectbox("Mercado", ["GC=F", "^IXIC", "^GSPC"])

# =========================
# DATA
# =========================
@st.cache_data(ttl=60)
def get_data():
    df = yf.download(symbol, period="1d", interval="1m")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

df = get_data()

# =========================
# INDICADORES
# =========================
df["ema_fast"] = df["Close"].ewm(span=20).mean()
df["ema_slow"] = df["Close"].ewm(span=50).mean()

df["rsi"] = 100 - (100 / (1 + df["Close"].pct_change().rolling(14).mean() /
                         df["Close"].pct_change().rolling(14).std()))

df["atr"] = (df["High"] - df["Low"]).rolling(14).mean()

df = df.dropna()

# =========================
# BOT AGRESIVO
# =========================
risk_per_trade = 0.03   # 🔥 3%
atr_sl = 1.0
atr_tp = 3.0

last = df.iloc[-1]

if st.session_state.bot_active:

    # 🔒 PROTECCIÓN RACHA NEGATIVA
    if len(st.session_state.trades) > 3:
        last_trades = st.session_state.trades[-3:]
        if sum(last_trades) < 0:
            st.session_state.bot_active = False
            send_telegram("🛑 Bot parado por racha negativa")

    # ENTRADAS
    if st.session_state.position is None:

        if last["ema_fast"] > last["ema_slow"] and last["rsi"] < 30:
            entry = last["Close"]
            sl = entry - last["atr"] * atr_sl
            tp = entry + last["atr"] * atr_tp

            st.session_state.position = ("BUY", entry, sl, tp)
            send_telegram(f"🟢 BUY {symbol} @ {round(entry,2)}")

        elif last["ema_fast"] < last["ema_slow"] and last["rsi"] > 70:
            entry = last["Close"]
            sl = entry + last["atr"] * atr_sl
            tp = entry - last["atr"] * atr_tp

            st.session_state.position = ("SELL", entry, sl, tp)
            send_telegram(f"🔴 SELL {symbol} @ {round(entry,2)}")

    # GESTIÓN
    else:
        side, entry, sl, tp = st.session_state.position
        price = last["Close"]

        if side == "BUY":
            if price <= sl:
                loss = st.session_state.balance * risk_per_trade
                st.session_state.balance -= loss
                st.session_state.trades.append(-loss)

                send_telegram(f"❌ SL: -{round(loss,2)}€")
                st.session_state.position = None

            elif price >= tp:
                profit = st.session_state.balance * risk_per_trade * 3
                st.session_state.balance += profit
                st.session_state.trades.append(profit)

                send_telegram(f"💰 TP: +{round(profit,2)}€")
                st.session_state.position = None

        elif side == "SELL":
            if price >= sl:
                loss = st.session_state.balance * risk_per_trade
                st.session_state.balance -= loss
                st.session_state.trades.append(-loss)

                send_telegram(f"❌ SL: -{round(loss,2)}€")
                st.session_state.position = None

            elif price <= tp:
                profit = st.session_state.balance * risk_per_trade * 3
                st.session_state.balance += profit
                st.session_state.trades.append(profit)

                send_telegram(f"💰 TP: +{round(profit,2)}€")
                st.session_state.position = None

# =========================
# EQUITY
# =========================
st.session_state.equity.append(st.session_state.balance)

# =========================
# UI
# =========================
estado = "🟢 ACTIVO" if st.session_state.bot_active else "🔴 PARADO"

st.metric("Estado del bot", estado)
st.metric("Balance", round(st.session_state.balance, 2))

# PRECIO
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df["Close"], name="Precio"))
st.plotly_chart(fig, use_container_width=True)

# EQUITY
eq_fig = go.Figure()
eq_fig.add_trace(go.Scatter(y=st.session_state.equity, name="Equity"))
st.plotly_chart(eq_fig, use_container_width=True)

# =========================
# ESTADÍSTICAS
# =========================
st.subheader("📊 Estadísticas")

trades = st.session_state.trades

if trades:
    wins = [t for t in trades if t > 0]
    winrate = len(wins) / len(trades) * 100

    st.write(f"Trades: {len(trades)}")
    st.write(f"Winrate: {round(winrate,2)}%")
    st.write(f"Ganancia total: {round(sum(trades),2)}€")
