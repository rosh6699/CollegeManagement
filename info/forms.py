from django import forms
from .models import *


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'prof_image'
        ]

class TeacherProfileForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [
            'prof_image'
        ]
