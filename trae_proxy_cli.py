#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import argparse
import yaml
import json
import logging
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('trae_proxy_cli')

# Global variables
config_file = "config.yaml"

def load_config():
    """Load configuration from config file"""
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data

        # If config is empty, return default configuration
        return {
            "domain": "api.openai.com",
            "apis": [
                {
                    "name": "Default OpenAI API",
                    "endpoint": "https://api.openai.com",
                    "custom_model_id": "gpt-4",
                    "target_model_id": "gpt-4",
                    "stream_mode": None,
                    "active": True
                }
            ],
            "server": {
                "port": 443,
                "debug": True
            }
        }
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        return {
            "domain": "api.openai.com",
            "apis": [
                {
                    "name": "Default OpenAI API",
                    "endpoint": "https://api.openai.com",
                    "custom_model_id": "gpt-4",
                    "target_model_id": "gpt-4",
                    "stream_mode": None,
                    "active": True
                }
            ],
            "server": {
                "port": 443,
                "debug": True
            }
        }

def save_config(config):
    """Save configuration to config file"""
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)
        logger.info(f"Configuration saved to {config_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to save configuration: {str(e)}")
        return False

def list_apis():
    """List all API configurations"""
    config = load_config()
    apis = config.get('apis', [])

    print("\nCurrent API configuration list:")
    print("-" * 80)
    print(f"Proxy domain: {config.get('domain', 'api.openai.com')}")
    print("-" * 80)

    for i, api in enumerate(apis):
        status = "Active" if api.get('active', False) else "Inactive"
        print(f"{i+1}. {api['name']} [{status}]")
        print(f"   Backend API: {api.get('endpoint', '')}")
        print(f"   Custom model ID: {api.get('custom_model_id', '')}")
        print(f"   Target model ID: {api.get('target_model_id', '')}")
        print(f"   Stream mode: {api.get('stream_mode', 'None')}")
        print("-" * 80)

    return config

def add_api(name, endpoint, custom_model, target_model, stream_mode, active=False):
    """Add new API configuration"""
    config = load_config()

    # Validate URL format
    try:
        parsed_url = urlparse(endpoint)
        if not parsed_url.scheme or not parsed_url.netloc:
            logger.error("Invalid API URL format")
            return False
    except:
        logger.error("Invalid API URL format")
        return False

    # Handle stream mode
    if stream_mode == "true":
        stream_mode = "true"
    elif stream_mode == "false":
        stream_mode = "false"
    else:
        stream_mode = None

    # Create new API configuration
    new_api = {
        'name': name,
        'endpoint': endpoint,
        'custom_model_id': custom_model,
        'target_model_id': target_model,
        'stream_mode': stream_mode,
        'active': active
    }

    # Add to API list
    if 'apis' not in config:
        config['apis'] = []

    config['apis'].append(new_api)

    # Save configuration
    if save_config(config):
        logger.info(f"Added new API configuration: {name}")
        return True
    return False

def remove_api(index):
    """Remove API configuration"""
    config = load_config()
    apis = config.get('apis', [])

    # Check if index is valid
    if index < 0 or index >= len(apis):
        logger.error(f"Invalid API index: {index}")
        return False

    # Check if at least one API configuration should be kept
    if len(apis) <= 1:
        logger.error("At least one API configuration must be kept")
        return False

    # Remove API configuration
    removed = apis.pop(index)
    config['apis'] = apis

    # Save configuration
    if save_config(config):
        logger.info(f"Removed API configuration: {removed['name']}")
        return True
    return False

def update_api(index, name=None, endpoint=None, custom_model=None, target_model=None, stream_mode=None, active=None):
    """Update API configuration"""
    config = load_config()
    apis = config.get('apis', [])

    # Check if index is valid
    if index < 0 or index >= len(apis):
        logger.error(f"Invalid API index: {index}")
        return False

    # Get current API configuration
    api = apis[index]

    # Update API configuration
    if name is not None:
        api['name'] = name

    if endpoint is not None:
        # Validate URL format
        try:
            parsed_url = urlparse(endpoint)
            if not parsed_url.scheme or not parsed_url.netloc:
                logger.error("Invalid API URL format")
                return False
            api['endpoint'] = endpoint
        except:
            logger.error("Invalid API URL format")
            return False

    if custom_model is not None:
        api['custom_model_id'] = custom_model

    if target_model is not None:
        api['target_model_id'] = target_model

    if stream_mode is not None:
        if stream_mode == "true":
            api['stream_mode'] = "true"
        elif stream_mode == "false":
            api['stream_mode'] = "false"
        else:
            api['stream_mode'] = None

    if active is not None:
        api['active'] = active

        # If activating current API, deactivate other APIs
        if active:
            for i, other_api in enumerate(apis):
                if i != index:
                    other_api['active'] = False

    # Save configuration
    if save_config(config):
        logger.info(f"Updated API configuration: {api['name']}")
        return True
    return False

def activate_api(index):
    """Activate specified API configuration"""
    config = load_config()
    apis = config.get('apis', [])

    # Check if index is valid
    if index < 0 or index >= len(apis):
        logger.error(f"Invalid API index: {index}")
        return False

    # Deactivate all APIs
    for api in apis:
        api['active'] = False

    # Activate specified API
    apis[index]['active'] = True

    # Save configuration
    if save_config(config):
        logger.info(f"Activated API configuration: {apis[index]['name']}")
        return True
    return False

def update_domain(domain):
    """Update proxy domain"""
    config = load_config()

    # Update domain
    config['domain'] = domain

    # Save configuration
    if save_config(config):
        logger.info(f"Updated proxy domain: {domain}")
        return True
    return False

def generate_certificates(domain=None):
    """Generate certificates"""
    if domain is None:
        config = load_config()
        domain = config.get('domain', 'api.openai.com')

    logger.info(f"Generating certificates for domain {domain}...")

    # Create ca directory (if it doesn't exist)
    os.makedirs("ca", exist_ok=True)

    # Run certificate generation script
    cmd = [sys.executable, "generate_certs.py", "--domain", domain]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )

    # Read output
    for line in process.stdout:
        logger.info(line.strip())

    # Wait for process to complete
    process.wait()

    if process.returncode == 0:
        logger.info("Certificate generation successful")
        return True
    else:
        logger.error(f"Certificate generation failed, return code: {process.returncode}")
        return False

def start_proxy_server(debug=False, http_mode=False, port=None):
    """Start proxy server"""
    config = load_config()
    domain = config.get('domain', 'api.openai.com')
    apis = config.get('apis', [])

    # Check if there are active API configurations
    active_apis = [api for api in apis if api.get('active', False)]
    if not active_apis:
        if apis:
            logger.warning(f"No active API configuration found, will activate first one: {apis[0]['name']}")
            apis[0]['active'] = True
            active_apis = [apis[0]]
        else:
            logger.error("No API configuration found")
            return False

    logger.info(f"Multi-backend configuration enabled, total {len(apis)} API configurations, {len(active_apis)} active")
    for api in apis:
        status = "Active" if api.get('active', False) else "Inactive"
        logger.info(f"  - {api['name']} [{status}]: {api.get('endpoint', '')} -> {api.get('custom_model_id', '')}")

    # Build command - no longer passing specific API parameters, let proxy server automatically select based on config file
    cmd = [sys.executable, "trae_proxy.py"]

    # HTTP mode does not require certificates
    if http_mode:
        cmd.append("--http-mode")
        if port is None:
            port = 8443
        logger.info("Starting HTTP mode (suitable for use behind reverse proxy)")
    else:
        # HTTPS mode requires certificates
        cert_file = os.path.join("ca", f"{domain}.crt")
        key_file = os.path.join("ca", f"{domain}.key")

        if not os.path.exists(cert_file) or not os.path.exists(key_file):
            logger.error(f"Certificate files do not exist: {cert_file} or {key_file}")
            logger.info("Generating certificates...")
            if not generate_certificates(domain):
                return False

        cmd.extend(["--cert", cert_file, "--key", key_file])
        if port is None:
            port = 443

    # Add port parameter
    if port is not None:
        cmd.extend(["--port", str(port)])

    if debug or config.get('server', {}).get('debug', False):
        cmd.append("--debug")

    logger.info(f"Starting proxy server: {' '.join(cmd)}")
    logger.info("Proxy server will automatically select backend API based on requested model ID")

    # Execute command
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Read output
        for line in process.stdout:
            print(line.strip())

        # Wait for process to complete
        process.wait()

        if process.returncode != 0:
            logger.error(f"Proxy server exited abnormally, return code: {process.returncode}")
            return False

        return True

    except KeyboardInterrupt:
        logger.info("Received interrupt signal, stopping proxy server...")
        process.terminate()
        process.wait()
        logger.info("Proxy server stopped")
        return True

    except Exception as e:
        logger.error(f"Error starting proxy server: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Trae Proxy Command Line Tool')
    subparsers = parser.add_subparsers(dest='command', help='Subcommands')

    # list command
    list_parser = subparsers.add_parser('list', help='List all API configurations')

    # add command
    add_parser = subparsers.add_parser('add', help='Add new API configuration')
    add_parser.add_argument('--name', required=True, help='Configuration name')
    add_parser.add_argument('--endpoint', required=True, help='Backend API URL')
    add_parser.add_argument('--custom-model', required=True, help='Custom model ID')
    add_parser.add_argument('--target-model', required=True, help='Target model ID')
    add_parser.add_argument('--stream-mode', choices=['true', 'false', 'none'], default='none', help='Stream mode')
    add_parser.add_argument('--active', action='store_true', help='Activate this API configuration')

    # remove command
    remove_parser = subparsers.add_parser('remove', help='Remove API configuration')
    remove_parser.add_argument('--index', type=int, required=True, help='API index (starting from 0)')

    # update command
    update_parser = subparsers.add_parser('update', help='Update API configuration')
    update_parser.add_argument('--index', type=int, required=True, help='API index (starting from 0)')
    update_parser.add_argument('--name', help='Configuration name')
    update_parser.add_argument('--endpoint', help='Backend API URL')
    update_parser.add_argument('--custom-model', help='Custom model ID')
    update_parser.add_argument('--target-model', help='Target model ID')
    update_parser.add_argument('--stream-mode', choices=['true', 'false', 'none'], help='Stream mode')
    update_parser.add_argument('--active', action='store_true', help='Activate this API configuration')

    # activate command
    activate_parser = subparsers.add_parser('activate', help='Activate API configuration')
    activate_parser.add_argument('--index', type=int, required=True, help='API index (starting from 0)')

    # domain command
    domain_parser = subparsers.add_parser('domain', help='Update proxy domain')
    domain_parser.add_argument('--name', required=True, help='Domain name')

    # cert command
    cert_parser = subparsers.add_parser('cert', help='Generate certificates')
    cert_parser.add_argument('--domain', help='Domain name (default: use domain from configuration)')

    # start command
    start_parser = subparsers.add_parser('start', help='Start proxy server')
    start_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    start_parser.add_argument('--http-mode', action='store_true', help='Enable HTTP mode (no SSL, for use behind reverse proxy)')
    start_parser.add_argument('--port', type=int, help='Server port (default 443 for HTTPS mode, 8443 for HTTP mode)')

    # Parse command line arguments
    args = parser.parse_args()

    # Execute command
    if args.command == 'list':
        list_apis()

    elif args.command == 'add':
        stream_mode = None if args.stream_mode == 'none' else args.stream_mode
        add_api(args.name, args.endpoint, args.custom_model, args.target_model, stream_mode, args.active)

    elif args.command == 'remove':
        remove_api(args.index)

    elif args.command == 'update':
        stream_mode = None
        if hasattr(args, 'stream_mode') and args.stream_mode is not None:
            stream_mode = None if args.stream_mode == 'none' else args.stream_mode
        update_api(args.index, args.name, args.endpoint, args.custom_model, args.target_model, stream_mode, args.active)

    elif args.command == 'activate':
        activate_api(args.index)

    elif args.command == 'domain':
        update_domain(args.name)

    elif args.command == 'cert':
        generate_certificates(args.domain)

    elif args.command == 'start':
        http_mode = getattr(args, 'http_mode', False)
        port = getattr(args, 'port', None)
        start_proxy_server(args.debug, http_mode, port)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()