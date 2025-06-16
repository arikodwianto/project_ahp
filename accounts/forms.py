from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

from django import forms
from .models import CustomUser

class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Konfirmasi Password", widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'bidang']

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            self.add_error("password2", "Password tidak cocok.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


from django import forms
from .models import Kegiatan, SubKegiatan, Rekening

class KegiatanForm(forms.ModelForm):
    class Meta:
        model = Kegiatan
        fields = ['bidang', 'kode_kegiatan', 'nama_kegiatan']
        widgets = {
            'bidang': forms.Select(attrs={'class': 'form-control'}),
            'kode_kegiatan': forms.TextInput(attrs={'class': 'form-control'}),
            'nama_kegiatan': forms.TextInput(attrs={'class': 'form-control'}),
        }

class SubKegiatanForm(forms.ModelForm):
    class Meta:
        model = SubKegiatan
        # Hilangkan 'kegiatan' dari field, karena nanti di-set di view lewat hidden input
        fields = ['kode_sub_kegiatan', 'nama_sub_kegiatan']
        widgets = {
            'kode_sub_kegiatan': forms.TextInput(attrs={'class': 'form-control'}),
            'nama_sub_kegiatan': forms.TextInput(attrs={'class': 'form-control'}),
        }

    # Hilangkan __init__ karena tidak perlu filter bidang/kegiatan lagi

class RekeningForm(forms.ModelForm):
    class Meta:
        model = Rekening
        # Hilangkan 'sub_kegiatan' dari field, diset juga di view
        fields = ['kode_rekening', 'nama_rekening']
        widgets = {
            'kode_rekening': forms.TextInput(attrs={'class': 'form-control'}),
            'nama_rekening': forms.TextInput(attrs={'class': 'form-control'}),
        }
from .models import PenggunaanBelanja

class PenggunaanBelanjaForm(forms.ModelForm):
    class Meta:
        model = PenggunaanBelanja
        # 'rekening' tidak dimasukkan di sini, diset di view melalui hidden input
        fields = ['nama_penggunaan', 'jumlah']
        widgets = {
            'nama_penggunaan': forms.TextInput(attrs={'class': 'form-control'}),
            'jumlah': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

from django import forms
from .models import Kriteria

SKALA_PERBANDINGAN = [
    (1, 'Sama penting'),
    (2, 'Sedikit lebih penting'),
    (3, 'Lebih penting'),
    (4, 'Lebih dari cukup penting'),
    (5, 'Sangat penting'),
    (6, 'Antara sangat dan sangat sekali penting'),
    (7, 'Sangat sekali penting'),
    (8, 'Antara sangat sekali dan ekstrim'),
    (9, 'Ekstrim penting'),
]

class KriteriaForm(forms.ModelForm):
    class Meta:
        model = Kriteria
        fields = ['nama']
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Kriteria'})
        }

class PerbandinganKriteriaForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        kriteria = Kriteria.objects.all()

        for i in range(len(kriteria)):
            for j in range(i+1, len(kriteria)):
                field_name = f'kriteria_{kriteria[i].id}_vs_{kriteria[j].id}'
                label_left = kriteria[i].nama
                label_right = kriteria[j].nama
                self.fields[field_name] = forms.ChoiceField(
                    label=f"{label_left} vs {label_right}",
                    choices=SKALA_PERBANDINGAN,
                    widget=forms.Select(attrs={'class': 'form-control'}),
                )
                # Simpan label kiri dan kanan sebagai atribut tambahan
                self.fields[field_name].label_left = label_left
                self.fields[field_name].label_right = label_right

from django import forms
from .models import Kriteria, PenggunaanBelanja

SKALA_PERBANDINGAN = [
    (1, 'Sama penting'),
    (2, 'Sedikit lebih penting'),
    (3, 'Lebih penting'),
    (4, 'Lebih dari cukup penting'),
    (5, 'Sangat penting'),
    (6, 'Antara sangat dan sangat sekali penting'),
    (7, 'Sangat sekali penting'),
    (8, 'Antara sangat sekali dan ekstrim'),
    (9, 'Ekstrim penting'),
]

class PerbandinganAlternatifForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        kriteria_list = Kriteria.objects.all()
        alternatif_list = PenggunaanBelanja.objects.all()

        for kriteria in kriteria_list:
            for i in range(len(alternatif_list)):
                for j in range(i + 1, len(alternatif_list)):
                    field_name = f'kriteria_{kriteria.id}_alt_{alternatif_list[i].id}_vs_{alternatif_list[j].id}'
                    label_left = alternatif_list[i].nama_penggunaan
                    label_right = alternatif_list[j].nama_penggunaan
                    self.fields[field_name] = forms.ChoiceField(
                        label=f"{label_left} vs {label_right}",
                        choices=SKALA_PERBANDINGAN,
                        widget=forms.Select(attrs={
                            'class': 'form-control',
                        }),
                    )
                    self.fields[field_name].label_left = label_left
                    self.fields[field_name].label_right = label_right
                    self.fields[field_name].kriteria_nama = kriteria.nama




