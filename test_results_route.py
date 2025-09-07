#!/usr/bin/env python3
"""
Test script to check results route
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from flask import url_for

def test_results_route():
    """Test the results route with mock data."""
    
    print("🧪 Testing Results Route")
    print("=" * 50)
    
    with app.test_client() as client:
        with app.app_context():
            try:
                # Test accessing results without authentication
                response = client.get('/student/results/1')
                print(f"Response status: {response.status_code}")
                
                if response.status_code == 302:
                    print("✅ Redirected to login (expected)")
                elif response.status_code == 200:
                    print("✅ Results page accessible")
                    print(f"Response length: {len(response.data)} bytes")
                else:
                    print(f"❌ Unexpected status: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error accessing results route: {str(e)}")
                return False
    
    return True

if __name__ == "__main__":
    success = test_results_route()
    sys.exit(0 if success else 1)

