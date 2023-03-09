from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].widget.attrs['placeholder'] = (
            'Здесь Вы можете оставить Вашу запись'
        )
        self.fields['group'].empty_label = (
            'Пожалуйста, выберите сообщество'
        )

    class Meta:
        model = Post
        fields = (
            "text",
            "group",
            "image",
        )


class CommentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].widget.attrs['placeholder'] = (
            'Здесь Вы можете оставить комментарий'
        )

    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст',
        }
        help_texts = {
            'text': 'Текст нового комментария',
        }
