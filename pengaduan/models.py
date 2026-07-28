from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class CustomUser(AbstractUser):
    nama_lengkap = models.CharField(max_length=150, verbose_name="Nama Lengkap")
    nomor_hp = models.CharField(max_length=20, verbose_name="Nomor HP")
    foto_profil = models.ImageField(upload_to='profil/', blank=True, null=True, verbose_name="Foto Profil")

    def __str__(self):
        return f"{self.nama_lengkap} (@{self.username})"

class Pengaduan(models.Model):
    KATEGORI_CHOICES = [
        ('Jalan', 'Kerusakan Jalan'),
        ('Jembatan', 'Kerusakan Jembatan'),
        ('Penerangan', 'Lampu Penerangan Jalan'),
        ('Fasilitas', 'Fasilitas Umum Lainnya'),
        ('Irigasi', 'Saluran Air / Irigasi'),
        ('Lainnya', 'Lain-lain'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Diverifikasi', 'Diverifikasi'),
        ('Diproses', 'Diproses'),
        ('Selesai', 'Selesai'),
        ('Ditolak', 'Ditolak'),
    ]

    URGENSI_CHOICES = [
        ('Rendah', 'Rendah'),
        ('Normal', 'Normal'),
        ('Tinggi', 'Tinggi'),
        ('Sangat Tinggi', 'Sangat Tinggi'),
    ]

    PRIORITAS_CHOICES = [
        ('Rendah', 'Rendah'),
        ('Normal', 'Normal'),
        ('Tinggi', 'Tinggi'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pengaduan_list',
        verbose_name="Pelapor"
    )
    kategori = models.CharField(
        max_length=50,
        choices=KATEGORI_CHOICES,
        default='Jalan',
        verbose_name="Kategori Masalah"
    )
    lokasi = models.TextField(verbose_name="Lokasi Kejadian")
    deskripsi = models.TextField(verbose_name="Deskripsi Laporan")
    foto = models.ImageField(
        upload_to='pengaduan/',
        blank=True,
        null=True,
        verbose_name="Foto Dokumentasi"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending',
        verbose_name="Status Penanganan"
    )
    urgensi = models.CharField(
        max_length=20,
        choices=URGENSI_CHOICES,
        default='Normal',
        verbose_name="Tingkat Urgensi"
    )
    prioritas = models.CharField(
        max_length=20,
        choices=PRIORITAS_CHOICES,
        default='Normal',
        verbose_name="Prioritas Pengerjaan"
    )
    estimasi_selesai = models.DateField(
        blank=True,
        null=True,
        verbose_name="Estimasi Tanggal Selesai"
    )
    petugas = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        default='Belum Ditugaskan',
        verbose_name="Petugas Lapangan"
    )
    aset_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        default='-',
        verbose_name="Aset ID"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Tanggal Laporan")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Tanggal Pembaruan")
    catatan_admin = models.TextField(
        blank=True,
        null=True,
        verbose_name="Catatan Admin / Tindak Lanjut"
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Latitude"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Longitude"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Pengaduan"
        verbose_name_plural = "Daftar Pengaduan"

    def __str__(self):
        return f"Laporan #{self.id} - {self.get_kategori_display()} ({self.status})"

class Pengumuman(models.Model):
    judul = models.CharField(max_length=200, verbose_name="Judul Pengumuman")
    konten = models.TextField(verbose_name="Isi Pengumuman")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Tanggal Dibuat")
    is_active = models.BooleanField(default=True, verbose_name="Aktif / Tampilkan")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Pengumuman"
        verbose_name_plural = "Daftar Pengumuman"

    def __str__(self):
        return self.judul

