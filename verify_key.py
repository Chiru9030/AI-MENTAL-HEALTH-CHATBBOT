import google.generativeai as genai
import os

# The key provided by the user
KEY = "AIzaSyBg1oDlPfpHhAHhyWDTRSMVBrf-Zopbjk0"

print(f"Testing API Key: {KEY}")

genai.configure(api_key=KEY)
model = genai.GenerativeModel('gemini-pro')

model = genai.GenerativeModel('gemini-2.0-flash')

try:
    response = model.generate_content("Hello, are you working?")
    print("SUCCESS! Response received:")
    print(response.text)
except Exception as e:
    print("FAILED. Error details:")
    print(e)
