from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import json
import sys
from datetime import datetime
import logging
import traceback

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Directory for temporary config files
if not os.path.exists('temp'):
    os.makedirs('temp')

# Check for the correct bot script file
BOT_SCRIPT = "linkedin_bot.py"  # Default name
if not os.path.exists(BOT_SCRIPT) and os.path.exists("linkedin_hr_bot.py"):
    BOT_SCRIPT = "linkedin_hr_bot.py"
    logger.info(f"Using alternative bot script: {BOT_SCRIPT}")

@app.route('/server-status', methods=['GET'])
def server_status():
    """
    Endpoint to check if the server is up and running
    """
    return jsonify({
        "status": "online",
        "botScript": BOT_SCRIPT,
        "version": "1.0.0"
    })

@app.route('/run-bot', methods=['POST'])
def run_bot():
    try:
        # Get data from request
        data = request.json
        
        # Validate required fields
        required_fields = ['email', 'password', 'keyword']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}", "message": f"Missing required field: {field}"}), 400
        
        # Create a temporary config file
        config = {
            "LINKEDIN_USERNAME": data.get('email'),
            "LINKEDIN_PASSWORD": data.get('password'),
            "SEARCH_KEYWORD": data.get('keyword'),
            "NUM_PAGES": int(data.get('numPages', 10)),
            "MAX_REQUESTS": int(data.get('maxRequests', 50)),
            "MESSAGE": data.get('message', "Hi {name}, I'm exploring opportunities and would love to connect with professionals in your field. Looking forward to learning from your insights!"),
            "HEADLESS": True if data.get('headless') is None else data.get('headless'),  # Run headless in production
            "DAILY_REQUEST_LIMIT": 80
        }
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        config_file = f"temp/config_{timestamp}.json"
        
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        logger.info(f"Created config file: {config_file}")
        
        # Check if bot script exists
        if not os.path.exists(BOT_SCRIPT):
            logger.error(f"Bot script {BOT_SCRIPT} not found!")
            return jsonify({
                "error": f"Bot script {BOT_SCRIPT} not found in the current directory", 
                "message": f"Bot script {BOT_SCRIPT} not found in the current directory"
            }), 500
        
        # Run the bot script with the config file
        logger.info(f"Executing bot script: {BOT_SCRIPT}")
        result = subprocess.run(
            [
                sys.executable,  # Use the current Python interpreter
                BOT_SCRIPT,
                "--config", config_file
            ],
            capture_output=True,
            text=True,
            timeout=300  # 5-minute timeout
        )
        
        # Log the output
        logger.info(f"Bot stdout: {result.stdout}")
        if result.stderr:
            logger.error(f"Bot stderr: {result.stderr}")
        
        # Parse the output to get the number of connections sent
        connections_sent = 0
        for line in result.stdout.split('\n'):
            if "Total connection requests sent:" in line:
                try:
                    connections_sent = int(line.split(':')[1].strip())
                except (IndexError, ValueError):
                    pass
        
        # Clean up the config file
        try:
            os.remove(config_file)
            logger.info(f"Removed config file: {config_file}")
        except Exception as e:
            logger.warning(f"Failed to remove config file: {e}")
        
        return jsonify({
            "success": True,
            "connectionsSent": connections_sent,
            "output": result.stdout,
            "errors": result.stderr if result.stderr else None
        })
        
    except subprocess.TimeoutExpired:
        logger.error("Bot process timed out after 5 minutes")
        return jsonify({
            "error": "Operation timed out after 5 minutes", 
            "message": "Bot operation timed out after 5 minutes. Please try with fewer pages or connection requests."
        }), 504
    except Exception as e:
        logger.exception("Error running bot")
        error_details = traceback.format_exc()
        return jsonify({
            "error": str(e), 
            "message": f"An error occurred: {str(e)}",
            "details": error_details
        }), 500

@app.route('/', methods=['GET'])
def index():
    """
    Serve the HTML interface
    """
    try:
        with open('interface.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "Interface file not found!", 404

@app.route('/interface.js', methods=['GET'])
def serve_js():
    """
    Serve the JavaScript interface file
    """
    try:
        with open('interface.js', 'r') as f:
            return f.read(), 200, {'Content-Type': 'application/javascript'}
    except FileNotFoundError:
        return "JavaScript file not found!", 404

if __name__ == '__main__':
    logger.info(f"Starting server with bot script: {BOT_SCRIPT}")
    app.run(host='0.0.0.0', port=5000, debug=False)