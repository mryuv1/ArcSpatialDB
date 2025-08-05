#!/usr/bin/env python3
"""
Environment Switcher for ArcSpatialDB
This script helps you easily switch between different deployment environments.
"""

import os
import sys
import re

def update_config_file(environment, domain=None):
    """
    Update config.py file to switch to the specified environment
    
    Args:
        environment (str): 'local', 'staging', or 'production'
        domain (str): Domain name for staging/production (optional)
    """
    
    config_file = "config.py"
    
    if not os.path.exists(config_file):
        print(f"❌ Error: {config_file} not found!")
        return False
    
    # Read the current config file
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update the ENVIRONMENT variable
    content = re.sub(
        r'ENVIRONMENT = "[^"]*"',
        f'ENVIRONMENT = "{environment}"',
        content
    )
    
    # Update domain URLs if provided
    if domain:
        if environment == "staging":
            staging_url = f"http://staging.{domain}"
            content = re.sub(
                r'"API_BASE_URL": "http://staging\.yourdomain\.com"',
                f'"API_BASE_URL": "{staging_url}"',
                content
            )
        elif environment == "production":
            production_url = f"https://{domain}"
            content = re.sub(
                r'"API_BASE_URL": "https://yourdomain\.com"',
                f'"API_BASE_URL": "{production_url}"',
                content
            )
    
    # Write the updated content back
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def print_current_environment():
    """Print the current environment configuration"""
    try:
        from config import ENVIRONMENT, API_BASE_URL, print_current_config
        print("🔧 Current Configuration:")
        print("=" * 40)
        print_current_config()
        print("=" * 40)
    except ImportError as e:
        print(f"❌ Error reading config: {e}")

def main():
    """Main function to handle command line arguments"""
    
    if len(sys.argv) < 2:
        print("🔧 ArcSpatialDB Environment Switcher")
        print("=" * 50)
        print("Usage:")
        print("  python switch_environment.py local")
        print("  python switch_environment.py staging yourdomain.com")
        print("  python switch_environment.py production yourdomain.com")
        print("  python switch_environment.py show")
        print()
        print("Examples:")
        print("  python switch_environment.py local")
        print("  python switch_environment.py staging mysite.com")
        print("  python switch_environment.py production arcspatialdb.com")
        print()
        print_current_environment()
        return
    
    command = sys.argv[1].lower()
    
    if command == "show":
        print_current_environment()
        return
    
    if command not in ["local", "staging", "production"]:
        print(f"❌ Error: Unknown environment '{command}'")
        print("Valid environments: local, staging, production")
        return
    
    domain = None
    if command in ["staging", "production"]:
        if len(sys.argv) < 3:
            print(f"❌ Error: Domain required for {command} environment")
            print(f"Usage: python switch_environment.py {command} yourdomain.com")
            return
        domain = sys.argv[2]
    
    # Update the configuration
    if update_config_file(command, domain):
        print(f"✅ Successfully switched to {command} environment")
        if domain:
            print(f"🌐 Domain: {domain}")
        print()
        print_current_environment()
    else:
        print("❌ Failed to update configuration")

if __name__ == "__main__":
    main() 