import streamlit as st
import streamlit_authenticator as stauth
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="CRM MUK", page_icon="📋", layout="wide")

# ===== KAMOVI I STATUSSI =====
KAMOVI = [
    "Andreja Bartol",
    "Nikola Hitzhaler",
    "Kristian Crnjak",
    "Marija Šprišiš Mihelić",
    "Mario Žuti",
    "Kristijan Marčec",
    "Tomislav Fabečić",
    "Petra Trukhno"
]

STATUSI_KUPCI = ["Aktivan", "U riziku", "Neaktivan"]
STATUSI_POTENCIJALI = ["Novi", "Kontaktiran", "Sastanak", "Ponuda", "Pretvoren", "Odbačen"]

# ===== AUTENTIKACIJA =====
credentials = {
    "usernames": {
        "andreja.bartol": {
            "email": "andreja.bartol@muk.hr",
            "name": "Andreja Bartol",
            "password": st.secrets["passwords"]["andreja.bartol"]
        },
        "nikola.hitzhaler": {
            "email": "nikola.hitzhaler@muk.hr",
            "name": "Nikola Hitzhaler",
            "password": st.secrets["passwords"]["nikola.hitzhaler"]
        },
        "kristian.crnjak": {
            "email": "kristian.crnjak@muk.hr",
            "name": "Kristian Crnjak",
            "password": st.secrets["passwords"]["kristian.crnjak"]
        },
        "marija.sprisis.mihelic": {
            "email": "marija.sprisis.mihelic@muk.hr",
            "name": "Marija Šprišiš Mihelić",
            "password": st.secrets["passwords"]["marija.sprisis.mihelic"]
        },
        "mario.zuti": {
            "email": "mario.zuti@muk.hr",
            "name": "Mario Žuti",
            "password": st.secrets["passwords"]["mario.zuti"]
        },
        "kristijan.marcec": {
            "email": "kristijan.marcec@muk.hr",
            "name": "Kristijan Marčec",
            "password": st.secrets["passwords"]["kristijan.marcec"]
        },
        "tomislav.fabecic": {
            "email": "tomislav.fabecic@muk.hr",
            "name": "Tomislav Fabečić",
            "password": st.secrets["passwords"]["tomislav.fabecic"]
        },
        "petra.trukhno": {
            "email": "petra.trukhno@muk.hr",
            "name": "Petra Trukhno",
            "password": st.secrets["passwords"]["petra.trukhno"]
        }
    }
}

cookie = {
    "expiry_days": 30,
    "key": st.secrets["cookie_key"],
    "name": "crm_muk_cookie"
}

authenticator = stauth.Authenticate(
    credentials,
    cookie["name"],
    cookie["key"],
    cookie["expiry_days"]
)

# ===== GOOGLE SHEETS =====
@st.cache_resource
def get_gspread_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    return gspread.authorize(creds)

def get_sheet(sheet_name):
    client = get_gspread_client()
    spreadsheet = client.open("CRM MUK")
    return spreadsheet.worksheet(sheet_name)

def load_data(sheet_name):
    try:
        ws = get_sheet(sheet_name)
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Greška pri učitavanju {sheet_name}: {e}")
        return pd.DataFrame()

def save_dataframe(sheet_name, df):
    ws = get_sheet(sheet_name)
    ws.clear()
    # Pretvori sve u string da izbjegnemo probleme s tipovima
    df = df.astype(str)
    ws.update([df.columns.values.tolist()] + df.fillna("").values.tolist())

# ===== LOGIN =====
name, authentication_status, username = authenticator.login("Prijava", "main")

if authentication_status == False:
    st.error("Netočno korisničko ime ili lozinka")
elif authentication_status == None:
    st.warning("Unesite korisničko ime i lozinku")
elif authentication_status:

    authenticator.logout("Odjava", "sidebar")
    st.sidebar.success(f"Prijavljeni: **{name}**")

    st.title("📋 CRM MUK")
    st.caption("Praćenje kupaca i potencijala")

    tab1, tab2, tab3 = st.tabs(["👥 Kupci", "🌱 Potencijali", "📝 Bilješke"])

    # ========== KUPCI ==========
    with tab1:
        st.subheader("Kupci")
        df_kupci = load_data("Kupci")

        with st.expander("➕ Dodaj novog kupca", expanded=False):
            with st.form("novi_kupac"):
                col1, col2 = st.columns(2)
                with col1:
                    naziv = st.text_input("Naziv kupca *")
                    oib = st.text_input("OIB *", max_chars=11)
                    kam = st.selectbox("KAM", KAMOVI)
                with col2:
                    status = st.selectbox("Status", STATUSI_KUPCI)
                    biljeske = st.text_area("Bilješke")

                if st.form_submit_button("Spremi kupca"):
                    if not naziv or not oib:
                        st.error("Naziv i OIB su obavezni")
                    elif len(oib) != 11 or not oib.isdigit():
                        st.error("OIB mora imati točno 11 znamenki")
                    elif not df_kupci.empty and oib in df_kupci["OIB"].astype(str).values:
                        st.error("Kupac s ovim OIB-om već postoji!")
                    else:
                        new_row = {
                            "Naziv kupca": naziv,
                            "OIB": oib,
                            "KAM": kam,
                            "Status": status,
                            "Bilješke": biljeske,
                            "Zadnji izmijenio": name,
                            "Vrijeme izmjene": datetime.now().strftime("%d.%m.%Y %H:%M")
                        }
                        df_kupci = pd.concat([df_kupci, pd.DataFrame([new_row])], ignore_index=True)
                        save_dataframe("Kupci", df_kupci)
                        st.success("Kupac uspješno dodan!")
                        st.rerun()

        if not df_kupci.empty:
            st.dataframe(df_kupci, use_container_width=True, hide_index=True)
        else:
            st.info("Još nema kupaca.")

    # ========== POTENCIJALI ==========
    with tab2:
        st.subheader("Potencijali")
        df_pot = load_data("Potencijali")
        df_kupci = load_data("Kupci")

        with st.expander("➕ Dodaj novog potencijala", expanded=False):
            with st.form("novi_potencijal"):
                col1, col2 = st.columns(2)
                with col1:
                    naziv = st.text_input("Naziv potencijala *")
                    oib = st.text_input("OIB *", max_chars=11)
                    kontakt = st.text_input("Kontakt osoba")
                    telefon = st.text_input("Telefon / Email")
                with col2:
                    kam = st.selectbox("KAM", KAMOVI)
                    status = st.selectbox("Status", STATUSI_POTENCIJALI)
                    biljeske = st.text_area("Kratke bilješke")

                if st.form_submit_button("Spremi potencijal"):
                    if not naziv or not oib:
                        st.error("Naziv i OIB su obavezni")
                    elif len(oib) != 11 or not oib.isdigit():
                        st.error("OIB mora imati točno 11 znamenki")
                    else:
                        if not df_kupci.empty and oib in df_kupci["OIB"].astype(str).values:
                            postojeci = df_kupci[df_kupci["OIB"].astype(str) == oib]["Naziv kupca"].values[0]
                            st.warning(f"⚠️ Ovaj OIB već postoji kao kupac: {postojeci}")
                        elif not df_pot.empty and oib in df_pot["OIB"].astype(str).values:
                            st.error("Potencijal s ovim OIB-om već postoji!")
                        else:
                            new_row = {
                                "Naziv potencijala": naziv,
                                "OIB": oib,
                                "Kontakt osoba": kontakt,
                                "Telefon/Email": telefon,
                                "KAM": kam,
                                "Status": status,
                                "Bilješke": biljeske,
                                "Zadnji izmijenio": name,
                                "Vrijeme izmjene": datetime.now().strftime("%d.%m.%Y %H:%M")
                            }
                            df_pot = pd.concat([df_pot, pd.DataFrame([new_row])], ignore_index=True)
                            save_dataframe("Potencijali", df_pot)
                            st.success("Potencijal uspješno dodan!")
                            st.rerun()

        if not df_pot.empty:
            st.dataframe(df_pot, use_container_width=True, hide_index=True)
        else:
            st.info("Još nema potencijala.")

    # ========== BILJEŠKE ==========
    with tab3:
        st.subheader("Povijest bilješki")
        df_biljeske = load_data("Bilješke")

        with st.expander("➕ Nova bilješka", expanded=True):
            with st.form("nova_biljeska"):
                tip = st.radio("Tip", ["Kupac", "Potencijal"], horizontal=True)
                naziv = st.text_input("Naziv (kupca ili potencijala) *")
                oib = st.text_input("OIB (opcionalno)")
                tekst = st.text_area("Tekst bilješke *", height=120)

                if st.form_submit_button("Spremi bilješku"):
                    if not naziv or not tekst:
                        st.error("Naziv i tekst bilješke su obavezni")
                    else:
                        new_row = {
                            "Datum": datetime.now().strftime("%d.%m.%Y %H:%M"),
                            "Tip": tip,
                           
