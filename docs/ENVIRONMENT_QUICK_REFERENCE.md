# 🚀 Environment Switching - Quick Reference

## 🔧 Setup

### Production Environment (Default)
```bash
# Environment variables
LUNO_API_KEY_ID=your_production_key
LUNO_API_SECRET=your_production_secret

# No ENV variable needed (defaults to PROD)
```

### Staging Environment 
```bash
# Environment variables
ENV=DEV
LUNO_API_KEY_ID_DEV=your_staging_key
LUNO_API_SECRET_DEV=your_staging_secret
```

## 💻 Usage

### Method 1: Environment Variable (Recommended)
```bash
# For testing
export ENV=DEV && python run_bot.py

# For live trading  
export ENV=PROD && python run_bot.py
# or just: python run_bot.py (defaults to PROD)
```

### Method 2: Code Override
```python
from core.luno_api import LunoAPI

# Force staging
api = LunoAPI(environment='DEV')

# Force production
api = LunoAPI(environment='PROD')

# Use default (production)
api = LunoAPI()
```

## 🔍 Environment Status

### Check Current Environment
```python
# Get environment details
env_info = api.get_environment_info()
print(f"Environment: {env_info['environment']}")
print(f"URL: {env_info['base_url']}")
print(f"Is Staging: {env_info['is_staging']}")

# Log full status
api.log_environment_status()
```

## ⚡ Quick Commands

```bash
# Verify environment switching works
python verify_environment_switching.py

# Test comprehensive functionality
python test_environment_switching.py

# Interactive demo
python demos/demo_environment_switching.py
```

## 🔒 Safety Notes

- ✅ **Production is the default** - safe by design
- ⚠️ **Staging shows warnings** - clear when testing  
- 🔐 **Credentials are separated** - no cross-contamination
- 📝 **All operations logged** - full transparency

## 🎯 Status: Ready to Use! ✅
