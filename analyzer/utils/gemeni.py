# import os
# import django
# import sys

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# # ✅ Step 2: Set settings module
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_analyzer.settings')

# # ✅ Step 3: Setup Django
# django.setup()
# analyzer/utils/gemini.py
import google.generativeai as genai
from django.conf import settings
import json

genai.configure(api_key=settings.GEMINI_API_KEY)

def analyze_resume(text):
    """Analyze resume text using Gemini and return JSON string"""
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = """
    Analyze this resume and return STRICT JSON format with:
    - name (string)
    - email (string)
    - skills (list)
    - experience (float)
    - summary (string)
    - education (list)
    - projects (list)
    
    Example Output:
    {
        "name": "John Doe",
        "email": "john@example.com",
        "skills": ["Python", "Django"],
        "experience": 3.5,
        "summary": "Experienced developer...",
        "education": ["MS in Computer Science"],
        "projects": ["Built resume analyzer"]
    }
    
    Resume Text:
    """ + text[:15000]  # Gemini token limit
    
    try:
        response = model.generate_content(prompt)
        return response.text  # Return as JSON string
    except Exception as e:
        print(f"Gemini Error: {e}")
        return json.dumps({"error": str(e)})
def format_chat_history(chat_history):
    return "CHAT HISTORY:\n" + "\n".join(chat_history) if chat_history else ""

def ask_about_resume(resume_text, question, chat_history=None):
    """
    Enhanced resume Q&A with robust error handling
    """
    try:
        # 1. Input validation
        if not resume_text:
            return "Error: No resume text provided for analysis"
            
        if not isinstance(resume_text, str):
            resume_text = str(resume_text)  # Force conversion if needed

        # 2. Safe content truncation
        resume_content = resume_text[:15000] if len(resume_text) > 15000 else resume_text
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # 3. Build chat history section safely
        history_section = ""
        if chat_history:
            try:
                history_section = "CHAT HISTORY:\n" + "\n".join(str(msg) for msg in chat_history) + "\n\n"
            except Exception as e:
                print(f"Error formatting chat history: {e}")

        # 4. Construct prompt
        prompt = f"""
        ROLE: You are a professional resume analyst. Answer questions strictly based on the provided resume.

        RESUME CONTENT:
        {resume_content}

        CURRENT QUESTION:
        {question}

        {history_section}
        STRICT RESPONSE FORMATTING RULES:
        1. ALWAYS format lists using Markdown-style bullet points with asterisks (*)
        2. For projects/experience, use this EXACT format:
        * **Project Name:** Description (Technologies: Tech1, Tech2, Tech3)
        3. For skills/technologies, use:
        * **Category:** Item1, Item2, Item3
        4. Put each item on its own line
        5. Never use HTML tags in responses
        6. Separate sections with blank lines

        EXAMPLE FORMAT:
        Ahsan Iqbal's projects include:

        * **Project 1:** Description (Technologies: A, B)
        * **Project 2:** Description (Technologies: C, D)

        MANDATORY INSTRUCTIONS:
        1. If information isn't in resume: "This information is not in the resume"
        2. For skills questions: Provide specific examples in bullet lists
        3. Never invent information
        4. Keep answers concise but properly formatted
        5. Use **bold** for categories/subcategories
        """

        generation_config = {
            "temperature": 0.3,  # Keep low for factual responses
            "top_p": 0.7,
            "top_k": 40,
            "max_output_tokens": 512,
        }

        # 6. Execute API call
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
        )
        
        return response.text.strip() if response.text else "No response generated"
        
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "I encountered an error processing your request. Please try again."