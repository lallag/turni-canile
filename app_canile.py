from datetime import datetime, timedelta
import json
import urllib.error
import urllib.request
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Gestione Turni Canile", page_icon="🐾", layout="wide"
)
st.markdown(
    """
    <head>
        <link rel="apple-touch-icon" href="zampa.png">
        <link rel="icon" type="image/png" href="zampa.png">
    </head>
""",
    unsafe_allow_html=True,
)

# --- GESTIONE DATI PERSISTENTI TRAMITE GITHUB ---
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


# Inizializzazione stato con i file su GitHub (e lista cani predefinita)
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

st.title("🐾 Gestione Turni e Copertura Canile")

adesso = datetime.now()
giorno_settimana = adesso.weekday()
ora_attuale = adesso.hour

is_weekend_reale = (giorno_settimana > 4) or (
    giorno_settimana == 4 and ora_attuale >= 18
)
is_weekend_o_venerdi_sera = is_weekend_reale

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

  # --- SIMULATORE PER ANTEPRIMA (VISIBILE SOLO AGLI ADMIN) ---
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

  if st.sidebar.button("🔒 Esci da Modalità Admin"):
    st.session_state.is_admin = False
    st.rerun()

# --- MENU PRINCIPALE AGGIORNATO ---
opzioni_menu = [
    "📅 Inserisci / Modifica Turno",
    "👀 Visualizza Panoramica Settimanale",
    "🐶 Gestione Cani",
    "📊 Statistiche Cani",
    "📚 Archivio Storico",
]
menu = st.sidebar.selectbox("Menu", opzioni_menu)


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

if menu == "📅 Inserisci / Modifica Turno":
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

  with st.form("form_turno"):
    col1, col2 = st.columns(2)

    with col1:
      volontario = st.text_input("Tuo Nome e Cognome:")
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
      orario = st.text_input(
          "Orario di presenza (es. 09:00 - 12:00):", "09:00 - 12:00"
      )
      note = st.text_area("Note aggiuntive (opzionale):")

    st.subheader("Gestione Cani per questo turno")

    seleziona_tutti = st.checkbox("🐾 Seleziona TUTTI i cani")

    if seleziona_tutti:
      cani_fatti = st.multiselect(
          "✅ Cani che sei autorizzato a gestire:",
          st.session_state.cani,
          default=st.session_state.cani,
      )
    else:
      cani_fatti = st.multiselect(
          "✅ Cani che sei autorizzato a gestire:", st.session_state.cani
      )

    submit_button = st.form_submit_button(label="Registra Turno 🚀")

    if submit_button:
      if volontario.strip() == "":
        st.warning(
            "Per favore, inserisci il tuo nome prima di registrare il turno."
        )
      else:
        lista_turni = carica_file_json(DB_TURNI, [])
        nuovo_turno = {
            "id": str(datetime.now().timestamp()),
            "settimana": settimana_scelta,
            "volontario": volontario.strip(),
            "giorno": giorno,
            "fascia": fascia,
            "orario": orario,
            "cani_fatti": cani_fatti,
            "note": note,
        }
        lista_turni.append(nuovo_turno)
        salva_file_json(DB_TURNI, lista_turni)
        st.success(f"Turno registrato con successo per {volontario}!")

elif menu == "👀 Visualizza Panoramica Settimanale":
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
                ", ".join(t["cani_fatti"]) if t["cani_fatti"] else "Nessuno"
            )
            st.write(
                f"• **{t['volontario']}** ({t['orario']}) 🐾 [{cani_str}]"
            )
            if t["note"]:
              st.caption(f"Note: {t['note']}")

            if st.session_state.is_admin:
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
                st.success("Turno eliminato!")
                st.rerun()

          cani_coperti = set()
          for t in turni_fascia:
            for c in t["cani_fatti"]:
              cani_coperti.add(c)

          cani_scoperti = [
              c for c in st.session_state.cani if c not in cani_coperti
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

elif menu == "🐶 Gestione Cani":
  st.header("Gestione Anagrafica Cani")

  if not st.session_state.is_admin:
    st.warning(
        "🔒 Questa sezione è protetta. Inserisci la password da amministratrice"
        " nella barra laterale a sinistra per aggiungere o rimuovere i cani."
    )
    st.subheader("Lista attuale dei cani in canile:")
    for dog in st.session_state.cani:
      st.write(f"🐾 **{dog}**")
  else:
    st.markdown(
        "Aggiungi o rimuovi i cani presenti in canile (Modalità Admin attiva)."
    )

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

elif menu == "📊 Statistiche Cani":
  st.header("📊 Statistiche Uscite Cani")
  st.markdown(
      "Panoramica delle uscite settimanali per ogni cane (calcolate a livello"
      " di fascia oraria, così se più volontari portano lo stesso cane nello"
      " stesso turno, viene contato come un'unica uscita)."
  )

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

  turni_stat = [t for t in tutti_i_turni if t.get("settimana") == settimana_stat]

  # --- CALCOLO CORRETTO: UN'USCITA PER FASCIA ORARIA (Giorno + Mattina/Pomeriggio) ---
  uscite_per_cane = {cane: 0 for cane in st.session_state.cani}

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
    for fascia in ["Mattina", "Pomeriggio"]:
      turni_fascia = [
          t
          for t in turni_stat
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
            list(uscite_per_cane.items()), columns=["Cane", "Numero Uscite"]
        )
        df_stat = df_stat.set_index("Cane")
        st.bar_chart(df_stat)

    with col_tabella:
      st.subheader("📋 Tabella Dati")
      df_tabella = pd.DataFrame(
          list(uscite_per_cane.items()), columns=["Cane", "Uscite"]
      )
      df_tabella = df_tabella.sort_values(
          by="Uscite", ascending=False
      ).reset_index(drop=True)
      st.dataframe(df_tabella, use_container_width=True)

elif menu == "📚 Archivio Storico":
  st.header("📚 Archivio Storico delle Settimane Passate")
  st.markdown(
      "Qui puoi consultare lo storico di tutte le settimane registrate in"
      " precedenza."
  )

  tutti_i_turni = carica_file_json(DB_TURNI, [])
  tutte_le_settimane = sorted(
      list(set(t.get("settimana") for t in tutti_i_turni))
  )
  settimane_storiche = [
      s for s in tutte_le_settimane if s != label_corr and s != label_pros
  ]

  if not settimane_storiche and not tutti_i_turni:
    st.info("Nessun dato presente nell'archivio storico.")
  else:
    settimane_disponibili = (
        settimane_storiche if settimane_storiche else tutte_le_settimane
    )

    if not settimane_disponibili:
      st.info("Non ci sono ancora settimane passate archiviate.")
    else:
      storico_scelto = st.selectbox(
          "Seleziona la settimana dall'archivio:", settimane_disponibili
      )

      turni_storico = [
          t for t in tutti_i_turni if t.get("settimana") == storico_scelto
      ]

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
                  ", ".join(t["cani_fatti"]) if t["cani_fatti"] else "Nessuno"
              )
              st.write(
                  f"• **{t['volontario']}** ({t['orario']}) 🐾 [{cani_str}]"
              )
              if t["note"]:
                st.caption(f"Note: {t['note']}")

              if st.session_state.is_admin:
                if st.button(
                    f"🗑️ Elimina ({t['volontario']})",
                    key=f"del_storico_{giorno}_{fascia_nome}_{t['id']}",
                ):
                  lista_aggiornata = [
                      item
                      for item in carica_file_json(DB_TURNI, [])
                      if item["id"] != t["id"]
                  ]
                  salva_file_json(DB_TURNI, lista_aggiornata)
                  st.success("Turno eliminato!")
                  st.rerun()

        with col_m:
          mostra_fascia_storica("Mattina", col_m)
        with col_p:
          mostra_fascia_storica("Pomeriggio", col_p)

        st.markdown("---")
