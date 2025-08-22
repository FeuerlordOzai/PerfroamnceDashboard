import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pickle
import os

st.set_page_config(page_title="ReparaturMeister Performance Dashboard", layout="wide")
st.title("🔧 ReparaturMeister Performance Dashboard")

# --- Datenpersistenz ---
DATA_FILE = "reparaturmeister_data.pkl"


def load_data():
    """Lädt gespeicherte Daten aus Datei"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'rb') as f:
                data = pickle.load(f)
                data["Datum"] = pd.to_datetime(data["Datum"])
                return data
        except:
            return pd.DataFrame(
                columns=["Datum", "Mitarbeiter", "Auftraege", "Bar", "EC_Karte", "Ueberweisung", "Materialkosten",
                         "Umsatz", "Gewinn"])
    else:
        return pd.DataFrame(
            columns=["Datum", "Mitarbeiter", "Auftraege", "Bar", "EC_Karte", "Ueberweisung", "Materialkosten", "Umsatz",
                     "Gewinn"])


def save_data(data):
    """Speichert Daten in Datei"""
    with open(DATA_FILE, 'wb') as f:
        pickle.dump(data, f)


# --- Session State für Daten speichern ---
if "data" not in st.session_state:
    st.session_state["data"] = load_data()

# --- Eingabeformular ---
st.sidebar.header("📊 Neue Daten eingeben")
with st.sidebar.form("eingabe_form"):
    datum = st.date_input("Datum")
    mitarbeiter = st.selectbox("Mitarbeiter", ["Momo", "Lom", "Musti", "Murat", "Jan", "Mehdi", "Antonio"])
    auftraege = st.number_input("Anzahl Aufträge", min_value=0, step=1)

    st.write("**Umsatz aufteilen:**")
    bar = st.number_input("Bar (€)", min_value=0.0, step=10.0)
    ec_karte = st.number_input("EC-Karte (€)", min_value=0.0, step=10.0)
    ueberweisung = st.number_input("Überweisung (€)", min_value=0.0, step=10.0)

    st.write("**Kosten:**")
    materialkosten = st.number_input("Materialkosten/Neugerät (€)", min_value=0.0, step=10.0)

    umsatz_gesamt = bar + ec_karte + ueberweisung
    gewinn = umsatz_gesamt - materialkosten

    st.write(f"**Gesamtumsatz: {umsatz_gesamt:.2f} €**")
    st.write(f"**Gewinn: {gewinn:.2f} €**")

    submit = st.form_submit_button("Hinzufügen")

if submit:
    neue_daten = pd.DataFrame(
        [[datum, mitarbeiter, auftraege, bar, ec_karte, ueberweisung, materialkosten, umsatz_gesamt, gewinn]],
        columns=["Datum", "Mitarbeiter", "Auftraege", "Bar", "EC_Karte", "Ueberweisung", "Materialkosten", "Umsatz",
                 "Gewinn"])
    neue_daten["Datum"] = pd.to_datetime(neue_daten["Datum"])
    st.session_state["data"] = pd.concat([st.session_state["data"], neue_daten], ignore_index=True)

    # Daten speichern
    save_data(st.session_state["data"])

    st.success(f"✅ Daten für {mitarbeiter} am {datum} hinzugefügt!")

# --- Datenanzeige mit Filter ---
st.subheader("📋 Gespeicherte Daten")

if not st.session_state["data"].empty:
    # Filter für Datenanzeige
    col1, col2 = st.columns(2)
    with col1:
        anzeige_filter = st.selectbox(
            "Anzeige filtern:",
            ["Alle", "Täglich", "Wöchentlich", "Monatlich"]
        )

    with col2:
        if anzeige_filter != "Alle":
            datum_von = st.date_input("Von Datum", value=st.session_state["data"]["Datum"].min().date())
            datum_bis = st.date_input("Bis Datum", value=st.session_state["data"]["Datum"].max().date())

    # Daten filtern
    df_filtered = st.session_state["data"].copy()

    if anzeige_filter != "Alle":
        df_filtered = df_filtered[
            (df_filtered["Datum"].dt.date >= datum_von) &
            (df_filtered["Datum"].dt.date <= datum_bis)
            ]

        if anzeige_filter == "Wöchentlich":
            df_filtered = df_filtered.groupby([
                pd.Grouper(key="Datum", freq="W-MON"),
                "Mitarbeiter"
            ]).agg({
                "Auftraege": "sum",
                "Bar": "sum",
                "EC_Karte": "sum",
                "Ueberweisung": "sum",
                "Materialkosten": "sum",
                "Umsatz": "sum",
                "Gewinn": "sum"
            }).reset_index()

        elif anzeige_filter == "Monatlich":
            df_filtered = df_filtered.groupby([
                pd.Grouper(key="Datum", freq="M"),
                "Mitarbeiter"
            ]).agg({
                "Auftraege": "sum",
                "Bar": "sum",
                "EC_Karte": "sum",
                "Ueberweisung": "sum",
                "Materialkosten": "sum",
                "Umsatz": "sum",
                "Gewinn": "sum"
            }).reset_index()

    # Löschfunktion
    df_display = df_filtered.copy()
    df_display["Löschen"] = False
    delete_form = st.form("delete_form")
    with delete_form:
        edited_df = st.data_editor(df_display, num_rows="fixed")
        delete_submit = st.form_submit_button("Ausgewählte Einträge löschen")

    if delete_submit and anzeige_filter == "Alle":
        st.session_state["data"] = edited_df[~edited_df["Löschen"]].drop(columns="Löschen")
        # Daten speichern nach Löschung
        save_data(st.session_state["data"])
        st.success("🗑️ Ausgewählte Einträge gelöscht!")
    elif delete_submit and anzeige_filter != "Alle":
        st.warning("⚠️ Löschen nur in der 'Alle' Ansicht möglich!")

    st.dataframe(df_filtered)

    # --- Exportfunktion ---
    st.download_button(
        label="📥 Daten als CSV herunterladen",
        data=df_filtered.to_csv(index=False).encode("utf-8"),
        file_name=f"reparaturmeister_daten_{anzeige_filter.lower()}.csv",
        mime="text/csv"
    )

if not st.session_state["data"].empty:
    df = st.session_state["data"].copy()
    df["Datum"] = pd.to_datetime(df["Datum"])

    # --- KPIs Gesamt mit Zeitraum ---
    st.subheader("📈 Gesamtübersicht")

    min_datum = df["Datum"].min().strftime("%d.%m.%Y")
    max_datum = df["Datum"].max().strftime("%d.%m.%Y")
    zeitraum_text = f"Zeitraum: {min_datum} bis {max_datum}"

    st.write(f"**{zeitraum_text}**")

    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    col1.metric("Gesamt Umsatz (€)", f"{df['Umsatz'].sum():,.2f}")
    col2.metric("Materialkosten (€)", f"{df['Materialkosten'].sum():,.2f}")
    col3.metric("Gewinn (€)", f"{df['Gewinn'].sum():,.2f}")
    col4.metric("Gesamt Aufträge", f"{df['Auftraege'].sum()}")
    col5.metric("Bar (€)", f"{df['Bar'].sum():,.2f}")
    col6.metric("EC-Karte (€)", f"{df['EC_Karte'].sum():,.2f}")
    col7.metric("Überweisung (€)", f"{df['Ueberweisung'].sum():,.2f}")

    # --- Tortendiagramm: Gewinn vs Materialkosten ---
    st.subheader("🥧 Gewinn vs. Materialkosten")

    col1, col2 = st.columns(2)

    with col1:
        gesamt_gewinn = df['Gewinn'].sum()
        gesamt_materialkosten = df['Materialkosten'].sum()

        if gesamt_gewinn > 0 or gesamt_materialkosten > 0:
            fig_pie = go.Figure(data=[go.Pie(
                labels=['Gewinn', 'Materialkosten'],
                values=[gesamt_gewinn, gesamt_materialkosten],
                marker_colors=['green', 'red'],
                hovertemplate="<b>%{label}</b><br>%{value:.2f}€<br>%{percent}<extra></extra>"
            )])

            fig_pie.update_layout(
                title="Gewinn vs. Materialkosten",
                height=400
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Keine Daten für Tortendiagramm verfügbar")

    with col2:
        # Gewinnmarge berechnen
        if df['Umsatz'].sum() > 0:
            gewinnmarge = (df['Gewinn'].sum() / df['Umsatz'].sum()) * 100
            st.metric("Gewinnmarge (%)", f"{gewinnmarge:.1f}%")

        # Durchschnittlicher Gewinn pro Auftrag
        if df['Auftraege'].sum() > 0:
            gewinn_pro_auftrag = df['Gewinn'].sum() / df['Auftraege'].sum()
            st.metric("Ø Gewinn/Auftrag (€)", f"{gewinn_pro_auftrag:.2f}")

    # --- Plot: Umsatz pro Mitarbeiter ---
    st.subheader("💰 Umsatz pro Mitarbeiter")
    umsatz_pro_ma = df.groupby("Mitarbeiter").agg({
        "Umsatz": "sum",
        "Gewinn": "sum",
        "Materialkosten": "sum",
        "Bar": "sum",
        "EC_Karte": "sum",
        "Ueberweisung": "sum"
    }).sort_values("Umsatz", ascending=False)

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=umsatz_pro_ma.index,
        y=umsatz_pro_ma["Bar"],
        name="Bar",
        marker_color="green",
        hovertemplate="<b>%{x}</b><br>Bar: %{y:.2f}€<extra></extra>"
    ))
    fig_bar.add_trace(go.Bar(
        x=umsatz_pro_ma.index,
        y=umsatz_pro_ma["EC_Karte"],
        name="EC-Karte",
        marker_color="blue",
        hovertemplate="<b>%{x}</b><br>EC-Karte: %{y:.2f}€<extra></extra>"
    ))
    fig_bar.add_trace(go.Bar(
        x=umsatz_pro_ma.index,
        y=umsatz_pro_ma["Ueberweisung"],
        name="Überweisung",
        marker_color="orange",
        hovertemplate="<b>%{x}</b><br>Überweisung: %{y:.2f}€<extra></extra>"
    ))

    fig_bar.update_layout(
        title="Umsatz nach Mitarbeitern (aufgeteilt nach Zahlungsart)",
        xaxis_title="Mitarbeiter",
        yaxis_title="Umsatz (€)",
        barmode="stack",
        height=500
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- Plot: Gewinn pro Mitarbeiter ---
    st.subheader("💚 Gewinn pro Mitarbeiter")

    fig_gewinn = go.Figure()
    fig_gewinn.add_trace(go.Bar(
        x=umsatz_pro_ma.index,
        y=umsatz_pro_ma["Gewinn"],
        name="Gewinn",
        marker_color="darkgreen",
        hovertemplate="<b>%{x}</b><br>" +
                      "Gewinn: %{y:.2f}€<br>" +
                      "Umsatz: %{customdata[0]:.2f}€<br>" +
                      "Materialkosten: %{customdata[1]:.2f}€<extra></extra>",
        customdata=umsatz_pro_ma[["Umsatz", "Materialkosten"]].values
    ))

    fig_gewinn.update_layout(
        title="Gewinn nach Mitarbeitern",
        xaxis_title="Mitarbeiter",
        yaxis_title="Gewinn (€)",
        height=500
    )
    st.plotly_chart(fig_gewinn, use_container_width=True)

    # --- Plot: Entwicklung über Zeit (gesamt) ---
    st.subheader("📊 Umsatz- und Gewinnentwicklung (gesamt)")

    ansicht = st.radio(
        "Ansicht wählen:",
        ["Täglich", "Wöchentlich", "Monatlich"],
        horizontal=True,
        key="gesamtansicht"
    )

    if ansicht == "Täglich":
        df_grouped = df.groupby("Datum").agg({
            "Umsatz": "sum",
            "Gewinn": "sum",
            "Materialkosten": "sum",
            "Bar": "sum",
            "EC_Karte": "sum",
            "Ueberweisung": "sum"
        }).reset_index()
        title = "Umsatz- und Gewinnentwicklung pro Tag"
    elif ansicht == "Wöchentlich":
        df_grouped = df.groupby(pd.Grouper(key="Datum", freq="W-MON")).agg({
            "Umsatz": "sum",
            "Gewinn": "sum",
            "Materialkosten": "sum",
            "Bar": "sum",
            "EC_Karte": "sum",
            "Ueberweisung": "sum"
        }).reset_index()
        title = "Umsatz- und Gewinnentwicklung pro Woche"
    else:  # Monatlich
        df_grouped = df.groupby(pd.Grouper(key="Datum", freq="M")).agg({
            "Umsatz": "sum",
            "Gewinn": "sum",
            "Materialkosten": "sum",
            "Bar": "sum",
            "EC_Karte": "sum",
            "Ueberweisung": "sum"
        }).reset_index()
        title = "Umsatz- und Gewinnentwicklung pro Monat"

    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=df_grouped["Datum"],
        y=df_grouped["Umsatz"],
        mode="lines+markers",
        name="Umsatz",
        line=dict(color="blue", width=3),
        marker=dict(size=8),
        hovertemplate="<b>%{x}</b><br>" +
                      "Umsatz: %{y:.2f}€<br>" +
                      "Bar: %{customdata[0]:.2f}€<br>" +
                      "EC-Karte: %{customdata[1]:.2f}€<br>" +
                      "Überweisung: %{customdata[2]:.2f}€<extra></extra>",
        customdata=df_grouped[["Bar", "EC_Karte", "Ueberweisung"]].values
    ))

    fig_line.add_trace(go.Scatter(
        x=df_grouped["Datum"],
        y=df_grouped["Gewinn"],
        mode="lines+markers",
        name="Gewinn",
        line=dict(color="green", width=3),
        marker=dict(size=8),
        hovertemplate="<b>%{x}</b><br>" +
                      "Gewinn: %{y:.2f}€<br>" +
                      "Materialkosten: %{customdata:.2f}€<extra></extra>",
        customdata=df_grouped["Materialkosten"].values
    ))

    fig_line.update_layout(
        title=title,
        xaxis_title="Datum",
        yaxis_title="Betrag (€)",
        height=500
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # --- Mitarbeiter Detailansicht ---
    st.subheader("🔍 Detailansicht Mitarbeiter")
    ma_choice = st.selectbox("Mitarbeiter auswählen", df["Mitarbeiter"].unique())
    df_ma = df[df["Mitarbeiter"] == ma_choice]

    ansicht_ma = st.radio(
        "Ansicht wählen (Mitarbeiter):",
        ["Täglich", "Wöchentlich", "Monatlich"],
        horizontal=True,
        key="ma_ansicht"
    )

    if ansicht_ma == "Täglich":
        df_ma_grouped = df_ma.groupby("Datum").agg({
            "Umsatz": "sum",
            "Gewinn": "sum",
            "Materialkosten": "sum",
            "Bar": "sum",
            "EC_Karte": "sum",
            "Ueberweisung": "sum"
        }).reset_index()
        title = f"Umsatz- und Gewinnentwicklung (täglich) von {ma_choice}"
    elif ansicht_ma == "Wöchentlich":
        df_ma_grouped = df_ma.groupby(pd.Grouper(key="Datum", freq="W-MON")).agg({
            "Umsatz": "sum",
            "Gewinn": "sum",
            "Materialkosten": "sum",
            "Bar": "sum",
            "EC_Karte": "sum",
            "Ueberweisung": "sum"
        }).reset_index()
        title = f"Umsatz- und Gewinnentwicklung (wöchentlich) von {ma_choice}"
    else:  # Monatlich
        df_ma_grouped = df_ma.groupby(pd.Grouper(key="Datum", freq="M")).agg({
            "Umsatz": "sum",
            "Gewinn": "sum",
            "Materialkosten": "sum",
            "Bar": "sum",
            "EC_Karte": "sum",
            "Ueberweisung": "sum"
        }).reset_index()
        title = f"Umsatz- und Gewinnentwicklung (monatlich) von {ma_choice}"

    fig_ma = go.Figure()
    fig_ma.add_trace(go.Scatter(
        x=df_ma_grouped["Datum"],
        y=df_ma_grouped["Umsatz"],
        mode="lines+markers",
        name="Umsatz",
        line=dict(color="blue", width=3),
        marker=dict(size=8),
        hovertemplate="<b>%{x}</b><br>" +
                      "Umsatz: %{y:.2f}€<br>" +
                      "Bar: %{customdata[0]:.2f}€<br>" +
                      "EC-Karte: %{customdata[1]:.2f}€<br>" +
                      "Überweisung: %{customdata[2]:.2f}€<extra></extra>",
        customdata=df_ma_grouped[["Bar", "EC_Karte", "Ueberweisung"]].values
    ))

    fig_ma.add_trace(go.Scatter(
        x=df_ma_grouped["Datum"],
        y=df_ma_grouped["Gewinn"],
        mode="lines+markers",
        name="Gewinn",
        line=dict(color="green", width=3),
        marker=dict(size=8),
        hovertemplate="<b>%{x}</b><br>" +
                      "Gewinn: %{y:.2f}€<br>" +
                      "Materialkosten: %{customdata:.2f}€<extra></extra>",
        customdata=df_ma_grouped["Materialkosten"].values
    ))

    fig_ma.update_layout(
        title=title,
        xaxis_title="Datum",
        yaxis_title="Betrag (€)",
        height=500
    )
    st.plotly_chart(fig_ma, use_container_width=True)

# --- Daten-Reset Button (nur für Entwicklung) ---
st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Alle Daten löschen", type="secondary"):
    if st.sidebar.button("⚠️ Wirklich löschen?", type="secondary"):
        st.session_state["data"] = pd.DataFrame(
            columns=["Datum", "Mitarbeiter", "Auftraege", "Bar", "EC_Karte", "Ueberweisung", "Materialkosten", "Umsatz",
                     "Gewinn"])
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        st.success("Alle Daten gelöscht!")
        st.rerun()