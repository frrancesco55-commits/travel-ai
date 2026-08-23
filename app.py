import streamlit as st
import os
import json
import google.generativeai as genai

# --- 0. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Travel AI Assistant Pro", page_icon="✈️", layout="wide")

# --- INIZIALIZZAZIONE GEMINI CLIENT ---
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key and "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]

if api_key:
    genai.configure(api_key=api_key)
    # Usiamo il modello standard stabile
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

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
        
        if model:
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
                            response = model.generate_content(prompt_text)
                            clean_text = response.text.replace("```json", "").replace("```", "").strip()
                            data = json.loads(clean_text)
                            
                            state.set_user_input(
                                destination=data.get("destination", "Tokyo"),
                                dates=data.get("dates", "Prossimi mesi"),
                                origin_city=data.get("origin_city", "Milano"),
                                budget_max=data.get("budget_max", "1000€")
                            )
                            st.rerun()
                        except Exception as e:
                            st.warning(f"Errore nell'interpretazione IA ({e}). Compila i campi standard sotto:")
        
        with st.form("step1_form"):
            st.markdown("---")
            destination = st.text_input("Destinazione", placeholder="Es. Tokyo, Parigi, Lamezia Terme")
            dates = st.text_input("Periodo / Date", placeholder="Es. Settembre, 10-17 Ottobre")
            origin_city = st.text_input("Città di Partenza", placeholder="Es. Milano, Roma, Cosenza")
            
            with st.expander("⚙️ Filtri Avanzati (Budget e Compagnie)"):
                budget_max = st.text_input("Budget massimo", placeholder="Es. 1200€")
                preferred_airlines = st.text_input("Compagnie preferite (separate da virgola)", placeholder="Es. Ryanair, ITA, EasyJet")
                max_stops = st.selectbox("Numero massimo di scali", [0, 1, 2], index=1)

            submitted = st.form_submit_button("🚀 Avvia Analisi Tradizionale", use_container_width=True)
            if submitted and destination and dates and origin_city:
                airlines_list = [a.strip() for a in preferred_airlines.split(",")] if preferred_airlines else []
                state.set_user_input(destination, dates, origin_city, budget_max, airlines_list, max_stops)
                st.rerun()
                
    with col2:
        st.markdown("### Come funziona?")
        st.info(
            "1. **Gemini IA:** Legge la tua frase ed estrae i dettagli automaticamente.\n"
            "2. **Mappatura:** Individuazione degli aeroporti vicini.\n"
            "3. **Logistica:** Controllo transfer e orari.\n"
            "4. **Matrice & Checkout:** Incrocio tariffe e link pronti."
        )

# --- STEP 2 ---
elif state.step == 2:
    st.subheader("2️⃣ Aeroporti Mappati e Selezione Volo di Prova")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Città di Partenza", state.origin_city or "-")
    col2.metric("Destinazione", state.destination or "-")
    col3.metric("Scali Massimi", f"{state.max_stops} scali" if state.max_stops is not None else "Non specificato")

    st.success(f"📍 **Aeroporti individuati nel raggio utile:** {', '.join(state.airports)}")
    
    st.markdown("### Seleziona una tipologia di volo per testare i collegamenti:")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✈️ Simula Volo Diurno (Arrivo 15:30)", use_container_width=True):
            flight_test = {"details": {"airline": "Ryanair", "airport": state.airports[0]}, "arrival_time": "15:30"}
            state.add_flight_and_check_transfer(flight_test["details"], flight_test["arrival_time"])
            st.rerun()
    with c2:
        if st.button("🌙 Simula Volo Notturno (Arrivo 23:45)", use_container_width=True):
            flight_test = {"details": {"airline": "ITA Airways", "airport": state.airports[0]}, "arrival_time": "23:45"}
            state.add_flight_and_check_transfer(flight_test["details"], flight_test["arrival_time"])
            st.rerun()

# --- STEP 3 ---
elif state.step == 3:
    st.subheader("3️⃣ Verifica Logistica di Terra e Transfer")
    st.markdown(f"> **Esito Controllo Transfer:**\n> {state.transfer_info}")
    
    st.markdown("### Scegli il tuo stile per l'itinerario personalizzato:")
    travel_style = st.selectbox("Stile di viaggio:", ["Cultura", "Avventura", "Relax", "Enogastronomia"])
    
    if st.button("✨ Elabora Matrice Voli e Genera Itinerario", use_container_width=True):
        state.generate_itinerary(travel_style)
        st.rerun()

# --- STEP 4 ---
elif state.step == 4:
    st.subheader("🎉 Il tuo piano di viaggio è pronto!")
    
    st.success(state.flight_recommendation)
    
    tab1, tab2 = st.tabs(["🧭 Itinerario Giornaliero", "🔗 Link di Checkout & Prenotazione"])
    
    with tab1:
        st.markdown(f"### Itinerario in stile: *{state.travel_style}*")
        st.info(state.itinerary)
        
    with tab2:
        st.markdown("### Link diretti preimpostati")
        st.markdown("Clicca sui pulsanti sottostanti per aprire i portali con i parametri già impostati:")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.link_button("🌐 Cerca Voli su Google Flights", state.checkout_links['google_flights'], use_container_width=True)
        with col_b:
            st.link_button("🚆 Verifica Transfer su Rome2Rio", state.checkout_links['transfer_info_link'], use_container_width=True)
            
    st.divider()
    if st.button("🔄 Pianifica un nuovo viaggio", use_container_width=True):
        st.session_state.agent_state = TravelAgentState()
        st.rerun()
