from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='login', permanent=False)),
    path('beranda/', views.beranda_view, name='beranda'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profil/', views.profile_view, name='profile'),
    path('pengaduan/baru/', views.form_pengaduan_view, name='form_pengaduan'),
    path('pengaduan/tracking/', views.tracking_view, name='tracking'),
    path('pengaduan/konfirmasi/<int:pk>/', views.konfirmasi_view, name='konfirmasi'),
    path('pengaduan/<int:pk>/', views.user_detail_view, name='user_detail'),
]
