from datetime import datetime, timedelta, time
import json
import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Gestione Turni Canile", page_icon="icona.jpg", layout="wide"
)

# Tag aggiornati con versione forzata (?v=7) per aggirare la cache testarda di iOS
st.markdown(
    """
    <head>
        <link rel="manifest" href="manifest.json">
        <link rel="apple-touch-icon" href="https://github.com/lallag/turni-canile/blob/main/icona.jpg?raw=true&v=7">
    </head>
""",
    unsafe_allow_html=True,
)

# --- GESTIONE DATI PERSISTENTI TRAMITE GITHUB / JSON ---
DB_TURNI = "turni.json"
DB_CANI = "cani.json"


def carica_file_json(filename, default_val):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except Exception:
        return default_val


def salva_file_json(filename, data):
    try:
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        pass


# Inizializzazione stato
if "cani" not in st.session_state:
    st.session_state.cani = carica_file_json(
        DB_CANI,
        [
            "Marley",
            "Diego",
            "Lucky",
            "Macchia",
            "Sami",
            "Bonnie",
            "Giada",
            "Nelson",
            "Amber",
        ],
    )

if "turni" not in st.session_state:
    st.session_state.turni = carica_file_json(DB_TURNI, [])

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

adesso = datetime.now()
giorno_settimana = adesso.weekday()
ora_attuale = adesso.hour

is_weekend_reale = (giorno_settimana > 4) or (
    giorno_settimana == 4 and ora_attuale >= 18
)
is_weekend_o_venerdi_sera = is_weekend_reale

# --- BARRA LATERALE (SIDEBAR) PER: I MIEI TURNI & ADMIN ---
with st.sidebar:
    if os.path.exists("icona.jpg"):
        st.image("icona.jpg", width=80)
    
    st.title("🐾 Menu Rapido")
    
    # Sezione "I miei turni" nella sidebar
    with st.expander("🔍 Cerca i miei turni", expanded=False):
        volontari_esistenti_side = carica_file_json(DB_TURNI, [])
        nomi_side = sorted(list(set(t.get("volontario", "").strip() for t in volontari_esistenti_side if t.get("volontario"))))
        
        if not nomi_side:
            st.info("Nessun turno registrato nel sistema.")
        else:
            nome_cercato_side = st.selectbox("Seleziona il tuo nome:", nomi_side, key="selettore_miei_turni_sidebar")
            turni_pers_side = [t for t in volontari_esistenti_side if t.get("volontario", "").strip().lower() == nome_cercato_side.lower()]
            
            if not turni_pers_side:
                st.write("Nessun turno trovato.")
            else:
                for tp in turni_pers_side:
                    cani_str = ", ".join(tp.get("cani_fatti", []))
                    st.markdown(f"• **{tp.get('settimana')}**<br>📅 {tp.get('giorno')} ({tp.get('fascia')})<br>⏰ {tp.get('orario')}<br>🐾 [{cani_str}]", unsafe_allow_html=True)
                    st.markdown("---")

    st.markdown("---")

    # Sezione "Admin / Simulatore" nella sidebar
    with st.expander("🔒 Area Admin", expanded=False):
        ADMIN_PASSWORD_CORRETTA = "canile2026"
        if not st.session_state.is_admin:
            with st.form("form_login_admin_side"):
                pwd_input = st.text_input("Password:", type="password", key="pwd_side")
                btn_login = st.form_submit_button("Sblocca")
                if btn_login:
                    if pwd_input == ADMIN_PASSWORD_CORRETTA:
                        st.session_state.is_admin = True
                        st.success("Sbloccato!")
                        st.rerun()
                    else:
                        st.error("Errata.")
        else:
            st.success("🔓 Admin attivo")
            scelta_simulazione = st.selectbox(
                "Simulazione:",
                [
                    "📅 Automatico",
                    "⚠️ Simula Weekend",
                    "🟢 Simula Feriale",
                ],
                key="selettore_simulazione_side",
            )

            if scelta_simulazione == "⚠️ Simula Weekend":
                is_weekend_o_venerdi_sera = True
            elif scelta_simulazione == "🟢 Simula Feriale":
                is_weekend_o_venerdi_sera = False
            else:
                is_weekend_o_venerdi_sera = is_weekend_reale

            if st.button("🔒 Esci Admin", key="esci_admin_side"):
                st.session_state.is_admin = False
                st.rerun()

# --- INTESTAZIONE PRINCIPALE ---
st.title("🐾 Turni Canile")

# --- MENU PRINCIPALE IN ALTO ---
opzioni_menu = [
    "📅 Inserisci",
    "👀 Panoramica",
    "🐶 Cani",
    "📊 Statistiche",
    "📚 Archivio",
]
menu = st.pills("Seleziona sezione:", opzioni_menu, default=opzioni_menu[0])
st.markdown("---")


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

if is_weekend_o_venerdi_sera:
    st.warning(
        "⚠️ **Promemoria Canile:** È iniziato il fine settimana! Ricordati di"
        " selezionare la **'Prossima Settimana'** qui sotto per inserire i tuoi"
        " turni per la settimana che sta per arrivare."
    )


def get_lista_volontari():
    turni_esistenti = carica_file_json(DB_TURNI, [])
    nomi = set()
    for t in turni_esistenti:
        nome = t.get("volontario", "").strip()
        if nome:
            nomi.add(nome)
    return sorted(list(nomi))


def get_cani_frequenti_volontario(nome_volontario):
    if not nome_volontario or nome_volontario == "➕ Altro / Nuovo volontario" or nome_volontario == "-- Seleziona il tuo nome --":
        return []
    
    turni_esistenti = carica_file_json(DB_TURNI, [])
    conteggio_cani = {}
    
    for t in turni_esistenti:
        if t.get("volontario", "").strip().lower() == nome_volontario.strip().lower():
            for c in t.get("cani_fatti", []):
                if c in st.session_state.cani:
                    conteggio_cani[c] = conteggio_cani.get(c, 0) + 1
                    
    cani_ordinati = sorted(conteggio_cani.items(), key=lambda x: x[1], reverse=True)
    return [c[0] for c in cani_ordinati if c[1] >= 1]


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

    # --- SEZIONE NOME FUORI DAL FORM PER ESSERE LIBERA E REATTIVA ---
    st.markdown("### 👤 1. Il tuo Nome")
    scelte_volontario = ["-- Seleziona il tuo nome --"] + volontari_registrati + ["➕ Altro / Nuovo volontario"]
    
    # Usiamo un widget interattivo reattivo fuori dal form
    scelta_volontario_dropdown = st.selectbox("Seleziona o inserisci il tuo Nome e Cognome:", scelte_volontario, key="selettore_nome_principale")
    
    volontario_finale = ""
    if scelta_volontario_dropdown == "➕ Altro / Nuovo volontario":
        volontario_nuovo_input = st.text_input("Scrivi qui il tuo Nome e Cognome:", key="input_nuovo_volontario_libero")
        volontario_finale = volontario_nuovo_input.strip()
    elif scelta_volontario_dropdown != "-- Seleziona il tuo nome --":
        volontario_finale = scelta_volontario_dropdown

    st.markdown("---")

    # --- FORM PER IL RESTO DEL TURNO ---
    with st.form("form_turno"):
        st.markdown("### 🕒 2. Dettagli Turno e Cani")
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

        # Recuperiamo i suggerimenti in base al nome già digitato/selezionato sopra
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
                    st.warning("⚠️ Per favore, seleziona il tuo nome dal menu a tendina o scrivi il tuo nome e cognome nell'apposita casella in alto prima di registrare.")
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

elif menu == "👀 Panoramica":
    st.header("Gestione Turni e Copertura")

    turni_attuali = carica_file_json(DB_TURNI, [])

    if is_weekend_o_venerdi_sera:
        scelte_visualizzazione = [label_corr, label_pros]
    else:
        scelte_visualizzazione = [label_corr]

    settimana_vista = st.radio(
        "Seleziona la settimana da visualizzare:",
        scelte_visualizzazione,
        horizontal=True,
    )

    turni_filtrati = [
        t for t in turni_attuali if t.get("settimana") == settimana_vista
    ]

    if not turni_filtrati:
        st.info("Nessun turno inserito al momento per questo periodo.")
    else:
        giorni_settimana = [
            "Lunedì",
            "Martedì",
            "Mercoledì",
            "Giovedì",
            "Venerdì",
            "Sabato",
            "Domenica",
        ]

        for giorno in giorni_settimana:
            st.markdown(f"## 📌 {giorno}")
            turni_giorno = [t for t in turni_filtrati if t["giorno"] == giorno]

            col_m, col_p = st.columns(2)

            def mostra_fascia_calendario(fascia_nome, col_container):
                with col_container:
                    st.markdown(f"### ☀️ {fascia_nome}")
                    turni_fascia = [
                        t for t in turni_giorno if t["fascia"] == fascia_nome
                    ]

                    if not turni_fascia:
                        st.caption("Nessun volontario registrato.")
                        st.markdown("**Cani scoperti:**")
                        for c in sorted(st.session_state.cani):
                            st.error(f"❌ {c}")
                        return

                    st.markdown("**Volontari presenti:**")
                    for t in turni_fascia:
                        cani_str = (
                            ", ".join(t["cani_fatti"])
                            if t["cani_fatti"]
                            else "Nessuno"
                        )
                        st.write(
                            f"• **{t['volontario']}** ({t['orario']}) 🐾 [{cani_str}]"
                        )
                        if t["note"]:
                            st.caption(f"Note: {t['note']}")

                        if st.session_state.is_admin:
                            col_mod, col_del = st.columns(2)
                            with col_mod:
                                if st.button(
                                    f"✏️ Modifica ({t['volontario']})",
                                    key=f"mod_btn_{giorno}_{fascia_nome}_{t['id']}",
                                ):
                                    st.session_state[f"editing_{t['id']}"] = not st.session_state.get(f"editing_{t['id']}", False)
                                    st.rerun()
                            with col_del:
                                if st.button(
                                    f"🗑️ Elimina ({t['volontario']})",
                                    key=f"del_{giorno}_{fascia_nome}_{t['id']}",
                                ):
                                    lista_aggiornata = [
                                        item
                                        for item in carica_file_json(DB_TURNI, [])
                                        if item["id"] != t["id"]
                                    ]
                                    salva_file_json(DB_TURNI, lista_aggiornata)
                                    if f"editing_{t['id']}" in st.session_state:
                                        del st.session_state[f"editing_{t['id']}"]
                                    st.success("Turno eliminato!")
                                    st.rerun()

                            if st.session_state.get(f"editing_{t['id']}", False):
                                with st.form(key=f"form_mod_{t['id']}"):
                                    st.subheader(f"Modifica Turno di {t['volontario']}")
                                    
                                    col_m1, col_m2 = st.columns(2)
                                    with col_m1:
                                        m_inizio = st.time_input("Ora Inizio:", value=time(8, 30), key=f"min_{t['id']}")
                                    with col_m2:
                                        m_fine = st.time_input("Ora Fine:", value=time(12, 0), key=f"mfin_{t['id']}")
                                    
                                    nuovo_orario = f"{m_inizio.strftime('%H:%M')} - {m_fine.strftime('%H:%M')}"
                                    nuove_note = st.text_area("Note:", value=t.get("note", ""), key=f"note_mod_{t['id']}")
                                    
                                    nuovi_cani = st.multiselect(
                                        "Cani gestiti:",
                                        st.session_state.cani,
                                        default=[c for c in t["cani_fatti"] if c in st.session_state.cani],
                                        key=f"cani_mod_{t['id']}"
                                    )
                                    btn_salva_mod = st.form_submit_button("Salva Modifiche ✅")
                                    if btn_salva_mod:
                                        if not nuovi_cani:
                                            st.error("Errore: seleziona almeno un cane.")
                                        else:
                                            lista_completa = carica_file_json(DB_TURNI, [])
                                            for item in lista_completa:
                                                if item["id"] == t["id"]:
                                                    item["orario"] = nuovo_orario
                                                    item["note"] = nuove_note
                                                    item["cani_fatti"] = nuovi_cani
                                            salva_file_json(DB_TURNI, lista_completa)
                                            st.session_state[f"editing_{t['id']}"] = False
                                            st.success("Turno modificato con successo!")
                                            st.rerun()

                    cani_coperti = set()
                    for t in turni_fascia:
                        for c in t["cani_fatti"]:
                            cani_coperti.add(c)

                    cani_scoperti = [
                        c
                        for c in st.session_state.cani
                        if c not in cani_coperti
                    ]

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

elif menu == "🐶 Cani":
    st.header("Gestione Anagrafica Cani")

    if not st.session_state.is_admin:
        st.warning(
            "🔒 Questa sezione è protetta. Apri l'area 'Admin' nella barra"
            " laterale a sinistra per inserire la password."
        )
        st.subheader("Lista attuale dei cani in canile:")
        for dog in st.session_state.cani:
            st.write(f"🐾 **{dog}**")
    else:
        st.markdown("Aggiungi o rimuovi i cani presenti in canile (Modalità Admin attiva).")

        new_dog = st.text_input("Nome del nuovo cane:")
        if st.button("Aggiungi Cane"):
            if new_dog.strip() and new_dog not in st.session_state.cani:
                st.session_state.cani.append(new_dog.strip())
                salva_file_json(DB_CANI, st.session_state.cani)
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
                    salva_file_json(DB_CANI, st.session_state.cani)
                    st.rerun()

elif menu == "📊 Statistiche":
    st.header("📊 Statistiche Uscite Cani")
    
    tutti_i_turni = carica_file_json(DB_TURNI, [])
    tutte_le_settimane = sorted(
        list(set(t.get("settimana") for t in tutti_i_turni))
    )

    if label_corr not in tutte_le_settimane:
        tutte_le_settimane.insert(0, label_corr)
    if label_pros not in tutte_le_settimane and is_weekend_o_venerdi_sera:
        tutte_le_settimane.append(label_pros)

    settimana_stat = st.selectbox(
        "Seleziona settimana da analizzare:", tutte_le_settimane
    )

    turni_stat = [
        t for t in tutti_i_turni if t.get("settimana") == settimana_stat
    ]

    uscite_per_cane = {cane: 0 for cane in st.session_state.cani}
    giorni_settimana = [
        "Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"
    ]

    for giorno in giorni_settimana:
        for fascia in ["Mattina", "Pomeriggio"]:
            turni_fascia = [
                t for t in turni_stat
                if t.get("giorno") == giorno and t.get("fascia") == fascia
            ]
            cani_in_questa_fascia = set()
            for t in turni_fascia:
                for c in t.get("cani_fatti", []):
                    cani_in_questa_fascia.add(c)

            for c in cani_in_questa_fascia:
                if c in uscite_per_cane:
                    uscite_per_cane[c] += 1

    if not st.session_state.cani:
        st.info("Nessun cane registrato nel sistema.")
    else:
        st.markdown("---")
        st.subheader("🎯 Riepilogo Uscite")
        cols = st.columns(3)

        lista_cani_ordinata = sorted(
            uscite_per_cane.items(), key=lambda x: x[1], reverse=True
        )

        for idx, (cane, conteggio) in enumerate(lista_cani_ordinata):
            col_corrente = cols[idx % 3]
            with col_corrente:
                st.metric(label=f"🐾 {cane}", value=f"{conteggio} uscite")

        st.markdown("---")
        col_grafico, col_tabella = st.columns([1.5, 1])

        with col_grafico:
            st.subheader("📈 Grafico a Barre")
            if sum(uscite_per_cane.values()) == 0:
                st.info("Nessuna uscita registrata per i cani in questa settimana.")
            else:
                df_stat = pd.DataFrame(
                    list(uscite_per_cane.items()),
                    columns=["Cane", "Numero Uscite"],
                ).set_index("Cane")
                st.bar_chart(df_stat)

        with col_tabella:
            st.subheader("📋 Tabella Dati")
            df_tabella = pd.DataFrame(
                list(uscite_per_cane.items()), columns=["Cane", "Uscite"]
            ).sort_values(by="Uscite", ascending=False).reset_index(drop=True)
            st.dataframe(df_tabella, use_container_width=True)

elif menu == "📚 Archivio":
    st.header("📚 Archivio Storico delle Settimane Passate")
    
    tutti_i_turni = carica_file_json(DB_TURNI, [])
    tutte_le_settimane = sorted(
        list(set(t.get("settimana") for t in tutti_i_turni))
    )
    settimane_storiche = [
        s for s in tutte_le_settimane if s != label_corr and s != label_pros
    ]

    settimane_disponibili = (
        settimane_storiche if settimane_storiche else tutte_le_settimane
    )

    if not settimane_disponibili:
        st.info("Nessun dato presente nell'archivio storico.")
    else:
        storico_scelto = st.selectbox(
            "Seleziona la settimana dall'archivio:", settimane_disponibili
        )

        turni_storico = [
            t for t in tutti_i_turni if t.get("settimana") == storico_scelto
        ]

        giorni_settimana = [
            "Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"
        ]

        for giorno in giorni_settimana:
            st.markdown(f"## 📌 {giorno}")
            turni_giorno = [t for t in turni_storico if t["giorno"] == giorno]
            col_m, col_p = st.columns(2)

            def mostra_fascia_storica(fascia_nome, col_container):
                with col_container:
                    st.markdown(f"### ☀️ {fascia_nome}")
                    turni_fascia = [
                        t for t in turni_giorno if t["fascia"] == fascia_nome
                    ]

                    if not turni_fascia:
                        st.caption("Nessun volontario registrato in questa fascia.")
                        return

                    st.markdown("**Volontari presenti:**")
                    for t in turni_fascia:
                        cani_str = (
                            ", ".join(t["cani_fatti"])
                            if t["cani_fatti"]
                            else "Nessuno"
                        )
                        st.write(
                            f"• **{t['volontario']}** ({t['orario']}) 🐾 [{cani_str}]"
                        )
                        if t["note"]:
                            st.caption(f"Note: {t['note']}")

            with col_m:
                mostra_fascia_storica("Mattina", col_m)
            with col_p:
                mostra_fascia_storica("Pomeriggio", col_p)

            st.markdown("---")
