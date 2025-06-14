#!/usr/bin/env python3

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
import re

from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Configuration
RETELL_API_KEY = os.getenv('RETELL_API_KEY')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
DEFAULT_VOICE_ID = os.getenv('DEFAULT_VOICE_ID', '11labs-Adrian')

# Parse MAX_SEARCH_RADIUS more safely to handle comments
max_radius_str = os.getenv('MAX_SEARCH_RADIUS', '50')
try:
    # Split by '#' to remove comments and strip whitespace
    MAX_SEARCH_RADIUS = float(max_radius_str.split('#')[0].strip())
except (ValueError, AttributeError):
    MAX_SEARCH_RADIUS = 50.0  # Default fallback

# Initialize geocoder
geolocator = Nominatim(user_agent="ezcaters_voice_agent")

class CateringService:
    """Mock catering service database for demonstration"""
    
    def __init__(self):
        self.services = [
            {
                "id": 1,
                "name": "Bella's Italian Catering",
                "cuisine": "Italian",
                "location": "Boston, MA",
                "coordinates": (42.3601, -71.0589),
                "rating": 4.8,
                "price_range": "$$",
                "min_order": 25,
                "specialties": ["pasta", "pizza", "sandwiches", "salads"],
                "phone": "+1-555-0101",
                "description": "Authentic Italian cuisine with fresh ingredients"
            },
            {
                "id": 2,
                "name": "Taco Fiesta Catering",
                "cuisine": "Mexican",
                "location": "Cambridge, MA",
                "coordinates": (42.3736, -71.1097),
                "rating": 4.6,
                "price_range": "$",
                "min_order": 20,
                "specialties": ["tacos", "burritos", "nachos", "fajitas"],
                "phone": "+1-555-0102",
                "description": "Fresh Mexican food with vegetarian options"
            },
            {
                "id": 3,
                "name": "Golden Dragon Chinese",
                "cuisine": "Chinese",
                "location": "Somerville, MA",
                "coordinates": (42.3875, -71.0995),
                "rating": 4.7,
                "price_range": "$$",
                "min_order": 30,
                "specialties": ["lo mein", "fried rice", "dumplings", "sweet and sour"],
                "phone": "+1-555-0103",
                "description": "Traditional Chinese dishes with modern presentation"
            },
            {
                "id": 4,
                "name": "Mediterranean Delights",
                "cuisine": "Mediterranean",
                "location": "Newton, MA",
                "coordinates": (42.3370, -71.2092),
                "rating": 4.9,
                "price_range": "$$$",
                "min_order": 35,
                "specialties": ["hummus", "falafel", "kebabs", "pita wraps"],
                "phone": "+1-555-0104",
                "description": "Fresh Mediterranean cuisine with healthy options"
            },
            {
                "id": 5,
                "name": "Southern Comfort Catering",
                "cuisine": "American",
                "location": "Brookline, MA",
                "coordinates": (42.3317, -71.1211),
                "rating": 4.5,
                "price_range": "$$",
                "min_order": 25,
                "specialties": ["bbq", "fried chicken", "mac and cheese", "cornbread"],
                "phone": "+1-555-0105",
                "description": "Classic American comfort food for any occasion"
            }
        ]
    
    def search_by_cuisine(self, cuisine: str) -> List[Dict]:
        """Search catering services by cuisine type"""
        return [service for service in self.services 
                if cuisine.lower() in service['cuisine'].lower()]
    
    def search_by_location(self, location: str, radius: float = MAX_SEARCH_RADIUS) -> List[Dict]:
        """Search catering services by location"""
        try:
            user_location = geolocator.geocode(location)
            if not user_location:
                return []
            
            user_coords = (user_location.latitude, user_location.longitude)
            nearby_services = []
            
            for service in self.services:
                distance = geodesic(user_coords, service['coordinates']).miles
                if distance <= radius:
                    service_copy = service.copy()
                    service_copy['distance'] = round(distance, 1)
                    nearby_services.append(service_copy)
            
            return sorted(nearby_services, key=lambda x: x['distance'])
        except Exception as e:
            print(f"Location search error: {e}")
            return []
    
    def search_by_menu_item(self, menu_item: str) -> List[Dict]:
        """Search catering services by menu item"""
        results = []
        for service in self.services:
            if any(menu_item.lower() in specialty.lower() for specialty in service['specialties']):
                results.append(service)
        return results

# Initialize catering service
catering_service = CateringService()

class VoiceAssistant:
    """Voice assistant logic for handling customer inquiries with conversation memory"""
    
    def __init__(self):
        self.conversation_context = {}
    
    def process_inquiry(self, call_id: str, message: str, user_location: str = None) -> str:
        """Process customer inquiry and return appropriate response with conversation context"""
        
        # Initialize or update conversation context
        if call_id not in self.conversation_context:
            self.conversation_context[call_id] = {
                "stage": "greeting",
                "preferences": {},
                "location": user_location,
                "recommendations": [],
                "dialogue_history": [],
                "last_intent": None,
                "pending_actions": []
            }
        
        context = self.conversation_context[call_id]
        
        # Add user message to dialogue history
        context["dialogue_history"].append({
            "speaker": "user",
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Analyze intent with conversation context
        intent = self.analyze_intent_with_context(message, context)
        context["last_intent"] = intent
        
        # Generate contextual response
        response = self.generate_contextual_response(call_id, intent, message)
        
        # Add assistant response to dialogue history
        context["dialogue_history"].append({
            "speaker": "assistant",
            "message": response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update conversation stage
        self.update_conversation_stage(context, intent)
        
        return response
    
    def analyze_intent_with_context(self, message: str, context: Dict) -> Dict:
        """Analyze customer intent using rule-based pattern matching with conversation context"""
        message_lower = message.lower().strip()
        
        # Check for continuation phrases that reference previous context
        continuation_patterns = [
            r'\b(yes|yeah|yep|sure|ok|okay|sounds good|that works|perfect)\b',
            r'\b(no|nope|not really|maybe not|different|something else)\b',
            r'\b(tell me more|more info|details|what else|continue)\b',
            r'\b(the first one|first option|second one|third option)\b',
            r'\b(call them|contact|phone|order|book)\b'
        ]
        
        # Check if user is responding to previous recommendations
        for pattern in continuation_patterns:
            if re.search(pattern, message_lower):
                return self.handle_contextual_response(message_lower, context)
        
        # Regular intent analysis (existing logic)
        return self.analyze_intent(message)
    
    def handle_contextual_response(self, message_lower: str, context: Dict) -> Dict:
        """Handle responses that reference previous conversation context"""
        last_intent = context.get("last_intent", {})
        recommendations = context.get("recommendations", [])
        
        # Positive responses
        if re.search(r'\b(yes|yeah|yep|sure|ok|okay|sounds good|that works|perfect)\b', message_lower):
            if recommendations:
                return {
                    "type": "booking_confirmation",
                    "cuisine": last_intent.get("cuisine"),
                    "location": context.get("location"),
                    "selected_caterer": recommendations[0] if recommendations else None
                }
            else:
                return {"type": "general_affirmation", "context": "positive"}
        
        # Negative responses
        elif re.search(r'\b(no|nope|not really|maybe not|different|something else)\b', message_lower):
            return {"type": "search_refinement", "context": "negative"}
        
        # More information requests
        elif re.search(r'\b(tell me more|more info|details|what else|continue)\b', message_lower):
            return {"type": "detail_request", "target": recommendations[0] if recommendations else None}
        
        # Specific selection
        elif re.search(r'\b(first one|first option)\b', message_lower) and recommendations:
            return {
                "type": "specific_selection",
                "selected_caterer": recommendations[0],
                "selection_index": 0
            }
        elif re.search(r'\b(second one|second option)\b', message_lower) and len(recommendations) > 1:
            return {
                "type": "specific_selection",
                "selected_caterer": recommendations[1],
                "selection_index": 1
            }
        elif re.search(r'\b(third one|third option)\b', message_lower) and len(recommendations) > 2:
            return {
                "type": "specific_selection",
                "selected_caterer": recommendations[2],
                "selection_index": 2
            }
        
        # Contact/booking requests
        elif re.search(r'\b(call them|contact|phone|order|book)\b', message_lower):
            return {
                "type": "contact_request",
                "selected_caterer": recommendations[0] if recommendations else None
            }
        
        # Default to general inquiry if no clear context match
        return {"type": "general_inquiry"}
    
    def generate_contextual_response(self, call_id: str, intent: Dict, original_message: str) -> str:
        """Generate response that considers conversation history and context"""
        context = self.conversation_context[call_id]
        dialogue_count = len([msg for msg in context["dialogue_history"] if msg["speaker"] == "user"])
        
        # Handle different intent types with context awareness
        if intent["type"] == "booking_confirmation":
            return self.handle_booking_confirmation(call_id, intent)
        elif intent["type"] == "search_refinement":
            return self.handle_search_refinement(call_id)
        elif intent["type"] == "detail_request":
            return self.handle_detail_request(call_id, intent)
        elif intent["type"] == "specific_selection":
            return self.handle_specific_selection(call_id, intent)
        elif intent["type"] == "contact_request":
            return self.handle_contact_request(call_id, intent)
        elif intent["type"] == "general_affirmation":
            return self.handle_general_affirmation(call_id)
        elif intent["type"] == "cuisine_preference":
            return self.handle_cuisine_inquiry_contextual(call_id, intent["cuisine"])
        elif intent["type"] == "location_inquiry":
            return self.handle_location_inquiry_contextual(call_id, intent["location"])
        elif intent["type"] == "menu_inquiry":
            return self.handle_menu_inquiry_contextual(call_id, intent["menu_item"])
        elif intent["type"] == "booking_inquiry":
            return self.handle_booking_inquiry_contextual(call_id, intent)
        elif intent["type"] == "general_inquiry":
            if dialogue_count == 1:
                return self.handle_first_interaction(call_id)
            else:
                return self.handle_general_inquiry_contextual(call_id)
        else:
            return self.handle_unclear_intent(call_id, original_message)
    
    def handle_booking_confirmation(self, call_id: str, intent: Dict) -> str:
        """Handle when user confirms they want to book a specific caterer"""
        context = self.conversation_context[call_id]
        selected = intent.get("selected_caterer")
        
        if selected:
            context["pending_actions"].append("booking_confirmed")
            return f"Excellent choice! I'll help you place an order with {selected['name']}. You can reach them directly at {selected['phone']}. They're rated {selected['rating']} stars and their minimum order is ${selected['min_order']}. Would you like me to provide any other information before you call them?"
        else:
            return "I'd be happy to help you place an order! Which caterer from our recommendations would you like to book?"
    
    def handle_search_refinement(self, call_id: str) -> str:
        """Handle when user wants different options"""
        context = self.conversation_context[call_id]
        last_intent = context.get("last_intent", {})
        
        if last_intent.get("type") == "cuisine_preference":
            return "No problem! What other type of cuisine would you prefer? We have Italian, Mexican, Chinese, Mediterranean, and American options available."
        elif last_intent.get("type") == "location_inquiry":
            return "I understand. Would you like to try a different location, or would you prefer to see caterers that can deliver to a wider area?"
        else:
            return "I'd be happy to find different options for you. Could you tell me more specifically what you're looking for?"
    
    def handle_detail_request(self, call_id: str, intent: Dict) -> str:
        """Handle requests for more details about recommendations"""
        context = self.conversation_context[call_id]
        target = intent.get("target")
        recommendations = context.get("recommendations", [])
        
        if target and recommendations:
            service = target
            details = f"Here are more details about {service['name']}:\n\n"
            details += f"• Cuisine: {service['cuisine']}\n"
            details += f"• Location: {service['location']}\n"
            details += f"• Rating: {service['rating']} stars\n"
            details += f"• Price Range: {service['price_range']}\n"
            details += f"• Minimum Order: ${service['min_order']}\n"
            details += f"• Specialties: {', '.join(service['specialties'])}\n"
            details += f"• Phone: {service['phone']}\n\n"
            details += f"Description: {service['description']}\n\n"
            details += "Would you like to place an order with them, or would you like information about other caterers?"
            return details
        elif recommendations:
            return self.provide_detailed_recommendations(recommendations[:3])
        else:
            return "I don't have specific recommendations to detail right now. What type of catering are you looking for?"
    
    def handle_specific_selection(self, call_id: str, intent: Dict) -> str:
        """Handle when user selects a specific option by number/position"""
        selected = intent.get("selected_caterer")
        index = intent.get("selection_index", 0)
        
        if selected:
            context = self.conversation_context[call_id]
            context["preferences"]["selected_caterer"] = selected
            
            return f"Great choice! You've selected {selected['name']}. They specialize in {selected['cuisine']} cuisine and are rated {selected['rating']} stars. Their minimum order is ${selected['min_order']} and they're located in {selected['location']}. Would you like their contact information to place an order, or do you need more details?"
        else:
            return "I'm not sure which option you're referring to. Could you tell me the name of the caterer you're interested in?"
    
    def handle_contact_request(self, call_id: str, intent: Dict) -> str:
        """Handle requests to contact or book a caterer"""
        selected = intent.get("selected_caterer")
        context = self.conversation_context[call_id]
        recommendations = context.get("recommendations", [])
        
        if selected:
            context["pending_actions"].append("contact_requested")
            return f"Perfect! Here's how to contact {selected['name']}:\n\nPhone: {selected['phone']}\nLocation: {selected['location']}\nMinimum Order: ${selected['min_order']}\n\nWhen you call, mention you found them through EZCaters. Is there anything else I can help you with for your catering needs?"
        elif recommendations:
            first_option = recommendations[0]
            return f"I'll give you the contact information for {first_option['name']}, our top recommendation:\n\nPhone: {first_option['phone']}\nLocation: {first_option['location']}\nMinimum Order: ${first_option['min_order']}\n\nWould you like contact information for any of the other caterers I mentioned?"
        else:
            return "I'd be happy to help you contact a caterer! First, let me find some options for you. What type of cuisine or location are you looking for?"
    
    def handle_general_affirmation(self, call_id: str) -> str:
        """Handle general positive responses"""
        context = self.conversation_context[call_id]
        recommendations = context.get("recommendations", [])
        
        if recommendations:
            return f"Wonderful! Would you like me to provide contact information for {recommendations[0]['name']}, or would you like to hear about more options first?"
        else:
            return "Great! How can I help you find the perfect catering service today?"

    def update_conversation_stage(self, context: Dict, intent: Dict) -> None:
        """Update the conversation stage based on the current intent"""
        if intent["type"] in ["cuisine_preference", "location_inquiry", "menu_inquiry"]:
            context["stage"] = "searching"
        elif intent["type"] in ["booking_confirmation", "contact_request"]:
            context["stage"] = "booking"
        elif intent["type"] == "specific_selection":
            context["stage"] = "selected"
        elif intent["type"] == "search_refinement":
            context["stage"] = "refining"
    
    def provide_detailed_recommendations(self, services: List[Dict]) -> str:
        """Provide detailed information about multiple services"""
        response = "Here are the details for our top recommendations:\n\n"
        
        for i, service in enumerate(services, 1):
            response += f"{i}. **{service['name']}** ({service['cuisine']})\n"
            response += f"   • Rating: {service['rating']} stars\n"
            response += f"   • Location: {service['location']}\n"
            response += f"   • Price: {service['price_range']}\n"
            response += f"   • Min Order: ${service['min_order']}\n"
            response += f"   • Phone: {service['phone']}\n\n"
        
        response += "Which one interests you most, or would you like me to help you narrow down the options?"
        return response

    def analyze_intent(self, message: str) -> Dict:
        """Analyze customer intent using rule-based pattern matching"""
        message_lower = message.lower().strip()
        
        # Define cuisine keywords
        cuisine_keywords = {
            'italian': ['italian', 'pasta', 'pizza', 'spaghetti', 'lasagna', 'marinara'],
            'mexican': ['mexican', 'tacos', 'burritos', 'nachos', 'fajitas', 'quesadilla', 'salsa'],
            'chinese': ['chinese', 'lo mein', 'fried rice', 'dumplings', 'sweet and sour', 'chow mein'],
            'mediterranean': ['mediterranean', 'hummus', 'falafel', 'kebabs', 'pita', 'greek'],
            'american': ['american', 'bbq', 'barbecue', 'fried chicken', 'mac and cheese', 'burger', 'sandwich']
        }
        
        # Define location keywords/patterns
        location_patterns = [
            r'\b(in|near|around|from)\s+([a-zA-Z\s]+(?:,\s*[A-Z]{2})?)\b',
            r'\b([A-Z][a-zA-Z\s]+(?:,\s*[A-Z]{2})?)\s+area\b',
            r'\b(boston|cambridge|somerville|newton|brookline)\b'
        ]
        
        # Define menu item keywords
        menu_items = ['pizza', 'pasta', 'tacos', 'burritos', 'sandwiches', 'salads', 'chicken', 'rice', 'noodles']
        
        # Define booking keywords
        booking_keywords = ['order', 'book', 'place an order', 'want to order', 'schedule', 'reserve', 'buy']
        
        # Check for specific menu items first (before cuisine)
        found_menu_items = [item for item in menu_items if item in message_lower]
        if found_menu_items:
            return {
                "type": "menu_inquiry",
                "cuisine": None,
                "location": None,
                "menu_item": found_menu_items[0]
            }
        
        # Check for cuisine preference
        for cuisine, keywords in cuisine_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return {
                    "type": "cuisine_preference",
                    "cuisine": cuisine,
                    "location": None,
                    "menu_item": None
                }
        
        # Check for location inquiry
        for pattern in location_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                # Extract location based on which group matched
                if len(match.groups()) >= 2 and match.group(2):
                    location = match.group(2)
                else:
                    location = match.group(1)
                return {
                    "type": "location_inquiry",
                    "cuisine": None,
                    "location": location.strip(),
                    "menu_item": None
                }
        
        # Check for booking intent
        if any(keyword in message_lower for keyword in booking_keywords):
            return {
                "type": "booking_inquiry",
                "cuisine": None,
                "location": None,
                "menu_item": None
            }
        
        # Default to general inquiry
        return {
            "type": "general_inquiry",
            "cuisine": None,
            "location": None,
            "menu_item": None
        }
    
    def handle_first_interaction(self, call_id: str) -> str:
        """Handle the very first interaction with a user"""
        return """Welcome to EZCaters! I'm here to help you find the perfect catering service for your needs. 
        I can help you search by:
        - Cuisine type (Italian, Mexican, Chinese, etc.)
        - Your location and delivery area
        - Specific menu items you're craving
        - Budget and group size
        
        What would you like to know about our catering partners?"""
    
    def handle_cuisine_inquiry_contextual(self, call_id: str, cuisine: str) -> str:
        """Handle cuisine-specific inquiries with conversation context"""
        context = self.conversation_context[call_id]
        context["preferences"]["cuisine"] = cuisine
        
        services = catering_service.search_by_cuisine(cuisine)
        
        if not services:
            return f"I don't currently have {cuisine} caterers in our network, but I can suggest some similar options. Would you like to hear about other cuisines we offer?"
        
        context["recommendations"] = services
        
        # Check if this is a follow-up to previous conversation
        dialogue_count = len([msg for msg in context["dialogue_history"] if msg["speaker"] == "user"])
        
        if len(services) == 1:
            service = services[0]
            response = f"Great choice! I found {service['name']} that specializes in {cuisine} cuisine. They're rated {service['rating']} stars and are located in {service['location']}. They specialize in {', '.join(service['specialties'])}."
            if dialogue_count > 1:
                response += " This seems perfect based on what you've been looking for! Would you like their contact information?"
            else:
                response += " Would you like their contact information or should I help you find more options?"
            return response
        else:
            names = [s['name'] for s in services[:3]]  # Top 3
            response = f"Excellent! I found {len(services)} {cuisine} caterers for you. The top options are {', '.join(names)}."
            if dialogue_count > 1:
                response += " These should work well with your other preferences. Which one interests you most?"
            else:
                response += " Would you like me to tell you more about any of these, or do you have a specific location in mind?"
            return response
    
    def handle_location_inquiry_contextual(self, call_id: str, location: str) -> str:
        """Handle location-based inquiries with conversation context"""
        context = self.conversation_context[call_id]
        context["location"] = location
        
        services = catering_service.search_by_location(location)
        
        if not services:
            return f"I couldn't find any caterers currently delivering to {location}. Could you try a nearby city or let me know if you'd like to expand the search radius?"
        
        context["recommendations"] = services
        
        # Consider previous preferences
        cuisine_pref = context["preferences"].get("cuisine")
        dialogue_count = len([msg for msg in context["dialogue_history"] if msg["speaker"] == "user"])
        
        response = f"Perfect! I found {len(services)} caterers serving the {location} area. "
        
        if cuisine_pref:
            # Filter by previous cuisine preference
            filtered = [s for s in services if cuisine_pref.lower() in s['cuisine'].lower()]
            if filtered:
                response += f"I see {len(filtered)} {cuisine_pref} caterers that match your previous preference: "
                response += ", ".join([f"{s['name']}" for s in filtered[:2]])
                response += ". "
                context["recommendations"] = filtered + [s for s in services if s not in filtered]
        
        if len(services) >= 3:
            top_services = services[:3]
            descriptions = []
            for service in top_services:
                descriptions.append(f"{service['name']} ({service['cuisine']}, {service['distance']} miles away)")
            
            response += f"The closest options are: {', '.join(descriptions)}. "
        else:
            for service in services:
                response += f"{service['name']} offers {service['cuisine']} cuisine and is {service['distance']} miles away. "
        
        response += "Would you like to hear more details about any of these caterers?"
        
        return response
    
    def handle_menu_inquiry_contextual(self, call_id: str, menu_item: str) -> str:
        """Handle menu item specific inquiries with conversation context"""
        context = self.conversation_context[call_id]
        
        services = catering_service.search_by_menu_item(menu_item)
        
        if not services:
            return f"I don't see any caterers currently offering {menu_item}, but let me suggest some similar options. What type of cuisine were you thinking?"
        
        # Filter by location if previously specified
        location = context.get("location")
        if location:
            location_filtered = []
            for service in services:
                try:
                    service_coords = service['coordinates']
                    user_location = geolocator.geocode(location)
                    if user_location:
                        user_coords = (user_location.latitude, user_location.longitude)
                        distance = geodesic(user_coords, service_coords).miles
                        if distance <= MAX_SEARCH_RADIUS:
                            service_copy = service.copy()
                            service_copy['distance'] = round(distance, 1)
                            location_filtered.append(service_copy)
                except:
                    pass
            
            if location_filtered:
                services = sorted(location_filtered, key=lambda x: x.get('distance', 999))
                context["recommendations"] = services
                
                response = f"Great news! I found {len(services)} caterers near {location} that offer {menu_item}. "
                if len(services) == 1:
                    service = services[0]
                    response += f"{service['name']} specializes in {service['cuisine']} cuisine and is {service['distance']} miles away. Would you like their contact information?"
                else:
                    names = [f"{s['name']} ({s['distance']} miles)" for s in services[:3]]
                    response += f"Your closest options are {', '.join(names)}. Which one interests you most?"
                return response
        
        context["recommendations"] = services
        
        if len(services) == 1:
            service = services[0]
            return f"Great news! {service['name']} offers {menu_item}. They specialize in {service['cuisine']} cuisine and also offer {', '.join([s for s in service['specialties'] if s != menu_item.lower()])}. Would you like their contact information?"
        else:
            names = [s['name'] for s in services[:3]]
            return f"I found {len(services)} caterers that offer {menu_item}! Your top options are {', '.join(names)}. Would you like me to tell you more about any of these?"
    
    def handle_booking_inquiry_contextual(self, call_id: str, intent: Dict) -> str:
        """Handle booking and ordering inquiries with conversation context"""
        context = self.conversation_context[call_id]
        recommendations = context.get("recommendations", [])
        
        if not recommendations:
            return "I'd be happy to help you place an order! First, let me know what type of cuisine you're interested in or your delivery location."
        
        selected_caterer = context["preferences"].get("selected_caterer")
        
        if selected_caterer:
            return f"Perfect! I'll help you place an order with {selected_caterer['name']}. You can call them at {selected_caterer['phone']}. Their minimum order is ${selected_caterer['min_order']}. Would you like me to provide any other details before you call?"
        elif len(recommendations) == 1:
            service = recommendations[0]
            return f"Excellent! To place an order with {service['name']}, you can call them directly at {service['phone']} or I can connect you. Their minimum order is ${service['min_order']} and they're rated {service['rating']} stars. Would you like me to connect you now?"
        else:
            return f"I have {len(recommendations)} great options for you. Which caterer would you like to place an order with? You can say 'the first one' or mention the caterer's name specifically."
    
    def handle_general_inquiry_contextual(self, call_id: str) -> str:
        """Handle general inquiries with conversation context"""
        context = self.conversation_context[call_id]
        recommendations = context.get("recommendations", [])
        preferences = context.get("preferences", {})
        
        if recommendations:
            return "I can help you with more information about the caterers I found, help you make a selection, or search for different options. What would you like to do next?"
        elif preferences:
            return "Based on our conversation, I can search for more options or help you refine your preferences. What specific aspect of catering would you like to explore?"
        else:
            return "I'm here to help you find the perfect catering service. You can ask me about cuisine types, locations, specific menu items, or pricing. What interests you most?"
    
    def handle_unclear_intent(self, call_id: str, original_message: str) -> str:
        """Handle cases where the intent is unclear"""
        context = self.conversation_context[call_id]
        recommendations = context.get("recommendations", [])
        
        if recommendations:
            return f"I'm not sure I understood that completely. Were you asking about one of the caterers I mentioned ({', '.join([r['name'] for r in recommendations[:2]])}), or would you like me to search for something else?"
        else:
            return "I want to make sure I understand what you're looking for. Could you tell me what type of cuisine you'd like, your location, or any specific menu items you have in mind?"

# Initialize voice assistant
voice_assistant = VoiceAssistant()

# Routes
@app.route('/')
def index():
    """Home page with basic information"""
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint for Retell AI"""
    try:
        data = request.get_json()
        
        # Extract relevant information from Retell webhook
        call_id = data.get('call_id')
        event_type = data.get('event_type')
        
        if event_type == 'call_started':
            return jsonify({"message": "Call started"})
        
        elif event_type == 'call_ended':
            # Clean up conversation context
            if call_id in voice_assistant.conversation_context:
                del voice_assistant.conversation_context[call_id]
            return jsonify({"message": "Call ended"})
        
        elif event_type == 'speech_recognition':
            # Process the customer's speech
            transcript = data.get('transcript', '')
            
            # Get response from voice assistant
            response = voice_assistant.process_inquiry(call_id, transcript)
            
            # Return response for Retell to speak
            return jsonify({
                "response": response,
                "end_call": False
            })
        
        return jsonify({"message": "Event processed"})
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/search', methods=['POST'])
def search():
    """API endpoint for searching catering services"""
    try:
        data = request.get_json()
        search_type = data.get('type')
        query = data.get('query')
        
        if search_type == 'cuisine':
            results = catering_service.search_by_cuisine(query)
        elif search_type == 'location':
            results = catering_service.search_by_location(query)
        elif search_type == 'menu':
            results = catering_service.search_by_menu_item(query)
        else:
            return jsonify({"error": "Invalid search type"}), 400
        
        return jsonify({"results": results})
        
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({"error": "Search failed"}), 500

@app.route('/services')
def list_services():
    """API endpoint to list all catering services"""
    return jsonify({"services": catering_service.services})

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug) 