#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import tempfile
import atexit
import shutil

# Temporary file list for cleanup on exit
temp_files = []

def error(message):
    """Print error message and exit"""
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)

def run_command(command, check=True):
    """Run command and check return code"""
    print(f"Executing command: {command}")
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if check and result.returncode != 0:
        error(f"Command execution failed: {command}\n{result.stderr}")
    return result

def create_temp_file(content):
    """Create temporary file and return its path"""
    fd, path = tempfile.mkstemp()
    os.write(fd, content.encode('utf-8'))
    os.close(fd)
    temp_files.append(path)
    return path

def cleanup_temp_files():
    """Clean up all temporary files"""
    for path in temp_files:
        try:
            os.unlink(path)
        except:
            pass

# Register cleanup function on exit
atexit.register(cleanup_temp_files)

def check_openssl():
    """Check if OpenSSL is installed"""
    try:
        run_command("openssl version")
    except:
        error("OpenSSL not found. Please ensure OpenSSL is installed and in PATH.")

def create_default_config_files(domain="api.openai.com"):
    """Create default OpenSSL configuration files"""
    # Create ca directory (if it doesn't exist)
    os.makedirs("ca", exist_ok=True)

    # Basic OpenSSL configuration
    openssl_cnf = """
[ req ]
default_bits        = 2048
default_md          = sha256
default_keyfile     = privkey.pem
distinguished_name  = req_distinguished_name
req_extensions      = v3_req
x509_extensions     = v3_ca

[ req_distinguished_name ]
countryName                     = Country Code (2 characters)
countryName_default             = CN
stateOrProvinceName             = State/Province
stateOrProvinceName_default     = State
localityName                    = City
localityName_default            = City
organizationName                = Organization Name
organizationName_default        = Organization
organizationalUnitName          = Organizational Unit Name
organizationalUnitName_default  = Unit
commonName                      = Common Name
commonName_max                  = 64
commonName_default              = localhost
emailAddress                    = Email Address
emailAddress_max                = 64
emailAddress_default            = admin@example.com

[ v3_req ]
basicConstraints       = CA:FALSE
keyUsage               = nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage       = serverAuth
subjectAltName         = @alt_names

[ v3_ca ]
basicConstraints       = critical, CA:true
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid:always, issuer:always
keyUsage               = cRLSign, keyCertSign, digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
"""

    # CA certificate extension configuration (without subjectAltName)
    v3_ca_cnf = """
[ v3_ca ]
basicConstraints       = critical, CA:true
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid:always, issuer:always
keyUsage               = cRLSign, keyCertSign, digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
"""

    # Server certificate extension configuration
    v3_req_cnf = """
[ v3_req ]
basicConstraints       = CA:FALSE
keyUsage               = nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage       = serverAuth
subjectAltName         = @alt_names
"""

    # Write configuration files (if they don't exist)
    if not os.path.exists("ca/openssl.cnf"):
        with open("ca/openssl.cnf", "w") as f:
            f.write(openssl_cnf)

    if not os.path.exists("ca/v3_ca.cnf"):
        with open("ca/v3_ca.cnf", "w") as f:
            f.write(v3_ca_cnf)

    if not os.path.exists("ca/v3_req.cnf"):
        with open("ca/v3_req.cnf", "w") as f:
            f.write(v3_req_cnf)

    # Subject Alternative Name configuration
    domain_cnf = f"""
[ alt_names ]
DNS.1 = {domain}
"""

    # Certificate subject information
    domain_subj = f"/C=CN/ST=State/L=City/O=Organization/OU=Unit/CN={domain}"

    # Write domain-specific configuration
    if not os.path.exists(f"ca/{domain}.cnf"):
        with open(f"ca/{domain}.cnf", "w") as f:
            f.write(domain_cnf)

    if not os.path.exists(f"ca/{domain}.subj"):
        with open(f"ca/{domain}.subj", "w") as f:
            f.write(domain_subj)

def generate_ca_cert():
    """Generate CA certificate and private key"""
    print("Generating CA certificate...")

    # Generate CA private key
    run_command("openssl genrsa -out ca/ca.key 2048")

    # Use simple command to generate self-signed CA certificate, avoiding complex configuration files
    run_command("openssl req -new -x509 -days 36500 -key ca/ca.key -out ca/ca.crt -subj \"/C=CN/ST=State/L=City/O=TraeProxy CA/OU=TraeProxy/CN=TraeProxy Root CA\"")

    print("CA certificate generation completed")

def generate_server_cert(domain="api.openai.com"):
    """Generate server certificate for specified domain"""
    print(f"Generating server certificate for domain {domain}...")

    # Check required files
    required_files = [
        "ca/openssl.cnf",
        "ca/v3_req.cnf",
        f"ca/{domain}.cnf",
        f"ca/{domain}.subj",
        "ca/ca.key",
        "ca/ca.crt"
    ]

    for file in required_files:
        if not os.path.exists(file):
            error(f"Missing required file: {file}")

    # Read configuration files
    with open("ca/openssl.cnf", "r") as f:
        openssl_cnf = f.read()

    with open("ca/v3_req.cnf", "r") as f:
        v3_req_cnf = f.read()

    with open(f"ca/{domain}.cnf", "r") as f:
        domain_cnf = f.read()

    with open(f"ca/{domain}.subj", "r") as f:
        domain_subj = f.read().strip()

    # Merge configurations
    merged_cnf = openssl_cnf + "\n" + v3_req_cnf + "\n" + domain_cnf
    temp_cnf = create_temp_file(merged_cnf)

    # Generate server private key
    run_command(f"openssl genrsa -out ca/{domain}.key 2048")

    # Convert to PKCS#8 format
    run_command(f"openssl pkcs8 -topk8 -nocrypt -in ca/{domain}.key -out ca/{domain}.key.pkcs8")
    shutil.move(f"ca/{domain}.key.pkcs8", f"ca/{domain}.key")

    # Generate CSR
    run_command(f"openssl req -reqexts v3_req -sha256 -new -key ca/{domain}.key -out ca/{domain}.csr -config {temp_cnf} -subj \"{domain_subj}\"")

    # Sign certificate with CA
    run_command(f"openssl x509 -req -days 365 -in ca/{domain}.csr -CA ca/ca.crt -CAkey ca/ca.key -CAcreateserial -out ca/{domain}.crt -extfile {temp_cnf} -extensions v3_req")

    # Remove CSR file
    os.remove(f"ca/{domain}.csr")

    print(f"Server certificate generation completed: ca/{domain}.crt")

def main():
    """Main function"""
    # Parse command line arguments
    domain = "api.openai.com"
    if len(sys.argv) > 1 and sys.argv[1] == "--domain" and len(sys.argv) > 2:
        domain = sys.argv[2]

    # Check OpenSSL
    check_openssl()

    # Create default configuration files
    create_default_config_files(domain)

    # Generate CA certificate
    generate_ca_cert()

    # Generate server certificate
    generate_server_cert(domain)

    print("All certificate generation completed")

if __name__ == "__main__":
    main()