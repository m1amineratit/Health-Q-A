from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator
from rest_framework import serializers
from .models import Question, Answer

class RegisterSerializer(serializers.Serializer):
    speciality = serializers.ChoiceField(
        choices=[
            ('eyes', 'Ophthalmologist'),
            ('heart', 'Cardiologist'),
            ('generaliste', 'General Practitioner'),
            ('dentist', 'Dentist'),
            ('pediatrics', 'Pediatrician'),
            ('neurology', 'Neurologist'),
        ]
    )
    username = serializers.CharField(
        max_length=150,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(write_only=True, min_length=6)
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)


class AnswerSerializer(serializers.ModelSerializer):
    answered_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Answer
        fields = ['id', 'question', 'answer_text', 'answered_by', 'answered_by_name', 'created_at', 'updated_at', 'answer_sent', 'views_count']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_answered_by_name(self, obj):
        return obj.answered_by.get_full_name() if obj.answered_by else None


class QuestionSerializer(serializers.ModelSerializer):
    answer = AnswerSerializer(read_only=True)
    doctor_name = serializers.SerializerMethodField()
    answered_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = ['id', 'doctor', 'doctor_name', 'category', 'instagram_username', 'instagram_user_id', 
                  'question_text', 'created_at', 'status', 'answer', 'views_count']
        read_only_fields = ['created_at', 'id']
    
    def get_doctor_name(self, obj):
        return obj.doctor.get_full_name() if obj.doctor else None
    
    def get_answered_by_name(self, obj):
        return obj.answer.answered_by.get_full_name() if hasattr(obj, 'answer') and obj.answer.answered_by else None


class QuestionDetailSerializer(serializers.ModelSerializer):
    answer = AnswerSerializer(read_only=True)
    doctor_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = ['id', 'doctor', 'doctor_name', 'category', 'instagram_username', 'instagram_user_id', 
                  'question_text', 'created_at', 'status', 'answer', 'views_count']
        read_only_fields = ['created_at', 'id']
    
    def get_doctor_name(self, obj):
        return obj.doctor.get_full_name() if obj.doctor else None


class CreateAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['question', 'answer_text', 'answer_sent']
        extra_kwargs = {
            'question': {'required': True}
        }
