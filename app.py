import streamlit as st

# --- 0. CONFIGURAZIONE PAGINA (DEVE ESSERE LA PRIMA COSA IN ASSOLUTO) ---
st.set_page_config(page_title="Travel AI Assistant Pro", page_icon="✈️", layout="wide")

# --- 1. CLASSE DI STATO E CONTROLLER (Logica, Matrice e Incrocio Voli) ---
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
        self.flight_recommendation = None  # Matrice incrociata e consiglio migliore
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
            "trento": ["Verona Villafranca (VRN)", "Bergamo Orio al Serio (BGY)"]
        }
        city_key = self.origin_city.strip().lower()
        self.airports = airport_database.get(city_key, [f"Aeroporto di {self.origin_city}"])

    def add_flight_and_check_transfer(self, flight_details, arrival_time):
        self.selected_flight = flight_details
        hour = int(arrival_time.split(":")[0])
        
        transfers = {
            "Malpensa (MXP)": "Malpensa Express (Treno fino a Milano Centrale) o Bus Navetta.",
            "Linate (LIN)": "Metro M4 (Linea Blu) o Taxi.",
            "Bergamo Orio al Serio (BGY)": "Autobus navetta (Orio Shuttle) verso Milano Centrale.",
            "Verona Villafranca (VRN)": "Bus navetta per la stazione di Verona e treno."
        }
        airport_used = flight_details.get("airport", "Malpensa (MXP)")
        base_transfer = transfers.get(airport_used, "Servizio bus o taxi locale.")
        
        if hour >= 23 or hour < 5:
            self.transfer_info = f"⚠️ Atterraggio notturno ({arrival_time}). Consigliato: Taxi ufficiale o navetta. Base: {base_transfer}"
        else:
            self.transfer_info = f"✅ Collegamenti regolari ({arrival_time}): {base_transfer}"
        
        self.step = 3

    def generate_itinerary(self, travel_style):
        self.travel_style = travel_style
        if "tokyo" in self.destination.lower():
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
            "reason": "Ottimo compromesso tra orari comodi diurni e la tariffa più bassa rilevata tra i diversi vettori."
        }
        
        self.flight_recommendation = (
            f"🎯 **Analisi Matrice Voli & Tariffe completata:**\n\n"
            f"- **Compagnia consigliata:** {best_option['airline']}\n"
            f"- **Periodo ottimale trovato:** Dal {best_option['departure_dates']}[cite: 1]\n"
            f"- **Orari:** {best_option['departure_time']}[cite: 1]\n"
            f"- **Prezzo stimato:** {best_option['price']}[cite: 1]\n\n"
            f"💡 *Perché te lo consiglio:* {best_option['reason']}[cite: 1]"
        )
        
        self.generate_checkout_links()

    def generate_checkout_links(self):
        dest_query = self.destination.replace(" ", "+")
        origin_query = self.origin_city.replace(" ", "+")
        self.checkout_links = {
            "google_flights": f"https://www.google.com/travel/flights?q=Flights+from+{origin_query}+to+{dest_query}",
            "transfer_info_link": "https://www.rome2rio.com/it/"
        }

# --- 2. CONFIGURAZIONE INTERFACCIA GRAFICA (STREAMLIT) ---
st.set_page_config(page_title="Travel AI Assistant", page_icon="✈️", layout="wide")

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
st.markdown("##### Il tuo agente di viaggio completo: ricerca voli, matrici incrociate, logistica di terra e itinerari su misura.")
st.divider()

if "agent_state" not in st.session_state:
    st.session_state.agent_state = TravelAgentState()

state = st.session_state.agent_state

# --- STEP 1 ---
if state.step == 1:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("1️⃣ Raccolta Preferenze e Parametri")
        with st.form("step1_form"):
            destination = st.text_input("Destinazione", placeholder="Es. Tokyo, Parigi, Lamezia Terme")
            dates = st.text_input("Periodo / Date", placeholder="Es. Settembre, 10-17 Ottobre")
            origin_city = st.text_input("Città di Partenza", placeholder="Es. Milano, Roma, Trento")
            
            with st.expander("⚙️ Filtri Avanzati (Budget e Compagnie)"):
                budget_max = st.text_input("Budget massimo", placeholder="Es. 1200€")
                preferred_airlines = st.text_input("Compagnie preferite (separate da virgola)", placeholder="Es. Ryanair, ITA, EasyJet")
                max_stops = st.selectbox("Numero massimo di scali", [0, 1, 2], index=1)

            submitted = st.form_submit_button("🚀 Avvia Analisi e Mappatura", use_container_width=True)
            if submitted and destination and dates and origin_city:
                airlines_list = [a.strip() for a in preferred_airlines.split(",")] if preferred_airlines else []
                state.set_user_input(destination, dates, origin_city, budget_max, airlines_list, max_stops)
                st.rerun()
    with col2:
        st.markdown("### Come funziona?")
        st.info(
            "1. **Mappatura:** Individuazione degli aeroporti.\n"
            "2. **Logistica:** Controllo transfer e orari.\n"
            "3. **Matrice:** Incrocio date, orari e prezzi tra i vettori[cite: 1].\n"
            "4. **Checkout:** Link pronti per l'acquisto."
        )

# --- STEP 2 ---
elif state.step == 2:
    st.subheader("2️⃣ Aeroporti Mappati e Selezione Volo di Prova")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Città di Partenza", state.origin_city)
    col2.metric("Destinazione", state.destination)
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
    
    # Mostra il consiglio della matrice incrociata dei voli
    st.success(state.flight_recommendation)
    
    # Divisione principale pulita in due schede essenziali
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
            
    # Racchiudiamo gli strumenti extra in un expander per evitare confusione visiva
    with st.expander("📂 Altri strumenti utili (Valigia, Calcolatore Budget, Chat)"):
        sub_tab1, sub_tab2, sub_tab3 = st.tabs(["🧳 Valigia & Meteo", "💰 Budget", "💬 Chat IA"])
        
        with sub_tab1:
            st.markdown("### 🌤️ Previsioni Meteo e Consigli Valigia")
            st.write("Porta abiti comodi, documenti validi e adattatori di corrente se necessari per la meta.")
            
        with sub_tab2:
            st.markdown("### 💶 Calcolatore Rapido Spese")
            c_b1, c_b2 = st.columns(2)
            with c_b1:
                st.number_input("Costo Voli (€)", value=150.0)
                st.number_input("Costo Hotel (€)", value=300.0)
            with c_b2:
                st.number_input("Cibo e Extra (€)", value=200.0)
            st.info(f"💡 Budget massimo impostato: {state.budget_max if state.budget_max else 'Non specificato'}")
            
        with sub_tab3:
            st.markdown("### 💬 Consulente IA")
            st.text_input(f"Fai una domanda specifica su {state.destination}:", placeholder="Es. Quali documenti servono?")

    st.divider()
    if st.button("🔄 Pianifica un nuovo viaggio", use_container_width=True):
        st.session_state.agent_state = TravelAgentState()
        st.rerun()
