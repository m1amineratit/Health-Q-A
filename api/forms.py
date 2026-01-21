from django import forms
from .models import Answer

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['answer_text']
        widgets = {
            'answer_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Write your answer here...'
            })
        }