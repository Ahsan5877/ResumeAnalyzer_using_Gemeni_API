from django.db import models

# Create your models here.
class Resume(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    file = models.FileField(upload_to='resumes/')
    content = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    class Meta: 
        db_table = 'resume_data_table' # This specifies the name of the database table to use for this model
        managed = False

class AnalysisResume(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='analysis_results') # This creates a foreign key relationship with the Resume model
    analysis_result = models.TextField()
    analyzed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for {self.resume.name} at {self.analyzed_at}" # This will return a string representation of the analysis result
    class Meta:
        db_table = 'analysis_resume_table'
        managed = False

class ChatSession(models.Model):
    resume = models.ForeignKey('Resume', on_delete=models.CASCADE, related_name='chat_sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    topic = models.CharField(max_length=100, blank=True)
    history = models.JSONField(default=list)

    def __str__(self):
        return f"Chat about {self.resume.name} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

    def save(self, *args, **kwargs):
        if not self.topic and self.history:
            first_question = self.history[0].get('question', '')[:50]
            self.topic = f"Chat: {first_question}..." if first_question else "New Chat"
        super().save(*args, **kwargs)