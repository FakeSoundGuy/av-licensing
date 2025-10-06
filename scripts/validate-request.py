#!/usr/bin/env python3
"""
Request Validation Script for GitHub Actions
Validates activation requests and extracts required information
"""

import json
import re
import sys
import argparse
from datetime import datetime

def validate_hardware_fingerprint(fingerprint):
    """Validate hardware fingerprint format"""
    # Hardware fingerprint should be alphanumeric (16 characters for this system)
    pattern = r'^[A-Za-z0-9]{16}$'
    return bool(re.match(pattern, fingerprint))

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def extract_issue_info(title, body):
    """Extract information from GitHub issue title and body"""
    info = {
        'fingerprint': None,
        'company': None,
        'email': None,
        'name': None,
        'valid': False,
        'errors': []
    }
    
    # Extract from title: "Auto-Activation Request - Company - Fingerprint"
    title_match = re.match(r'Auto-Activation Request - (.+?) - (.+)', title)
    if title_match:
        info['company'] = title_match.group(1).strip()
        info['fingerprint'] = title_match.group(2).strip()
    
    # Extract from body
    if body:
        # Extract email
        email_match = re.search(r'Email:\s*([^\n]+)', body)
        if email_match:
            info['email'] = email_match.group(1).strip()
        
        # Extract contact name
        name_match = re.search(r'Contact:\s*([^\n]+)', body)
        if name_match:
            info['name'] = name_match.group(1).strip()
        
        # Extract hardware fingerprint from body if not in title
        if not info['fingerprint']:
            fingerprint_match = re.search(r'Hardware Fingerprint:\s*([^\n]+)', body)
            if fingerprint_match:
                info['fingerprint'] = fingerprint_match.group(1).strip()
        
        # Extract company from body if not in title
        if not info['company']:
            company_match = re.search(r'Company:\s*([^\n]+)', body)
            if company_match:
                info['company'] = company_match.group(1).strip()
    
    # Validate extracted information
    if not info['fingerprint']:
        info['errors'].append('Hardware fingerprint not found')
    elif not validate_hardware_fingerprint(info['fingerprint']):
        info['errors'].append('Invalid hardware fingerprint format')
    
    if not info['company']:
        info['errors'].append('Company name not found')
    elif len(info['company']) < 2:
        info['errors'].append('Company name too short')
    
    if not info['email']:
        info['errors'].append('Contact email not found')
    elif not validate_email(info['email']):
        info['errors'].append('Invalid email format')
    
    # Mark as valid if no errors
    info['valid'] = len(info['errors']) == 0
    
    return info

def main():
    parser = argparse.ArgumentParser(description='Validate activation request')
    parser.add_argument('title', help='GitHub issue title')
    parser.add_argument('body', help='GitHub issue body')
    
    args = parser.parse_args()
    
    # Extract and validate information
    info = extract_issue_info(args.title, args.body)
    
    if info['valid']:
        # Output valid information for GitHub Actions
        print(f"::set-output name=fingerprint::{info['fingerprint']}")
        print(f"::set-output name=company::{info['company']}")
        print(f"::set-output name=email::{info['email']}")
        print(f"::set-output name=name::{info['name'] or ''}")
        print(f"::set-output name=valid::true")
        
        # Also output as JSON for debugging
        print(f"::set-output name=info::{json.dumps(info)}")
        
        sys.exit(0)
    else:
        # Output errors
        print(f"::set-output name=valid::false")
        print(f"::set-output name=errors::{json.dumps(info['errors'])}")
        
        # Print errors to stderr
        for error in info['errors']:
            print(f"ERROR: {error}", file=sys.stderr)
        
        sys.exit(1)

if __name__ == "__main__":
    main()
