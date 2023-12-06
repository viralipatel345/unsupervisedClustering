import re
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import UserModel

class SignUpForm(UserCreationForm):
    email = forms.EmailField(label="", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    first_name = forms.CharField(label="", max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(label="", max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    phone_number = forms.IntegerField(label="", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}))
    password2 = forms.CharField(label="", max_length=100, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['placeholder'] = 'User Name'
        self.fields['username'].label = ''
        self.fields['username'].help_text = '<span class="form-text text-muted"><small>150 characters max with letters, digits, dashes, and underscores only.</small></span>'

        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['password1'].label = ''
        self.fields['password1'].help_text = '<ul class="form-text text-muted small"><li>Your password can\'t be too similar to your other personal information.</li><li>Your password must contain at least 8 characters.</li><li>Your password can\'t be a commonly used password.</li><li>Your password can\'t be entirely numeric.</li></ul>'

    def clean_username(self):
        username = self.cleaned_data['username']
        if not re.match('^[a-zA-Z0-9_-]+$', username):
            raise forms.ValidationError("Username can only contain letters, digits, dashes, and underscores.")
        return username

class ModelUploadForm(forms.ModelForm):
    scores_file = forms.FileField(required=False)
    scores_text = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = UserModel
        fields = ['model_name']

    def clean(self):
        cleaned_data = super().clean()
        scores_file = cleaned_data.get('scores_file')
        scores_text = cleaned_data.get('scores_text')

        if not scores_file and not scores_text:
            raise forms.ValidationError("You must provide either a file or text scores.")

        if scores_file and scores_text:
            raise forms.ValidationError("Please provide only a file or text scores, not both.")

        return cleaned_data

class ModelTestForm(forms.Form):
    test_scores_file = forms.FileField(required=False)
    test_scores_text = forms.CharField(widget=forms.Textarea, required=False)
    model_choice = forms.ModelChoiceField(queryset=UserModel.objects.none())

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['model_choice'].queryset = UserModel.objects.filter(user=user)

    def clean(self):
        cleaned_data = super().clean()
        test_scores_file = cleaned_data.get('test_scores_file')
        test_scores_text = cleaned_data.get('test_scores_text')

        if not test_scores_file and not test_scores_text:
            raise forms.ValidationError("You must provide either a file or text scores.")

        if test_scores_file and test_scores_text:
            raise forms.ValidationError("Please provide only a file or text scores, not both.")

        return cleaned_data

