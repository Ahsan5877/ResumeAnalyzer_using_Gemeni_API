from datetime import timezone
from datetime import datetime
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from .models import Resume, AnalysisResume
from .serializers import ResumeSerializer, AnalysisResumeSerializer
from .utils.extract import extract_text_from_file
from .utils.gemeni import analyze_resume, ask_about_resume

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

def chat_view(request, resume_id):
    resume = Resume.objects.get(id=resume_id)
    
    # Initialize chat history in session if it doesn't exist
    if f'chat_history_{resume_id}' not in request.session:
        request.session[f'chat_history_{resume_id}'] = []
    
    if request.method == 'POST':
        question = request.POST.get('question', '').strip()
        if question:
            # Get answer from your chatbot function
            answer = ask_about_resume(resume.content, question)
            
            # Add to chat history
            request.session[f'chat_history_{resume_id}'].append({
                'question': question,
                'answer': answer
            })
            request.session.modified = True
    
    return render(request, 'analyzer/chat.html', {
        'resume': resume,
        'chat_history': request.session.get(f'chat_history_{resume_id}', [])
    })