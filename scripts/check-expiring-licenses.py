#!/usr/bin/env python3
"""
Check Expiring Licenses Script
Identifies licenses that need reactivation
"""

import json
import os
from datetime import datetime, timedelta
import sys

def load_active_licenses():
    """Load all active license files"""
    licenses = []
    licenses_dir = "data/active-licenses"
    
    if not os.path.exists(licenses_dir):
        return licenses
    
    for filename in os.listdir(licenses_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(licenses_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    license_data = json.load(f)
                    licenses.append(license_data)
            except Exception as e:
                print(f"Error loading license {filename}: {e}", file=sys.stderr)
    
    return licenses

def find_expiring_licenses(licenses, days_ahead=5):
    """Find licenses that will expire within the specified days"""
    expiring = []
    cutoff_date = datetime.now() + timedelta(days=days_ahead)
    
    for license_data in licenses:
        if license_data.get('status') != 'active':
            continue
        
        expires_date_str = license_data.get('expires_date')
        if not expires_date_str:
            continue
        
        try:
            expires_date = datetime.fromisoformat(expires_date_str.replace('Z', '+00:00'))
            if expires_date <= cutoff_date:
                expiring.append(license_data)
        except Exception as e:
            print(f"Error parsing expiration date for license {license_data.get('hardware_fingerprint', 'unknown')}: {e}", file=sys.stderr)
    
    return expiring

def main():
    # Load active licenses
    licenses = load_active_licenses()
    
    # Find expiring licenses (within 5 days)
    expiring = find_expiring_licenses(licenses, days_ahead=5)
    
    # Output results
    print(f"::set-output name=total_licenses::{len(licenses)}")
    print(f"::set-output name=expiring_count::{len(expiring)}")
    
    # Save expiring licenses to file for other scripts
    with open('expiring_licenses.json', 'w') as f:
        json.dump(expiring, f, indent=2)
    
    # Also create empty file if no expiring licenses
    if not expiring:
        with open('expiring_licenses.json', 'w') as f:
            json.dump([], f)
    
    # Print summary
    print(f"Total active licenses: {len(licenses)}")
    print(f"Licenses expiring within 5 days: {len(expiring)}")
    
    if expiring:
        print("\nExpiring licenses:")
        for license_data in expiring:
            print(f"  - {license_data.get('company_name', 'Unknown')} ({license_data.get('hardware_fingerprint', 'Unknown')})")
            print(f"    Expires: {license_data.get('expires_date', 'Unknown')}")
    
    # Exit with error code if there are expiring licenses (for workflow logic)
    if expiring:
        sys.exit(0)  # Success - found expiring licenses
    else:
        sys.exit(0)  # Success - no expiring licenses

if __name__ == "__main__":
    main()
