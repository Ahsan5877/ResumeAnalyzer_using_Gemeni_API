from rest_framework  import serializers
from .models import Resume, AnalysisResume

class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = '__all__'

class AnalysisResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisResume
        fields = '__all__'  