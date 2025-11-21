import os
import google.generativeai as genai
from dotenv import load_dotenv


def test_api_key():
    print("Starting API Key Test...")
    print("-" * 50)

    # Load environment variables
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")

    # Check if API key exists
    print(f"1. API Key Check:")
    if not api_key:
        print("❌ No API key found in .env file")
        return
    print("✓ API key found in .env file")
    print(f"API Key: {api_key[:12]}...")

    try:
        # Configure the API
        print("\n2. API Configuration:")
        genai.configure(api_key=api_key)
        print("✓ Successfully configured Gemini AI")

        # List available models
        print("\n3. Available Models:")
        models = genai.list_models()
        for model in models:
            print(f"✓ Found model: {model.name}")

        # Create model instance
        print("\n4. Model Initialization:")
        model = genai.GenerativeModel("gemini-2.0-flash")
        print("✓ Successfully initialized Gemini 2.0 Flash model")

        # Test simple generation
        print("\n5. Test Generation:")
        response = model.generate_content("Say 'Hello, testing Gemini AI connection!'")

        if response and response.text:
            print("✓ Successfully generated response")
            print("\nTest Response:")
            print("-" * 50)
            print(response.text)
            print("-" * 50)
            print("\n✅ All tests passed! Your API key is working correctly!")
        else:
            print("❌ Response was empty")

    except Exception as e:
        print("\n❌ Error occurred:")
        print(str(e))
        print("\nPossible solutions:")
        print("1. Make sure you've enabled the Gemini API in your Google Cloud Console")
        print("2. Check if your API key has access to the Gemini API")
        print("3. Verify your internet connection")
        print("4. Make sure you're not exceeding API quotas")


if __name__ == "__main__":
    test_api_key()
