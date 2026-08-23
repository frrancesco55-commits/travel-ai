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
        self.packing_list = None
        self.weather_tips = None
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
            "cosenza": ["Lamezia Terme (SUF)"],
            "napoli": ["Napoli Capodichino (NAP)"]
        }
        city_key = self.origin_city.strip().lower() if self.origin_city else ""
        self.airports = airport_database.get(city_key, [f"Aeroporto principale di {self.origin_city}"])

    def add_flight_and_check_transfer(self, flight_details, arrival_time):
        self.selected_flight = flight_details
        hour = int(arrival_time.split(":")[0])
        
        transfers = {
            "Malpensa (MXP)": "Malpensa Express (Treno fino a Milano Centrale) o Bus Navetta.",
            "Linate (LIN)": "Metro M4 (Linea Blu) o Taxi.",
            "Bergamo Orio al Serio (BGY)": "Autobus navetta (Orio Shuttle) verso Milano Centrale.",
            "Verona Villafranca (VRN)": "Bus navetta per la stazione di Verona e treno.",
            "Lamezia Terme (SUF)": "Servizio navetta o treno regionale.",
            "Napoli Capodichino (NAP)": "Alibus (navetta aeroportuale) per la Stazione Centrale o Porto."
        }
        airport_used = flight_details.get("airport", self.airports[0] if self.airports else "Aeroporto principale")
        base_transfer = transfers.get(airport_used, "Servizio bus, treno o taxi locale.")
        
        if hour >= 23 or hour < 5:
            self.transfer_info = f"⚠️ Atterraggio notturno ({arrival_time}). Consigliato: Taxi ufficiale o navetta h24. Base: {base_transfer}"
        else:
            self.transfer_info = f"✅ Collegamenti regolari ({arrival_time}): {base_transfer}"
        
        self.step = 3

    def generate_real_ai_content(self, travel_style):
        self.travel_style = travel_style
        
        if model:
            try:
                # 1. Itinerario
                itinerary_prompt = f"""
                Agisci come un travel planner esperto. Crea un itinerario di viaggio dettagliato di 3 giorni per la destinazione '{self.destination}', 
                incentrato sullo stile di viaggio '{travel_style}'. Usa elenchi puntati puliti per ogni giornata.
                """
                it_response = model.generate_content(itinerary_prompt)
                self.itinerary = it_response.text

                # 2. Analisi Voli e Budget
                flight_prompt = f"""
                Agisci come un esperto di viaggi. Analizza un volo da '{self.origin_city}' a '{self.destination}' nel periodo '{self.dates}' con budget massimo '{self.budget_max}'.
                Fornisci un'analisi con: compagnia ideale, scali consigliati, prezzo stimato e un consiglio strategico.
                """
                fl_response = model.generate_content(flight_prompt)
                self.flight_recommendation = fl_response.text

                # 3. Lista Valigia (Packing List) e Meteo
                packing_prompt = f"""
                Crea una valigia intelligente e una previsione meteo/consigli di abbigliamento per un viaggio a '{self.destination}' nel periodo '{self.dates}' con stile '{travel_style}'. 
                Dividi in: 1. Condizioni meteo attese e abbigliamento consigliato, 2. Cose essenziali da mettere in valigia.
                """
                pack_response = model.generate_content(packing_prompt)
                self.packing_list = pack_response.text

            except Exception as e:
                self.itinerary = f"Errore nella generazione IA: {e}"
                self.flight_recommendation = "Impossibile elaborare i dati dei voli."
                self.packing_list = "Impossibile generare la valigia intelligente."
        else:
            self.itinerary = f"Itinerario standard per {self.destination} ({travel_style})."
            self.flight_recommendation = "Analisi voli standard."
            self.packing_list = "Porta abiti comodi e documenti."

        self.generate_checkout_links()
        self.step = 4

    def generate_checkout_links(self):
        dest_query = (self.destination or "").replace(" ", "+")
        origin_query = (self.origin_city or "").replace(" ", "+")
        self.checkout_links = {
            "google_flights": f"https://www.google.com/travel/flights?q=Flights+from+{origin_query}+to+{dest_query}",
            "transfer_info_link": "https://www.rome2rio.com/it/",
            "booking_hotel": f"https://www.booking.com/searchresults.it.html?ss={dest_query}"
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
st.markdown("##### Il tuo assistente di viaggio intelligente, completo di budget, valigia e itinerari.")
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
            st.info("✨ **Modalità Smart AI attiva:** scrivi liberamente la tua idea di viaggio.")
            with st.form("ai_form"):
                user_prompt = st.text_area("Raccontami il tuo viaggio ideale:", placeholder="Es. Vorrei andare a Tokyo a novembre partendo da Milano con un budget di 1500 euro.")
                ai_submitted = st.form_submit_button("🤖 Elabora con Gemini", use_container_width=True)
                
                if ai_submitted and user_prompt:
                    with st.spinner("Gemini sta analizzando la richiesta..."):
                        try:
                            prompt_text = f"""
                            Analizza questa richiesta di viaggio ed estrai i dati in formato JSON puro (senza markdown):
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
                            st.warning(f"Errore IA ({e}). Compila i campi sotto:")
        
        with st.form("step1_form"):
            st.markdown("---")
            destination = st.text_input("Destinazione", placeholder="Es. Tokyo, Parigi, Lamezia Terme")
            dates = st.text_input("Periodo / Date", placeholder="Es. Settembre, 10-17 Ottobre")
            origin_city = st.text_input("Città di Partenza", placeholder="Es. Milano, Roma, Cosenza")
            
            with st.expander("⚙️ Filtri Avanzati (Budget e Compagnie)"):
                budget_max = st.text_input("Budget massimo", placeholder="Es. 1200€")
                preferred_airlines = st.text_input("Compagnie preferite (separate da virgola)", placeholder="Es. Ryanair, ITA")
                max_stops = st.selectbox("Numero massimo di scali", [0, 1, 2], index=1)

            submitted = st.form_submit_button("🚀 Avvia Analisi Tradizionale", use_container_width=True)
            if submitted and destination and dates and origin_city:
                airlines_list = [a.strip() for a in preferred_airlines.split(",")] if preferred_airlines else []
                state.set_user_input(destination, dates, origin_city, budget_max, airlines_list, max_stops)
                st.rerun()
                
    with col2:
        st.markdown("### Come funziona?")
        st.info(
            "1. **Gemini IA:** Estrae i dati ed elabora il piano.\n"
            "2. **Logistica:** Aeroporti e transfer.\n"
            "3. **Budget & Valigia:** Calcoli e liste intelligenti.\n"
            "4. **Checkout:** Link pronti per prenotare."
        )

# --- STEP 2 ---
elif state.step == 2:
    st.subheader("2️⃣ Aeroporti Mappati e Selezione Volo")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Città di Partenza", state.origin_city or "-")
    col2.metric("Destinazione", state.destination or "-")
    col3.metric("Scali Massimi", f"{state.max_stops} scali" if state.max_stops is not None else "Non specificato")

    st.success(f"📍 **Aeroporti individuati:** {', '.join(state.airports)}")
    
    st.markdown("### Seleziona una tipologia di volo per testare i collegamenti:")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✈️ Simula Volo Diurno (Arrivo 15:30)", use_container_width=True):
            flight_test = {"details": {"airline": "Compagnia Principale", "airport": state.airports[0]}, "arrival_time": "15:30"}
            state.add_flight_and_check_transfer(flight_test["details"], flight_test["arrival_time"])
            st.rerun()
    with c2:
        if st.button("🌙 Simula Volo Notturno (Arrivo 23:45)", use_container_width=True):
            flight_test = {"details": {"airline": "Compagnia Notturna", "airport": state.airports[0]}, "arrival_time": "23:45"}
            state.add_flight_and_check_transfer(flight_test["details"], flight_test["arrival_time"])
            st.rerun()

# --- STEP 3 ---
elif state.step == 3:
    st.subheader("3️⃣ Verifica Logistica di Terra e Transfer")
    st.markdown(f"> **Esito Controllo Transfer:**\n> {state.transfer_info}")
    
    st.markdown("### Scegli il tuo stile di viaggio:")
    travel_style = st.selectbox("Stile:", ["Cultura", "Avventura", "Relax", "Enogastronomia", "Lusso a basso costo"])
    
    if st.button("✨ Genera Piano Completo con Gemini (Voli, Itinerario & Valigia)", use_container_width=True):
        with st.spinner("L'intelligenza artificiale sta costruendo il tuo assistente di viaggio definitivo..."):
            state.generate_real_ai_content(travel_style)
            st.rerun()

# --- STEP 4 ---
elif state.step == 4:
    st.subheader("🎉 Il tuo piano di viaggio definitivo è pronto!")
    
    st.success(state.flight_recommendation)
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "🧭 Itinerario", 
        "🧳 Valigia & Meteo", 
        "💰 Calcolatore Budget", 
        "🔗 Link Prenotazione"
    ])
    
    with tab1:
        st.markdown(f"### Itinerario su misura ({state.travel_style})")
        st.markdown(state.itinerary)
        
    with tab2:
        st.markdown("### 🌤️ Previsioni Meteo e 🧳 Valigia Intelligente")
        st.markdown(state.packing_list)
        
    with tab3:
        st.markdown("### 💶 Calcolatore Interattivo delle Spese")
        st.write("Inserisci i costi stimati per capire se rientri nel budget:")
        
        c_bud1, c_bud2 = st.columns(2)
        with c_bud1:
            cost_flight = st.number_input("Costo Voli (€)", min_value=0.0, value=150.0, step=10.0)
            cost_hotel = st.number_input("Costo Hotel / Alloggio (€)", min_value=0.0, value=300.0, step=20.0)
        with c_bud2:
            cost_food = st.number_input("Cibo e Ristoranti (€)", min_value=0.0, value=150.0, step=10.0)
            cost_extras = st.number_input("Attività, Transfer e Extra (€)", min_value=0.0, value=100.0, step=10.0)
            
        total_spent = cost_flight + cost_hotel + cost_food + cost_extras
        st.divider()
        st.metric(label="Spesa Totale Stimata", value=f"{total_spent} €")
        
        if state.budget_max:
            st.info(f"💡 Il tuo budget massimo desiderato era: **{state.budget_max}**")

    with tab4:
        st.markdown("### Link diretti di prenotazione")
        st.markdown("Usa i link rapidi per bloccare le tariffe migliori sui portali ufficiali:")
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.link_button("🌐 Cerca Voli (Google Flights)", state.checkout_links['google_flights'], use_container_width=True)
        with col_b:
            st.link_button("🏨 Cerca Hotel (Booking)", state.checkout_links['booking_hotel'], use_container_width=True)
        with col_c:
            st.link_button("🚆 Verifica Transfer (Rome2Rio)", state.checkout_links['transfer_info_link'], use_container_width=True)
            
    st.divider()
    if st.button("🔄 Pianifica un nuovo viaggio", use_container_width=True):
        st.session_state.agent_state = TravelAgentState()
        st.rerun()
