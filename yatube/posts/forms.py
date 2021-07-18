from django import forms
from django.forms.widgets import Textarea

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['group', 'text', 'image']
        widgets = {
            'text': Textarea(
                attrs={
                    'placeholder': 'Введите текст'}
            )
        }
        error_messages = {
            'text': {
                'required': 'Пост обязательно должен '
                            'содержать текст!'
            }
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': Textarea(
                attrs={
                    'placeholder': 'Введите текст комментария'}
            )
        }
