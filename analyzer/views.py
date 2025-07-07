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
