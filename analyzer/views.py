from venv import logger
import logging
from django.forms import ValidationError
from markdown import markdown
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from .models import Resume, AnalysisResume, ChatSession, JobDescription
from .serializers import ResumeSerializer, AnalysisResumeSerializer
from .utils.extract import extract_text_from_file
from .utils.gemeni import analyze_resume, ask_about_resume
from datetime import datetime
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.views.decorators.http import require_POST
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)

class ResumeUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        if 'file' not in request.FILES:
            return Response({"error": "No file uploaded"}, status=400)

        serializer = ResumeSerializer(data=request.data)

        if serializer.is_valid():
            resume = serializer.save()

            # 🔍 Extract text from the uploaded resume file
            try:
                file_path = resume.file.path
                content = extract_text_from_file(file_path)

                if content:
                    resume.content = content
                    resume.save()

                    # Also store in AnalysisResume
                    AnalysisResume.objects.create(
                        resume=resume,
                        analysis_result=content
                    )
                    # save contents to a .txt file
                    with open(f'{file_path}.txt', 'w', encoding='utf-8') as f:
                        f.write(content)
                else:
                    resume.content = "No content extracted"
                    resume.save()

            except Exception as e:
                print(f"[Text Extraction Error] {e}")
                resume.content = "Extraction failed"
                resume.save()

            return Response({
                "id": resume.id,
                "name": resume.name,
                "email": resume.email,
                "file_url": resume.file.url,
                "content": resume.content,
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=400)

def upload_view(request):
    if request.method == 'POST':
        try:
            # 1. Save resume base info
            resume = Resume.objects.create(
                name=request.POST.get('name', '').strip() or None,
                email=request.POST.get('email', '').strip() or None,
                file=request.FILES['file']
            )

            # 2. Extract text from file
            file_content = extract_text_from_file(resume.file.path)

            if file_content:
                # Save to Resume model
                resume.content = file_content
                resume.save()

                # Save to AnalysisResume model
                AnalysisResume.objects.create(
                    resume=resume,
                    analysis_result=file_content
                )
                # Optionally write raw text to a .txt file
                try:
                    with open(f'{resume.file.path}.txt', 'w', encoding='utf-8') as f:
                        f.write(file_content)
                except Exception as e:
                    print(f"[Warning] Could not write .txt backup: {str(e)}")

            else:
                print("[Error] extract_text_from_file returned empty result.")
                resume.content = "Text extraction failed"
                resume.save()

        except Exception as e:
            print(f"[Upload Error] {str(e)}")
            return render(request, 'analyzer/upload.html', {'error': str(e)})

        return redirect('chat', resume_id=resume.id)

    return render(request, 'analyzer/upload.html')

def chat_view(request, resume_id, session_id=None):
    # Get resume object or return 404
    resume = get_object_or_404(Resume, id=resume_id)
    
    # Handle new chat creation
    if 'new_chat' in request.GET:
        new_session = ChatSession.objects.create(resume=resume)
        return redirect('chat_session', resume_id=resume.id, session_id=new_session.id)
    
    # Get or create session
    if session_id:
        current_session = get_object_or_404(ChatSession, id=session_id, resume=resume)
    else:
        current_session = ChatSession.objects.filter(resume=resume).last()
        if not current_session:
            current_session = ChatSession.objects.create(resume=resume)
        return redirect('chat_session', resume_id=resume.id, session_id=current_session.id)
    
    # Handle POST requests (both chat messages and JD analysis)
    if request.method == 'POST':
        # JD Analysis Request
        if 'jd_text' in request.POST:
            jd_text = request.POST.get('jd_text', '').strip()
            if not jd_text:
                messages.error(request, "Please enter a job description")
                return redirect('chat_session', resume_id=resume.id, session_id=current_session.id)
            
            try:
                # Create JobDescription record
                jd = JobDescription.objects.create(
                    resume=resume,
                    text=jd_text
                )
                
                # Get analysis results (replace with your actual analysis logic)
                ats_results = {
                    'score': 75,  # Example value - replace with real analysis
                    'improvements': [
                        "Add missing keyword: 'Python' in skills section",
                        "Quantify achievements (e.g., 'Improved performance by 30%')"
                    ],
                    'matched_keywords': ["Python", "SQL"],
                    'missing_keywords': ["Docker", "AWS"],
                    'jd_id': jd.id  # Include JD ID for reference
                }
                
                # Save results
                jd.analysis_results = ats_results
                jd.save()
                
                # Store in session for display
                request.session['ats_results'] = ats_results
                
                # Add to chat history
                chat_message = f"**ATS Analysis Result:** {ats_results['score']}% match\n\n"
                chat_message += "**Key Improvements:**\n- " + "\n- ".join(ats_results['improvements'])
                
                current_session.history.append({
                    'question': "Job Description Analysis",
                    'answer': mark_safe(markdown(chat_message)),
                    'timestamp': datetime.now().isoformat()
                })
                current_session.save()
                
                messages.success(request, "Analysis completed successfully")
                
            except Exception as e:
                logger.error(f"JD Analysis Error: {str(e)}")
                messages.error(request, "Analysis failed. Please try again.")
            
            return redirect('chat_session', resume_id=resume.id, session_id=current_session.id)
        
        # Normal Chat Message
        question = request.POST.get('question', '').strip()
        if question:
            try:
                answer = ask_about_resume(resume.content, question)
                formatted_answer = mark_safe(markdown(answer))
                
                current_session.history.append({
                    'question': question,
                    'answer': formatted_answer,
                    'timestamp': datetime.now().isoformat()
                })
                
                if not current_session.topic:
                    current_session.topic = f"Chat: {question[:50]}..." if question else "New Chat"
                
                current_session.save()
                
            except Exception as e:
                logger.error(f"Chat Error: {str(e)}")
                messages.error(request, "Failed to process your question. Please try again.")
            
            return redirect('chat_session', resume_id=resume.id, session_id=current_session.id)
    
    # Prepare context for template
    context = {
        'resume': resume,
        'current_session': current_session,
        'chat_sessions': ChatSession.objects.filter(resume=resume).order_by('-created_at'),
        'ats_results': request.session.pop('ats_results', None),
        'recent_jds': JobDescription.objects.filter(resume=resume).order_by('-created_at')[:5]
    }
    
    return render(request, 'analyzer/chat.html', context)


def analyze_ats(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id)
    current_session = ChatSession.objects.filter(resume=resume).last() or ChatSession.objects.create(resume=resume)
    
    if request.method == 'POST':
        jd_text = request.POST.get('jd_text', '').strip()
        if not jd_text:
            messages.error(request, "Please enter a job description")
            return redirect('chat_session', resume_id=resume.id, session_id=current_session.id)
        
        try:
            # Configure Gemini API
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            # Enhanced prompt with strict formatting requirements
            prompt = f"""
            Analyze this resume against the job description for ATS compatibility.
            Provide feedback in this EXACT format:

            ```json
            {{
                "score": 85,
                "improvements": [
                    "Add 2-3 projects using Django",
                    "Include AWS experience in skills",
                    "Quantify achievements with metrics"
                ],
                "matched_keywords": ["Python", "SQL", "JavaScript"],
                "missing_keywords": ["Django", "AWS", "REST APIs"]
            }}
            ```

            RULES:
            1. Keep improvements as bullet points (max 8 words each)
            2. List exactly 5 matched and 5 missing keywords
            3. Keywords must be single words or short phrases (2-3 words max)
            4. Never use the same keyword in both matched and missing lists

            RESUME:
            {resume.content[:3000]}

            JOB DESCRIPTION:
            {jd_text[:3000]}
            """
            
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean the response
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            ats_results = json.loads(response_text)
                    
            score = ats_results['score']
            color = '#2ecc71' if score > 75 else '#e67e22' if score > 50 else '#e74c3c'
            improvements = "".join(f"<li>{imp}</li>" for imp in ats_results['improvements'])  # HTML list

            chat_message = (
                "<h2 style='color:#2980b9;'>📊 ATS Compatibility Analysis</h2>"
                f"<p><strong>Match Score:</strong> <span style='color:{color}; font-weight:bold;'>{score}%</span></p>"

                "<h3>🔧 Key Improvements</h3>"
                f"<ul>{improvements}</ul>"

                "<h3>🔑 Keyword Analysis</h3>"
                "<table style='width:100%; border-collapse:collapse; margin:10px 0;'>"
                "<thead style='background-color:#f2f2f2;'>"
                "<tr>"
                "<th style='padding:8px; border:1px solid #ddd; text-align:left;'>✅ Matched Keywords</th>"
                "<th style='padding:8px; border:1px solid #ddd; text-align:left;'>❌ Missing Keywords</th>"
                "</tr>"
                "</thead>"
                # You'll need to loop matched/missing keywords and add <tr> rows below this in your final output
                "<tbody>"
                )

               # Determine color based on score         
            # Add keyword rows
            for i in range(5):
                matched = ats_results['matched_keywords'][i] if i < len(ats_results['matched_keywords']) else ""
                missing = ats_results['missing_keywords'][i] if i < len(ats_results['missing_keywords']) else ""
                chat_message += (
                    f"<tr>"
                    f"<td style='padding:8px; border:1px solid #ddd;'>{matched}</td>"
                    f"<td style='padding:8px; border:1px solid #ddd;'>{missing}</td>"
                    f"</tr>"
                )
            
            chat_message += "</table>"
            
            # Save results
            jd = JobDescription.objects.create(
                resume=resume,
                text=jd_text,
                analysis_results=ats_results
            )
            
            current_session.history.append({
                'question': "Job Description Analysis",
                'answer': mark_safe(chat_message),  # Using mark_safe for HTML
                'timestamp': datetime.now().isoformat()
            })
            current_session.save()
            
            request.session['ats_results'] = ats_results
            messages.success(request, "Analysis completed successfully")
            
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}\nResponse: {response_text if 'response_text' in locals() else ''}")
            messages.error(request, "Analysis failed. Please try again with a different JD.")
    
    return redirect('chat_session', resume_id=resume.id, session_id=current_session.id)

def add_ats_to_chat(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id)
    current_session = ChatSession.objects.filter(resume=resume).last()
    
    if request.method == 'POST':
        score = request.POST.get('score')
        improvements = request.POST.get('improvements', '').split('|||')
        
        chat_message = f"ATS Analysis Result: {score}% match\n\n"
        chat_message += "Key Improvements:\n- " + "\n- ".join(improvements)
        
        current_session.history.append({
            'question': "Job Description Analysis",
            'answer': mark_safe(markdown(chat_message)),
            'timestamp': datetime.now().isoformat()
        })
        current_session.save()
        messages.success(request, "Analysis added to chat history")
    
    return redirect('chat_session', resume_id=resume.id, session_id=current_session.id)
