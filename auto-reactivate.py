#!/usr/bin/env python3
"""
Auto-Reactivation Script
Automatically reactivates expiring licenses
"""

import json
import os
from datetime import datetime, timedelta
import sys

def load_expiring_licenses():
    """Load expiring licenses from file"""
    if not os.path.exists('expiring_licenses.json'):
        return []
    
    with open('expiring_licenses.json', 'r') as f:
        return json.load(f)

def reactivate_license(license_data):
    """Reactivate a single license by extending its expiration date"""
    # Extend expiration by 30 days
    current_expires = datetime.fromisoformat(license_data['expires_date'].replace('Z', '+00:00'))
    new_expires = current_expires + timedelta(days=30)
    
    # Update license data
    license_data['expires_date'] = new_expires.isoformat()
    license_data['last_reactivated'] = datetime.now().isoformat()
    license_data['reactivation_count'] = license_data.get('reactivation_count', 0) + 1
    license_data['status'] = 'active'
    
    return license_data

def save_reactivated_license(license_data):
    """Save reactivated license back to file"""
    filename = f"license-{license_data['hardware_fingerprint']}.json"
    filepath = os.path.join("data/active-licenses", filename)
    
    with open(filepath, 'w') as f:
        json.dump(license_data, f, indent=2)
    
    # Also save to history
    history_filename = f"license-{license_data['hardware_fingerprint']}-reactivated-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    history_filepath = os.path.join("data/license-history", history_filename)
    
    with open(history_filepath, 'w') as f:
        json.dump(license_data, f, indent=2)

def main():
    # Load expiring licenses
    expiring_licenses = load_expiring_licenses()
    
    if not expiring_licenses:
        print("No expiring licenses found")
        sys.exit(0)
    
    reactivated_count = 0
    
    for license_data in expiring_licenses:
        try:
            # Reactivate the license
            reactivated_license = reactivate_license(license_data)
            
            # Save the reactivated license
            save_reactivated_license(reactivated_license)
            
            reactivated_count += 1
            
            print(f"Reactivated license for {license_data.get('company_name', 'Unknown')}")
            print(f"  Hardware Fingerprint: {license_data.get('hardware_fingerprint', 'Unknown')}")
            print(f"  New Expiration: {reactivated_license['expires_date']}")
            
        except Exception as e:
            print(f"Error reactivating license for {license_data.get('company_name', 'Unknown')}: {e}", file=sys.stderr)
    
    # Output results
    print(f"::set-output name=reactivated_count::{reactivated_count}")
    print(f"::set-output name=total_expiring::{len(expiring_licenses)}")
    
    print(f"\nReactivation Summary:")
    print(f"  Total expiring licenses: {len(expiring_licenses)}")
    print(f"  Successfully reactivated: {reactivated_count}")
    print(f"  Failed reactivations: {len(expiring_licenses) - reactivated_count}")
    
    # Exit with success
    sys.exit(0)

if __name__ == "__main__":
    main()
