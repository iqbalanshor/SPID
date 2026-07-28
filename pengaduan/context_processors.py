from pengaduan.models import Pengaduan, Pengumuman

def latest_reports(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return {
                'notifications': Pengaduan.objects.filter(status='Pending').order_by('-created_at')[:5],
                'notification_count': Pengaduan.objects.filter(status='Pending').count()
            }
        else:
            active_announcements = Pengumuman.objects.filter(is_active=True).order_by('-created_at')[:5]
            return {
                'announcements': active_announcements,
                'announcement_count': active_announcements.count()
            }
    return {
        'notifications': [],
        'notification_count': 0,
        'announcements': [],
        'announcement_count': 0
    }

