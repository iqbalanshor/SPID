from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm, PengaduanForm, UserProfileForm
from .models import Pengaduan, Pengumuman
import random

def generate_captcha(request):
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    request.session['captcha_result'] = num1 + num2
    return num1, num2

@login_required
def beranda_view(request):
    announcements = Pengumuman.objects.filter(is_active=True)[:5]
    return render(request, 'beranda.html', {
        'active_menu': 'beranda',
        'announcements': announcements
    })

def login_view(request):
    if request.user.is_authenticated:
        logout(request)

    if request.method == 'POST':
        form = LoginForm(request.POST, request=request)
        if form.is_valid():
            user = form.cleaned_data.get('user')
            remember_me = form.cleaned_data.get('remember_me')
            
            login(request, user)
            
            if not remember_me:
                request.session.set_expiry(0)
            else:
                request.session.set_expiry(1209600)
                
            if 'captcha_result' in request.session:
                del request.session['captcha_result']
                
            messages.success(request, f"Selamat datang kembali, {user.nama_lengkap}!")
            
            if user.is_staff:
                return redirect('admin_dashboard')
            return redirect('beranda')
        else:
            num1, num2 = generate_captcha(request)
    else:
        form = LoginForm(request=request)
        num1, num2 = generate_captcha(request)

    return render(request, 'login.html', {
        'form': form,
        'num1': num1,
        'num2': num2
    })

def admin_login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('beranda')

    if request.method == 'POST':
        form = LoginForm(request.POST, request=request)
        if form.is_valid():
            user = form.cleaned_data.get('user')
            if not user.is_staff:
                messages.error(request, "Anda tidak memiliki hak akses admin.")
                num1, num2 = generate_captcha(request)
                return render(request, 'admin/login.html', {
                    'form': form,
                    'num1': num1,
                    'num2': num2
                })
            
            remember_me = form.cleaned_data.get('remember_me')
            login(request, user)
            
            if not remember_me:
                request.session.set_expiry(0)
            else:
                request.session.set_expiry(1209600)
                
            if 'captcha_result' in request.session:
                del request.session['captcha_result']

            messages.success(request, f"Selamat datang Admin, {user.nama_lengkap}!")
            return redirect('admin_dashboard')
        else:
            num1, num2 = generate_captcha(request)
    else:
        form = LoginForm(request=request)
        num1, num2 = generate_captcha(request)

    return render(request, 'admin/login.html', {
        'form': form,
        'num1': num1,
        'num2': num2
    })

def register_view(request):
    if request.user.is_authenticated:
        return redirect('beranda')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in after registration
            login(request, user)
            messages.success(request, f"Pendaftaran berhasil! Selamat datang di SPID, {user.nama_lengkap}!")
            return redirect('beranda')
        else:
            messages.error(request, "Silakan perbaiki kesalahan di bawah ini.")
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, "Anda telah berhasil keluar dari sistem.")
    return redirect('login')

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil Anda berhasil diperbarui!")
            return redirect('profile')
        else:
            messages.error(request, "Terjadi kesalahan. Silakan perbaiki data Anda.")
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'profil.html', {
        'form': form,
        'active_menu': 'profile'
    })

@login_required
def form_pengaduan_view(request):
    if request.method == 'POST':
        form = PengaduanForm(request.POST, request.FILES)
        if form.is_valid():
            pengaduan = form.save(commit=False)
            pengaduan.user = request.user
            pengaduan.save()
            messages.success(request, "Aduan Anda berhasil dikirim dan sedang menunggu verifikasi.")
            return redirect('konfirmasi', pk=pengaduan.pk)
        else:
            messages.error(request, "Terjadi kesalahan dalam pengisian formulir.")
    else:
        form = PengaduanForm()

    return render(request, 'form_pengaduan.html', {
        'form': form,
        'active_menu': 'form'
    })

@login_required
def konfirmasi_view(request, pk):
    pengaduan = get_object_or_404(Pengaduan, pk=pk, user=request.user)
    return render(request, 'konfirmasi.html', {
        'pengaduan': pengaduan,
        'active_menu': 'form'
    })

@login_required
def user_detail_view(request, pk):
    pengaduan = get_object_or_404(Pengaduan, pk=pk, user=request.user)
    
    # Prepare status timeline checks
    if pengaduan.status == 'Ditolak':
        timeline = [
            {'title': 'Laporan Diterima', 'desc': 'Sistem menerima laporan awal dari Anda.', 'status': True, 'date': pengaduan.created_at},
            {'title': 'Laporan Ditolak', 'desc': 'Laporan Anda ditolak karena tidak memenuhi kriteria/bukti kurang lengkap.', 'status': True, 'date': pengaduan.updated_at},
        ]
    else:
        timeline = [
            {'title': 'Laporan Diterima', 'desc': 'Sistem menerima laporan awal dari Anda.', 'status': True, 'date': pengaduan.created_at},
            {'title': 'Verifikasi Admin', 'desc': 'Admin memvalidasi kelengkapan data bukti foto.', 'status': pengaduan.status in ['Diverifikasi', 'Diproses', 'Selesai'], 'date': pengaduan.created_at if pengaduan.status in ['Diverifikasi', 'Diproses', 'Selesai'] else None},
            {'title': 'Dalam Proses Penugasan', 'desc': 'Sedang mencari tim teknis terdekat dari lokasi.', 'status': pengaduan.status in ['Diproses', 'Selesai'], 'date': pengaduan.updated_at if pengaduan.status in ['Diproses', 'Selesai'] else None},
            {'title': 'Pengerjaan Lapangan', 'desc': 'Tim teknis melakukan perbaikan di lokasi.', 'status': pengaduan.status in ['Diproses', 'Selesai'], 'date': pengaduan.updated_at if pengaduan.status in ['Diproses', 'Selesai'] else None},
            {'title': 'Selesai', 'desc': 'Konfirmasi perbaikan oleh pelapor dan sistem.', 'status': pengaduan.status == 'Selesai', 'date': pengaduan.updated_at if pengaduan.status == 'Selesai' else None},
        ]
    
    return render(request, 'user_detail.html', {
        'active_menu': 'tracking',
        'pengaduan': pengaduan,
        'timeline': timeline
    })

@login_required
def tracking_view(request):
    # Fetch user's complaints
    pengaduans = Pengaduan.objects.filter(user=request.user)
    total_count = pengaduans.count()
    pending_count = pengaduans.filter(status='Pending').count()
    processed_count = pengaduans.filter(status__in=['Diverifikasi', 'Diproses']).count()
    completed_count = pengaduans.filter(status='Selesai').count()
    rejected_count = pengaduans.filter(status='Ditolak').count()
    
    return render(request, 'tracking.html', {
        'pengaduans': pengaduans,
        'active_menu': 'tracking',
        'total_count': total_count,
        'pending_count': pending_count,
        'processed_count': processed_count,
        'completed_count': completed_count,
        'rejected_count': rejected_count,
    })

# ==========================================================================
# Custom Admin Portal Views (Port 8001)
# ==========================================================================
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.paginator import Paginator
import csv
from django.http import HttpResponse
from datetime import datetime

@staff_member_required(login_url='admin_login')
def admin_dashboard_view(request):
    total_reports = Pengaduan.objects.count()
    processed_reports = Pengaduan.objects.filter(status='Diproses').count()
    completed_reports = Pengaduan.objects.filter(status='Selesai').count()
    urgent_reports = Pengaduan.objects.filter(status='Pending').count()

    # Monthly Trend (Mock data for the dashboard bar chart)
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul']
    volumes = [25, 42, 38, 92, 48, 65, 30]
    chart_data = zip(months, volumes)

    # Category Popularity
    jalan_count = Pengaduan.objects.filter(kategori='Jalan').count()
    penerangan_count = Pengaduan.objects.filter(kategori='Penerangan').count()
    irigasi_count = Pengaduan.objects.filter(kategori='Irigasi').count()
    jembatan_count = Pengaduan.objects.filter(kategori='Jembatan').count()
    fasilitas_count = Pengaduan.objects.filter(kategori='Fasilitas').count()
    lainnya_count = Pengaduan.objects.filter(kategori='Lainnya').count()
    
    denom = total_reports if total_reports > 0 else 1
    percentages = {
        'jalan': round((jalan_count / denom) * 100),
        'penerangan': round((penerangan_count / denom) * 100),
        'irigasi': round(((irigasi_count + jembatan_count) / denom) * 100),
        'lainnya': round(((fasilitas_count + lainnya_count) / denom) * 100),
    }

    # Recent 5 reports
    recent_reports = Pengaduan.objects.all()[:5]

    return render(request, 'admin_dashboard.html', {
        'active_menu': 'dashboard',
        'total_reports': total_reports,
        'processed_reports': processed_reports,
        'completed_reports': completed_reports,
        'urgent_reports': urgent_reports,
        'chart_data': chart_data,
        'percentages': percentages,
        'recent_reports': recent_reports,
    })

@staff_member_required(login_url='admin_login')
def admin_data_view(request):
    query = request.GET.get('q', '')
    kategori_tab = request.GET.get('kategori', 'Semua')
    status_filter = request.GET.get('status', 'Semua Status')

    reports = Pengaduan.objects.all()

    # Search filter
    if query:
        reports = reports.filter(
            Q(id__icontains=query) |
            Q(lokasi__icontains=query) |
            Q(deskripsi__icontains=query) |
            Q(user__nama_lengkap__icontains=query) |
            Q(user__username__icontains=query)
        )

    # Category tab
    if kategori_tab != 'Semua':
        reports = reports.filter(kategori=kategori_tab)

    # Status dropdown
    if status_filter != 'Semua Status':
        reports = reports.filter(status=status_filter)

    # Pagination
    paginator = Paginator(reports, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Counts
    total_count = Pengaduan.objects.count()
    pending_count = Pengaduan.objects.filter(status='Pending').count()
    processed_count = Pengaduan.objects.filter(status='Diproses').count()
    completed_count = Pengaduan.objects.filter(status='Selesai').count()

    return render(request, 'admin_data.html', {
        'active_menu': 'data',
        'page_obj': page_obj,
        'query': query,
        'kategori_tab': kategori_tab,
        'status_filter': status_filter,
        'total_count': total_count,
        'pending_count': pending_count,
        'processed_count': processed_count,
        'completed_count': completed_count,
    })

@staff_member_required(login_url='admin_login')
def admin_detail_view(request, pk):
    report = get_object_or_404(Pengaduan, pk=pk)
    
    # Prepare timeline checks
    if report.status == 'Ditolak':
        timeline = [
            {'title': 'Laporan Diterima', 'desc': 'Sistem menerima laporan awal dari warga.', 'status': True, 'date': report.created_at},
            {'title': 'Laporan Ditolak', 'desc': 'Laporan ditolak oleh admin dengan alasan tertentu.', 'status': True, 'date': report.updated_at},
        ]
    else:
        timeline = [
            {'title': 'Laporan Diterima', 'desc': 'Sistem menerima laporan awal dari warga.', 'status': True, 'date': report.created_at},
            {'title': 'Verifikasi Admin', 'desc': 'Admin memvalidasi kelengkapan data bukti foto.', 'status': report.status in ['Diverifikasi', 'Diproses', 'Selesai'], 'date': report.created_at if report.status in ['Diverifikasi', 'Diproses', 'Selesai'] else None},
            {'title': 'Dalam Proses Penugasan', 'desc': 'Sedang mencari tim teknis terdekat dari lokasi kejadian.', 'status': report.status in ['Diproses', 'Selesai'], 'date': report.updated_at if report.status in ['Diproses', 'Selesai'] else None},
            {'title': 'Pengerjaan Lapangan', 'desc': 'Tim teknis melakukan perbaikan di lokasi.', 'status': report.status in ['Diproses', 'Selesai'], 'date': report.updated_at if report.status in ['Diproses', 'Selesai'] else None},
            {'title': 'Selesai', 'desc': 'Konfirmasi perbaikan oleh pelapor dan sistem.', 'status': report.status == 'Selesai', 'date': report.updated_at if report.status == 'Selesai' else None},
        ]

    return render(request, 'admin_detail.html', {
        'active_menu': 'data',
        'report': report,
        'timeline': timeline,
    })

@staff_member_required(login_url='admin_login')
def admin_update_status_view(request, pk):
    report = get_object_or_404(Pengaduan, pk=pk)

    if request.method == 'POST':
        status = request.POST.get('status')
        estimasi_str = request.POST.get('estimasi_selesai')
        prioritas = request.POST.get('prioritas')
        petugas = request.POST.get('petugas')
        aset_id = request.POST.get('aset_id')
        catatan_admin = request.POST.get('catatan_admin')
        
        report.status = status
        report.prioritas = prioritas
        report.catatan_admin = catatan_admin
        if petugas:
            report.petugas = petugas
        if aset_id:
            report.aset_id = aset_id
            
        if estimasi_str:
            try:
                report.estimasi_selesai = datetime.strptime(estimasi_str, '%Y-%m-%d').date()
            except ValueError:
                pass
                
        # If progress photo uploaded, update the image
        if 'foto_progress' in request.FILES:
            report.foto = request.FILES['foto_progress']
            
        report.save()
        messages.success(request, f"Status laporan #SPID-{report.id} berhasil diperbarui!")
        return redirect('admin_detail', pk=report.pk)

    return render(request, 'admin_update.html', {
        'active_menu': 'data',
        'report': report,
    })

@staff_member_required(login_url='admin_login')
def admin_export_view(request):
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')
    kategori_filter = request.GET.getlist('kategori')
    status_filter = request.GET.getlist('status')

    reports = Pengaduan.objects.all()

    # Date range filters
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            reports = reports.filter(created_at__gte=timezone.make_aware(start_date))
        except ValueError:
            pass
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            # include entire end day
            reports = reports.filter(created_at__lte=timezone.make_aware(end_date.replace(hour=23, minute=59, second=59)))
        except ValueError:
            pass

    # Kategori filter
    if kategori_filter and 'Semua' not in kategori_filter:
        reports = reports.filter(kategori__in=kategori_filter)

    # Status filter
    if status_filter:
        reports = reports.filter(status__in=status_filter)

    # Export formats
    export_format = request.GET.get('export', '')
    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="laporan_berkala_spid.csv"'
        writer = csv.writer(response)
        writer.writerow(['Tanggal', 'Kategori', 'Lokasi', 'Status'])
        for r in reports:
            writer.writerow([
                r.created_at.strftime('%d/%m/%Y'),
                r.get_kategori_display(),
                r.lokasi,
                r.status
            ])
        return response
    elif export_format == 'print':
        total_count = reports.count()
        completed_count = reports.filter(status='Selesai').count()
        ratio = round((completed_count / total_count) * 100) if total_count > 0 else 0
        return render(request, 'admin_export_print.html', {
            'reports': reports,
            'total_count': total_count,
            'completed_count': completed_count,
            'ratio': ratio,
            'print_date': timezone.now(),
        })

    # Stats for preview
    total_count = reports.count()
    completed_count = reports.filter(status='Selesai').count()
    ratio = round((completed_count / total_count) * 100) if total_count > 0 else 0
    preview_reports = reports[:5]

    return render(request, 'admin_export.html', {
        'active_menu': 'export',
        'reports': preview_reports,
        'total_count': total_count,
        'completed_count': completed_count,
        'ratio': ratio,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'kategori_filter': kategori_filter,
        'status_filter': status_filter,
    })

@staff_member_required(login_url='admin_login')
def admin_users_view(request):
    User = get_user_model()
    users = User.objects.all().order_by('-last_login')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        nama_lengkap = request.POST.get('nama_lengkap')
        email = request.POST.get('email')
        nomor_hp = request.POST.get('nomor_hp')
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username sudah digunakan.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email sudah terdaftar.")
        else:
            User.objects.create_user(
                username=username,
                nama_lengkap=nama_lengkap,
                email=email,
                nomor_hp=nomor_hp,
                password=password,
                is_staff=True,
                is_superuser=True
            )
            messages.success(request, f"Admin baru '{nama_lengkap}' berhasil ditambahkan!")
            return redirect('admin_users')

    # Active sessions
    active_sessions = []
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    for s in sessions:
        decoded = s.get_decoded()
        user_id = decoded.get('_auth_user_id')
        if user_id:
            try:
                user_obj = User.objects.get(pk=user_id)
                active_sessions.append({
                    'session_key': s.session_key,
                    'user': user_obj,
                    'expire_date': s.expire_date
                })
            except User.DoesNotExist:
                pass

    return render(request, 'admin_users.html', {
        'active_menu': 'users',
        'users': users,
        'active_sessions': active_sessions,
    })

def admin_logout_view(request):
    logout(request)
    messages.success(request, "Anda berhasil logout dari portal admin.")
    return redirect('admin_login')

@staff_member_required(login_url='admin_login')
def admin_reject_view(request, pk):
    report = get_object_or_404(Pengaduan, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('catatan_admin', '')
        if not reason:
            messages.error(request, "Alasan penolakan wajib diisi.")
            return redirect('admin_detail', pk=report.pk)
        
        report.status = 'Ditolak'
        report.catatan_admin = reason
        report.save()
        messages.success(request, f"Laporan #SPID-{report.id} berhasil ditolak!")
    return redirect('admin_detail', pk=report.pk)

@staff_member_required(login_url='admin_login')
def admin_delete_view(request, pk):
    report = get_object_or_404(Pengaduan, pk=pk)
    if request.method == 'POST':
        report_id = report.id
        report.delete()
        messages.success(request, f"Laporan pengaduan #SPID-{report_id} berhasil dihapus secara permanen.")
    return redirect('admin_data')

@staff_member_required(login_url='admin_login')
def admin_profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil admin Anda berhasil diperbarui!")
            return redirect('admin_profile')
        else:
            messages.error(request, "Terjadi kesalahan. Silakan perbaiki data Anda.")
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'admin_profile.html', {
        'form': form,
        'active_menu': 'profile'
    })
