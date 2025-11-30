import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------

def to_decimal(t):
    """Konvertiert Excel-Zeiten in Dezimalstunden."""
    if pd.isna(t):
        return None

    if isinstance(t, (int, float)):
        return float(t)

    if isinstance(t, str):
        try:
            h, m = t.split(":")
            return int(h) + int(m)/60
        except:
            pass

    if hasattr(t, "hour"):
        return t.hour + t.minute/60

    raise ValueError(f"Unbekanntes Zeitformat: {t}")


def format_time(hour):
    """Formatiert Dezimalstunden als HH:MM."""
    h = int(hour)
    m = int(round((hour - h) * 60))
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
                    if row["Start"] is not None and row["Ende"] is not None:
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


# ---------------------------------------------------------
# Neue Funktion – Zeiten mit maximal vielen freien Personen
# ---------------------------------------------------------

def finde_teilweise_freie_zeiten(df, tage, uni_zeit=(8, 18), schritt=0.25):
    """
    Findet für jeden Tag Intervalle, in denen möglichst viele Personen gleichzeitig frei sind.
    0.25 Stunden = 15-Minuten-Schritte.
    """
    personen = df["Person"].unique()
    result = {}

    for tag in tage:
        slots = []
        t = uni_zeit[0]
        while t < uni_zeit[1]:
            slots.append(t)
            t += schritt

        frei_counts = []
        for t in slots:
            frei = 0
            for person in personen:
                besetzt = False
                for _, row in df[(df["Person"] == person) & (df["Tag"] == tag)].iterrows():
                    if row["Start"] <= t < row["Ende"]:
                        besetzt = True
                        break
                if not besetzt:
                    frei += 1
            frei_counts.append(frei)

        # Intervalle gleicher Anzahl Personen zusammenfassen
        intervalle = []
        start = slots[0]
        current_count = frei_counts[0]

        for i in range(1, len(slots)):
            if frei_counts[i] != current_count:
                intervalle.append((start, slots[i], current_count))
                start = slots[i]
                current_count = frei_counts[i]

        intervalle.append((start, slots[-1], current_count))
        result[tag] = intervalle

    return result


# ---------------------------------------------------------
# Streamlit App
# ---------------------------------------------------------

st.title("📅 Gemeinsame freie Zeiten finden")
st.markdown("Lade deine Stundenplan-Datei hoch (.xlsx) und wähle Tagesbeginn/-ende:")

uploaded_file = st.file_uploader("Excel-Datei hochladen", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    required_columns = {"Person", "Tag", "Start", "Ende"}
    if not required_columns.issubset(df.columns):
        st.error("Fehlende Spalten! Es werden benötigt: Person, Tag, Start, Ende")
        st.stop()

    df["Start"] = df["Start"].apply(to_decimal)
    df["Ende"] = df["Ende"].apply(to_decimal)

    tage = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]

    col1, col2 = st.columns(2)
    with col1:
        start_tag = st.number_input("Tagesbeginn", min_value=0, max_value=23, value=8)
    with col2:
        ende_tag = st.number_input("Tagesende", min_value=1, max_value=24, value=18)

    freie_zeiten = finde_freie_zeiten(df, tage, uni_zeit=(start_tag, ende_tag))
    teilweise_frei = finde_teilweise_freie_zeiten(df, tage, uni_zeit=(start_tag, ende_tag))

    st.subheader("Ergebnisse:")

    for tag in tage:
        fenster = freie_zeiten[tag]

        # ──────────────────────────────────────────────────────────
        # Fall 1: gemeinsame freie Zeiten existieren
        # ──────────────────────────────────────────────────────────
        if fenster:
            zeiten = [f"{format_time(s)} - {format_time(e)}" for s, e in fenster]
            st.success(f"{tag}: {', '.join(zeiten)}")

        # ──────────────────────────────────────────────────────────
        # Fall 2: keine gemeinsamen freien Zeiten → Alternativen zeigen
        # ──────────────────────────────────────────────────────────
        else:
            st.error(f"{tag}: keine gemeinsamen freien Zeiten")

            teile = teilweise_frei[tag]
            max_frei = max(c for _, _, c in teile)
            beste = [(s, e, c) for s, e, c in teile if c == max_frei]

            st.info(f"➡ Beste Alternative: Maximal {max_frei} Personen gleichzeitig frei:")

            for s, e, c in beste:
                st.write(f"- {format_time(s)} – {format_time(e)} ({c} Personen)")
