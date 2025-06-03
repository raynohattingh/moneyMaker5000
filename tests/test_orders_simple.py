#!/usr/bin/env python3
"""
Simple debug script to test orders API
"""
import requests
from requests.auth import HTTPBasicAuth
import os

def test_orders_simple():
    api_key = os.getenv('LUNO_API_KEY')
    api_secret = os.getenv('LUNO_API_SECRET')
    
    if not api_key or not api_secret:
        print("Missing API credentials in environment variables")
        return
    
    url = "https://api.luno.com/api/1/listorders"
    
    try:
        # Test basic call
        response = requests.get(url, auth=HTTPBasicAuth(api_key, api_secret))
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response data: {data}")
            
            if 'orders' in data:
                print(f"Number of orders: {len(data['orders'])}")
                if data['orders']:
                    print(f"First order: {data['orders'][0]}")
            else:
                print("No 'orders' key in response")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_orders_simple()
