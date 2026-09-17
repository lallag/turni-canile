import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestione Turni Canile", page_icon="🐾", layout="wide")

if 'cani' not in st.session_state:
    st.session_state.cani = ["Fido", "Luna", "Rocky", "Maya", "Thor", "Nina", "Zoe", "Leo"]

if 'turni' not in st.session_state:
    st.session_state.turni = []

st.title("🐾 Gestione Turni e Copertura Canile")
st.markdown("Benvenuto! Inserisci il tuo turno, seleziona i cani di cui ti occuperai e controlla la copertura giornaliera.")

menu = st.sidebar.selectbox("Menu", ["📅 Inserisci / Modifica Turno", "👀 Visualizza Turni e Copertura Giornaliera", "🐶 Gestione Cani"])

if menu == "📅 Inserisci / Modifica Turno":
    st.header("Inserisci la tua disponibilità per il turno")
    
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
        st.markdown("Seleziona **solo** i cani che farai in questo turno (i non selezionati si considerano automaticamente esclusi):")
        
        cani_fatti = st.multiselect("✅ Cani presi in carico:", st.session_state.cani)
        
        submit_button = st.form_submit_button(label="Registra Turno 🚀")
        
        if submit_button:
            if volontario.strip() == "":
                st.warning("Per favore, inserisci il tuo nome prima di registrare il turno.")
            else:
                nuovo_turno = {
                    "volontario": volontario,
                    "giorno": giorno,
                    "fascia": fascia,
                    "orario": orario,
                    "cani_fatti": cani_fatti,
                    "note": note
                }
                st.session_state.turni.append(nuovo_turno)
                st.success(f"Turno registrato con successo per {volontario}!")

elif menu == "👀 Visualizza Turni e Copertura Giornaliera":
    st.header("Panoramica Giornaliera e Controllo Copertura")
    
    giorno_selezionato = st.selectbox(
        "Seleziona il giorno da controllare:", 
        ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
    )
    
    if not st.session_state.turni:
        st.info("Nessun turno inserito al momento. Usa il menu a sinistra per aggiungerne uno!")
    else:
        turni_giorno = [t for t in st.session_state.turni if t['giorno'] == giorno_selezionato]
        
        col_m, col_p = st.columns(2)
        
        def analisi_fascia(fascia_nome):
            st.subheader(f"☀️ {fascia_nome}")
            turni_fascia = [t for t in turni_giorno if t['fascia'] == fascia_nome]
            
            if not turni_fascia:
                st.write("Nessun volontario registrato in questa fascia.")
                st.markdown("### ❌ Cani SCOPERTI:")
                for c in sorted(st.session_state.cani):
                    st.error(f"• {c}")
                return

            with st.expander(f"📋 Dettaglio Volontari ({len(turni_fascia)})"):
                for t in turni_fascia:
                    st.write(f"• **{t['volontario']}** ({t['orario']}) -> Cani: {', '.join(t['cani_fatti']) if t['cani_fatti'] else 'Nessuno'}")
                    if t['note']:
                        st.caption(f"Note: {t['note']}")

            cani_coperti_fascia = set()
            for t in turni_fascia:
                for c in t['cani_fatti']:
                    cani_coperti_fascia.add(c)
                    
            cani_scoperti_fascia = [c for c in st.session_state.cani if c not in cani_coperti_fascia]
            
            st.markdown("### ✅ Cani coperti")
            if cani_coperti_fascia:
                for c in sorted(cani_coperti_fascia):
                    st.success(f"• {c}")
            else:
                st.write("Nessun cane coperto.")
                
            st.markdown("### ❌ Cani SCOPERTI:")
            if cani_scoperti_fascia:
                for c in sorted(cani_scoperti_fascia):
                    st.error(f"• {c}")
            else:
                st.success("Tutti i cani sono coperti in questa fascia!")

        with col_m:
            analisi_fascia("Mattina")
            
        with col_p:
            analisi_fascia("Pomeriggio")

elif menu == "🐶 Gestione Cani":
    st.header("Gestione Anagrafica Cani")
    st.markdown("Aggiungi o rimuovi i cani presenti in canile.")
    
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
