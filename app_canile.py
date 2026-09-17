import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import urllib.request
import urllib.error

st.set_page_config(page_title="Gestione Turni Canile", page_icon="🐾", layout="wide")

# --- GESTIONE DATI PERSISTENTI TRAMITE GITHUB ---
# Usiamo un file JSON nel repository per condividere i turni tra tutti i dispositivi a costo zero.
DB_FILE = "turni.json"

def carica_turni_da_github():
    if 'turni' in st.session_state and st.session_state.turni:
        return st.session_state.turni
    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            st.session_state.turni = data
            return data
    except Exception:
        st.session_state.turni = []
        return []

def salva_turni_su_github(turni):
    st.session_state.turni = turni
    try:
        with open(DB_FILE, "w") as f:
            json.dump(turni, f, indent=4)
    except Exception as e:
        # Se siamo su Streamlit Cloud in sola lettura locale, i dati restano comunque in sessione
        pass

# Inizializzazione stato
if 'cani' not in st.session_state:
    st.session_state.cani = ["Fido", "Luna", "Rocky", "Maya", "Thor", "Nina", "Zoe", "Leo"]

if 'turni' not in st.session_state:
    st.session_state.turni = carica_turni_da_github()

if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
adesso = datetime.now()
giorno_settimana = adesso.weekday()
ora_attuale = adesso.hour

is_weekend_reale = (giorno_settimana > 4) or (
    giorno_settimana == 4 and ora_attuale >= 18
)
is_weekend_o_venerdi_sera = is_weekend_reale

# --- SIMULATORE PER ANTEPRIMA (VISIBILE SOLO AGLI ADMIN) ---
if st.session_state.is_admin:
  st.sidebar.markdown("---")
  st.sidebar.subheader("🧪 Simulatore Anteprima (Admin)")
  scelta_simulazione = st.sidebar.selectbox(
      "Forza visualizzazione:",
      [
          "📅 Automatico (Tempo Reale)",
          "⚠️ Simula Venerdì Sera / Weekend",
          "🟢 Simula Lunedì - Giovedì",
      ],
  )

  if scelta_simulazione == "⚠️ Simula Venerdì Sera / Weekend":
    is_weekend_o_venerdi_sera = True
  elif scelta_simulazione == "🟢 Simula Lunedì - Giovedì":
    is_weekend_o_venerdi_sera = False
  else:
    is_weekend_o_venerdi_sera = is_weekend_reale

if is_weekend_o_venerdi_sera:
    st.warning("⚠️ **Promemoria Canile:** È iniziato il fine settimana! Ricordati di selezionare la **'Prossima Settimana'** qui sotto per inserire i tuoi turni per la settimana che sta per arrivare.")

opzioni_menu = ["📅 Inserisci / Modifica Turno", "👀 Visualizza Panoramica Settimanale", "🐶 Gestione Cani", "📚 Archivio Storico"]
menu = st.sidebar.selectbox("Menu", opzioni_menu)

# Area Riservata Amministratrici nella Sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("🔒 Area Amministratrici")

ADMIN_PASSWORD_CORRETTA = "canile2026"

if not st.session_state.is_admin:
    with st.sidebar.form("form_login_admin"):
        pwd_input = st.text_input("Password Admin:", type="password")
        btn_login = st.form_submit_button("Sblocca Admin")
        if btn_login:
            if pwd_input == ADMIN_PASSWORD_CORRETTA:
                st.session_state.is_admin = True
                st.success("Accesso effettuato!")
                st.rerun()
            else:
                st.error("Password errata.")
else:
    st.sidebar.success("🔓 Modulo Admin Attivo")
    if st.sidebar.button("🔒 Esci da Modalità Admin"):
        st.session_state.is_admin = False
        st.rerun()

def get_intervalli_settimane():
    oggi = datetime.now()
    lunedi_corrente = oggi - timedelta(days=oggi.weekday())
    domenica_corrente = lunedi_corrente + timedelta(days=6)
    
    lunedi_prossimo = lunedi_corrente + timedelta(days=7)
    domenica_prossima = domenica_corrente + timedelta(days=7)
    
    fmt = "%d/%m/%Y"
    str_corr = f"Settimana Corrente ({lunedi_corrente.strftime(fmt)} - {domenica_corrente.strftime(fmt)})"
    str_pros = f"Prossima Settimana ({lunedi_prossimo.strftime(fmt)} - {domenica_prossima.strftime(fmt)})"
    
    return str_corr, str_pros

label_corr, label_pros = get_intervalli_settimane()

if menu == "📅 Inserisci / Modifica Turno":
    st.header("Gestione Turni")
    
    if is_weekend_o_venerdi_sera:
        opzioni_settimana = [label_corr, label_pros]
    else:
        opzioni_settimana = [label_corr]
    
    settimana_scelta = st.radio("Per quale settimana vuoi inserire il turno?", opzioni_settimana, horizontal=True)
    
    with st.form("form_turno"):
        col1, col2 = st.columns(2)
        
        with col1:
            volontario = st.text_input("Tuo Nome e Cognome:")
            giorno = st.selectbox("Giorno della settimana:", ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"])
            fascia = st.selectbox("Fascia oraria:", ["Mattina", "Pomeriggio"])
            
        with col2:
            orario = st.text_input("Orario di presenza (es. 09:00 - 12:00):", "09:00 - 12:00")
            note = st.text_area("Note aggiuntive (opzionale):")
            
        st.subheader("Gestione Cani per questo turno")
        
        seleziona_tutti = st.checkbox("🐾 Seleziona TUTTI i cani")
        
        if seleziona_tutti:
            cani_fatti = st.multiselect("✅ Cani che sei autorizzato a gestire:", st.session_state.cani, default=st.session_state.cani)
        else:
            cani_fatti = st.multiselect("✅ Cani che sei autorizzato a gestire:", st.session_state.cani)
        
        submit_button = st.form_submit_button(label="Registra Turno 🚀")
        
        if submit_button:
            if volontario.strip() == "":
                st.warning("Per favore, inserisci il tuo nome prima di registrare il turno.")
            else:
                lista_corrente = carica_turni_da_github()
                nuovo_turno = {
                    "id": str(datetime.now().timestamp()),
                    "settimana": settimana_scelta,
                    "volontario": volontario.strip(),
                    "giorno": giorno,
                    "fascia": fascia,
                    "orario": orario,
                    "cani_fatti": cani_fatti,
                    "note": note
                }
                lista_corrente.append(nuovo_turno)
                salva_turni_su_github(lista_corrente)
                st.success(f"Turno registrato con successo per {volontario}!")

elif menu == "👀 Visualizza Panoramica Settimanale":
    st.header("Gestione Turni e Copertura")
    
    turni_attuali = carica_turni_da_github()
    
    if is_weekend_o_venerdi_sera:
        scelte_visualizzazione = [label_corr, label_pros]
    else:
        scelte_visualizzazione = [label_corr]
    
    settimana_vista = st.radio(
        "Seleziona la settimana da visualizzare:", 
        scelte_visualizzazione, 
        horizontal=True
    )
    
    turni_filtrati = [t for t in turni_attuali if t.get('settimana') == settimana_vista]
    
    if not turni_filtrati:
        st.info("Nessun turno inserito al momento per questo periodo.")
    else:
        giorni_settimana = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        
        for giorno in giorni_settimana:
            st.markdown(f"## 📌 {giorno}")
            turni_giorno = [t for t in turni_filtrati if t['giorno'] == giorno]
            
            col_m, col_p = st.columns(2)
            
            def mostra_fascia_calendario(fascia_nome, col_container):
                with col_container:
                    st.markdown(f"### ☀️ {fascia_nome}")
                    turni_fascia = [t for t in turni_giorno if t['fascia'] == fascia_nome]
                    
                    if not turni_fascia:
                        st.caption("Nessun volontario registrato.")
                        st.markdown("**Cani scoperti:**")
                        for c in sorted(st.session_state.cani):
                            st.error(f"❌ {c}")
                        return
                    
                    st.markdown("**Volontari presenti:**")
                    for t in turni_fascia:
                        cani_str = ', '.join(t['cani_fatti']) if t['cani_fatti'] else 'Nessuno'
                        st.write(f"• **{t['volontario']}** ({t['orario']}) 🐾 [{cani_str}]")
                        if t['note']:
                            st.caption(f"Note: {t['note']}")
                        
                        if st.session_state.is_admin:
                            if st.button(f"🗑️ Elimina ({t['volontario']})", key=f"del_{giorno}_{fascia_nome}_{t['id']}"):
                                lista_aggiornata = [item for item in carica_turni_da_github() if item['id'] != t['id']]
                                salva_turni_su_github(lista_aggiornata)
                                st.success("Turno eliminato!")
                                st.rerun()
                    
                    cani_coperti = set()
                    for t in turni_fascia:
                        for c in t['cani_fatti']:
                            cani_coperti.add(c)
                            
                    cani_scoperti = [c for c in st.session_state.cani if c not in cani_coperti]
                        
                    st.markdown("**Cani scoperti:**")
                    if cani_scoperti:
                        for c in sorted(cani_scoperti):
                            st.error(f"❌ {c}")
                    else:
                        st.success("Tutti i cani sono coperti!")

            with col_m:
                mostra_fascia_calendario("Mattina", col_m)
            with col_p:
                mostra_fascia_calendario("Pomeriggio", col_p)
                
            st.markdown("---")

elif menu == "🐶 Gestione Cani":
    st.header("Gestione Anagrafica Cani")
    
    if not st.session_state.is_admin:
        st.warning("🔒 Questa sezione è protetta. Inserisci la password da amministratrice nella barra laterale a sinistra per aggiungere o rimuovere i cani.")
        st.subheader("Lista attuale dei cani in canile:")
        for dog in st.session_state.cani:
            st.write(f"🐾 **{dog}**")
    else:
        st.markdown("Aggiungi o rimuovi i cani presenti in canile (Modalità Admin attiva).")
        
        new_dog = st.text_input("Nome del nuovo cane:")
        if st.button("Aggiungi Cane"):
            if new_dog.strip() and new_dog not in st.session_state.cani:
                st.session_state.cani.append(new_dog.strip())
                st.success(f"Cane '{new_dog}' aggiunto con successo!")
                st.rerun()
            elif new_dog in st.session_state.cani:
                st.warning("Questo cane è già presente nella lista.")
                
        st.subheader("Lista attuale dei cani in canile:")
        for dog in st.session_state.cani:
            col_d1, col_d2 = st.columns([4, 1])
            with col_d1:
                st.write(f"🐾 **{dog}**")
            with col_d2:
                if st.button("Elimina", key=f"del_{dog}"):
                    st.session_state.cani.remove(dog)
                    st.rerun()

elif menu == "📚 Archivio Storico":
    st.header("📚 Archivio Storico delle Settimane Passate")
    st.markdown("Qui puoi consultare lo storico di tutte le settimane registrate in precedenza.")
    
    tutti_i_turni = carica_turni_da_github()
    tutte_le_settimane = sorted(list(set(t.get('settimana') for t in tutti_i_turni)))
    settimane_storiche = [s for s in tutte_le_settimane if s != label_corr and s != label_pros]
    
    if not settimane_storiche and not tutti_i_turni:
        st.info("Nessun dato presente nell'archivio storico.")
    else:
        settimane_disponibili = settimane_storiche if settimane_storiche else tutte_le_settimane
        
        if not settimane_disponibili:
            st.info("Non ci sono ancora settimane passate archiviate.")
        else:
            storico_scelto = st.selectbox("Seleziona la settimana dall'archivio:", settimane_disponibili)
            
            turni_storico = [t for t in tutti_i_turni if t.get('settimana') == storico_scelto]
            
            giorni_settimana = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
            
            for giorno in giorni_settimana:
                st.markdown(f"## 📌 {giorno}")
                turni_giorno = [t for t in turni_storico if t['giorno'] == giorno]
                
                col_m, col_p = st.columns(2)
                
                def mostra_fascia_storica(fascia_nome, col_container):
                    with col_container:
                        st.markdown(f"### ☀️ {fascia_nome}")
                        turni_fascia = [t for t in turni_giorno if t['fascia'] == fascia_nome]
                        
                        if not turni_fascia:
                            st.caption("Nessun volontario registrato in questa fascia.")
                            return
                        
                        st.markdown("**Volontari presenti:**")
                        for t in turni_fascia:
                            cani_str = ', '.join(t['cani_fatti']) if t['cani_fatti'] else 'Nessuno'
                            st.write(f"• **{t['volontario']}** ({t['orario']}) 🐾 [{cani_str}]")
                            if t['note']:
                                st.caption(f"Note: {t['note']}")
                            
                            if st.session_state.is_admin:
                                if st.button(f"🗑️ Elimina ({t['volontario']})", key=f"del_storico_{giorno}_{fascia_nome}_{t['id']}"):
                                    lista_aggiornata = [item for item in carica_turni_da_github() if item['id'] != t['id']]
                                    salva_turni_su_github(lista_aggiornata)
                                    st.success("Turno eliminato!")
                                    st.rerun()

                with col_m:
                    mostra_fascia_storica("Mattina", col_m)
                with col_p:
                    mostra_fascia_storica("Pomeriggio", col_p)
                    
                st.markdown("---")
