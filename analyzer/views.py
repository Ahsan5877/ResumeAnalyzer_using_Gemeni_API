import json
from django.shortcuts import render
from rest_framework.views import APIView
from  rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from .models import Resume, AnalysisResume
from .serializers import ResumeSerializer, AnalysisResumeSerializer



class ResumeUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request):
        serializer = ResumeSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            
            # Extract text and save
            instance.content = extract_text_from_file(instance.file)
            instance.save()
            
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
class ResumeAnalysisView(APIView):
    def get(self, request, pk):
        try:
            # Get analysis for SPECIFIC resume
            analysis_results = AnalysisResume.objects.filter(resume_id=pk)
            serializer = AnalysisResumeSerializer(analysis_results, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Resume.DoesNotExist:
            return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)
