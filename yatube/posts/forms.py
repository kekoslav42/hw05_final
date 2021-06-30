from django import forms

from .models import Comment, Post


# Добавил labels, вроде как почитал полезно
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['group', 'text', 'image']
        widgets = {
            'text': forms.Textarea()
        }
        labels = {
            'text': 'Текст',
            'group': 'Группа',
            'image': 'Изображение'
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea()
        }
        labels = {
            'text': 'Текст'
        }
