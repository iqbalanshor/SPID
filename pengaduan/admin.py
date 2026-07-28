from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.http import HttpResponse
import csv
from .models import CustomUser, Pengaduan, Pengumuman

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'nama_lengkap', 'email', 'nomor_hp', 'is_staff', 'is_active', 'last_login')
    fieldsets = UserAdmin.fieldsets + (
        ('Informasi SPID', {'fields': ('nama_lengkap', 'nomor_hp')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informasi SPID', {'fields': ('nama_lengkap', 'nomor_hp')}),
    )

def export_pengaduan_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="laporan_pengaduan_spid.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID Laporan', 'Pelapor', 'Kategori', 'Lokasi', 'Deskripsi', 'Status', 'Tanggal Laporan', 'Tanggal Update', 'Catatan Admin'
    ])
    
    for obj in queryset:
        writer.writerow([
            f"SPID-{obj.id}",
            f"{obj.user.nama_lengkap} (@{obj.user.username})",
            obj.get_kategori_display(),
            obj.lokasi,
            obj.deskripsi,
            obj.status,
            obj.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            obj.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            obj.catatan_admin or ''
        ])
    return response

export_pengaduan_csv.short_description = "Export Laporan Terpilih Ke CSV"

class PengaduanAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_info', 'kategori_label', 'status_badge', 'created_at')
    list_filter = ('status', 'kategori', 'created_at')
    search_fields = ('user__username', 'user__nama_lengkap', 'lokasi', 'deskripsi')
    readonly_fields = ('created_at', 'updated_at')
    actions = [export_pengaduan_csv]
    
    fieldsets = (
        ('Informasi Pelapor & Status', {
            'fields': ('user', 'status', 'catatan_admin')
        }),
        ('Rincian Laporan', {
            'fields': ('kategori', 'lokasi', 'deskripsi', 'foto')
        }),
        ('Waktu', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def user_info(self, obj):
        return f"{obj.user.nama_lengkap} (@{obj.user.username})"
    user_info.short_description = "Pelapor"

    def kategori_label(self, obj):
        return obj.get_kategori_display()
    kategori_label.short_description = "Kategori"

    def status_badge(self, obj):
        return obj.status
    status_badge.short_description = "Status"

class PengumumanAdmin(admin.ModelAdmin):
    list_display = ('judul', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('judul', 'konten')

class SessionAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'user_info', 'expire_date', 'status_session')
    readonly_fields = ('session_key', 'session_data', 'expire_date')
    search_fields = ('session_key',)

    def user_info(self, obj):
        decoded = obj.get_decoded()
        user_id = decoded.get('_auth_user_id')
        if user_id:
            User = get_user_model()
            try:
                user = User.objects.get(pk=user_id)
                return f"{user.nama_lengkap} (@{user.username})"
            except User.DoesNotExist:
                return f"User ID: {user_id}"
        return "Anonymous / Guest"
    user_info.short_description = "Pengguna Sesi"

    def status_session(self, obj):
        if obj.expire_date > timezone.now():
            return "Aktif (Online/Belum Logout)"
        return "Expired"
    status_session.short_description = "Status Akses"

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Pengaduan, PengaduanAdmin)
admin.site.register(Pengumuman, PengumumanAdmin)
admin.site.register(Session, SessionAdmin)

