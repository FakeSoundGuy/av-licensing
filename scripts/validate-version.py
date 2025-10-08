#!/usr/bin/env python3
"""
Version Validation Script for GitHub Actions
Validates client software version against minimum requirements
"""

import json
import os
import sys
import re

def load_version_config():
    """Load version requirements from config"""
    config_file = "config/activation-config.json"
    
    if not os.path.exists(config_file):
        return {
            'minimum_version': '3.2.4',
            'latest_version': '3.2.4',
            'enforce_version_check': True,
            'allow_older_reactivations': True
        }
    
    with open(config_file, 'r') as f:
        config = json.load(f)
        return config.get('activation_settings', {})

def extract_version_from_body(body):
    """Extract software version from issue body"""
    if not body:
        return None
    
    # Look for "Software Version: X.X.X" pattern
    patterns = [
        r'Software Version:\s*([0-9]+\.[0-9]+\.[0-9]+)',
        r'Client Version:\s*([0-9]+\.[0-9]+\.[0-9]+)',
        r'Version:\s*([0-9]+\.[0-9]+\.[0-9]+)',
        r'App Version:\s*([0-9]+\.[0-9]+\.[0-9]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def is_reactivation_request(title, body):
    """Check if this is a reactivation request vs new activation"""
    if 'reactivation' in title.lower():
        return True
    if 'auto-reactivation' in title.lower():
        return True
    if body and 'reactivation' in body.lower():
        return True
    return False

def compare_versions(v1, v2):
    """
    Compare two version strings (simple comparison)
    Returns: 1 if v1 > v2, -1 if v1 < v2, 0 if equal
    """
    try:
        v1_parts = [int(x) for x in v1.split('.')]
        v2_parts = [int(x) for x in v2.split('.')]
        
        # Pad to same length
        while len(v1_parts) < len(v2_parts):
            v1_parts.append(0)
        while len(v2_parts) < len(v1_parts):
            v2_parts.append(0)
        
        for i in range(len(v1_parts)):
            if v1_parts[i] > v2_parts[i]:
                return 1
            elif v1_parts[i] < v2_parts[i]:
                return -1
        
        return 0
    except Exception as e:
        print(f"Error comparing versions: {e}", file=sys.stderr)
        return 0

def validate_version(client_version, minimum_version, latest_version, is_reactivation, allow_older_reactivations):
    """Validate client version against requirements"""
    result = {
        'valid': False,
        'client_version': client_version or 'unknown',
        'minimum_version': minimum_version,
        'latest_version': latest_version,
        'is_latest': False,
        'is_acceptable': False,
        'is_reactivation': is_reactivation,
        'message': '',
        'warning_only': False
    }
    
    if not client_version:
        if is_reactivation and allow_older_reactivations:
            result['valid'] = True
            result['warning_only'] = True
            result['message'] = 'Reactivation request - version not provided but allowed for existing licenses'
        else:
            result['message'] = 'No software version information provided in request'
        return result
    
    # Compare versions
    vs_minimum = compare_versions(client_version, minimum_version)
    vs_latest = compare_versions(client_version, latest_version)
    
    result['is_acceptable'] = vs_minimum >= 0  # Greater than or equal to minimum
    result['is_latest'] = vs_latest >= 0  # Greater than or equal to latest
    
    # Special handling for reactivations
    if is_reactivation and allow_older_reactivations:
        result['valid'] = True
        if not result['is_latest']:
            result['warning_only'] = True
            result['message'] = f'Reactivation allowed for version {client_version}, but please update to {latest_version} for latest features'
        else:
            result['message'] = f'Reactivation approved for current version {client_version}'
    else:
        # New activation - enforce minimum version
        result['valid'] = result['is_acceptable']
        
        if vs_minimum < 0:
            result['message'] = f'Version {client_version} is outdated. Minimum required: {minimum_version}. Latest: {latest_version}. Please update software before activation.'
        elif vs_latest < 0:
            result['message'] = f'Version {client_version} is acceptable but not latest. Latest version: {latest_version}. Consider updating for new features and bug fixes.'
            result['warning_only'] = True
        else:
            result['message'] = f'Version {client_version} is current and up to date.'
    
    return result

def main():
    if len(sys.argv) < 3:
        print("ERROR: Requires title and body arguments", file=sys.stderr)
        sys.exit(1)
    
    issue_title = sys.argv[1]
    issue_body = sys.argv[2]
    
    # Load config
    config = load_version_config()
    minimum_version = config.get('minimum_version', '3.2.4')
    latest_version = config.get('latest_version', '3.2.4')
    enforce_check = config.get('enforce_version_check', True)
    allow_older_reactivations = config.get('allow_older_reactivations', True)
    
    # Check if this is a reactivation
    is_reactivation = is_reactivation_request(issue_title, issue_body)
    
    # Extract version from issue body
    client_version = extract_version_from_body(issue_body)
    
    # Validate version
    result = validate_version(
        client_version, 
        minimum_version, 
        latest_version,
        is_reactivation,
        allow_older_reactivations
    )
    
    # Output for GitHub Actions
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"version_valid={str(result['valid']).lower()}\n")
            f.write(f"client_version={result['client_version']}\n")
            f.write(f"is_latest={str(result['is_latest']).lower()}\n")
            f.write(f"is_acceptable={str(result['is_acceptable']).lower()}\n")
            f.write(f"version_message={result['message']}\n")
            f.write(f"warning_only={str(result['warning_only']).lower()}\n")
    
    # Print results for debugging
    print(f"=== Version Validation Results ===")
    print(f"Client Version: {result['client_version']}")
    print(f"Minimum Required: {minimum_version}")
    print(f"Latest Version: {latest_version}")
    print(f"Is Reactivation: {is_reactivation}")
    print(f"Valid: {result['valid']}")
    print(f"Is Latest: {result['is_latest']}")
    print(f"Is Acceptable: {result['is_acceptable']}")
    print(f"Message: {result['message']}")
    print(f"Warning Only: {result['warning_only']}")
    
    # Exit based on validation and enforcement
    if enforce_check and not result['valid']:
        print("Version check FAILED - Request will be rejected", file=sys.stderr)
        sys.exit(1)  # Fail - version check failed
    else:
        print("Version check PASSED")
        sys.exit(0)  # Success

if __name__ == "__main__":
    main()


