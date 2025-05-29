from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class SignUpForm(UserCreationForm):
    student_id = forms.CharField(
        label="학번",
        max_length=20,
        help_text="학번을 입력해주세요. (숫자만)"
    )
    email = forms.EmailField(
        label="학교 이메일",
        help_text="학교 이메일(@hufs.ac.kr)만 사용 가능합니다.",
    )

    class Meta:
        model = User
        fields = ('student_id', 'email', 'password1', 'password2',)

    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id')
        if not student_id.isdigit():
            raise forms.ValidationError('학번은 숫자만 입력 가능합니다.')
        if User.objects.filter(student_id=student_id).exists():
            raise forms.ValidationError('이미 사용 중인 학번입니다.')
        return student_id

    def clean_email(self):
        email = self.cleaned_data.get('email')
        domain = email.split('@')[-1]
        if domain.lower() != 'hufs.ac.kr':
            raise forms.ValidationError('학교 이메일(@hufs.ac.kr)로만 가입할 수 있습니다.')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('이미 등록된 이메일입니다.')
        return email