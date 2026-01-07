#!/usr/bin/env python3
"""
Test OpenAI API key and connection for Lens.

This script validates that:
1. The OpenAI API key is valid
2. The API connection works
3. The configured model is available

Usage:
    python scripts/test-ai-key.py
    # or from backend directory:
    cd backend && python ../scripts/test-ai-key.py
"""

import sys
import os
from pathlib import Path

# Add backend to path so we can import modules
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

try:
    import httpx
    from dotenv import load_dotenv
except ImportError as e:
    print("❌ Error: Required packages not installed")
    print(f"   {e}")
    print("\nPlease run from the backend directory or install dependencies:")
    print("  cd backend && pip install -r requirements.txt")
    sys.exit(1)


def load_env():
    """Load environment variables from backend/.env"""
    env_path = backend_dir / ".env"
    if not env_path.exists():
        print(f"❌ Error: .env file not found at {env_path}")
        print("\nPlease create backend/.env from backend/.env.example")
        sys.exit(1)
    
    load_dotenv(env_path)


def get_config():
    """Get AI configuration from environment"""
    return {
        "enabled": os.getenv("AI_ENABLED", "false").lower() == "true",
        "api_key": os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "2000")),
        "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
        "timeout": int(os.getenv("OPENAI_TIMEOUT", "60")),
    }


def mask_api_key(key):
    """Mask API key for display"""
    if not key:
        return "Not set"
    if len(key) < 20:
        return "***"
    return f"{key[:10]}...{key[-8:]}"


def test_api_key(api_key, base_url, timeout=10):
    """Test if the API key is valid"""
    try:
        response = httpx.get(
            f"{base_url}/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            models = [m["id"] for m in data.get("data", [])]
            return True, models, None
        elif response.status_code == 401:
            return False, [], "Invalid or expired API key"
        else:
            return False, [], f"HTTP {response.status_code}: {response.text[:100]}"
    
    except Exception as e:
        return False, [], f"Connection error: {str(e)}"


def check_model_availability(model, available_models):
    """Check if the configured model is available"""
    if model in available_models:
        return True, None
    
    # Find similar models
    similar = [m for m in available_models if model.split("-")[0] in m]
    return False, similar[:10]


def main():
    print("=" * 60)
    print("🔍 Lens AI Configuration Validator")
    print("=" * 60)
    print()
    
    # Load environment
    load_env()
    config = get_config()
    
    # Display configuration
    print("📋 Configuration:")
    print(f"  AI Enabled:    {config['enabled']}")
    print(f"  Base URL:      {config['base_url']}")
    print(f"  API Key:       {mask_api_key(config['api_key'])}")
    print(f"  Model:         {config['model']}")
    print(f"  Max Tokens:    {config['max_tokens']}")
    print(f"  Temperature:   {config['temperature']}")
    print(f"  Timeout:       {config['timeout']}s")
    print()
    
    # Check if AI is enabled
    if not config['enabled']:
        print("⚠️  Warning: AI is disabled in configuration (AI_ENABLED=false)")
        print()
    
    # Check if API key is set
    if not config['api_key']:
        print("❌ Error: OpenAI API key is not set")
        print("\nPlease set OPENAI_API_KEY in backend/.env")
        sys.exit(1)
    
    # Test API key
    print("🔑 Testing API Key...")
    is_valid, models, error = test_api_key(
        config['api_key'], 
        config['base_url'], 
        config['timeout']
    )
    
    if not is_valid:
        print(f"❌ API Key Test Failed: {error}")
        sys.exit(1)
    
    print("✅ API Key is valid!")
    print(f"   Found {len(models)} available models")
    print()
    
    # Check configured model
    print("🤖 Checking Configured Model...")
    model_available, similar_models = check_model_availability(config['model'], models)
    
    if model_available:
        print(f"✅ Model '{config['model']}' is available!")
    else:
        print(f"❌ Model '{config['model']}' is NOT available")
        if similar_models:
            print("\n   Similar models you can use:")
            for model in similar_models:
                print(f"     - {model}")
            print(f"\n   Update OPENAI_MODEL in backend/.env")
        sys.exit(1)
    
    print()
    
    # Show some recommended models
    print("💡 Recommended Models for Lens:")
    recommended = [
        ("gpt-4o-mini", "Fast, cost-effective, great for log analysis"),
        ("gpt-4o", "More capable, higher quality, more expensive"),
        ("gpt-4-turbo", "Good balance of speed and capability"),
    ]
    
    for model_name, description in recommended:
        if model_name in models:
            indicator = "✓" if model_name == config['model'] else " "
            print(f"  [{indicator}] {model_name:20} - {description}")
    
    print()
    print("=" * 60)
    print("✅ All checks passed! AI features are ready to use.")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

