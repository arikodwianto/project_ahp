from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.conf import settings
from django.utils.timezone import now

from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('kepala_dinas', 'Kepala Dinas'),
        ('admin_bidang', 'Admin Bidang'),
        ('jf_perencana', 'JF Perencana'),
    ]

    BIDANG_CHOICES = [
        ('bina_konstruksi', 'Bina Konstruksi'),
        ('sumber_daya_air', 'Sumber Daya Air'),
        ('penataan_ruang', 'Penataan Ruang'),
        ('keuangan', 'Keuangan'),
        ('umum_kepegawaian', 'Umum & Kepegawaian'),
        ('program_cipta_karya', 'Program Cipta Karya'),
        ('binta_marga', 'Binta Marga'),
        ('upt_air_minum', 'UPT Air Minum'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='kepala_dinas')
    bidang = models.CharField(max_length=50, choices=BIDANG_CHOICES, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    
# models.py
class Kegiatan(models.Model):
    BIDANG_CHOICES = [
        ('bina_konstruksi', 'Bina Konstruksi'),
        ('sumber_daya_air', 'Sumber Daya Air'),
        ('penataan_ruang', 'Penataan Ruang'),
        ('keuangan', 'Keuangan'),
        ('umum_kepegawaian', 'Umum & Kepegawaian'),
        ('program_cipta_karya', 'Program Cipta Karya'),
        ('binta_marga', 'Binta Marga'),
        ('upt_air_minum', 'UPT Air Minum'),
    ]

    bidang = models.CharField(max_length=100, choices=BIDANG_CHOICES)
    kode_kegiatan = models.CharField(max_length=20, unique=True)
    nama_kegiatan = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.kode_kegiatan} - {self.nama_kegiatan}"
class SubKegiatan(models.Model):
    kegiatan = models.ForeignKey(Kegiatan, on_delete=models.CASCADE, related_name='sub_kegiatans')
    kode_sub_kegiatan = models.CharField(max_length=20)
    nama_sub_kegiatan = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.kode_sub_kegiatan} - {self.nama_sub_kegiatan}"
class Rekening(models.Model):
    sub_kegiatan = models.ForeignKey(SubKegiatan, on_delete=models.CASCADE, related_name='rekenings')
    kode_rekening = models.CharField(max_length=20)
    nama_rekening = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.kode_rekening} - {self.nama_rekening}"

class PenggunaanBelanja(models.Model):
    rekening = models.ForeignKey(Rekening, on_delete=models.CASCADE, related_name='penggunaan_belanjas')
    nama_penggunaan = models.CharField(max_length=200)
    jumlah = models.DecimalField(max_digits=14, decimal_places=2)

    def __str__(self):
        return f"{self.nama_penggunaan} - {self.jumlah}"

from django.db import models

class Kriteria(models.Model):
    nama = models.CharField(max_length=100)

    def __str__(self):
        return self.nama

class PerbandinganKriteria(models.Model):
    kriteria_1 = models.ForeignKey(Kriteria, related_name='perbandingan_kriteria_1', on_delete=models.CASCADE)
    kriteria_2 = models.ForeignKey(Kriteria, related_name='perbandingan_kriteria_2', on_delete=models.CASCADE)
    nilai = models.FloatField()

    def __str__(self):
        return f"{self.kriteria_1} vs {self.kriteria_2} = {self.nilai}"


class BobotKriteria(models.Model):
    kriteria = models.ForeignKey(Kriteria, on_delete=models.CASCADE)
    nilai_bobot = models.FloatField()

    def __str__(self):
        return f"{self.kriteria.nama}: {self.nilai_bobot:.4f}"
    

 # sesuaikan jika kamu meletakkan model Kriteria di file terpisah

class PerbandinganAlternatif(models.Model):
    kriteria = models.ForeignKey(Kriteria, on_delete=models.CASCADE)
    alternatif_1 = models.ForeignKey(PenggunaanBelanja, on_delete=models.CASCADE, related_name='alt1')
    alternatif_2 = models.ForeignKey(PenggunaanBelanja, on_delete=models.CASCADE, related_name='alt2')
    nilai = models.FloatField()

    def __str__(self):
        return f"{self.kriteria.nama}: {self.alternatif_1} vs {self.alternatif_2} = {self.nilai}"

from django.db import models
from django.utils import timezone

class PersetujuanPenggunaanBelanja(models.Model):
    # Simpan data snapshot dari PenggunaanBelanja
    penggunaan_belanja_id = models.IntegerField()  # ID asli untuk referensi (optional)
    nama_penggunaan = models.CharField(max_length=200)
    jumlah = models.DecimalField(max_digits=14, decimal_places=2)
    
    # Info dari relasi Rekening > SubKegiatan > Kegiatan (salin juga)
    kode_rekening = models.CharField(max_length=20)
    nama_rekening = models.CharField(max_length=100)
    
    kode_sub_kegiatan = models.CharField(max_length=20)
    nama_sub_kegiatan = models.CharField(max_length=100)
    
    kode_kegiatan = models.CharField(max_length=20)
    nama_kegiatan = models.CharField(max_length=100)
    bidang = models.CharField(max_length=100)
    
    disetujui = models.BooleanField(default=False)
    ditolak = models.BooleanField(default=False)
    tanggal_persetujuan = models.DateTimeField(null=True, blank=True)

    def set_approved(self):
        self.disetujui = True
        self.ditolak = False
        self.tanggal_persetujuan = timezone.now()
        self.save()

    def set_rejected(self):
        self.disetujui = False
        self.ditolak = True
        self.tanggal_persetujuan = timezone.now()
        self.save()

    def __str__(self):
        status = "Disetujui" if self.disetujui else ("Ditolak" if self.ditolak else "Belum Disetujui")
        return f"{self.nama_penggunaan} ({status})"

from django.db import models
from django.utils import timezone

class DPA(models.Model):
    penggunaan_belanja = models.ForeignKey('PenggunaanBelanja', on_delete=models.CASCADE, related_name='dpa_entries')
    status = models.CharField(max_length=20, choices=[('disetujui', 'Disetujui'), ('ditolak', 'Ditolak')], default='disetujui')
    tanggal_persetujuan = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"DPA untuk {self.penggunaan_belanja.nama_penggunaan} - Status: {self.status}"





