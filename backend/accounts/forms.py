from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

Account = get_user_model()

class RegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Account
        fields = ['username', 'email', 'password1', 'password2']
