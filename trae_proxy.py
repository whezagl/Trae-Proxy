#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, Response, jsonify, stream_with_context
import requests
import json
import ssl
import argparse
import logging
import os
import sys
import yaml
from datetime import datetime

# Default configuration
TARGET_API_BASE_URL = "https://api.openai.com"
CUSTOM_MODEL_ID = "gpt-4"
TARGET_MODEL_ID = "gpt-4"
STREAM_MODE = None  # None: no change, 'true': force on, 'false': force off
DEBUG_MODE = False

# Certificate file paths
CERT_FILE = os.path.join("ca", "api.openai.com.crt")
KEY_FILE = os.path.join("ca", "api.openai.com.key")

# Multi-backend configuration
MULTI_BACKEND_CONFIG = None

# Initialize Flask application
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('trae_proxy')

@app.route('/', methods=['GET'])
def root():
    """Handle root path requests"""
    return jsonify({
        "message": "Welcome to the OpenAI API! Documentation is available at https://platform.openai.com/docs/api-reference"
    })

@app.route('/v1', methods=['GET'])
def v1_root():
    """Handle /v1 path requests"""
    return jsonify({
        "message": "OpenAI API v1 endpoint",
        "endpoints": {
            "chat/completions": "/v1/chat/completions"
        }
    })

@app.route('/v1/models', methods=['GET'])
def list_models():
    """List available models"""
    try:
        # Get model list from configuration
        models = []
        if MULTI_BACKEND_CONFIG:
            apis = MULTI_BACKEND_CONFIG.get('apis', [])
            for api in apis:
                if api.get('active', False):
                    models.append({
                        "id": api.get('custom_model_id', ''),
                        "object": "model",
                        "created": 1,
                        "owned_by": "trae-proxy"
                    })
        else:
            models.append({
                "id": CUSTOM_MODEL_ID,
                "object": "model",
                "created": 1,
                "owned_by": "trae-proxy"
            })

        return jsonify({
            "object": "list",
            "data": models
        })
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

def debug_log(message):
    """Debug logging"""
    if DEBUG_MODE:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with open("debug_request.log", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
        logger.debug(message)

def load_multi_backend_config():
    """Load multi-backend configuration"""
    global MULTI_BACKEND_CONFIG
    try:
        config_file = "config.yaml"
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                MULTI_BACKEND_CONFIG = config
                logger.info(f"Loaded multi-backend configuration, total {len(config.get('apis', []))} API configs")
                return True
        else:
            logger.warning("Configuration file does not exist, using single backend mode")
            return False
    except Exception as e:
        logger.error(f"Failed to load multi-backend configuration: {str(e)}")
        return False

def select_backend_by_model(requested_model):
    """Select backend API based on requested model"""
    if not MULTI_BACKEND_CONFIG:
        return None

    apis = MULTI_BACKEND_CONFIG.get('apis', [])

    # First try exact match by model ID
    for api in apis:
        if api.get('active', False) and api.get('custom_model_id') == requested_model:
            logger.info(f"Matched backend by model ID: {api['name']} -> {api['endpoint']}")
            return api

    # If no exact match, use first active API
    for api in apis:
        if api.get('active', False):
            logger.info(f"Using default active backend: {api['name']} -> {api['endpoint']}")
            return api

    # If none are active, use the first one
    if apis:
        logger.warning(f"No active API configuration, using first one: {apis[0]['name']}")
        return apis[0]

    return None

def generate_stream(response):
    """Generate streaming response"""
    for chunk in response.iter_content(chunk_size=None):
        yield chunk

def simulate_stream(response_json):
    """Simulate streaming response from non-streaming response"""
    # Extract content from complete response
    try:
        content = response_json["choices"][0]["message"]["content"]

        # Simulate streaming response format
        yield b'data: {"id":"chatcmpl-simulated","object":"chat.completion.chunk","created":1,"model":"' + CUSTOM_MODEL_ID.encode() + b'","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}\n\n'

        # Split content into multiple chunks
        for i in range(0, len(content), 4):
            chunk = content[i:i+4]
            yield f'data: {{"id":"chatcmpl-simulated","object":"chat.completion.chunk","created":1,"model":"{CUSTOM_MODEL_ID}","choices":[{{"index":0,"delta":{{"content":"{chunk}"}},"finish_reason":null}}]}}\n\n'.encode()

        # Send completion marker
        yield b'data: {"id":"chatcmpl-simulated","object":"chat.completion.chunk","created":1,"model":"' + CUSTOM_MODEL_ID.encode() + b'","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}\n\n'
        yield b'data: [DONE]\n\n'
    except Exception as e:
        logger.error(f"Failed to simulate streaming response: {e}")
        yield f'data: {{"error": "Failed to simulate streaming response: {str(e)}"}}\n\n'.encode()

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """Handle chat completion requests"""
    try:
        # Check Content-Type
        content_type = request.headers.get('Content-Type', '')
        if 'application/json' not in content_type:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        # Parse request JSON
        try:
            req_json = request.json
            if req_json is None:
                return jsonify({"error": "Invalid JSON request body"}), 400
        except Exception as e:
            return jsonify({"error": f"JSON parsing failed: {str(e)}"}), 400

        # Debug logging
        if DEBUG_MODE:
            debug_log(f"Request headers: {dict(request.headers)}")
            debug_log(f"Request body: {json.dumps(req_json, ensure_ascii=False)}")

        # Get requested model ID
        requested_model = req_json.get('model', '')

        # Select backend API
        if MULTI_BACKEND_CONFIG:
            # Multi-backend mode: select backend based on model
            selected_backend = select_backend_by_model(requested_model)
            if selected_backend:
                target_api_url = selected_backend.get('endpoint', '').strip()
                target_model_id = selected_backend.get('target_model_id', '').strip()
                custom_model_id = selected_backend.get('custom_model_id', '').strip()
                stream_mode = selected_backend.get('stream_mode')

                logger.info(f"Selected backend: {selected_backend['name']} -> {target_api_url}")

                # Modify model ID
                if 'model' in req_json:
                    original_model = req_json['model']
                    req_json['model'] = target_model_id
                    debug_log(f"Model ID changed from {original_model} to {target_model_id}")
                else:
                    req_json['model'] = target_model_id
                    debug_log(f"Added model ID: {target_model_id}")

                # Handle stream mode
                if stream_mode is not None:
                    original_stream = req_json.get('stream', False)
                    req_json['stream'] = stream_mode == 'true'
                    debug_log(f"Stream mode changed from {original_stream} to {req_json['stream']}")
                elif STREAM_MODE is not None:
                    original_stream = req_json.get('stream', False)
                    req_json['stream'] = STREAM_MODE == 'true'
                    debug_log(f"Stream mode changed from {original_stream} to {req_json['stream']}")
            else:
                # Fallback to single backend mode
                target_api_url = TARGET_API_BASE_URL
                target_model_id = TARGET_MODEL_ID
                custom_model_id = CUSTOM_MODEL_ID
                stream_mode = STREAM_MODE

                logger.warning("Multi-backend configuration invalid, falling back to single backend mode")

                # Modify model ID
                if 'model' in req_json:
                    original_model = req_json['model']
                    req_json['model'] = target_model_id
                    debug_log(f"Model ID changed from {original_model} to {target_model_id}")
                else:
                    req_json['model'] = target_model_id
                    debug_log(f"Added model ID: {target_model_id}")

                # Handle stream mode
                if stream_mode is not None:
                    original_stream = req_json.get('stream', False)
                    req_json['stream'] = stream_mode == 'true'
                    debug_log(f"Stream mode changed from {original_stream} to {req_json['stream']}")
        else:
            # Single backend mode
            target_api_url = TARGET_API_BASE_URL
            target_model_id = TARGET_MODEL_ID
            custom_model_id = CUSTOM_MODEL_ID
            stream_mode = STREAM_MODE

            # Modify model ID
            if 'model' in req_json:
                original_model = req_json['model']
                req_json['model'] = target_model_id
                debug_log(f"Model ID changed from {original_model} to {target_model_id}")
            else:
                req_json['model'] = target_model_id
                debug_log(f"Added model ID: {target_model_id}")

            # Handle stream mode
            if stream_mode is not None:
                original_stream = req_json.get('stream', False)
                req_json['stream'] = stream_mode == 'true'
                debug_log(f"Stream mode changed from {original_stream} to {req_json['stream']}")

        # Prepare forwarding request
        headers = {
            'Content-Type': 'application/json'
        }

        # Copy Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header:
            headers['Authorization'] = auth_header

        # Build target URL
        target_url = f"{target_api_url}/v1/chat/completions"
        debug_log(f"Forwarding request to: {target_url}")

        # Send request to target API
        response = requests.post(
            target_url,
            json=req_json,
            headers=headers,
            stream=req_json.get('stream', False),
            timeout=300
        )

        # Check response status
        response.raise_for_status()

        # Process response
        if req_json.get('stream', False):
            # Streaming response
            debug_log("Returning streaming response")
            return Response(
                stream_with_context(generate_stream(response)),
                content_type=response.headers.get('Content-Type', 'text/event-stream')
            )
        else:
            # Non-streaming response
            response_json = response.json()

            if DEBUG_MODE:
                debug_log(f"Response body: {json.dumps(response_json, ensure_ascii=False)}")

            # If client requested streaming but target API returned non-streaming, and stream_mode is False
            if stream_mode == 'false':
                debug_log("Simulating streaming response")
                return Response(
                    stream_with_context(simulate_stream(response_json)),
                    content_type='text/event-stream'
                )

            # Modify model ID in response
            if 'model' in response_json:
                response_json['model'] = custom_model_id

            return jsonify(response_json)

    except requests.exceptions.HTTPError as e:
        # HTTP error
        status_code = e.response.status_code
        try:
            error_json = e.response.json()
            return jsonify(error_json), status_code
        except:
            return jsonify({"error": f"HTTP error: {str(e)}"}), status_code

    except requests.exceptions.RequestException as e:
        # Request exception
        logger.error(f"Request exception: {str(e)}")
        return jsonify({"error": f"Request exception: {str(e)}"}), 503

    except Exception as e:
        # Other exceptions
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

def main():
    """Main function"""
    global TARGET_API_BASE_URL, CUSTOM_MODEL_ID, TARGET_MODEL_ID, STREAM_MODE, DEBUG_MODE

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Trae Proxy Server')
    parser.add_argument('--target-api', help='Target API base URL')
    parser.add_argument('--custom-model', help='Model ID exposed to client')
    parser.add_argument('--target-model', help='Model ID sent to target API')
    parser.add_argument('--stream-mode', choices=['true', 'false'], help='Force stream mode setting')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--cert', help='Certificate file path')
    parser.add_argument('--key', help='Private key file path')
    parser.add_argument('--http-mode', action='store_true', help='Enable HTTP mode (no SSL, for use behind reverse proxy)')
    parser.add_argument('--port', type=int, help='Server port (default 443 for HTTPS mode, 8443 for HTTP mode)')
    args = parser.parse_args()

    # Determine running mode and port
    http_mode = args.http_mode
    port = args.port

    # Set default port based on mode if not specified
    if port is None:
        port = 8443 if http_mode else 443

    # Update configuration
    if args.target_api:
        TARGET_API_BASE_URL = args.target_api
    if args.custom_model:
        CUSTOM_MODEL_ID = args.custom_model
    if args.target_model:
        TARGET_MODEL_ID = args.target_model
    if args.stream_mode:
        STREAM_MODE = args.stream_mode
    if args.debug:
        DEBUG_MODE = True
    if args.cert:
        CERT_FILE = args.cert
    if args.key:
        KEY_FILE = args.key

    # Load multi-backend configuration
    load_multi_backend_config()

    # HTTP mode does not require certificates
    if http_mode:
        logger.info("Running in HTTP mode (no SSL) - suitable for use behind reverse proxy")
        logger.info(f"Listening on port: {port}")
    else:
        # HTTPS mode requires certificates
        if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
            logger.error(f"Certificate files do not exist: {CERT_FILE} or {KEY_FILE}")
            logger.info("Please run generate_certs.py to generate certificates, or use --http-mode to enable HTTP mode")
            sys.exit(1)

        # Create SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(CERT_FILE, KEY_FILE)
        logger.info(f"Certificate file: {CERT_FILE}")
        logger.info(f"Private key file: {KEY_FILE}")

    # Print configuration information
    if MULTI_BACKEND_CONFIG:
        logger.info("Multi-backend mode enabled")
        apis = MULTI_BACKEND_CONFIG.get('apis', [])
        for api in apis:
            status = "active" if api.get('active', False) else "inactive"
            logger.info(f"  - {api['name']} [{status}]: {api.get('endpoint', '')} -> {api.get('custom_model_id', '')}")
    else:
        logger.info(f"Target API: {TARGET_API_BASE_URL}")
        logger.info(f"Custom model ID: {CUSTOM_MODEL_ID}")
        logger.info(f"Target model ID: {TARGET_MODEL_ID}")

    logger.info(f"Stream mode: {STREAM_MODE}")
    logger.info(f"Debug mode: {DEBUG_MODE}")

    # Start server
    logger.info("Starting proxy server...")
    if http_mode:
        # HTTP mode - no SSL
        app.run(host='0.0.0.0', port=port, threaded=True)
    else:
        # HTTPS mode - with SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(CERT_FILE, KEY_FILE)
        app.run(host='0.0.0.0', port=port, ssl_context=context, threaded=True)

if __name__ == "__main__":
    main()