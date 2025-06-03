#!/usr/bin/env python3
"""
Test script for environment switching between production and staging
This script tests the LunoAPI class with different environment configurations
"""

import sys
import os
import logging

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.luno_api import LunoAPI

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_production_environment():
    """Test production environment configuration"""
    print("\n" + "="*60)
    print("TESTING PRODUCTION ENVIRONMENT")
    print("="*60)
    
    try:
        # Test with explicit PROD environment
        api_prod = LunoAPI(environment='PROD')
        env_info = api_prod.get_environment_info()
        
        print(f"✅ Production API initialized")
        print(f"   Environment: {env_info['environment']}")
        print(f"   Base URL: {env_info['base_url']}")
        print(f"   Exchange URL: {env_info['exchange_url']}")
        print(f"   Is Staging: {env_info['is_staging']}")
        print(f"   API Key: {env_info['api_key_masked']}")
        
        # Log environment status
        api_prod.log_environment_status()
        
        # Test a simple API call (if credentials are available)
        try:
            tickers = api_prod.get_tickers()
            print(f"✅ API connectivity test passed - found {len(tickers.get('tickers', []))} tickers")
        except Exception as e:
            print(f"⚠️  API connectivity test failed: {e}")
        
    except Exception as e:
        print(f"❌ Error testing production environment: {e}")

def test_staging_environment():
    """Test staging environment configuration"""
    print("\n" + "="*60)
    print("TESTING STAGING/DEV ENVIRONMENT")
    print("="*60)
    
    try:
        # Test with explicit DEV environment
        api_dev = LunoAPI(environment='DEV')
        env_info = api_dev.get_environment_info()
        
        print(f"✅ Staging API initialized")
        print(f"   Environment: {env_info['environment']}")
        print(f"   Base URL: {env_info['base_url']}")
        print(f"   Exchange URL: {env_info['exchange_url']}")
        print(f"   Is Staging: {env_info['is_staging']}")
        print(f"   API Key: {env_info['api_key_masked']}")
        
        # Log environment status
        api_dev.log_environment_status()
        
        # Test a simple API call (if staging credentials are available)
        try:
            tickers = api_dev.get_tickers()
            print(f"✅ Staging API connectivity test passed - found {len(tickers.get('tickers', []))} tickers")
        except Exception as e:
            print(f"⚠️  Staging API connectivity test failed: {e}")
            print(f"   This is expected if staging credentials are not configured")
        
    except Exception as e:
        print(f"❌ Error testing staging environment: {e}")

def test_environment_variable():
    """Test environment detection from ENV variable"""
    print("\n" + "="*60)
    print("TESTING ENVIRONMENT VARIABLE DETECTION")
    print("="*60)
    
    # Save original ENV value
    original_env = os.getenv('ENV')
    
    try:
        # Test with ENV=DEV
        os.environ['ENV'] = 'DEV'
        api_env_dev = LunoAPI()
        env_info_dev = api_env_dev.get_environment_info()
        print(f"✅ ENV=DEV detected: {env_info_dev['environment']}")
        print(f"   Base URL: {env_info_dev['base_url']}")
        
        # Test with ENV=PROD
        os.environ['ENV'] = 'PROD'
        api_env_prod = LunoAPI()
        env_info_prod = api_env_prod.get_environment_info()
        print(f"✅ ENV=PROD detected: {env_info_prod['environment']}")
        print(f"   Base URL: {env_info_prod['base_url']}")
        
        # Test with no ENV (should default to PROD)
        if 'ENV' in os.environ:
            del os.environ['ENV']
        api_env_default = LunoAPI()
        env_info_default = api_env_default.get_environment_info()
        print(f"✅ No ENV variable - default: {env_info_default['environment']}")
        print(f"   Base URL: {env_info_default['base_url']}")
        
    except Exception as e:
        print(f"❌ Error testing environment variable: {e}")
    finally:
        # Restore original ENV value
        if original_env:
            os.environ['ENV'] = original_env
        elif 'ENV' in os.environ:
            del os.environ['ENV']

def test_credential_validation():
    """Test credential validation for different environments"""
    print("\n" + "="*60)
    print("TESTING CREDENTIAL VALIDATION")
    print("="*60)
    
    # Check which credentials are available
    prod_key = os.getenv('LUNO_API_KEY_ID')
    prod_secret = os.getenv('LUNO_API_SECRET')
    dev_key = os.getenv('LUNO_API_KEY_ID_DEV')
    dev_secret = os.getenv('LUNO_API_SECRET_DEV')
    
    print(f"Production credentials: {'✅ Available' if prod_key and prod_secret else '❌ Missing'}")
    print(f"Development credentials: {'✅ Available' if dev_key and dev_secret else '❌ Missing'}")
    
    if prod_key and prod_secret:
        print(f"   LUNO_API_KEY_ID: {prod_key[:8]}...")
    else:
        print(f"   Missing: LUNO_API_KEY_ID or LUNO_API_SECRET")
    
    if dev_key and dev_secret:
        print(f"   LUNO_API_KEY_ID_DEV: {dev_key[:8]}...")
    else:
        print(f"   Missing: LUNO_API_KEY_ID_DEV or LUNO_API_SECRET_DEV")

def test_order_validation_environments():
    """Test order validation in different environments"""
    print("\n" + "="*60)
    print("TESTING ORDER VALIDATION IN DIFFERENT ENVIRONMENTS")
    print("="*60)
    
    test_environments = ['PROD', 'DEV']
    
    for env in test_environments:
        try:
            print(f"\n🔍 Testing {env} environment...")
            api = LunoAPI(environment=env)
            
            # Test market data retrieval
            market_info = api.get_market_info('XBTZAR')
            print(f"   Market data: Min vol {market_info['min_volume']}, Max vol {market_info['max_volume']}")
            
            # Test order validation (without placing)
            formatted_price, formatted_volume, is_valid = api.validate_and_format_order('XBTZAR', 1900000, 0.001)
            print(f"   Order validation: Price {formatted_price}, Volume {formatted_volume}, Valid: {is_valid}")
            
        except Exception as e:
            print(f"   ❌ Error in {env} environment: {e}")

def main():
    """Run all environment tests"""
    print("🧪 LUNO API ENVIRONMENT SWITCHING TESTS")
    print("=" * 80)
    
    print("\n💡 This test verifies:")
    print("1. Environment detection from ENV variable")
    print("2. Correct URL selection for staging vs production")
    print("3. Proper credential selection")
    print("4. API functionality in different environments")
    
    # Run all test functions
    test_credential_validation()
    test_production_environment()
    test_staging_environment()
    test_environment_variable()
    test_order_validation_environments()
    
    print("\n" + "="*80)
    print("🎉 ENVIRONMENT SWITCHING TESTS COMPLETED")
    print("="*80)
    
    print("\n📋 SETUP INSTRUCTIONS:")
    print("To use staging environment:")
    print("1. Set ENV=DEV in your environment variables")
    print("2. Configure LUNO_API_KEY_ID_DEV and LUNO_API_SECRET_DEV")
    print("3. Initialize LunoAPI() - it will automatically use staging")
    print("")
    print("To use production environment:")
    print("1. Set ENV=PROD (or leave unset - defaults to PROD)")
    print("2. Configure LUNO_API_KEY_ID and LUNO_API_SECRET")
    print("3. Initialize LunoAPI() - it will use production")
    print("")
    print("Manual override:")
    print("api = LunoAPI(environment='DEV')  # Force staging")
    print("api = LunoAPI(environment='PROD') # Force production")

if __name__ == "__main__":
    main()
