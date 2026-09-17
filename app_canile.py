from datetime import datetime, time
import json
import os
import streamlit as st

# Nomi dei file JSON per il salvataggio dei dati
DB_TURNI = "turni_volontari.json"
DB_CANI = "cani_autorizzati.json"

# Configurazione della pagina
st.set_page_config(
    page_title="Gestione Turni Rifugio", page_icon="🐾", layout="centered"
)


# --- FUNZIONI DI UTILITÀ PER I FILE JSON ---
def carica_file_json(filename, default_value):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default_value
    return default_value


def salva_file_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# --- INIZIALIZZAZIONE DATI GLOBALI ---
if "cani" not in st.session_state:
    # Lista predefinita di cani se il file non esiste
    cani_default = [
        "Giada",
        "Rocky",
        "Luna",
        "Thor",
        "Maya",
        "Spike",
        "Zoe",
        "Leo",
        "Nina",
        "Milo",
    ]
    st.session_state.cani = carica_file_json(DB_CANI, cani_default)


def get_lista_volontari():
    turni = carica_file_json(DB_TURNI, [])
    volontari = sorted(
        list(set(t.get("volontario", "").strip() for t in turni if t.get("volontario")))
    )
    return volontari


def get_cani_frequenti_volontario(nome_volontario):
    if not nome_volontario:
        return []
    turni = carica_file_json(DB_TURNI, [])
    cani_volontario = []
    for t in turni:
        if (
            t.get("volontario", "").strip().lower()
            == nome_volontario.strip().lower()
        ):
            cani_volontario.extend(t.get("cani_fatti", []))

    # Conta le frequenze e restituisce i più usati in ordine
    from collections import Counter

    conteggio = Counter(cani_volontario)
    return [cane for cane, _ in conteggio.most_common(5)]


# --- CALCOLO SETTIMANE (CORRENTE E PROSSIMA) ---
oggi = datetime.now()
giorno_settimana = oggi.weekday()  # 0=Lunedì, 5=Sabato, 6=Domenica

# Definiamo la logica delle etichette delle settimane
# Dal venerdì sera alla domenica si passa a pianificare la settimana prossima come principale
is_weekend_o_venerdi_sera = giorno_settimana >= 5 or (
    giorno_settimana == 4 and oggi.hour >= 18
)

if is_weekend_o_venerdi_sera:
    label_corr = "📅 Settimana in corso (questa)"
    label_pros = "⏭️ Settimana prossima"
else:
    label_corr = "📅 Questa settimana"
    label_pros = "⏭️ Settimana prossima (anteprima)"


# --- MENU LATERALE (SIDEBAR) ---
st.sidebar.title("🐾 Menu di Navigazione")
menu = st.sidebar.radio(
    "Vai a:",
    [
        "📅 Inserisci",
        "📋 Visualizza Turni",
        "📊 Riepilogo Cani",
        "⚙️ Gestione Cani",
    ],
)


# ==========================================
# 1. INSERISCI TURNO
# ==========================================
if menu == "📅 Inserisci":
    st.header("Gestione Turni")

    if is_weekend_o_venerdi_sera:
        opzioni_settimana = [label_corr, label_pros]
    else:
        opzioni_settimana = [label_corr]

    settimana_scelta = st.radio(
        "Per quale settimana vuoi inserire il turno?",
        opzioni_settimana,
        horizontal=True,
    )

    volontari_registrati = get_lista_volontari()

    # Gestione preventiva del nome fuori dal form per renderlo reattivo subito
    st.subheader("1. Il tuo Nome")
    scelte_volontario = ["-- Seleziona il tuo nome --"] + volontari_registrati + ["➕ Altro / Nuovo volontario"]
    
    scelta_volontario_dropdown = st.selectbox(
        "Seleziona o inserisci il tuo Nome e Cognome:", 
        scelte_volontario, 
        key="selettore_nome_principale"
    )
    
    volontario_inserito = ""
    if scelta_volontario_dropdown == "➕ Altro / Nuovo volontario":
        volontario_inserito = st.text_input("Scrivi qui il tuo Nome e Cognome esatto:", key="input_nuovo_volontario_libero")
        volontario_finale = volontario_inserito.strip()
    elif scelta_volontario_dropdown != "-- Seleziona il tuo nome --":
        volontario_finale = scelta_volontario_dropdown
    else:
        volontario_finale = ""

    st.markdown("---")

    with st.form("form_turno"):
        st.subheader("2. Dettagli Turno e Cani")
        col1, col2 = st.columns(2)

        with col1:
            giorno = st.selectbox(
                "Giorno della settimana:",
                [
                    "Lunedì",
                    "Martedì",
                    "Mercoledì",
                    "Giovedì",
                    "Venerdì",
                    "Sabato",
                    "Domenica",
                ],
            )
            fascia = st.selectbox("Fascia oraria:", ["Mattina", "Pomeriggio"])

        with col2:
            st.markdown(f"**Orario per {fascia}:**")
            
            default_inizio = time(8, 30) if fascia == "Mattina" else time(14, 30)
            default_fine = time(12, 0) if fascia == "Mattina" else time(18, 0)

            col_ora1, col_ora2 = st.columns(2)
            with col_ora1:
                ora_inizio = st.time_input("Da:", value=default_inizio)
            
            senza_fine = st.checkbox("Senza orario di fine (da quest'ora in poi)")

            with col_ora2:
                if not senza_fine:
                    ora_fine = st.time_input("A:", value=default_fine)
                else:
                    st.markdown("<br><i>Nessun limite</i>", unsafe_allow_html=True)
            
            if senza_fine:
                orario = f"Dalle {ora_inizio.strftime('%H:%M')}"
            else:
                orario = f"{ora_inizio.strftime('%H:%M')} - {ora_fine.strftime('%H:%M')}"

            note = st.text_area("Note aggiuntive (opzionale):")

        cani_suggeriti = get_cani_frequenti_volontario(volontario_finale)

        col_cani_op1, col_cani_op2 = st.columns([1, 1])
        with col_cani_op1:
            seleziona_tutti = st.checkbox("🐾 Seleziona TUTTI i cani")
        with col_cani_op2:
            if cani_suggeriti:
                st.caption(f"💡 Suggerimento abitudini: {', '.join(cani_suggeriti)}")

        if seleziona_tutti:
            cani_fatti = st.multiselect(
                "✅ Cani che sei autorizzato a gestire (obbligatorio selezionarne almeno uno):",
                st.session_state.cani,
                default=st.session_state.cani,
            )
        elif cani_suggeriti:
            cani_fatti = st.multiselect(
                "✅ Cani che sei autorizzato a gestire (obbligatorio selezionarne almeno uno):",
                st.session_state.cani,
                default=cani_suggeriti
            )
        else:
            cani_fatti = st.multiselect(
                "✅ Cani che sei autorizzato a gestire (obbligatorio selezionarne almeno uno):", 
                st.session_state.cani
            )

        submit_button = st.form_submit_button(label="Registra Turno 🚀")

        if submit_button:
            ora_limite_divisione = time(14, 0)
            errore_fascia = False
            
            if fascia == "Mattina" and ora_inizio >= ora_limite_divisione:
                st.error("❌ **Errore:** Hai scelto la fascia **Mattina**, ma l'orario di inizio è pomeridiano (dalle 14:00 in poi).")
                errore_fascia = True
            elif fascia == "Pomeriggio" and ora_inizio < ora_limite_divisione:
                st.error("❌ **Errore:** Hai scelto la fascia **Pomeriggio**, ma l'orario di inizio è mattutino (prima delle 14:00).")
                errore_fascia = True

            if not errore_fascia:
                if not volontario_finale:
                    st.warning("⚠️ Per favore, seleziona il tuo nome dal menu a tendina o scrivi il tuo nome e cognome nell'apposito campo prima di registrare.")
                elif not cani_fatti:
                    st.error("❌ **Errore:** Devi selezionare almeno un cane per poter registrare il turno!")
                else:
                    lista_turni = carica_file_json(DB_TURNI, [])
                    
                    volontario_normalizzato = volontario_finale.strip().lower()
                    doppione_trovato = any(
                        t.get("volontario", "").strip().lower() == volontario_normalizzato and
                        t.get("settimana") == settimana_scelta and
                        t.get("giorno") == giorno and
                        t.get("fascia") == fascia
                        for t in lista_turni
                    )

                    if doppione_trovato:
                        st.error(f"⚠️ **Attenzione:** {volontario_finale} risulta già registrato per {giorno} ({fascia}) in questa settimana!")
                    else:
                        nuovo_turno = {
                            "id": str(datetime.now().timestamp()),
                            "settimana": settimana_scelta,
                            "volontario": volontario_finale,
                            "giorno": giorno,
                            "fascia": fascia,
                            "orario": orario,
                            "cani_fatti": cani_fatti,
                            "note": note,
                        }
                        lista_turni.append(nuovo_turno)
                        salva_file_json(DB_TURNI, lista_turni)
                        st.success(f"Turno registrato con successo per {volontario_finale}!")


# ==========================================
# 2. VISUALIZZA TURNI
# ==========================================
elif menu == "📋 Visualizza Turni":
    st.header("📋 Tabellone Turni Registrati")

    lista_turni = carica_file_json(DB_TURNI, [])

    if not lista_turni:
        st.info("Nessun turno registrato al momento.")
    else:
        # Filtro per settimana
        settimane_disponibili = list(set(t.get("settimana") for t in lista_turni))
        settimana_filtro = st.selectbox("Filtra per settimana:", sorted(settimane_disponibili))

        turni_filtrati = [t for t in lista_turni if t.get("settimana") == settimana_filtro]

        if not turni_filtrati:
            st.info("Nessun turno trovato per questa settimana.")
        else:
            # Opzione per eliminare un turno
            st.subheader("Modifica o Cancella Turno")
            col_del1, col_del2 = st.columns([3, 1])

            with col_del1:
                opzioni_elimina = {
                    f"{t['volontario']} - {t['giorno']} ({t['fascia']})": t['id']
                    for t in turni_filtrati
                }
                scelta_da_eliminare = st.selectbox(
                    "Seleziona il turno da rimuovere:", 
                    list(opzioni_elimina.keys())
                )

            with col_del2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ Elimina Turno"):
                    id_da_rimuovere = opzioni_elimina[scelta_da_eliminare]
                    lista_turni = [t for t in lista_turni if t.get("id") != id_da_rimuovere]
                    salva_file_json(DB_TURNI, lista_turni)
                    st.success("Turno eliminato con successo!")
                    st.rerun()

            st.markdown("---")

            # Ordinamento dei giorni
            ordine_giorni = {
                "Lunedì": 1,
                "Martedì": 2,
                "Mercoledì": 3,
                "Giovedì": 4,
                "Venerdì": 5,
                "Sabato": 6,
                "Domenica": 7,
            }
            turni_filtrati.sort(key=lambda x: (ordine_giorni.get(x.get("giorno"), 8), x.get("fascia")))

            for t in turni_filtrati:
                with st.container():
                    st.markdown(
                        f"### 👤 {t['volontario']} — **{t['giorno']} ({t['fascia']})**"
                    )
                    st.write(f"⏰ **Orario:** {t['orario']}")
                    st.write(f"🐾 **Cani gestiti:** {', '.join(t['cani_fatti'])}")
                    if t.get("note"):
                        st.info(f"📝 **Note:** {t['note']}")
                    st.markdown("---")


# ==========================================
# 3. RIEPILOGO CANI
# ==========================================
elif menu == "📊 Riepilogo Cani":
    st.header("📊 Riepilogo Copertura Cani")

    lista_turni = carica_file_json(DB_TURNI, [])

    if not lista_turni:
        st.info("Nessun dato disponibile per il riepilogo.")
    else:
        settimane_disponibili = list(set(t.get("settimana") for t in lista_turni))
        settimana_filtro = st.selectbox("Seleziona settimana per il riepilogo:", sorted(settimane_disponibili))

        turni_filtrati = [t for t in lista_turni if t.get("settimana") == settimana_filtro]

        # Mappa dei cani e chi li porta
        report_cani = {cane: [] for cane in st.session_state.cani}

        for t in turni_filtrati:
            volontario = t.get("volontario")
            giorno = t.get("giorno")
            fascia = t.get("fascia")
            for cane in t.get("cani_fatti", []):
                if cane in report_cani:
                    report_cani[cane].append(f"{giorno} {fascia} ({volontario})")

        for cane, dettagli in report_cani.items():
            if dettagli:
                st.success(f"🐾 **{cane}**: gestito {len(dettagli)} volte")
                for d in dettagli:
                    st.markdown(f"- {d}")
            else:
                st.warning(f"⚠️ **{cane}**: Nessun turno assegnato in questa settimana!")
            st.markdown("---")


# ==========================================
# 4. GESTIONE CANI
# ==========================================
elif menu == "⚙️ Gestione Cani":
    st.header("⚙️ Gestione Elenco Cani del Rifugio")

    st.write("Aggiungi o rimuovi i cani presenti in struttura dall'elenco ufficiale.")

    col_ins, col_del = st.columns(2)

    with col_ins:
        st.subheader("Aggiungi un nuovo cane")
        nuovo_cane = st.text_input("Nome del cane:")
        if st.button("➕ Aggiungi Cane"):
            if nuovo_cane.strip():
                nome_pulito = nuovo_cane.strip().capitalize()
                if nome_pulito not in st.session_state.cani:
                    st.session_state.cani.append(nome_pulito)
                    salva_file_json(DB_CANI, st.session_state.cani)
                    st.success(f"Cane '{nome_pulito}' aggiunto con successo!")
                    st.rerun()
                else:
                    st.warning("Questo cane è già presente nell'elenco.")
            else:
                st.error("Inserisci un nome valido.")

    with col_del:
        st.subheader("Rimuovi un cane")
        if st.session_state.cani:
            cane_da_rimuovere = st.selectbox("Seleziona il cane da eliminare:", sorted(st.session_state.cani))
            if st.button("🗑️ Rimuovi Cane"):
                st.session_state.cani.remove(cane_da_rimuovere)
                salva_file_json(DB_CANI, st.session_state.cani)
                st.success(f"Cane '{cane_da_rimuovere}' rimosso con successo!")
                st.rerun()
        else:
            st.info("Nessun cane in elenco.")

    st.markdown("---")
    st.subheader("📋 Elenco attuale dei cani registrati:")
    st.write(", ".join(sorted(st.session_state.cani)))
