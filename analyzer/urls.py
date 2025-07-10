from .views import ResumeUploadView, upload_view, chat_view, analyze_ats, add_ats_to_chat, get_improvements 
from django.urls import path

urlpatterns = [
    path('', upload_view, name='upload'),
    path('chat/<int:resume_id>/', chat_view, name='chat_create'),  # For new chats
    path('chat/<int:resume_id>/<int:session_id>/', chat_view, name='chat_session'),  # For existing chats
    path('upload/', ResumeUploadView.as_view(), name='resume-upload'),
    path('resume/<int:resume_id>/analyze-ats/', analyze_ats, name='analyze_ats'),
    path('resume/<int:resume_id>/add-ats-to-chat/', add_ats_to_chat, name='add_ats_to_chat'),
    path('resume/<int:resume_id>/improvements/', get_improvements, name='get_improvements'),
]