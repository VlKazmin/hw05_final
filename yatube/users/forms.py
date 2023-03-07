from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django import forms

User = get_user_model()


#  создадим собственный класс для формы регистрации
#  сделаем его наследником предустановленного класса UserCreationForm
class CreationForm(UserCreationForm):
    first_name = forms.CharField(
        label=("Имя"),
        max_length=12,
        min_length=4,
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Введите ваше имя."}
        ),
    )
    last_name = forms.CharField(
        label=("Фамилия"),
        max_length=12,
        min_length=4,
        required=True,
        widget=(
            forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Введите вашу фамилию",
                }
            )
        ),
    )

    email = forms.EmailField(
        max_length=50,
        widget=(
            forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Укажите email",
                }
            )
        ),
    )

    class Meta(UserCreationForm.Meta):
        # укажем модель, с которой связана создаваемая форма
        model = User
        # укажем, какие поля должны быть видны в форме и в каком порядке
        fields = ("first_name", "last_name", "username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
