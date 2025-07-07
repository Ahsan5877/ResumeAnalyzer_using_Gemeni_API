import json
from django.shortcuts import render
from rest_framework.views import APIView
from  rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from .models import Resume, AnalysisResume
from .serializers import ResumeSerializer, AnalysisResumeSerializer
from .gemeni import analyze_resume
from .utils import extract_text_from_file
class ResumeUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)  
    def post(self, request):
        serializer = ResumeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ResumeAnalysisView(APIView):
    def get(self, request, pk):
        try:
            resume = Resume.objects.get(pk=pk) # Fetch the resume by primary key
            analysis_results = Resume.objects.all()
            serializer = AnalysisResumeSerializer(analysis_results, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Resume.DoesNotExist:
            return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, pk):
        try:
            resume = Resume.objects.get(pk=pk)
            
            # Extract text (if not already done)
            if not resume.content:
                resume.content = extract_text_from_file(resume.file)
                resume.save()
            
            # Call Gemini API
            analysis_raw = analyze_resume(resume.content)
            analysis_data = json.loads(analysis_raw)  # Parse JSON
            
            # Save to AnalysisResume model
            analysis = AnalysisResume.objects.create(
                resume=resume,
                analysis_result=analysis_data  # Store as JSON
            )
            
            return Response(analysis_data, status=200)
            
        except Resume.DoesNotExist:
            return Response({"error": "Resume not found"}, status=404)
        except json.JSONDecodeError:
            return Response({"error": "Failed to analyze resume"}, status=500)