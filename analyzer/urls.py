from .views import ResumeUploadView, ResumeAnalysisView
from django.urls import path

urlpatterns = [
    path('upload/', ResumeUploadView.as_view(), name='resume-upload'),
    path('analyze/<int:pk>/', ResumeAnalysisView.as_view(), name='resume-analysis'),
]