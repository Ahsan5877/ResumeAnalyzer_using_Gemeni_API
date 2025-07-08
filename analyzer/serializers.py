from rest_framework  import serializers
from .models import Resume, AnalysisResume

class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['id', 'name', 'email', 'file', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']
    
    def validate_file(self, value):
        if not value.name.lower().endswith(('.pdf', '.docx')):
            raise serializers.ValidationError("Only PDF and DOCX files are allowed")
        if value.size > 5 * 1024 * 1024:  # 5MB limit
            raise serializers.ValidationError("File too large (max 5MB)")
        return value

class AnalysisResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisResume
        fields = '__all__'  