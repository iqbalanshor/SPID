from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from .models import CustomUser, Pengaduan

class RegisterForm(UserCreationForm):
    nama_lengkap = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Masukkan nama lengkap Anda',
            'class': 'form-control-input'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'contoh@email.com',
            'class': 'form-control-input'
        })
    )
    nomor_hp = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': '08xxxxxxxxxx',
            'class': 'form-control-input'
        })
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Pilih username unik',
            'class': 'form-control-input',
            'autocomplete': 'off'
        })
    )
    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Masukkan kata sandi',
            'class': 'form-control-input',
            'autocomplete': 'new-password'
        })
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'nama_lengkap', 'email', 'nomor_hp')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Email ini sudah terdaftar.")
        return email

class LoginForm(forms.Form):
    username_or_email = forms.CharField(
        label="Username atau Email",
        widget=forms.TextInput(attrs={
            'placeholder': 'Masukkan username/email',
            'class': 'form-control-input'
        })
    )
    password = forms.CharField(
        label="Kata Sandi",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Masukkan kata sandi',
            'class': 'form-control-input'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    captcha_answer = forms.IntegerField(
        required=True,
        error_messages={
            'required': 'Silakan selesaikan tantangan captcha.',
            'invalid': 'Tantangan captcha harus diisi dengan angka.'
        },
        widget=forms.HiddenInput(attrs={'id': 'captcha-answer-field'})
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        username_or_email = cleaned_data.get('username_or_email')
        password = cleaned_data.get('password')
        captcha_answer = cleaned_data.get('captcha_answer')

        # Check captcha first
        if self.request:
            correct_answer = self.request.session.get('captcha_result')
            if correct_answer is None or captcha_answer != correct_answer:
                self.add_error('captcha_answer', "Hasil captcha salah. Silakan coba lagi.")

        if username_or_email and password:
            # Check if username_or_email is an email
            user = None
            if '@' in username_or_email:
                try:
                    user_obj = CustomUser.objects.get(email=username_or_email)
                    username = user_obj.username
                except CustomUser.DoesNotExist:
                    username = username_or_email
            else:
                username = username_or_email

            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError("Username/Email atau password salah.")
            
            # Check if normal user logins through port 8000 or if admin logs in through port 8001
            # We want to make sure normal users cannot access admin site and staff cannot access user site if needed
            cleaned_data['user'] = user
        return cleaned_data

class PengaduanForm(forms.ModelForm):
    class Meta:
        model = Pengaduan
        fields = ['kategori', 'lokasi', 'deskripsi', 'foto', 'latitude', 'longitude']
        widgets = {
            'kategori': forms.Select(attrs={
                'class': 'form-control-input select-input'
            }),
            'lokasi': forms.TextInput(attrs={
                'placeholder': 'Masukkan lokasi detail kejadian (jalan, RT/RW, kecamatan)',
                'class': 'form-control-input'
            }),
            'deskripsi': forms.Textarea(attrs={
                'placeholder': 'Jelaskan secara detail mengenai kerusakan infrastruktur yang dilaporkan...',
                'rows': 4,
                'class': 'form-control-input textarea-input'
            }),
            'foto': forms.FileInput(attrs={
                'class': 'form-file-input',
                'accept': 'image/*'
            }),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['nama_lengkap', 'email', 'nomor_hp', 'foto_profil']
        widgets = {
            'nama_lengkap': forms.TextInput(attrs={
                'class': 'form-control-input',
                'placeholder': 'Masukkan nama lengkap'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control-input',
                'placeholder': 'contoh@email.com'
            }),
            'nomor_hp': forms.TextInput(attrs={
                'class': 'form-control-input',
                'placeholder': '08xxxxxxxxxx'
            }),
            'foto_profil': forms.FileInput(attrs={
                'class': 'form-file-input',
                'accept': 'image/*'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Email ini sudah terdaftar.")
        return email
