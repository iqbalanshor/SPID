from django.urls import path
from pengaduan import views

urlpatterns = [
    path('', views.admin_dashboard_view, name='admin_dashboard'),
    path('login/', views.admin_login_view, name='admin_login'),
    path('data/', views.admin_data_view, name='admin_data'),
    path('detail/<int:pk>/', views.admin_detail_view, name='admin_detail'),
    path('detail/<int:pk>/reject/', views.admin_reject_view, name='admin_reject'),
    path('detail/<int:pk>/update/', views.admin_update_status_view, name='admin_update_status'),
    path('detail/<int:pk>/delete/', views.admin_delete_view, name='admin_delete'),
    path('export/', views.admin_export_view, name='admin_export'),
    path('users/', views.admin_users_view, name='admin_users'),
    path('profil/', views.admin_profile_view, name='admin_profile'),
    path('logout/', views.admin_logout_view, name='admin_logout'),
]
