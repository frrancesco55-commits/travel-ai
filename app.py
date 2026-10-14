import streamlit as st
import os
import json
import google.generativeai as genai

# --- 0. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Travel AI Assistant Pro", page_icon="✈️", layout="wide")

# --- INIZIALIZZAZIONE CLIENT IA (Gemini & Supporto OpenAI/ChatGPT) ---
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key and "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]

if api_key:
    genai.configure(api_key=api_key)
    # Usiamo il modello Gemini più recente ed efficiente
    model = genai.GenerativeModel('gemini-1.5-pro')
else:
    model = None

# Configurazione opzionale per ChatGPT (OpenAI) se la chiave è presente nei secrets o nelle env
openai_api_key = os.environ.get("OPENAI_API_KEY")
if not openai_api_key and "OPENAI_API_KEY" in st.secrets:
    openai_api_key = st.secrets["OPENAI_API_KEY"]


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
        self.checkout_links = {}
        self.chat_history = []
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
            "napoli": ["Napoli Capodichino (NAP)"],
            "palermo": ["Palermo Falcone-Borsellino (PMO)"],
            "catania": ["Catania Fontanarossa (CTA)"]
        }
        city_key = self.origin_city.strip().lower() if self.origin_city else ""
        self.airports = airport_database.get(city_key, [f"Aeroporto principale di {self.origin_city}"])

    def add_flight_and_check_transfer(self, flight_details, arrival_time):
        self.selected_flight = flight_details
        try:
            hour = int(arrival_time.split(":")[0])
        except:
            hour = 12
        
        # Logistica di terra integrata (Rome2Rio, Treni, Bus e Servizi locali)
        transfers = {
            "Malpensa (MXP)": "Malpensa Express (Treno fino a Milano Centrale) o Bus Navetta h24.",
            "Linate (LIN)": "Metro M4 (Linea Blu diretta al centro) o Taxi.",
            "Bergamo Orio al Serio (BGY)": "Autobus navetta (Orio Shuttle / Terravision) verso Milano Centrale.",
            "Fiumicino (FCO)": "Treno Leonardo Express per Roma Termini o Treni Regionali FL1.",
            "Ciampino (CIA)": "Bus navetta per stazione Anagnina o Roma Termini.",
            "Verona Villafranca (VRN)": "Bus navetta Aeribus per la stazione di Verona Porta Nuova.",
            "Lamezia Terme (SUF)": "Servizio navetta o treno regionale per Cosenza e centri limitrofi.",
            "Napoli Capodichino (NAP)": "Alibus per la Stazione Centrale di Piazza Garibaldi o Porto."
        }
        airport_used = flight_details.get("airport", self.airports[0] if self.airports else "Aeroporto")
        base_transfer = transfers.get(airport_used, "Servizio bus, treno regionale o taxi locale (verificabile su Rome2Rio).")
        
        if hour >= 23 or hour < 5:
            self.transfer_info = f"⚠️ Atterraggio notturno ({arrival_time}). Consigliato: Taxi ufficiale o navetta aeroportuale h24. Collegamenti di base: {base_transfer}"
        else:
            self.transfer_info = f"✅ Collegamenti regolari attivi ({arrival_time}): {base_transfer}"
        
        self.step = 3

    def generate_real_ai_content(self, travel_style):
        self.travel_style = travel_style
        
        if model:
            try:
                # 1. Itinerario dettagliato con Gemini
                itinerary_prompt = f"""
                Agisci come un travel planner professionista. Crea un itinerario dettagliato di 3 giorni per '{self.destination}', 
                incentrato sullo stile '{travel_style}'. Usa elenchi puntati puliti, suddividendo per mattina, pomeriggio e sera.
                """
                it_response = model.generate_content(itinerary_prompt)
                self.itinerary = it_response.text

                # 2. Analisi Avanzata e Raccomandazione Voli (Incrocio ITA, Ryanair, EasyJet, ecc.)
                airlines_str = ", ".join(self.preferred_airlines) se self.preferred_airlines else "Compagnie principali (ITA, Ryanair, EasyJet)"
                flight_prompt = f"""
                Agisci come un esperto di tariffe aeree e travel data analyst. Simula l'incrocio tra i vettori ({airlines_str}), 
                le date ({self.dates}), gli orari e i prezzi stimati per un volo da '{self.origin_city}' a '{self.destination}' con budget massimo '{self.budget_max}'.
                Fornisci una raccomandazione strategica dettagliata indicando la compagnia ideale, le fasce orarie ottimali e una stima di prezzo competitiva.
                """
                fl_response = model.generate_content(flight_prompt)
                self.flight_recommendation = fl_response.text

                # 3. Valigia Intelligente e Meteo
                packing_prompt = f"""
                Crea una valigia intelligente su misura e dai consigli meteo mirati per un viaggio a '{self.destination}' nel periodo '{self.dates}' con stile '{travel_style}'.
                """
                pack_response = model.generate_content(packing_prompt)
                self.packing_list = pack_response.text

            except Exception as e:
                self.itinerary = f"Errore nella generazione tramite IA: {e}"
                self.flight_recommendation = "Impossibile elaborare i dati avanzati dei voli in questo momento."
                self.packing_list = "Impossibile generare la lista valigia."
        else:
            self.itinerary = f"Itinerario standard per {self.destination} ({travel_style}). Inserisci una chiave Gemini API valida per attivare i contenuti avanzati."
            self.flight_recommendation = "Analisi voli standard basata sui parametri inseriti."
            self.packing_list = "Porta abiti comodi, adattatore di corrente e documenti di identità validi."

        self.generate_checkout_links()
        self.step = 4

    def generate_checkout_links(self):
        dest_query = (self.destination or "").replace(" ", "+")
        origin_query = (self.origin_city or "").replace(" ", "+")
        dates_query = (self.dates or "").replace(" ", "+")
        
        # Link diretti ai principali aggregatori e portali di prenotazione reali richiesti
        self.checkout_links = {
            "google_flights": f"https://www.google.com/travel/flights?q=Flights+from+{origin_query}+to+{dest_query}",
            "skyscanner": f"https://www.skyscanner.it/trasporti/voli/{origin_query.lower()}/{dest_query.lower()}/",
            "booking_hotel": f"https://www.booking.com/searchresults.it.html?ss={dest_query}",
            "rome2rio": f"https://www.rome2rio.com/it/s/{origin_query}/{dest_query}",
            "ita_airways": "https://www.ita-airways.com/it_it",
            "ryanair": "https://www.ryanair.com/it/it",
            "easyjet": "https://www.easyjet.com/it"
        }

# --- 2. INTERFACCIA GRAFICA STREAMLIT ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/airport.png", width=80)
    st.markdown("### 🗺️ Il tuo Viaggio Pro")
    if "agent_state" in st.session_state:
        st.info(f"**Step attuale:** {st.session_state.agent_state.step} di 4")
        if st.session_state.agent_state.destination:
            st.write(f"📍 **Destinazione:** {st.session_state.agent_state.destination}")
        if st.session_state.agent_state.origin_city:
            st.write(f"🛫 **Partenza:** {st.session_state.agent_state.origin_city}")

st.title("✈️ Travel AI Assistant Pro")
st.markdown("##### Il tuo assistente di viaggio intelligente integrato con IA (Gemini), Google Flights, Skyscanner, Booking, compagnie aeree e Rome2Rio.")
st.divider()

if "agent_state" not in st.session_state:
    st.session_state.agent_state = TravelAgentState()

state = st.session_state.agent_state

# --- STEP 1: RACCOLTA PREFERENZE ---
if state.step == 1:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("1️⃣ Preferenze di Viaggio")
        with st.form("step1_form"):
            destination = st.text_input("Destinazione", placeholder="Es. Tokyo, Parigi, New York, Londra")
            dates = st.text_input("Periodo / Date", placeholder="Es. 10-17 Ottobre, Settembre")
            origin_city = st.text_input("Città di Partenza", placeholder="Es. Milano, Roma, Napoli, Torino")
            
            with st.expander("⚙️ Filtri Avanzati (Budget, Compagnie e Scali)"):
                budget_max = st.text_input("Budget massimo stimato", placeholder="Es. 1200€")
                preferred_airlines = st.text_input("Compagnie preferite (es. ITA, Ryanair, EasyJet)", placeholder="Es. ITA Airways, Ryanair, Emirates")
                max_stops = st.selectbox("Numero massimo di scali", [0, 1, 2], index=1)

            submitted = st.form_submit_button("🚀 Avvia Mappatura e Intelligenza di Viaggio", use_container_width=True)
            if submitted and destination and dates and origin_city:
                airlines_list = [a.strip() for a in preferred_airlines.split(",")] if preferred_airlines else []
                state.set_user_input(destination, dates, origin_city, budget_max, airlines_list, max_stops)
                st.rerun()
    with col2:
        st.markdown("### 🔗 Servizi Integrati")
        st.info(
            "• **Intelligenza Artificiale:** Google Gemini (Modello avanzato)\n"
            "• **Voli & Aggregatori:** Google Flights, Skyscanner, ITA, Ryanair, EasyJet\n"
            "• **Logistica & Transfer:** Rome2Rio & Mappe regionali\n"
            "• **Hotel & Alloggi:** Booking.com"
        )

# --- STEP 2: AEROPORTI E SIMULAZIONE TRATTA ---
elif state.step == 2:
    st.subheader("2️⃣ Aeroporti Mappati e Selezione Volo")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Città di Partenza", state.origin_city)
    col2.metric("Destinazione", state.destination)
    col3.metric("Scali Massimi", f"{state.max_stops} scali" if state.max_stops is not None else "Non specificato")

    st.success(f"📍 **Aeroporti individuati nel raggio utile:** {', '.join(state.airports)}")
    
    st.markdown("### Seleziona un orario di arrivo per testare i collegamenti di terra:")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✈️ Simula Volo Diurno (Arrivo 15:30)", use_container_width=True):
            flight_test = {"details": {"airline": state.preferred_airlines[0] if state.preferred_airlines else "Ryanair", "airport": state.airports[0]}, "arrival_time": "15:30"}
            state.add_flight_and_check_transfer(flight_test["details"], flight_test["arrival_time"])
            st.rerun()
    with c2:
        if st.button("🌙 Simula Volo Notturno (Arrivo 23:45)", use_container_width=True):
            flight_test = {"details": {"airline": state.preferred_airlines[0] if state.preferred_airlines else "ITA Airways", "airport": state.airports[0]}, "arrival_time": "23:45"}
            state.add_flight_and_check_transfer(flight_test["details"], flight_test["arrival_time"])
            st.rerun()

# --- STEP 3: LOGISTICA E STILE ---
elif state.step == 3:
    st.subheader("3️⃣ Verifica Logistica di Terra e Transfer")
    st.markdown(f"> **Esito Controllo Transfer:**\n> {state.transfer_info}")
    
    st.markdown("### Scegli il tuo stile di viaggio per l'itinerario IA:")
    travel_style = st.selectbox("Stile:", ["Cultura", "Avventura", "Relax", "Enogastronomia", "Lusso a basso costo"])
    
    if st.button("✨ Elabora Analisi Completa e Genera Piano con IA", use_container_width=True):
        with st.spinner("L'intelligenza artificiale sta elaborando le opzioni di volo, l'itinerario e i collegamenti..."):
            state.generate_real_ai_content(travel_style)
            st.rerun()

# --- STEP 4: RISULTATI FINALI E LINK DIRETTI ---
elif state.step == 4:
    st.subheader("🎉 Il tuo piano di viaggio completo è pronto!")
    
    # Raccomandazione voli generata dall'IA
    st.success(state.flight_recommendation)
    
    # Tab di navigazione pulite
    tab1, tab2, tab3 = st.tabs(["🧭 Itinerario Giornaliero", "🔗 Prenotazioni & Link Diretti", "📂 Altri Strumenti & Chat IA"])
    
    with tab1:
        st.markdown(f"### Itinerario in stile: *{state.travel_style}*")
        st.markdown(state.itinerary)
        
    with tab2:
        st.markdown("### Portali di Volo e Comparatori Ufficiali")
        st.markdown("Accedi direttamente ai principali aggregatori con i dati della tua ricerca preimpostati:")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.link_button("🌐 Cerca su Google Flights", state.checkout_links['google_flights'], use_container_width=True)
            st.link_button("✈️ Cerca su Skyscanner", state.checkout_links['skyscanner'], use_container_width=True)
        with col_b:
            st.link_button("🏨 Cerca Hotel su Booking.com", state.checkout_links['booking_hotel'], use_container_width=True)
            st.link_button("🚆 Pianifica Transfer su Rome2Rio", state.checkout_links['rome2rio'], use_container_width=True)

        st.markdown("### Siti Diretti delle Compagnie Aeree")
        c_a1, c_a2, c_a3 = st.columns(3)
        with c_a1:
            st.link_button("🇮🇹 ITA Airways", state.checkout_links['ita_airways'], use_container_width=True)
        with c_a2:
            st.link_button("✈️ Ryanair", state.checkout_links['ryanair'], use_container_width=True)
        with c_a3:
            st.link_button("✈️ EasyJet", state.checkout_links['easyjet'], use_container_width=True)
            
    with tab3:
        sub_tab1, sub_tab2, sub_tab3 = st.tabs(["🧳 Valigia & Meteo", "💰 Calcolatore Budget", "💬 Consulente Chat IA"])
        
        with sub_tab1:
            st.markdown("### 🌤️ Previsioni e Lista Valigia")
            st.markdown(state.packing_list)
            
        with sub_tab2:
            st.markdown("### 💶 Calcolatore Rapido Spese")
            cb1, cb2 = st.columns(2)
            with cb1:
                st.number_input("Costo Voli (€)", value=150.0, key="b_volo")
                st.number_input("Costo Hotel (€)", value=350.0, key="b_hotel")
            with cb2:
                st.number_input("Cibo e Extra (€)", value=250.0, key="b_extra")
            st.info(f"💡 Budget massimo dichiarato: {state.budget_max if state.budget_max else 'Non specificato'}")
            
        with sub_tab3:
            st.markdown("### 💬 Chiedi al Consulente IA")
            user_chat = st.text_input(f"Fai una domanda specifica su {state.destination} (es. documenti, valuta, zone da evitare):", key="chat_input")
            if user_chat and model:
                try:
                    chat_resp = model.generate_content(f"Rispondi in modo chiaro e dettagliato a questa domanda sul viaggio a {state.destination}: {user_chat}")
                    st.write(chat_resp.text)
                except Exception as e:
                    st.error(f"Errore nella generazione della risposta: {e}")

    st.divider()
    if st.button("🔄 Pianifica un nuovo viaggio", use_container_width=True):
        st.session_state.agent_state = TravelAgentState()
        st.rerun()
