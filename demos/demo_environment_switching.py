#!/usr/bin/env python3
"""
Demo script showing environment switching in action
This demonstrates how easy it is to switch between production and staging
"""

import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.luno_api import LunoAPI

def demo_environment_switching():
    """Demonstrate environment switching capabilities"""
    
    print("🚀 LUNO API ENVIRONMENT SWITCHING DEMO")
    print("=" * 60)
    
    print("\n💡 This demo shows how the LunoAPI automatically:")
    print("   • Detects the environment (PROD/DEV)")
    print("   • Switches URLs and credentials")
    print("   • Provides safety warnings")
    print("   • Maintains environment awareness")
    
    # Demo 1: Default behavior (Production)
    print("\n" + "🔹" * 40)
    print("1️⃣  DEFAULT BEHAVIOR (Production)")
    print("🔹" * 40)
    try:
        print("Creating LunoAPI() with no parameters...")
        api_default = LunoAPI()
        api_default.log_environment_status()
    except Exception as e:
        print(f"Note: {e}")
    
    # Demo 2: Explicit production
    print("\n" + "🔹" * 40)
    print("2️⃣  EXPLICIT PRODUCTION")
    print("🔹" * 40)
    try:
        print("Creating LunoAPI(environment='PROD')...")
        api_prod = LunoAPI(environment='PROD')
        api_prod.log_environment_status()
    except Exception as e:
        print(f"Note: {e}")
    
    # Demo 3: Staging environment
    print("\n" + "🔹" * 40)
    print("3️⃣  STAGING ENVIRONMENT")
    print("🔹" * 40)
    try:
        print("Creating LunoAPI(environment='DEV')...")
        api_staging = LunoAPI(environment='DEV')
        api_staging.log_environment_status()
        
        # Show the differences
        env_info = api_staging.get_environment_info()
        print(f"\n🔍 Environment Details:")
        print(f"   Environment: {env_info['environment']}")
        print(f"   Base URL: {env_info['base_url']}")
        print(f"   Exchange URL: {env_info['exchange_url']}")
        print(f"   Is Staging: {env_info['is_staging']}")
        
    except Exception as e:
        print(f"Expected: {e}")
        print("   ℹ️  This is expected - staging credentials not configured")
    
    # Demo 4: Environment variable control
    print("\n" + "🔹" * 40)
    print("4️⃣  ENVIRONMENT VARIABLE CONTROL")
    print("🔹" * 40)
    
    original_env = os.getenv('ENV')
    
    try:
        print("Setting ENV=DEV and creating LunoAPI()...")
        os.environ['ENV'] = 'DEV'
        api_env = LunoAPI()
        env_info = api_env.get_environment_info()
        print(f"   ✅ Detected environment: {env_info['environment']}")
        print(f"   ✅ Using URL: {env_info['base_url']}")
        
    except Exception as e:
        print(f"Expected: {e}")
    finally:
        # Restore original environment
        if original_env:
            os.environ['ENV'] = original_env
        elif 'ENV' in os.environ:
            del os.environ['ENV']
    
    # Summary
    print("\n" + "🎯" * 40)
    print("📋 SUMMARY")
    print("🎯" * 40)
    print("✅ Environment switching works automatically")
    print("✅ Production is the safe default")
    print("✅ Staging provides clear warnings")
    print("✅ Multiple ways to control environment:")
    print("   • ENV environment variable")
    print("   • Constructor parameter")
    print("   • Automatic detection")
    
    print("\n🔧 TO USE STAGING:")
    print("1. Get staging credentials from Luno support")
    print("2. Set LUNO_API_KEY_ID_DEV and LUNO_API_SECRET_DEV")
    print("3. Set ENV=DEV or use LunoAPI(environment='DEV')")
    
    print("\n🚀 TO USE PRODUCTION:")
    print("1. Set LUNO_API_KEY_ID and LUNO_API_SECRET")
    print("2. Leave ENV unset or set ENV=PROD")
    print("3. Use LunoAPI() or LunoAPI(environment='PROD')")
    
    print("\n" + "=" * 60)
    print("🎉 DEMO COMPLETE - Environment switching is ready!")

if __name__ == "__main__":
    demo_environment_switching()
