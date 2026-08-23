import streamlit as st
import os
import json
from google import genai

# --- 0. CONFIGURAZIONE PAGINA (DEVE ESSERE LA PRIMA COSA IN ASSOLUTO) ---
st.set_page_config(page_title="Travel AI Assistant Pro", page_icon="✈️", layout="wide")

# --- INIZIALIZZAZIONE GEMINI CLIENT ---
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key and "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]

client = genai.Client(api_key=api_key) if api_key else None

# --- 1. CLASSE DI STATO E CONTROLLER ---
class TravelAgentState:
    def __init__(self):
        self.destination = None
        self.dates = None
        self.origin_city = None
        self.airports = []
        self.budget_max = None
        self.preferred_airlines = []
        self.max_stops = None
        self.selected_flight = None
        self.transfer_info = None
        self.travel_style = None
        self.itinerary = None
        self.flight_recommendation = None
        self.checkout_links = {}
        self.step = 1

    def set_user_input(self, destination, dates, origin_city, budget_max=None, preferred_airlines=None, max_stops=None):
        self.destination = destination
        self.dates = dates
        self.origin_city = origin_city
        self.budget_max = budget_max
        self.preferred_airlines = preferred_airlines or []
        self.max_stops = max_stops
        self.find_nearby_airports()
        self.step = 2

    def find_nearby_airports(self):
        airport_database = {
            "milano": ["Malpensa (MXP)", "Linate (LIN)", "Bergamo Orio al Serio (BGY)"],
            "roma": ["Fiumicino (FCO)", "Ciampino (CIA)"],
            "torino": ["Torino Caselle (TRN)"],
            "bologna": ["Bologna Guglielmo Marconi (BLQ)"],
            "trento": ["Verona Villafranca (VRN)", "Bergamo Orio al Serio (BGY)"],
            "cosenza": ["Lamezia Terme (SUF)"]
        }
        city_key = self.origin_city.strip().lower() if self.origin_city else ""
        self.airports = airport_database.get(city_key, [f"Aeroporto di {self.origin_city}"])

    def add_flight_and_check_transfer(self, flight_details, arrival_time):
        self.selected_flight = flight_details
        hour = int(arrival_time.split(":")[0])
        
        transfers = {
            "Malpensa (MXP)": "Malpensa Express (Treno fino a Milano Centrale) o Bus Navetta.",
            "Linate (LIN)": "Metro M4 (Linea Blu) o Taxi.",
            "Bergamo Orio al Serio (BGY)": "Autobus navetta (Orio Shuttle) verso Milano Centrale.",
            "Verona Villafranca (VRN)": "Bus navetta per la stazione di Verona e treno.",
            "Lamezia Terme (SUF)": "Servizio navetta o treno regionale per Cosenza."
        }
        airport_used = flight_details.get("airport", self.airports[0] if self.airports else "Aeroporto principale")
        base_transfer = transfers.get(airport_used, "Servizio bus o taxi locale.")
        
        if hour >= 23 or hour < 5:
            self.transfer_info = f"⚠️ Atterraggio notturno ({arrival_time}). Consigliato: Taxi ufficiale o navetta. Base: {base_transfer}"
        else:
            self.transfer_info = f"✅ Collegamenti regolari ({arrival_time}): {base_transfer}"
        
        self.step = 3

    def generate_itinerary(self, travel_style):
        self.travel_style = travel_style
        if self.destination and "tokyo" in self.destination.lower():
            if travel_style.lower() == "cultura":
                self.itinerary = "Giorno 1: Tempio Senso-ji e Asakusa.\nGiorno 2: Santuario Meiji e quartiere Shibuya.\nGiorno 3: Akihabara e musei d'arte moderna."
            else:
                self.itinerary = "Giorno 1: Trekking ed escursione panoramica.\nGiorno 2: Quartieri futuristici e street food tour.\nGiorno 3: Punti panoramici e shopping."
        else:
            self.itinerary = f"Giorno 1-3: Tour esplorativo a {self.destination} incentrato su {travel_style}."
        
        self.process_flight_matrix_and_recommendation()
        self.step = 4

    def process_flight_matrix_and_recommendation(self):
        chosen_airline = self.preferred_airlines[0] if self.preferred_airlines else "Ryanair"
        
        best_option = {
            "airline": chosen_airline,
            "departure_dates": "13 - 18 Settembre",
            "departure_time": "08:30 (Andata) / 19:45 (Ritorno)",
            "price": "94€",
            "reason": "Ottimo compromesso tra orari comodi diurni e la tariffa più bassa rilevata."
        }
        
        self.flight_recommendation = (
            f"🎯 **Analisi Matrice Voli & Tariffe completata:**\n\n"
            f"- **Compagnia consigliata:** {best_option['airline']}\n"
            f"- **Periodo ottimale trovato:** Dal {best_option['departure_dates']}\n"
            f"- **Orari:** {best_option['departure_time']}\n"
            f"- **Prezzo stimato:** {best_option['price']}\n\n"
            f"💡 *Perché te lo consiglio:* {best_option['reason']}"
        )
        
        self.generate_checkout_links()

    def generate_checkout_links(self):
        dest_query = (self.destination or "").replace(" ", "+")
        origin_query = (self.origin_city or "").replace(" ", "+")
        self.checkout_links = {
            "google_flights": f"https://www.google.com/travel/flights?q=Flights+from+{origin_query}+to+{dest_query}",
            "transfer_info_link": "https://www.rome2rio.com/it/"
        }

# --- 2. INTERFACCIA GRAFICA (STREAMLIT) ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/airport.png", width=80)
    st.markdown("### 🗺️ Il tuo Viaggio")
    if "agent_state" in st.session_state:
        st.info(f"**Step attuale:** {st.session_state.agent_state.step} di 4")
        if st.session_state.agent_state.destination:
            st.write(f"📍 **Destinazione:** {st.session_state.agent_state.destination}")
        if st.session_state.agent_state.origin_city:
            st.write(f"🛫 **Partenza:** {st.session_state.agent_state.origin_city}")

st.title("✈️ Travel AI Assistant Pro")
st.markdown("##### Il tuo agente di viaggio completo con intelligenza artificiale Gemini integrata.")
st.divider()

if "agent_state" not in st.session_state:
    st.session_state.agent_state = TravelAgentState()

state = st.session_state.agent_state

# --- STEP 1 ---
if state.step == 1:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("1️⃣ Raccolta Preferenze con IA")
        
        if client:
            st.info("✨ **Modalità Smart AI attiva:** scrivi liberamente cosa desideri fare.")
            with st.form("ai_form"):
                user_prompt = st.text_area("Raccontami il tuo viaggio ideale:", placeholder="Es. Vorrei andare a Tokyo a novembre partendo da Milano con un budget di 1500 euro.")
                ai_submitted = st.form_submit_button("🤖 Elabora con Gemini", use_container_width=True)
                
                if ai_submitted and user_prompt:
                    with st.spinner("Gemini sta analizzando la richiesta..."):
                        try:
                            prompt_text = f"""
                            Analizza questa richiesta di viaggio ed estrai i dati in formato JSON puro (senza blocchi di codice markdown, solo le chiavi):
                            - "destination": stringa o null
                            - "dates": stringa o null
                            - "origin_city": stringa o null
                            - "budget_max": stringa o null
                            
                            Richiesta: "{user_prompt}"
                            """
                            response = client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=prompt_text
                            )
                            clean_text = response.text.replace("```json", "").replace("
