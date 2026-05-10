from django import forms
from .models import ClassMessage

class ClassMessageForm(forms.ModelForm):
    class Meta:
        model = ClassMessage
        fields = ['text', 'file', 'image']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Введите сообщение...',
                'id': 'message-input',
                'style': 'resize: none;'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'id': 'file-input'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'id': 'image-input',
                'accept': 'image/*'
            }),
        }