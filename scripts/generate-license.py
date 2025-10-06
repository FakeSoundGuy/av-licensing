#!/usr/bin/env python3
"""
License Generation Script for GitHub Actions
Generates secure license files with 30-day expiration
"""

import json
import hashlib
import secrets
from datetime import datetime, timedelta
import sys
import argparse

def generate_license_key(fingerprint, company, email):
    """Generate a unique license key based on hardware fingerprint and company info"""
    data = f"{fingerprint}:{company}:{email}:{datetime.now().isoformat()}"
    return hashlib.sha256(data.encode()).hexdigest()[:32].upper()

def create_license(fingerprint, company, email, duration_days=30):
    """Create a complete license object"""
    now = datetime.now()
    expires = now + timedelta(days=duration_days)
    
    license_data = {
        "license_key": generate_license_key(fingerprint, company, email),
        "hardware_fingerprint": fingerprint,
        "company_name": company,
        "contact_email": email,
        "created_date": now.isoformat(),
        "expires_date": expires.isoformat(),
        "status": "active",
        "version": "3.2.0",
        "auto_generated": True,
        "reactivation_required": True,
        "generated_by": "github-actions",
        "generation_method": "automated"
    }
    
    return license_data

def main():
    parser = argparse.ArgumentParser(description='Generate license for activation request')
    parser.add_argument('--fingerprint', required=True, help='Hardware fingerprint')
    parser.add_argument('--company', required=True, help='Company name')
    parser.add_argument('--email', required=True, help='Contact email')
    parser.add_argument('--duration', type=int, default=30, help='License duration in days')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.fingerprint or len(args.fingerprint) < 32:
        print("ERROR: Invalid hardware fingerprint", file=sys.stderr)
        sys.exit(1)
    
    if not args.company or len(args.company) < 2:
        print("ERROR: Invalid company name", file=sys.stderr)
        sys.exit(1)
    
    if not args.email or '@' not in args.email:
        print("ERROR: Invalid email address", file=sys.stderr)
        sys.exit(1)
    
    # Generate license
    license_data = create_license(args.fingerprint, args.company, args.email, args.duration)
    
    # Output for GitHub Actions (legacy format)
    print(f"::set-output name=license_data::{json.dumps(license_data)}")
    print(f"::set-output name=expires_date::{license_data['expires_date']}")
    print(f"::set-output name=license_key::{license_data['license_key']}")
    
    # Output for GitHub Actions (new format)
    with open(os.environ.get('GITHUB_OUTPUT', '/dev/stdout'), 'a') as f:
        f.write(f"license_data={json.dumps(license_data)}\n")
        f.write(f"expires_date={license_data['expires_date']}\n")
        f.write(f"license_key={license_data['license_key']}\n")
    
    # Also print to stdout for debugging
    print(f"Generated license for {args.company}")
    print(f"License Key: {license_data['license_key']}")
    print(f"Expires: {license_data['expires_date']}")

if __name__ == "__main__":
    main()
