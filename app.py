import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
from vector_db import ServiceVectorDB
import time
import math
import requests
import json

# Load environment variables
load_dotenv()

def initialize_gemini():
    """Initialize Gemini AI model"""
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            st.error("❌ GEMINI_API_KEY not found. Please check your .env file.")
            return None
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
        return model
    except Exception as e:
        st.error(f"❌ Failed to initialize Gemini: {str(e)}")
        return None

def initialize_database():
    """Initialize vector database and load real data automatically"""
    try:
        db = ServiceVectorDB()
        
        # Check if database is empty and auto-load real data
        stats = db.get_stats()
        if stats.get('total_services', 0) == 0:
            # Auto-load real JustDial data
            if os.path.exists("real_justdial_comprehensive.json"):
                if db.load_services_from_json("real_justdial_comprehensive.json"):
                    st.success("✅ Real JustDial data loaded automatically!")
                else:
                    st.warning("⚠️ Failed to load real data")
        
        return db
    except Exception as e:
        st.error(f"❌ Database initialization failed: {str(e)}")
        return None

def is_conversational_message(user_input):
    """Detect if user input is a conversational message rather than a service search"""
    user_lower = user_input.lower().strip()
    
    # Greetings and casual chat
    greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'namaste', 'how are you']
    casual_chat = ['what are you', 'who are you', 'tell about yourself', 'about you', 'your name', 'what do you do']
    thanks = ['thank you', 'thanks', 'thx', 'appreciate']
    goodbye = ['bye', 'goodbye', 'see you', 'take care', 'good night']
    
    # Check if message contains conversational keywords
    all_conversational = greetings + casual_chat + thanks + goodbye
    
    for keyword in all_conversational:
        if keyword in user_lower:
            return True
    
    # Check if it's a very short message (likely conversational)
    if len(user_input.split()) <= 3 and not any(service_word in user_lower for service_word in 
        ['service', 'repair', 'doctor', 'restaurant', 'food', 'plumber', 'electrician', 'gym', 'salon']):
        return True
    
    return False

def generate_conversational_response(user_input):
    """Generate appropriate conversational responses"""
    user_lower = user_input.lower().strip()
    
    # Greetings
    if any(greeting in user_lower for greeting in ['hi', 'hello', 'hey']):
        return "Hello! 👋 I'm your friendly Local Service Finder assistant! How can I help you find services today? I can help you discover restaurants, repair services, doctors, salons, and much more in your area! ✨"
    
    elif 'good morning' in user_lower:
        return "Good morning! ☀️ What a beautiful day to find some great local services! How can I assist you today?"
    
    elif 'good afternoon' in user_lower:
        return "Good afternoon! 🌞 Hope you're having a wonderful day! What services are you looking for?"
    
    elif 'good evening' in user_lower:
        return "Good evening! 🌙 How can I help you find the perfect local services tonight?"
    
    elif 'namaste' in user_lower:
        return "Namaste! 🙏 Welcome! I'm here to help you discover amazing local services. What are you looking for today?"
    
    # About/Identity questions
    elif any(phrase in user_lower for phrase in ['what are you', 'who are you', 'tell about yourself', 'about you']):
        return "I'm your AI-powered Local Service Finder! 🤖✨ I help you discover and connect with local businesses and services. I can find restaurants, repair services, doctors, salons, gyms, and much more! Just tell me what you're looking for and I'll find the best options for you! 🎯"
    
    elif 'your name' in user_lower:
        return "I'm your Local Service Assistant! 🎯 You can just call me your service buddy! I'm here to help you find exactly what you need in your area! 😊"
    
    elif 'what do you do' in user_lower:
        return "I help you find local services! 🔍✨ Whether you need a plumber, want to try a new restaurant, looking for a doctor, or need any other service - I'll search through real business data to find the best matches for you! Just describe what you're looking for! 🌟"
    
    # Thanks
    elif any(thanks in user_lower for thanks in ['thank you', 'thanks', 'thx']):
        return "You're very welcome! 😊 I'm always happy to help you find great local services! Feel free to ask me anything else you need! ✨"
    
    # Goodbye
    elif any(bye in user_lower for bye in ['bye', 'goodbye', 'see you', 'take care']):
        return "Goodbye! 👋 It was great helping you today! Come back anytime you need to find local services! Take care! 🌟"
    
    elif 'good night' in user_lower:
        return "Good night! 🌙✨ Sweet dreams! I'll be here whenever you need to find local services again! 😴"
    
    # How are you
    elif 'how are you' in user_lower:
        return "I'm doing fantastic, thank you for asking! 😊 I'm excited to help you find amazing local services! How are you doing today? What can I help you discover? ✨"
    
    # Default friendly response for other conversational inputs
    else:
        return "That's nice! 😊 I'm here to help you find local services whenever you need them. You can ask me about restaurants, repair services, doctors, salons, gyms, or any other business you're looking for! What would you like to find today? ✨"

def get_user_location():
    """Get user's current location using Streamlit's geolocation capabilities"""
    # Add JavaScript for getting location that auto-triggers on page load
    location_component = st.components.v1.html(f"""
    <script>
    let locationRequested = false;
    
    function getLocation() {{
        if (locationRequested) return;
        locationRequested = true;
        
        if (navigator.geolocation) {{
            navigator.geolocation.getCurrentPosition(
                function(position) {{
                    const location = {{
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy,
                        timestamp: Date.now()
                    }};
                    
                    // Store in localStorage for persistence
                    localStorage.setItem('userLocation', JSON.stringify(location));
                    
                    // Try to communicate with Streamlit
                    if (window.parent) {{
                        window.parent.postMessage({{
                            type: 'location_success',
                            data: location
                        }}, '*');
                    }}
                }},
                function(error) {{
                    const errorResponse = {{
                        error: true,
                        message: error.message,
                        code: error.code,
                        timestamp: Date.now()
                    }};
                    
                    localStorage.setItem('locationError', JSON.stringify(errorResponse));
                    
                    if (window.parent) {{
                        window.parent.postMessage({{
                            type: 'location_error',
                            data: errorResponse
                        }}, '*');
                    }}
                }},
                {{
                    enableHighAccuracy: true,
                    timeout: 15000,
                    maximumAge: 300000
                }}
            );
        }} else {{
            const errorResponse = {{
                error: true,
                message: 'Geolocation is not supported by this browser.',
                timestamp: Date.now()
            }};
            
            localStorage.setItem('locationError', JSON.stringify(errorResponse));
            
            if (window.parent) {{
                window.parent.postMessage({{
                    type: 'location_error',
                    data: errorResponse
                }}, '*');
            }}
        }}
    }}
    
    // Check if we already have location data
    const savedLocation = localStorage.getItem('userLocation');
    const savedError = localStorage.getItem('locationError');
    
    if (savedLocation) {{
        const location = JSON.parse(savedLocation);
        // Check if location is fresh (less than 10 minutes old)
        if (Date.now() - location.timestamp < 600000) {{
            if (window.parent) {{
                window.parent.postMessage({{
                    type: 'location_success',
                    data: location
                }}, '*');
            }}
        }} else {{
            localStorage.removeItem('userLocation');
            getLocation();
        }}
    }} else if (savedError) {{
        const error = JSON.parse(savedError);
        if (window.parent) {{
            window.parent.postMessage({{
                type: 'location_error', 
                data: error
            }}, '*');
        }}
    }} else {{
        // First time - request location
        setTimeout(getLocation, 500);
    }}
    </script>
    <div style="padding: 15px; background: linear-gradient(45deg, #FF6B6B, #4ECDC4); 
                color: white; border-radius: 12px; text-align: center; margin: 10px 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2); animation: pulse 2s infinite;">
        <div style="font-size: 1.2em; margin-bottom: 10px;">📍 Location Access</div>
        <div style="font-size: 0.9em; opacity: 0.9;">
            Please allow location access to find nearest services!<br>
            <small>Click "Allow" when prompted by your browser</small>
        </div>
    </div>
    <style>
    @keyframes pulse {{
        0% {{ transform: scale(1); }}
        50% {{ transform: scale(1.02); }}
        100% {{ transform: scale(1); }}
    }}
    </style>
    """, height=120, key=f"location_detector_{st.session_state.get('location_key', 0)}")
    
    return location_component

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    return c * r

def get_coordinates_from_address(address):
    """Get latitude and longitude from address using a simple geocoding approach"""
    # City coordinates mapping for common Indian cities
    city_coordinates = {
        'hyderabad': (17.3850, 78.4867),
        'mumbai': (19.0760, 72.8777),
        'delhi': (28.6139, 77.2090),
        'bangalore': (12.9716, 77.5946),
        'chennai': (13.0827, 80.2707),
        'kolkata': (22.5726, 88.3639),
        'pune': (18.5204, 73.8567),
        'ahmedabad': (23.0225, 72.5714),
        'jaipur': (26.9124, 75.7873),
        'lucknow': (26.8467, 80.9462),
        'kanpur': (26.4499, 80.3319),
        'nagpur': (21.1458, 79.0882),
        'indore': (22.7196, 75.8577),
        'thane': (19.2183, 72.9781),
        'bhopal': (23.2599, 77.4126),
        'visakhapatnam': (17.6868, 83.2185),
        'patna': (25.5941, 85.1376),
        'vadodara': (22.3072, 73.1812),
        'ghaziabad': (28.6692, 77.4538),
        'ludhiana': (30.9010, 75.8573),
        'agra': (27.1767, 78.0081),
        'nashik': (19.9975, 73.7898),
        'faridabad': (28.4089, 77.3178),
        'meerut': (28.9845, 77.7064),
        'rajkot': (22.3039, 70.8022),
        'kalyan': (19.2437, 73.1355),
        'vasai': (19.4909, 72.8152),
        'varanasi': (25.3176, 82.9739),
        'srinagar': (34.0837, 74.7973),
        'aurangabad': (19.8762, 75.3433),
        'dhanbad': (23.7957, 86.4304),
        'amritsar': (31.6340, 74.8723),
        'navi mumbai': (19.0330, 73.0297),
        'allahabad': (25.4358, 81.8463),
        'ranchi': (23.3441, 85.3096),
        'howrah': (22.5958, 88.2636),
        'coimbatore': (11.0168, 76.9558),
        'jabalpur': (23.1815, 79.9864),
        'gwalior': (26.2183, 78.1828),
        'vijayawada': (16.5062, 80.6480),
        'jodhpur': (26.2389, 73.0243),
        'madurai': (9.9252, 78.1198),
        'raipur': (21.2514, 81.6296),
        'kota': (25.2138, 75.8648),
        'guntur': (16.3067, 80.4365),
        'bhubaneswar': (20.2961, 85.8245),
        'dehradun': (30.3165, 78.0322),
        'asansol': (23.6739, 86.9524),
        'nellore': (14.4426, 79.9865),
        'jammu': (32.7266, 74.8570),
        'belagavi': (15.8497, 74.4977),
        'rourkela': (22.2604, 84.8536),
        'mangaluru': (12.9141, 74.8560),
        'tirunelveli': (8.7139, 77.7567),
        'malegaon': (20.5579, 74.5287),
        'gaya': (24.7914, 85.0002)
    }
    
    # Extract city name from address
    address_lower = address.lower()
    for city, coords in city_coordinates.items():
        if city in address_lower:
            return coords
    
    # Default to Hyderabad if no match found
    return (17.3850, 78.4867)

def add_distances_to_services(services, user_lat, user_lon):
    """Add distance information to services and sort by proximity"""
    services_with_distance = []
    
    for service in services:
        address = service.get('address', '')
        if address:
            service_lat, service_lon = get_coordinates_from_address(address)
            distance = calculate_distance(user_lat, user_lon, service_lat, service_lon)
            service['distance'] = round(distance, 2)
            service['distance_text'] = f"{distance:.1f} km away"
        else:
            service['distance'] = 999  # Unknown distance
            service['distance_text'] = "Distance unknown"
        
        services_with_distance.append(service)
    
    # Sort by distance (nearest first)
    services_with_distance.sort(key=lambda x: x.get('distance', 999))
    return services_with_distance

def enhance_search_query(user_input):
    """Enhance search query for better matching"""
    query_mapping = {
        'bike repair': ['bike service', 'bike repair', 'two wheeler service', 'motorcycle repair'],
        'bike service': ['bike service', 'bike repair', 'two wheeler service', 'motorcycle repair'],
        'motorcycle': ['bike service', 'bike repair', 'two wheeler service'],
        'two wheeler': ['bike service', 'bike repair', 'two wheeler service'],
        'ac repair': ['ac repair', 'air conditioning', 'ac service'],
        'air conditioning': ['ac repair', 'air conditioning', 'ac service'],
        'plumber': ['plumber', 'plumbing service', 'water repair'],
        'electrician': ['electrician', 'electrical service', 'electrical repair'],
        'restaurant': ['restaurant', 'food', 'dining', 'eating'],
        'food': ['restaurant', 'food', 'dining', 'cafe'],
        'doctor': ['doctor', 'physician', 'medical', 'clinic'],
        'dentist': ['dentist', 'dental', 'tooth doctor'],
        'gym': ['gym', 'fitness', 'exercise', 'workout'],
        'beauty': ['beauty parlor', 'salon', 'beauty service'],
        'salon': ['beauty parlor', 'salon', 'beauty service']
    }
    
    user_lower = user_input.lower()
    for key, synonyms in query_mapping.items():
        if key in user_lower:
            return synonyms
    
    return [user_input]

def search_services_enhanced(db, user_input, category_filter=None, location_filter=None, max_price=1000, n_results=5):
    """Enhanced search with multiple strategies"""
    # Strategy 1: Try exact search first
    services = db.search_services(user_input, n_results=n_results)
    
    if services:
        filtered_services = []
        for service in services:
            # Apply filters
            if category_filter and service.get('category') != category_filter:
                continue
            if location_filter and location_filter.lower() not in service.get('location', '').lower():
                continue
            
            # Price filter
            price_str = service.get('price', '₹0')
            try:
                price_num = int(''.join(filter(str.isdigit, price_str)))
                if price_num > max_price:
                    continue
            except:
                pass
            
            filtered_services.append(service)
        
        if filtered_services:
            return filtered_services[:n_results]
    
    # Strategy 2: Try enhanced search with synonyms
    enhanced_queries = enhance_search_query(user_input)
    for query in enhanced_queries:
        services = db.search_services(query, n_results=n_results)
        if services:
            # Apply same filtering logic
            filtered_services = []
            for service in services:
                if category_filter and service.get('category') != category_filter:
                    continue
                if location_filter and location_filter.lower() not in service.get('location', '').lower():
                    continue
                
                price_str = service.get('price', '₹0')
                try:
                    price_num = int(''.join(filter(str.isdigit, price_str)))
                    if price_num > max_price:
                        continue
                except:
                    pass
                
                filtered_services.append(service)
            
            if filtered_services:
                return filtered_services[:n_results]
    
    # Strategy 3: Category-based search if category filter is applied
    if category_filter:
        services = db.search_services(category_filter, n_results=n_results*2)
        if services:
            filtered_services = []
            for service in services:
                if location_filter and location_filter.lower() not in service.get('location', '').lower():
                    continue
                
                price_str = service.get('price', '₹0')
                try:
                    price_num = int(''.join(filter(str.isdigit, price_str)))
                    if price_num > max_price:
                        continue
                except:
                    pass
                
                filtered_services.append(service)
            
            if filtered_services:
                return filtered_services[:n_results]
    
    return []

def generate_ai_response(model, query, services, category_filter=None, location_filter=None):
    """Generate AI response with rate limit handling"""
    if not model or not services:
        return None
    
    try:
        # Create context for AI
        services_context = []
        for service in services:
            context = f"- {service.get('name', 'N/A')} ({service.get('category', 'N/A')}) in {service.get('location', 'N/A')} - Price: {service.get('price', 'N/A')}, Rating: {service.get('rating', 'N/A')}"
            services_context.append(context)
        
        context_str = "\n".join(services_context)
        
        filters_str = ""
        if category_filter:
            filters_str += f" Category: {category_filter}."
        if location_filter:
            filters_str += f" Location: {location_filter}."
        
        prompt = f"""
        User Query: {query}
        Applied Filters:{filters_str}
        
        Found Services:
        {context_str}
        
        Provide a helpful text recommendation for the user based on their query and the services found. Be concise and practical.
        Include specific service recommendations with reasons why they're good choices.
        
        IMPORTANT: Return only plain text, no HTML, no markdown formatting, no code blocks. Just natural language text.
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "rate" in error_msg.lower():
            return "⚠️ **Rate Limit Reached** - Too many requests. Please wait a moment before trying again."
        else:
            return f"⚠️ **AI Response Error** - Unable to generate recommendations at the moment."

def main():
    st.set_page_config(
        page_title="Local Service Finder Bot", 
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for enhanced styling
    st.markdown("""
    <style>
    /* Main container styling */
    .main > div {
        padding-top: 2rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 2rem 2rem 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        text-align: center;
    }
    
    .main-header h1 {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.2rem;
        margin: 0;
        font-weight: 300;
    }
    
    /* Service card styling */
    .service-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .service-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    
    /* Chat input styling */
    .stChatInputContainer {
        background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 25px;
        padding: 0.5rem;
        margin: 1rem 0;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 10px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Enhanced header
    st.markdown("""
    <div class="main-header">
        <h1>🔍 Local Service Finder</h1>
        <p>✨ Discover trusted local services with AI-powered recommendations ✨</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize components
    try:
        model = initialize_gemini()
        db = initialize_database()
        
        if not db:
            st.error("❌ Failed to initialize database. Please check the setup.")
            return
            
    except Exception as e:
        st.error(f"❌ Initialization error: {str(e)}")
        return
    
    # Enhanced sidebar
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 15px; margin-bottom: 1rem; color: white;">
            <h2 style="margin: 0; font-weight: 600;">🔧 Dashboard</h2>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Service Statistics & Info</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Location Status Section
        st.markdown("### 📍 Your Location")
        
        # Display current location status
        if st.session_state.get('user_location'):
            loc = st.session_state.user_location
            st.success("✅ Location accessed!")
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); 
                        color: white; padding: 1rem; border-radius: 10px; text-align: center; margin: 0.5rem 0;">
                <div style="font-size: 0.95em; font-weight: 600;">📍 Your Location</div>
                <div style="font-size: 0.8em; margin: 0.3rem 0; opacity: 0.9;">
                    Lat: {loc['latitude']:.4f} • Lon: {loc['longitude']:.4f}
                </div>
                <div style="font-size: 0.8em; opacity: 0.9;">
                    🎯 Services sorted by distance
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        elif st.session_state.get('location_error'):
            st.error("❌ Location access denied")
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); 
                        color: white; padding: 1rem; border-radius: 10px; text-align: center; margin: 0.5rem 0;">
                <div style="font-size: 0.9em;">🚫 Location Error</div>
                <div style="font-size: 0.8em; margin-top: 0.3rem; opacity: 0.9;">
                    {st.session_state.location_error}
                </div>
                <div style="font-size: 0.8em; margin-top: 0.3rem; opacity: 0.9;">
                    Services shown without distance sorting
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        elif st.session_state.get('location_skipped'):
            st.info("⏭️ Location access skipped")
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #6c757d 0%, #5a6268 100%); 
                        color: white; padding: 1rem; border-radius: 10px; text-align: center; margin: 0.5rem 0;">
                <div style="font-size: 0.9em;">📍 Location Disabled</div>
                <div style="font-size: 0.8em; margin-top: 0.3rem; opacity: 0.9;">
                    Services shown without distance sorting
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        else:
            # Show clickable option to allow location
            st.info("📍 Allow location service")
            if st.button("🎯 Allow Location Access", 
                        key="sidebar_allow_location",
                        help="Click to enable location-based service sorting",
                        use_container_width=True):
                # Reset location_handled to show the location request again
                st.session_state.location_handled = False
                st.rerun()
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #ffc107 0%, #ff8c00 100%); 
                        color: white; padding: 1rem; border-radius: 10px; text-align: center; margin: 0.5rem 0;">
                <div style="font-size: 0.9em;">📍 Location Not Set</div>
                <div style="font-size: 0.8em; margin-top: 0.3rem; opacity: 0.9;">
                    Click above to enable location services
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("---")
        
        # Database stats
        stats = db.get_stats()
        
        # Enhanced metrics display
        st.markdown("### 📊 Live Statistics")
        
        # Create beautiful metric cards
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%); 
                        color: white; padding: 1rem; border-radius: 10px; text-align: center; margin-bottom: 0.5rem;">
                <h3 style="margin: 0; font-size: 1.8rem;">{stats.get('total_services', 0)}</h3>
                <p style="margin: 0; opacity: 0.9;">Services</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%); 
                        color: white; padding: 1rem; border-radius: 10px; text-align: center; margin-bottom: 0.5rem;">
                <h3 style="margin: 0; font-size: 1.8rem;">{stats.get('categories', 0)}</h3>
                <p style="margin: 0; opacity: 0.9;">Categories</p>
            </div>
            """, unsafe_allow_html=True)
            
        # Locations metric
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #45b7d1 0%, #96c93d 100%); 
                    color: white; padding: 1rem; border-radius: 10px; text-align: center; margin-bottom: 1rem;">
            <h3 style="margin: 0; font-size: 1.8rem;">{stats.get('locations', 0)}</h3>
            <p style="margin: 0; opacity: 0.9;">Locations</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced data status
        total_services = stats.get('total_services', 0)
        if total_services >= 100:
            st.markdown("""
            <div style="background: linear-gradient(90deg, #00b09b 0%, #96c93d 100%); 
                        color: white; padding: 1rem; border-radius: 10px; text-align: center; margin: 1rem 0;">
                <h4 style="margin: 0;">🎉 Real JustDial Data Active!</h4>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Authentic business information loaded</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: linear-gradient(90deg, #ff6b6b 0%, #ee5a52 100%); 
                        color: white; padding: 1rem; border-radius: 10px; text-align: center; margin: 1rem 0;">
                <h4 style="margin: 0;">❌ No Data Available</h4>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Please check data files</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Export Section
        st.markdown("---")
        st.markdown("### 📥 Export Options")
        
        if st.button("📊 Export Service Data", 
                    help="Download current search results as JSON",
                    use_container_width=True):
            if 'last_search_results' in st.session_state and st.session_state.last_search_results:
                # Prepare export data
                export_data = {
                    "search_query": st.session_state.get('last_search_query', ''),
                    "total_services": len(st.session_state.last_search_results),
                    "export_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "services": st.session_state.last_search_results
                }
                
                # Convert to JSON
                json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
                
                # Create download button
                st.download_button(
                    label="💾 Download JSON File",
                    data=json_str,
                    file_name=f"service_results_{int(time.time())}.json",
                    mime="application/json",
                    use_container_width=True
                )
                st.success("✅ Export ready! Click download button above.")
            else:
                st.warning("⚠️ No search results to export. Please search for services first.")
        
        # Help Section
        st.markdown("---")
        st.markdown("### ❓ Help & Tips")
        
        with st.expander("🔍 How to Search", expanded=False):
            st.markdown("""
            **Search Examples:**
            - "AC repair services in Hyderabad"
            - "Find plumbers under ₹300"
            - "Best electricians near me"
            - "Show me affordable AC repair"
            
            **Pro Tips:**
            - Use specific service names for better results
            - Mention your location for local services
            - Set price range using filters
            - Enable location for distance-based sorting
            """)
        
        with st.expander("🗺️ Location Features", expanded=False):
            st.markdown("""
            **Location Benefits:**
            - Get services sorted by distance
            - See "X km away" badges
            - One-click Google Maps navigation
            - Find nearest available services
            
            **How to Enable:**
            1. Click "Allow Location Access" button
            2. Accept browser location permission
            3. Enjoy distance-based results!
            """)
        
        with st.expander("📱 Contact Options", expanded=False):
            st.markdown("""
            **Quick Contact Methods:**
            - 📞 **Call Now**: Direct phone dialing
            - 💬 **WhatsApp**: Send pre-filled message
            - 🗺️ **Google Maps**: Get directions
            
            **Contact Features:**
            - One-click calling (mobile devices)
            - WhatsApp with pre-filled message
            - Google Maps navigation
            """)
        
        # App Info
        st.markdown("---")
        st.markdown("### ℹ️ App Information")
        
        st.markdown("""
        <div style="text-align: center; margin-top: 1rem; padding: 1rem; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; border-radius: 10px;">
            <div style="font-size: 0.9em; font-weight: bold;">🔍 Local Service Finder</div>
            <div style="font-size: 0.7em; opacity: 0.8; margin: 0.3rem 0;">
                Powered by Google Gemini AI & ChromaDB
            </div>
            <div style="font-size: 0.7em; opacity: 0.8;">
                Version 2.0 • Made with ❤️
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced filter section
        st.markdown("---")
        st.markdown("### 🎛️ Smart Filters")
        
        # Category filter
        categories = ["All"] + stats.get('category_list', [])
        selected_category = st.selectbox(
            "🏷️ Category", 
            categories,
            help="Filter services by category"
        )
        
        # Location filter
        locations = ["All"] + stats.get('location_list', [])
        selected_location = st.selectbox(
            "📍 Location", 
            locations,
            help="Filter services by location"
        )
        
        # Price filter
        max_price = st.slider(
            "💰 Max Price (₹)", 
            0, 1000, 1000, 
            step=50,
            help="Set maximum price range"
        )
        
        # Enhanced expandable sections
        with st.expander("🏪 Available Categories", expanded=False):
            category_list = stats.get('category_list', [])
            if category_list:
                for i in range(0, len(category_list), 2):
                    col1, col2 = st.columns(2)
                    with col1:
                        if i < len(category_list):
                            st.markdown(f"""
                            <div style="background: #f8f9fa; padding: 0.5rem; border-radius: 8px; 
                                        margin: 0.2rem 0; border-left: 3px solid #667eea;">
                                <span style="color: #2c3e50; font-weight: 500;">📋 {category_list[i]}</span>
                            </div>
                            """, unsafe_allow_html=True)
                    with col2:
                        if i + 1 < len(category_list):
                            st.markdown(f"""
                            <div style="background: #f8f9fa; padding: 0.5rem; border-radius: 8px; 
                                        margin: 0.2rem 0; border-left: 3px solid #667eea;">
                                <span style="color: #2c3e50; font-weight: 500;">📋 {category_list[i + 1]}</span>
                            </div>
                            """, unsafe_allow_html=True)
        
        with st.expander("📍 Coverage Areas", expanded=False):
            location_list = stats.get('location_list', [])
            if location_list:
                for i in range(0, len(location_list), 2):
                    col1, col2 = st.columns(2)
                    with col1:
                        if i < len(location_list):
                            st.markdown(f"""
                            <div style="background: #f8f9fa; padding: 0.5rem; border-radius: 8px; 
                                        margin: 0.2rem 0; border-left: 3px solid #28a745;">
                                <span style="color: #2c3e50; font-weight: 500;">🌍 {location_list[i]}</span>
                            </div>
                            """, unsafe_allow_html=True)
                    with col2:
                        if i + 1 < len(location_list):
                            st.markdown(f"""
                            <div style="background: #f8f9fa; padding: 0.5rem; border-radius: 8px; 
                                        margin: 0.2rem 0; border-left: 3px solid #28a745;">
                                <span style="color: #2c3e50; font-weight: 500;">🌍 {location_list[i + 1]}</span>
                            </div>
                            """, unsafe_allow_html=True)
        
        # Enhanced clear chat button
        if st.button("🗑️ Clear Chat", help="Clear conversation history"):
            st.session_state.messages = []
            st.rerun()
    
    # Main content area
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                border-radius: 10px; margin-bottom: 2rem;">
        <h3 style="margin: 0; color: #495057;">💬 How can I help you today?</h3>
        <p style="margin: 0.5rem 0 0 0; color: #6c757d;">Ask me about any local service you need!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "user_location" not in st.session_state:
        st.session_state.user_location = None
    if "location_handled" not in st.session_state:
        st.session_state.location_handled = False
    
    # Auto-show location popup on first visit
    if not st.session_state.get('location_handled', False):
        # Simple and clean location request dialog
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 2rem; border-radius: 20px; text-align: center; 
                    margin: 2rem 0; box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                    animation: fadeIn 1s ease-in;">
            <h2 style="margin: 0 0 1rem 0; font-size: 2rem;">📍 Location Access Required</h2>
            <p style="margin: 0 0 1.5rem 0; font-size: 1.1rem; opacity: 0.95;">
                Allow location access to find the nearest services around you!<br>
                <span style="font-size: 0.9rem; opacity: 0.8;">This helps us show you services sorted by distance</span>
            </p>
        </div>
        <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Create clearly visible buttons with proper spacing
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Allow Location Button
            if st.button("📍 Allow Location Access", 
                        key="allow_location_main",
                        help="Click to enable location-based service sorting",
                        type="primary",
                        use_container_width=True):
                
                # Show loading message
                with st.spinner("📡 Requesting location permission..."):
                    # Request location using JavaScript
                    location_request = st.components.v1.html("""
                    <div style="text-align: center; padding: 20px;">
                        <h3>Please allow location access in your browser</h3>
                        <p>Click "Allow" when your browser asks for location permission</p>
                    </div>
                    <script>
                    if (navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(
                            function(position) {
                                // Store location data
                                sessionStorage.setItem('userLocation', JSON.stringify({
                                    latitude: position.coords.latitude,
                                    longitude: position.coords.longitude,
                                    accuracy: position.coords.accuracy,
                                    timestamp: Date.now()
                                }));
                                // Reload page to update state
                                setTimeout(function() {
                                    window.location.reload();
                                }, 1000);
                            },
                            function(error) {
                                // Store error
                                sessionStorage.setItem('locationError', JSON.stringify({
                                    message: error.message,
                                    code: error.code,
                                    timestamp: Date.now()
                                }));
                                // Reload page to update state
                                setTimeout(function() {
                                    window.location.reload();
                                }, 1000);
                            },
                            {
                                enableHighAccuracy: true,
                                timeout: 10000,
                                maximumAge: 300000
                            }
                        );
                    } else {
                        sessionStorage.setItem('locationError', JSON.stringify({
                            message: 'Geolocation is not supported by this browser',
                            timestamp: Date.now()
                        }));
                        setTimeout(function() {
                            window.location.reload();
                        }, 1000);
                    }
                    </script>
                    """, height=150)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Skip Button
            if st.button("⏭️ Skip Location Access", 
                        key="skip_location_main",
                        help="Continue without location-based sorting",
                        use_container_width=True):
                st.session_state.location_handled = True
                st.session_state.location_skipped = True
                st.success("⏭️ Location access skipped. You can still search for services!")
                time.sleep(1)
                st.rerun()
        
        # Add some spacing
        st.markdown("<br><br>", unsafe_allow_html=True)
        
    # Always check for stored location data when location_handled is True
    if st.session_state.get('location_handled', False) and not st.session_state.get('user_location') and not st.session_state.get('location_error') and not st.session_state.get('location_skipped'):
        # Check session storage for location data
        location_data_check = st.components.v1.html("""
        <script>
        const userLocation = sessionStorage.getItem('userLocation');
        const locationError = sessionStorage.getItem('locationError');
        
        if (userLocation) {
            try {
                const loc = JSON.parse(userLocation);
                // Clear session storage after reading
                sessionStorage.removeItem('userLocation');
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: { type: 'location', data: loc }
                }, '*');
            } catch(e) {
                console.error('Error parsing location data:', e);
            }
        } else if (locationError) {
            try {
                const error = JSON.parse(locationError);
                // Clear session storage after reading  
                sessionStorage.removeItem('locationError');
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: { type: 'error', message: error.message }
                }, '*');
            } catch(e) {
                console.error('Error parsing location error:', e);
            }
        }
        </script>
        """, height=0)
        
        if location_data_check:
            if location_data_check.get('type') == 'location':
                st.session_state.user_location = location_data_check['data']
                st.success("✅ Location detected successfully!")
                time.sleep(1)
                st.rerun()
            elif location_data_check.get('type') == 'error':
                st.session_state.location_error = location_data_check['message']
                st.error(f"❌ Location error: {st.session_state.location_error}")
                time.sleep(1)
                st.rerun()
    
    # Display chat history with enhanced styling
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Enhanced user input
    user_input = st.chat_input("✨ Hi! Ask me anything - chat with me or search for local services! (e.g., 'Hi there!' or 'Find AC repair services')")
    
    if user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Check if it's a conversational message or service search
        with st.chat_message("assistant"):
            if is_conversational_message(user_input):
                # Handle conversational messages
                response = generate_conversational_response(user_input)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                # Handle service search
                with st.spinner("🔍 Searching for services..."):
                    # Apply filters
                    category_filter = None if selected_category == "All" else selected_category
                    location_filter = None if selected_location == "All" else selected_location
                    
                    # Use enhanced search
                    services = search_services_enhanced(
                        db=db,
                        user_input=user_input,
                        category_filter=category_filter,
                        location_filter=location_filter,
                        max_price=max_price,
                        n_results=10  # Get more results for better location filtering
                    )
                    
                    # Apply location-based sorting if user location is available
                    if services and 'user_location' in st.session_state and st.session_state.user_location:
                        user_loc = st.session_state.user_location
                        services = add_distances_to_services(
                            services, 
                            user_loc['latitude'], 
                            user_loc['longitude']
                        )
                        # Limit to top 5 after distance sorting
                        services = services[:5]
                        
                        st.success(f"📍 Found {len(services)} services sorted by distance from your location!")
                    else:
                        services = services[:5]  # Limit to 5 if no location
                
                if services:
                    # Store search results for export functionality
                    st.session_state.last_search_results = services
                    st.session_state.last_search_query = user_input
                    
                    # Display services with beautiful cards
                    st.markdown("### 🎯 Found Services")
                    
                    for i, service in enumerate(services, 1):
                        # Create gradient colors for different services
                        colors = [
                            "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                            "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
                            "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
                            "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
                            "linear-gradient(135deg, #fa709a 0%, #fee140 100%)"
                        ]
                        color = colors[(i-1) % len(colors)]
                        
                        # Distance badge for services with location data
                        distance_badge = ""
                        if 'distance' in service and service['distance'] < 999:
                            distance_badge = f"""
                            <div style="background: rgba(255,255,255,0.2); padding: 0.3rem 0.8rem; 
                                        border-radius: 20px; display: inline-block; margin-bottom: 0.5rem;">
                                🚗 {service.get('distance_text', '')}
                            </div>
                            """
                        
                        # Use native Streamlit components instead of HTML
                        with st.container():
                            # Create a colored container using columns for styling
                            col1, col2, col3 = st.columns([1, 8, 1])
                            with col2:
                                # Service name header
                                st.subheader(f"🏢 {service.get('name', 'N/A')}")
                                
                                # Distance badge if available
                                if 'distance' in service and service['distance'] < 999:
                                    st.info(f"� {service.get('distance_text', '')}")
                                
                                # Service details
                                address = service.get('address', 'N/A')
                                if address != 'N/A':
                                    # Display address
                                    st.write(f"📍 {address}")
                                    # Create Google Maps link
                                    maps_url = f"https://www.google.com/maps/search/?api=1&query={address.replace(' ', '+')}"
                                    st.markdown(f"🗺️ [**Open in Google Maps**]({maps_url}) 🚗")
                                else:
                                    st.write("📍 Address not available")
                                
                                # Contact and navigation options
                                phone = service.get('phone', 'N/A')
                                if phone != 'N/A':
                                    # Clean phone number for dialing
                                    clean_phone = ''.join(filter(str.isdigit, str(phone)))
                                    if clean_phone:
                                        st.write(f"📱 {phone}")
                                        # Add call and WhatsApp links
                                        call_col, whatsapp_col = st.columns(2)
                                        with call_col:
                                            st.markdown(f"📞 [**Call Now**](tel:{clean_phone})")
                                        with whatsapp_col:
                                            whatsapp_url = f"https://wa.me/91{clean_phone}?text=Hi, I found your service on Local Service Finder. I'm interested in your services."
                                            st.markdown(f"💬 [**WhatsApp**]({whatsapp_url})")
                                    else:
                                        st.write(f"📱 {phone}")
                                else:
                                    st.write("📱 Contact not available")
                                
                                # Rating and price in columns
                                rating_col, price_col = st.columns(2)
                                with rating_col:
                                    st.write(f"⭐ {service.get('rating', 'N/A')}")
                                with price_col:
                                    price_value = service.get('price', 'N/A')
                                    if price_value != 'N/A':
                                        clean_price = str(price_value).replace('₹₹', '₹')
                                        if not clean_price.startswith('₹'):
                                            clean_price = f"₹{clean_price}"
                                        st.write(f"💰 {clean_price}")
                                    else:
                                        st.write("💰 Price not available")
                                
                                st.divider()  # Add separator between services
                    
                    # Generate AI response with enhanced styling
                    with st.spinner("🤖 Generating personalized recommendations..."):
                        ai_response = generate_ai_response(
                            model=model, 
                            query=user_input, 
                            services=services, 
                            category_filter=category_filter,
                            location_filter=location_filter
                        )
                        
                        if ai_response:
                            # Clean AI response from any HTML tags and escape HTML entities
                            import re
                            import html
                            
                            # Remove HTML tags
                            clean_response = re.sub(r'<[^>]+>', '', ai_response)
                            # Unescape HTML entities
                            clean_response = html.unescape(clean_response)
                            # Remove extra whitespace
                            clean_response = re.sub(r'\s+', ' ', clean_response).strip()
                            
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                        color: white; padding: 1.5rem; border-radius: 15px; margin: 1rem 0;">
                                <h4 style="margin: 0 0 1rem 0;">🤖 AI Recommendation</h4>
                                <div style="opacity: 0.95;">{html.escape(clean_response)}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            response_content = f"Found {len(services)} services matching your requirements!\n\n{clean_response}"
                        else:
                            response_content = f"Found {len(services)} services matching your requirements!"
                            
                else:
                    # No services found - enhanced message
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%); 
                                color: white; padding: 1.5rem; border-radius: 15px; margin: 1rem 0; text-align: center;">
                        <h4 style="margin: 0 0 1rem 0;">😔 No Services Found</h4>
                        <p style="margin: 0; opacity: 0.9;">
                            Sorry, I couldn't find any services matching your criteria.<br>
                            Try adjusting your search terms or filters.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    response_content = "I couldn't find services matching your request. Please try different search terms or adjust the filters."
                
                # Add assistant response to chat history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response_content
                })
    
    # Enhanced footer
    st.markdown("---")
if __name__ == "__main__":
    main()
