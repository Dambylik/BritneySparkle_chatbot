import random
import requests
import os
import sys
import logging
from dotenv import load_dotenv
import json
from flask import Flask, render_template, request, jsonify

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
# Ensure Flask doesn't capture output
app.logger.handlers = []
app.logger.propagate = True

class BritneyLyricsRetriever:
    """Class responsible for retrieving Britney Spears lyrics using external APIs"""
    
    def __init__(self):
        # Initialize with API key from environment variables
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not self.gemini_api_key:
            self.gemini_api_key = "Add your key here"  # Fallback key
        self.musixmatch_api_key = os.getenv('MUSIXMATCH_API_KEY')
        
        # Default responses in case the API fails completely
        self.emergency_responses = [
            "Oops, I did it again!",
            "Hit me baby one more time!"
        ]
    
    def get_lyric_from_gemini(self, user_input):
        """Attempt to get a contextually relevant Britney Spears lyric using Gemini API"""
        if not self.gemini_api_key:
            return None
            
        try:
            # Gemini API endpoint for text generation (using v1 instead of v1beta)
            gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
            
            # Add the API key as a query parameter
            url_with_key = f"{gemini_url}?key={self.gemini_api_key}"
            
            # Log the API version we're using
            logger.info("Using Gemini API v1 endpoint")
            
            # Prepare the request payload
            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"Please provide a single short line of lyrics from a Britney Spears song that would be relevant to this message: '{user_input}'. Only respond with the lyric, nothing else."
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topP": 0.8,
                    "maxOutputTokens": 60
                }
            }
            # Detailed debugging of the API request
            logger.info("="*50)
            logger.info("GEMINI API DEBUG - REQUEST")
            logger.info(f"Payload: {json.dumps(payload, indent=2)}")
            logger.info(f"API endpoint: {url_with_key[:60]}...")
            
            # Make the API call
            headers = {"Content-Type": "application/json"}
            logger.info("Sending request to Gemini API...")
            
            response = requests.post(url_with_key, json=payload, headers=headers)
            logger.info(f"Gemini API response status code: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                logger.info("="*50)
                logger.info("GEMINI API DEBUG - SUCCESSFUL RESPONSE")
                logger.info(f"Full response: {json.dumps(response_data, indent=2)}")
                
                try:
                    # Extract the generated text from the response
                    candidates = response_data.get("candidates", [])
                    logger.info(f"Found {len(candidates)} candidates in response")
                    
                    if candidates:
                        content = candidates[0].get("content", {})
                        parts = content.get("parts", [])
                        logger.info(f"Found {len(parts)} parts in first candidate")
                        
                        if parts:
                            generated_text = parts[0].get("text", "")
                            logger.info(f"Generated lyric: '{generated_text}'")
                            
                            # If we got a response, return it
                            if generated_text and len(generated_text.strip()) > 0:
                                return generated_text.strip()
                        else:
                            logger.warning("No parts found in content")
                    else:
                        logger.warning("No candidates found in response")
                except (IndexError, KeyError) as e:
                    logger.error(f"Error extracting text from response: {e}")
                    logger.error(f"Response structure: {response_data}")
            
            return None
        except Exception as e:
            print(f"Error with Gemini API: {e}")
            return None
    
    def get_lyric_from_musixmatch(self, user_input):
        """Attempt to get a Britney Spears lyric from Musixmatch API"""
        if not self.musixmatch_api_key:
            return None
            
        try:
            # Search for Britney Spears lyrics related to user input
            search_url = "https://api.musixmatch.com/ws/1.1/track.search"
            params = {
                "q_artist": "Britney Spears",
                "q_lyrics": user_input,
                "apikey": self.musixmatch_api_key,
                "page_size": 5
            }
            
            response = requests.get(search_url, params=params)
            if response.status_code == 200:
                data = response.json()
                track_list = data.get("message", {}).get("body", {}).get("track_list", [])
                
                if track_list:
                    # Get a random track
                    track = random.choice(track_list)
                    track_id = track.get("track", {}).get("track_id")
                    
                    # Get the lyrics snippet
                    lyrics_url = "https://api.musixmatch.com/ws/1.1/track.snippet.get"
                    lyrics_params = {
                        "track_id": track_id,
                        "apikey": self.musixmatch_api_key
                    }
                    
                    lyrics_response = requests.get(lyrics_url, params=lyrics_params)
                    if lyrics_response.status_code == 200:
                        snippet = lyrics_response.json().get("message", {}).get("body", {}).get("snippet", {}).get("snippet_body")
                        if snippet:
                            return snippet
            
            return None
        except Exception:
            return None
    
    def get_emergency_britney_lyric(self):
        """Get a random Britney Spears lyric as emergency fallback using Gemini API"""
        if not self.gemini_api_key:
            return random.choice(self.emergency_responses)
            
        try:
            # Use Gemini API to generate a random Britney lyric (using v1 instead of v1beta)
            gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
            url_with_key = f"{gemini_url}?key={self.gemini_api_key}"
            logger.info("Using Gemini API v1 endpoint for emergency lyrics")
            
            # Request a random lyric without any context
            payload = {
                "contents": [{
                    "parts": [{
                        "text": "Generate one random famous Britney Spears lyric. Only respond with the lyric, nothing else."
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.9,
                    "maxOutputTokens": 50
                }
            }
            
            logger.info("Making emergency Gemini API request for random Britney lyric")
            headers = {"Content-Type": "application/json"}
            response = requests.post(url_with_key, json=payload, headers=headers)
            
            if response.status_code == 200:
                response_data = response.json()
                try:
                    return response_data.get("candidates", [])[0].get("content", {}).get("parts", [])[0].get("text", "")
                except (IndexError, KeyError):
                    pass
                    
            return random.choice(self.emergency_responses)
            
        except Exception as e:
            logger.error(f"Emergency lyric request failed: {e}")
            return random.choice(self.emergency_responses)

    def get_britney_lyric(self, user_input):
        """Get a Britney Spears lyric, always using API calls"""
        logger.info(f"Getting Britney lyric for input: '{user_input}'")
        
        # Try contextual Gemini API (main method)
        lyric = self.get_lyric_from_gemini(user_input)
        if lyric:
            logger.info(f"Returning contextual lyric: '{lyric}'")
            return lyric
            
        # Try Musixmatch API if available
        if self.musixmatch_api_key:
            lyric = self.get_lyric_from_musixmatch(user_input)
            if lyric:
                logger.info(f"Returning Musixmatch lyric: '{lyric}'")
                return lyric
            
        # If both contextual methods fail, get a random Britney lyric from Gemini
        logger.warning("Contextual methods failed, using emergency lyric generator")
        emergency_lyric = self.get_emergency_britney_lyric()
        logger.info(f"Returning emergency lyric: '{emergency_lyric}'")
        return emergency_lyric


class BritneySparkleAI:
    """BritneySparkle AI that formats Britney Spears lyrics with emojis"""
    
    def __init__(self):
        """Initialize BritneySparkle AI with emoji collection"""
        self.name = "BritneySparkle AI ✨🎤"
        self.emojis = ["✨", "💖", "💕", "⭐", "🎶", "💋", "😊", "👑", "💃", "🌟", "💎", "🎀", "🌈", "😘", "💅", "O:-)", "😉", "✌️", "💞", "🦋", "🔮", "💫", "👒", "👛", "💍"]

    def format_lyric(self, lyric, emoji_count=5):
        """Format a Britney Spears lyric with emojis
        
        This is the SOLE function of the BritneySparkle AI - to take a provided
        Britney Spears lyric and decorate it with emojis.
        """
        # Select random emojis, ensuring we have at least the minimum number requested
        selected_emojis = random.sample(self.emojis, min(emoji_count, len(self.emojis)))
        
        # Distribute emojis throughout the response for maximum sparkly effect
        formatted_response = ""
        
        # Add some emojis at the beginning
        prefix_emojis = random.sample(selected_emojis, min(3, len(selected_emojis)))
        formatted_response += " ".join(prefix_emojis) + " "
        
        # Add the actual lyric
        formatted_response += lyric
        
        # Add some emojis at the end
        suffix_emojis = random.sample(selected_emojis, min(3, len(selected_emojis)))
        formatted_response += " " + " ".join(suffix_emojis)
        
        return formatted_response

class SparkleBritneyBot:
    """Main chatbot class that integrates the lyrics retriever with the AI formatter"""
    
    def __init__(self):
        """Initialize SparkleBritneyBot with lyrics retriever and AI formatter"""
        # Create the lyrics retriever for backend logic
        self.lyrics_retriever = BritneyLyricsRetriever()
        
        # Create the AI formatter for presentation
        self.ai_formatter = BritneySparkleAI()
        
        # Use the AI's name for the overall bot
        self.name = self.ai_formatter.name
    
    def respond(self, user_input):
        """Process user input and generate a Britney Spears response
        
        Workflow:
        1. Backend: Use the lyrics retriever to find a relevant Britney lyric
        2. AI: Use the AI formatter to decorate the lyric with emojis
        3. Return the formatted response
        """
        # Backend logic: Get a relevant Britney Spears lyric based on user input
        britney_lyric = self.lyrics_retriever.get_britney_lyric(user_input)
        
        # AI formatting: Format the lyric with emojis (the SOLE function of BritneySparkle AI)
        formatted_response = self.ai_formatter.format_lyric(britney_lyric)
        
        return formatted_response


def setup_environment():
    """Setup the environment for the chatbot, including checking for API keys"""
    # Check for required environment variables
    gemini_api_key = "Add your key here"
    print
    musixmatch_api_key = os.getenv('MUSIXMATCH_API_KEY')
    
    # Display appropriate messages based on available API keys
    if not gemini_api_key:
        print("Warning: No Gemini API key found.")
        print("The chatbot will use a local collection of Britney Spears lyrics.")
        print("For better results, add a valid GEMINI_API_KEY to your .env file.")
        print()
    else:
        print("Using Gemini API for enhanced lyrics retrieval.")
    
    # Check if Musixmatch API key is missing or just set to the placeholder value
    if not musixmatch_api_key or musixmatch_api_key == "your_musixmatch_api_key_here":
        # Clear the API key if it's just the placeholder value
        os.environ['MUSIXMATCH_API_KEY'] = ""
        print("Musixmatch API will not be used (no valid API key provided).")
        print()


# Create a global bot instance
bot = None

@app.route('/')
def home():
    """Render the home page with the chat interface"""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Process chat messages and return responses"""
    global bot
    
    # Get the user message from the request
    user_input = request.json.get('message', '')
    
    # Get response from the bot
    response = bot.respond(user_input)
    
    # Return the response as JSON
    return jsonify({'response': response})

def init_app():
    """Initialize the application"""
    global bot
    
    # Setup the environment
    setup_environment()
    
    # Initialize the chatbot
    bot = SparkleBritneyBot()
    
    return app

def main():
    """Run the Flask application"""
    port = 5050  # Using port 5050 instead of the default 5000
    app = init_app()
    print(f"✨💖💕 Starting BritneySparkle AI Web Chat ✨💖💕")
    print(f"Open your browser and navigate to http://localhost:{port}")
    app.run(debug=True, port=port)


if __name__ == "__main__":
    main()
