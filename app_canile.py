from datetime import datetime, timedelta, time
import os
import json
import pandas as pd
import pytz
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

st.set_page_config(
    page_title="Gestione Turni Canile", page_icon="icona.jpg", layout="wide"
)

# Tag aggiornati con versione forzata (?v=10) per aggirare la cache testarda di iOS
st.markdown(
    """
    <head>
        <link rel="manifest" href="manifest.json">
        <link rel="apple-touch-icon" href="[https://github.com/lallag/turni-canile/blob/main/icona.jpg?raw=true&v=10](https://github.com/lallag/turni-canile/blob/main/icona.jpg?raw=true&v=10)">
    </head>
""",
    unsafe_allow_html=True,
)

# --- INIZIALIZZAZIONE FIREBASE FIRESTORE SICURA ---
if not firebase_admin._apps:
    try:
        # Legge il JSON completo salvato nei Secrets di Streamlit in modo sicuro
        firebase_json_str = st.secrets["FIREBASE_JSON"]
        cred_dict = json.loads(firebase_json_str)
        
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Errore di connessione a Firebase: {e}")
        st.stop()

db = firestore.client()

# --- FUNZIONI DI GESTIONE DATABASE FIRESTORE ---
def carica_da_firestore(collezione_nome, default_val):
    try:
        docs = db.collection(collezione_nome).stream()
        data = {}
        for doc in docs:
            data[doc.id] = doc.to_dict()
        
        if collezione_nome == "cani":
            if "lista" in data:
                return data["lista"].get("elementi", default_val)
            return default_val
        elif collezione_nome == "lpu_data":
            return data if data else default_val
        elif collezione_nome == "turni" or collezione_nome == "turni_lpu":
            lista = [doc.to_dict() for doc in docs]
            return lista if lista else default_val
        return default_val
    except Exception as e:
        return default_val

def salva_su_firestore(collezione_nome, doc_id, data_dict):
    try:
        db.collection(collezione_nome).document(str(doc_id)).set(data_dict)
        return True
    except Exception as e:
        st.error(f"Errore di salvataggio su Firebase: {e}")
        return False

def elimina_da_firestore(collezione_nome, doc_id):
    try:
        db.collection(collezione_nome).document(str(doc_id)).delete()
        return True
    except Exception as e:
        st.error(f"Errore di eliminazione: {e}")
        return False

# Inizializzazione stato con Firebase
if "cani" not in st.session_state:
    cani_caricati = carica_da_firestore("cani", None)
    if cani_caricati and isinstance(cani_caricati, list):
        st.session_state.cani = cani_caricati
    else:
        default_cani = [
            "Marley", "Diego", "Lucky", "Macchia", "Sami", "Bonnie", "Giada", "Nelson", "Amber"
        ]
        st.session_state.cani = default_cani
        db.collection("cani").document("lista").set({"elementi": default_cani})

if "lpu_data" not in st.session_state:
    lpu_caricati = db.collection("lpu_data").stream()
    lpu_dict = {doc.id: doc.to_dict() for doc in lpu_caricati}
    st.session_state.lpu_data = lpu_dict if lpu_dict else {}

if "turni_lpu" not in st.session_state:
    turni_lpu_docs = db.collection("turni_lpu").stream()
    st.session_state.turni_lpu = [doc.to_dict() for doc in turni_lpu_docs]

if "turni" not in st.session_state:
    turni_docs = db.collection("turni").stream()
    st.session_state.turni = [doc.to_dict() for doc in turni_docs]

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# --- GESTIONE ORARIO ITALIANO ESATTO ---
tz_italia = pytz.timezone("Europe/Rome")
adesso = datetime.now(tz_italia)
giorno_settimana = adesso.weekday()
ora_attuale = adesso.hour

is_weekend_reale = (giorno_settimana > 4) or (
    giorno_settimana == 4 and ora_attuale >= 17
)
is_weekend_o_venerdi_sera = is_weekend_reale

# --- BARRA LATERALE (SIDEBAR) ---
with st.sidebar:
    if os.path.exists("icona.jpg"):
        st.image("icona.jpg", width=80)
    
    st.title("🐾 Menu Rapido")
    
    with st.expander("🔍 Cerca i miei turni", expanded=False):
        turni_esistenti_side = carica_da_firestore("turni", [])
        nomi_side = sorted(list(set(t.get("volontario", "").strip() for t in turni_esistenti_side if t.get("volontario"))))
        
        if not nomi_side:
            st.info("Nessun turno registrato
