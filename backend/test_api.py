import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key found: {'Yes' if api_key else 'No'}")

try:
    # Configure the API
    genai.configure(api_key=api_key)

    # Create model
    model = genai.GenerativeModel("gemini-pro")

    # Test generation
    response = model.generate_content("Say hello!")

    print("\nTest successful!")
    print("Response:", response.text)

except Exception as e:
    print("\nError occurred:")
    print(str(e))
