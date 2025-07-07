# analyzer/utils/gemini.py
import google.generativeai as genai
from django.conf import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

def analyze_resume(text):
    """Send resume text to Gemini and get structured analysis."""
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = """
    Analyze this resume and return JSON with:
    - name (str)
    - email (str)
    - skills (list)
    - experience (years)
    - summary (str)
    Format: {"name": "...", "email": "...", "skills": [], "experience": float, "summary": "..."}
    Resume Text:
    """ + text[:15000]  # Limit to 15K chars (Gemini's limit)
    
    try:
        response = model.generate_content(prompt)
        return response.text  # Returns JSON string
    except Exception as e:
        print(f"Gemini Error: {e}")
        return None