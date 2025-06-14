#!/usr/bin/env python3

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RetellAIManager:
    """Manages Retell AI agents and phone calls for EZCaters"""
    
    def __init__(self):
        self.api_key = os.getenv('RETELL_API_KEY')
        self.base_url = "https://api.retellai.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.webhook_url = os.getenv('WEBHOOK_URL', 'https://your-domain.com/webhook')
        
    def create_retell_llm(self):
        """Create a Retell LLM for handling catering inquiries"""
        
        llm_config = {
            "general_prompt": """You are EZCaters AI voice assistant, helping customers find the perfect catering services for their events. You are friendly, professional, and knowledgeable about food and catering.

Your main goals:
1. Understand customer needs (cuisine type, location, budget, event size)
2. Search and recommend appropriate catering services
3. Provide contact information and help connect customers with caterers
4. Handle common questions about catering services

Guidelines:
- Be conversational and helpful
- Ask clarifying questions to better understand needs
- Provide specific recommendations with details
- Offer to connect customers directly with caterers
- Handle objections and provide alternatives
- Keep responses concise but informative

Available cuisine types: Italian, Mexican, Chinese, Mediterranean, American, Indian
Service areas: Boston, Cambridge, Somerville, Newton, Brookline (Massachusetts)

Always be enthusiastic about helping customers find great food for their events!""",
            
            "general_tools": [
                {
                    "type": "end_call",
                    "name": "end_call",
                    "description": "End the call when customer is satisfied or requests to end"
                },
                {
                    "type": "transfer_call", 
                    "name": "transfer_to_caterer",
                    "description": "Transfer call directly to a specific caterer when customer wants to book"
                }
            ],
            
            "states": [
                {
                    "name": "greeting",
                    "state_prompt": "Greet the customer warmly and ask how you can help them with their catering needs today. Be enthusiastic and professional.",
                    "edges": [
                        {
                            "destination_state_name": "cuisine_inquiry",
                            "description": "Customer mentions specific cuisine type or food preferences"
                        },
                        {
                            "destination_state_name": "location_inquiry", 
                            "description": "Customer mentions their location or delivery area"
                        },
                        {
                            "destination_state_name": "general_help",
                            "description": "Customer asks general questions about the service"
                        }
                    ]
                },
                {
                    "name": "cuisine_inquiry",
                    "state_prompt": "Help customer explore cuisine options. Ask about their preferred cuisine type, dietary restrictions, and event details. Provide recommendations based on their preferences.",
                    "edges": [
                        {
                            "destination_state_name": "location_inquiry",
                            "description": "Customer mentions location or asks about delivery areas"
                        },
                        {
                            "destination_state_name": "caterer_recommendation",
                            "description": "Ready to provide specific caterer recommendations"
                        }
                    ]
                },
                {
                    "name": "location_inquiry", 
                    "state_prompt": "Ask about the customer's location and delivery preferences. Help them understand service areas and find caterers in their area.",
                    "edges": [
                        {
                            "destination_state_name": "caterer_recommendation",
                            "description": "Ready to provide specific caterer recommendations based on location"
                        },
                        {
                            "destination_state_name": "cuisine_inquiry",
                            "description": "Customer wants to discuss cuisine preferences"
                        }
                    ]
                },
                {
                    "name": "caterer_recommendation",
                    "state_prompt": "Provide specific caterer recommendations based on customer preferences. Include details like ratings, specialties, pricing, and contact information. Offer to connect them directly.",
                    "edges": [
                        {
                            "destination_state_name": "booking_assistance",
                            "description": "Customer wants to book with a specific caterer"
                        },
                        {
                            "destination_state_name": "more_options",
                            "description": "Customer wants to see more options or different recommendations"
                        }
                    ]
                },
                {
                    "name": "booking_assistance",
                    "state_prompt": "Help customer with the booking process. Provide caterer contact information and offer to transfer the call directly to the caterer if needed.",
                    "tools": ["end_call", "transfer_to_caterer"]
                },
                {
                    "name": "more_options",
                    "state_prompt": "Provide additional caterer options or modify search criteria based on customer feedback. Be flexible and helpful.",
                    "edges": [
                        {
                            "destination_state_name": "caterer_recommendation",
                            "description": "Provide new recommendations"
                        },
                        {
                            "destination_state_name": "booking_assistance", 
                            "description": "Customer selects a caterer to book with"
                        }
                    ]
                },
                {
                    "name": "general_help",
                    "state_prompt": "Answer general questions about EZCaters services, how the platform works, pricing, and availability. Educate customers about the catering marketplace.",
                    "edges": [
                        {
                            "destination_state_name": "cuisine_inquiry",
                            "description": "Customer ready to discuss specific cuisine needs"
                        },
                        {
                            "destination_state_name": "location_inquiry",
                            "description": "Customer ready to discuss location and delivery"
                        }
                    ]
                }
            ],
            
            "beginning_message": "Hi there! Welcome to EZCaters, your AI catering assistant. I'm here to help you find the perfect catering service for your event. What type of food or catering are you looking for today?"
        }
        
        url = f"{self.base_url}/create-retell-llm"
        response = requests.post(url, headers=self.headers, json=llm_config)
        
        if response.status_code == 201:
            llm_data = response.json()
            print(f"✅ Created Retell LLM: {llm_data['llm_id']}")
            return llm_data['llm_id']
        else:
            print(f"❌ Failed to create Retell LLM: {response.text}")
            return None
    
    def create_voice_agent(self, llm_id):
        """Create a voice agent using the Retell LLM"""
        
        agent_config = {
            "agent_name": "EZCaters Voice Assistant",
            "voice_id": "11labs-Adrian",  # Professional male voice
            "voice_model": "eleven_turbo_v2",
            "voice_temperature": 0.8,
            "voice_speed": 1.0,
            "responsiveness": 1.0,
            "interruption_sensitivity": 1.0,
            "enable_backchannel": True,
            "backchannel_frequency": 0.8,
            "backchannel_words": ["yeah", "uh-huh", "I see", "right"],
            "language": "en-US",
            "webhook_url": self.webhook_url,
            "response_engine": {
                "type": "retell-llm",
                "llm_id": llm_id
            },
            "enable_voicemail_detection": True,
            "voicemail_message": "Hi! You've reached EZCaters voice assistant. We help connect you with amazing catering services. Please call back or visit our website to get started finding the perfect caterer for your event!",
            "max_call_duration_ms": 1800000,  # 30 minutes
            "end_call_after_silence_ms": 30000,  # 30 seconds
            "boosted_keywords": [
                "catering", "caterer", "food", "event", "party", "meeting",
                "Italian", "Mexican", "Chinese", "Mediterranean", "American",
                "Boston", "Cambridge", "Somerville", "delivery", "pickup",
                "budget", "price", "book", "order", "recommend"
            ],
            "pronunciation_dictionary": [
                {
                    "word": "EZCaters",
                    "alphabet": "ipa", 
                    "phoneme": "ˈiːzi ˈkeɪtərz"
                }
            ]
        }
        
        url = f"{self.base_url}/create-agent"
        response = requests.post(url, headers=self.headers, json=agent_config)
        
        if response.status_code == 201:
            agent_data = response.json()
            print(f"✅ Created Voice Agent: {agent_data['agent_id']}")
            return agent_data['agent_id']
        else:
            print(f"❌ Failed to create Voice Agent: {response.text}")
            return None
    
    def create_phone_call(self, agent_id, customer_phone, from_phone=None):
        """Create an outbound phone call to a customer"""
        
        call_config = {
            "from_number": from_phone or os.getenv('PHONE_NUMBER'),
            "to_number": customer_phone,
            "agent_id": agent_id,
            "metadata": {
                "customer_type": "potential_customer",
                "call_purpose": "catering_assistance"
            }
        }
        
        url = f"{self.base_url}/create-phone-call"
        response = requests.post(url, headers=self.headers, json=call_config)
        
        if response.status_code == 201:
            call_data = response.json()
            print(f"✅ Created Phone Call: {call_data['call_id']}")
            return call_data['call_id']
        else:
            print(f"❌ Failed to create phone call: {response.text}")
            return None
    
    def get_agent_info(self, agent_id):
        """Get information about a specific agent"""
        
        url = f"{self.base_url}/get-agent/{agent_id}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get agent info: {response.text}")
            return None
    
    def list_agents(self):
        """List all agents"""
        
        url = f"{self.base_url}/list-agents"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to list agents: {response.text}")
            return None

def setup_ezcaters_agent():
    """Set up the complete EZCaters voice agent"""
    
    if not os.getenv('RETELL_API_KEY'):
        print("❌ RETELL_API_KEY not found in environment variables")
        print("Please set your Retell AI API key in the .env file")
        return None
    
    manager = RetellAIManager()
    
    print("🚀 Setting up EZCaters Voice Agent with Retell AI...")
    print()
    
    # Step 1: Create Retell LLM
    print("1. Creating Retell LLM...")
    llm_id = manager.create_retell_llm()
    if not llm_id:
        return None
    
    # Step 2: Create Voice Agent
    print("2. Creating Voice Agent...")
    agent_id = manager.create_voice_agent(llm_id)
    if not agent_id:
        return None
    
    # Save configuration
    config = {
        "llm_id": llm_id,
        "agent_id": agent_id,
        "webhook_url": manager.webhook_url
    }
    
    with open('retell_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print()
    print("✅ EZCaters Voice Agent setup complete!")
    print(f"   LLM ID: {llm_id}")
    print(f"   Agent ID: {agent_id}")
    print(f"   Config saved to: retell_config.json")
    print()
    print("📞 To make test calls, use the agent_id in your application")
    print("🌐 Make sure your webhook URL is accessible from the internet")
    
    return config

def make_test_call(customer_phone):
    """Make a test call to a customer"""
    
    try:
        with open('retell_config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ No configuration found. Please run setup_ezcaters_agent() first")
        return None
    
    manager = RetellAIManager()
    call_id = manager.create_phone_call(config['agent_id'], customer_phone)
    
    if call_id:
        print(f"📞 Test call initiated to {customer_phone}")
        print(f"   Call ID: {call_id}")
        return call_id
    
    return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "setup":
            setup_ezcaters_agent()
        elif sys.argv[1] == "test" and len(sys.argv) > 2:
            make_test_call(sys.argv[2])
        else:
            print("Usage:")
            print("  python retell_agent.py setup              # Set up the voice agent")
            print("  python retell_agent.py test <phone>       # Make a test call")
    else:
        print("EZCaters Retell AI Manager")
        print()
        print("Available commands:")
        print("  setup    - Set up the voice agent")
        print("  test     - Make a test call")
        print()
        print("Usage:")
        print("  python retell_agent.py setup")
        print("  python retell_agent.py test +1234567890") 