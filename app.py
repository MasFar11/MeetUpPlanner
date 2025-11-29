import pandas as pd
import streamlit as st

def format_time(hour):
    """Formatiert Dezimalstunden als HH:MM"""
    h = int(hour)
    m = int((hour - h) * 60)
    return f"{h:02d}:{m:02d}"

def finde_freie_zeiten(df, tage, uni_zeit=(8, 18)):
    freie_zeiten = {}
    for tag in tage:
        personen = df["Person"].unique()
        person_frei = {}
        for person in personen:
            besetzt = []
            for _, row in df.iterrows():
                if row["Person"] == person and row["Tag"] == tag:
                    besetzt.append((row["Start"], row["Ende"]))
            frei = []
            start = uni_zeit[0]
            for s, e in sorted(besetzt):
                if s > start:
                    frei.append((start, s))
                start = max(start, e)
            if start < uni_zeit[1]:
                frei.append((start, uni_zeit[1]))
            person_frei[person] = frei

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

# ------------------- Streamlit Web-App -------------------
st.title("📅 Gemeinsame freie Zeiten finden")
st.markdown("Lade deine Stundenplan-Datei hoch (.xlsx) und wähle Tagesbeginn/-ende:")

uploaded_file = st.file_uploader("Excel-Datei hochladen", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    tage = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]

    # Benutzer wählt Tagesbeginn und -ende
    col1, col2 = st.columns(2)
    with col1:
        start_tag = st.number_input("start (z. B. 8 für 08:00)", min_value=0, max_value=23, value=8)
    with col2:
        ende_tag = st.number_input("Tagesende (z. B. 18 für 18:00)", min_value=1, max_value=24, value=18)

    # Berechnung
    freie_zeiten = finde_freie_zeiten(df, tage, uni_zeit=(start_tag, ende_tag))

    # Ergebnisse anzeigen
    st.subheader("Ergebnisse:")
    for tag, fenster in freie_zeiten.items():
        if fenster:
            zeiten = [f"{format_time(s)} - {format_time(e)}" for s, e in fenster]
            st.success(f"{tag}: {', '.join(zeiten)}")
        else:
            st.error(f"{tag}: keine gemeinsamen freien Zeiten")
