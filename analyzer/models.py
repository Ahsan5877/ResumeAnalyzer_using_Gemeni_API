from django.db import models

# Create your models here.
class Resume(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    file = models.FileField(upload_to='resumes/')
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