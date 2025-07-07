from rest_framework  import serializers
from .models import Resume, AnalysisResume

class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['id', 'file']  # Only expose necessary fields
        read_only_fields = ['id']
    
    def validate_file(self, value):
        # Add file validation
        ext = value.name.split('.')[-1].lower()
        if ext not in ['pdf', 'docx']:
            raise serializers.ValidationError("Unsupported file format")
        if value.size > 5 * 1024 * 1024:  # 5MB limit
            raise serializers.ValidationError("File too large")
        return value

class AnalysisResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisResume
        fields = '__all__'  