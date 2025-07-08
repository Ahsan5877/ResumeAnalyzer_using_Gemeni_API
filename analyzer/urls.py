from .views import ResumeUploadView, upload_view, chat_view
from django.urls import path

urlpatterns = [
    path('', upload_view, name='upload'),
    path('chat/<int:resume_id>/', chat_view, name='chat_create'),  # For new chats
    path('chat/<int:resume_id>/<int:session_id>/', chat_view, name='chat_session'),  # For existing chats
    path('upload/', ResumeUploadView.as_view(), name='resume-upload'),
]