"""
Check Gemini Model Status and Configuration
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

def check_gemini_status():
    """Check Gemini model status and configuration"""
    
    print("🔍 Checking Gemini Model Status")
    print("=" * 40)
    
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        print(f"✅ Gemini API Key: {'*' * (len(api_key) - 8) + api_key[-8:]}")
    else:
        print("❌ Gemini API Key: NOT FOUND")
        print("   Please add GEMINI_API_KEY to your .env file")
        return False
    
    # Configure Gemini
    try:
        genai.configure(api_key=api_key)
        print("✅ Gemini configured successfully")
    except Exception as e:
        print(f"❌ Gemini configuration failed: {e}")
        return False
    
    # List available models
    try:
        models = genai.list_models()
        print("\n📋 Available Gemini Models:")
        for model in models:
            if 'gemini' in model.name.lower():
                print(f"   - {model.name}")
    except Exception as e:
        print(f"❌ Could not list models: {e}")
    
    # Test model
    try:
        model = genai.GenerativeModel('gemini-pro')
        print("\n🧪 Testing Gemini Model...")
        
        response = model.generate_content("Hello! Please respond with 'Gemini is working!'")
        print(f"✅ Model Response: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

def show_configuration():
    """Show current configuration"""
    
    print("\n⚙️  Current Configuration")
    print("=" * 30)
    
    from config import Config
    
    config = Config()
    llm_config = config.get_llm_config()
    
    print(f"Primary Model: {llm_config['primary_model']}")
    print(f"Fallback Model: {llm_config['fallback_model']}")
    print(f"Max Tokens: {llm_config['max_tokens']}")
    print(f"Gemini API Key: {'*' * 20 + '...' if llm_config['gemini_api_key'] else 'NOT SET'}")

if __name__ == "__main__":
    print("🚀 Gemini Model Status Checker")
    print("=" * 40)
    
    show_configuration()
    success = check_gemini_status()
    
    if success:
        print("\n🎉 Gemini is ready to use!")
    else:
        print("\n⚠️  Please fix the issues above before using Gemini")


