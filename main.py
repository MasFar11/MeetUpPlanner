import pandas as pd
import streamlit as st
import datetime

# ------------------------------------------------------------
# Hilfsfunktionen
# ------------------------------------------------------------

def to_hour_float(value):
    """Konvertiert Zeitwerte in Dezimalstunden (z. B. 10.5 für 10:30)."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, datetime.time):
        return value.hour + value.minute / 60
    if isinstance(value, str):
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                t = datetime.datetime.strptime(value, fmt).time()
                return t.hour + t.minute / 60
            except ValueError:
                continue
    raise ValueError(f"❌ Unbekanntes Zeitformat: {value}")

def format_time(hour):
    """Formatiert Dezimalstunden zu HH:MM."""
    h = int(hour)
    m = int(round((hour - h) * 60))
    return f"{h:02d}:{m:02d}"

# ------------------------------------------------------------
# Hauptlogik: Gemeinsame freie Zeiten finden
# ------------------------------------------------------------

def finde_freie_zeiten(df, tage, uni_zeit=(8, 18), debug=False):
    freie_zeiten = {}
    for tag in tage:
        personen = df["Person"].unique()
        person_frei = {}

        for person in personen:
            besetzt = []
            # --- Alle belegten Zeiten dieser Person an diesem Tag sammeln ---
            for _, row in df.iterrows():
                if row["Person"] == person and row["Tag"] == tag:
                    s = to_hour_float(row["Start"])
                    e = to_hour_float(row["Ende"])
                    besetzt.append((s, e))

            frei = []
            start = uni_zeit[0]

            # --- Lücken zwischen belegten Zeiten finden ---
            for s, e in sorted(besetzt):
                if debug:
                    print(f"DEBUG {person=} {tag=} {s=} {start=}")
                if s > start:
                    frei.append((start, s))
                start = max(start, e)

            # --- Zeit nach letztem Termin bis Uni-Ende ---
            if start < uni_zeit[1]:
                frei.append((start, uni_zeit[1]))

            person_frei[person] = frei

        # --- Gemeinsame freie Zeitfenster berechnen ---
        gemeinsame_frei = person_frei[personen[0]]
        for person in personen[1:]:
            neue_frei = []
            for (a_start, a_ende) in gemeinsame_frei:
                for (b_start, b_ende) in person_frei[person]:
                    start = max(a_start, b_start)
                    ende = min(a_ende, b_ende)
                    if start < ende:
                        neue_frei.append((start, ende))
            gemeinsame_frei = neue_frei

        freie_zeiten[tag] = gemeinsame_frei

    return freie_zeiten

# ------------------------------------------------------------
# Konsolenmodus
# ------------------------------------------------------------

def console_mode():
    df = pd.read_excel("stundenplan.xlsx")
    tage = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
    freie_zeiten = finde_freie_zeiten(df, tage, debug=False)

    print("📅 Gemeinsame freie Zeiten:")
    for tag, fenster in freie_zeiten.items():
        if fenster:
            zeiten = [f"{format_time(s)} - {format_time(e)}" for s, e in fenster]
            print(f"{tag}: {', '.join(zeiten)}")
        else:
            print(f"{tag}: keine gemeinsamen freien Zeiten")

# ------------------------------------------------------------
# Streamlit-Modus
# ------------------------------------------------------------

def browser_mode():
    st.title("📅 Gemeinsame freie Zeiten finden")
    st.markdown("Lade deine Stundenplan-Datei hoch (.xlsx) und wähle Tagesbeginn/-ende:")

    uploaded_file = st.file_uploader("Excel-Datei hochladen", type="xlsx")

    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        tage = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]

        col1, col2 = st.columns(2)
        with col1:
            start_tag = st.number_input("Tagesbeginn (z. B. 8 für 08:00)", min_value=0, max_value=23, value=8)
        with col2:
            ende_tag = st.number_input("Tagesende (z. B. 18 für 18:00)", min_value=1, max_value=24, value=18)

        freie_zeiten = finde_freie_zeiten(df, tage, uni_zeit=(start_tag, ende_tag))

        st.subheader("Ergebnisse:")
        for tag, fenster in freie_zeiten.items():
            if fenster:
                zeiten = [f"{format_time(s)} - {format_time(e)}" for s, e in fenster]
                st.success(f"{tag}: {', '.join(zeiten)}")
            else:
                st.error(f"{tag}: keine gemeinsamen freien Zeiten")

# ------------------------------------------------------------
# Einstiegspunkt
# ------------------------------------------------------------

if __name__ == "__main__":
    import sys
    if "streamlit" in sys.argv[0]:
        browser_mode()
    else:
        console_mode()
