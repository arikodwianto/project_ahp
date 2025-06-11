from django.urls import path
from . import views 
from django.contrib.auth import views as auth_views
from .views import kriteria_dan_perbandingan, hasil_ahp

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('dashboard/kepala_dinas/', views.kepala_dinas_dashboard, name='kepala_dinas_dashboard'),
    path('dashboard/admin_bidang/', views.admin_bidang_dashboard, name='admin_bidang_dashboard'),
    path('dashboard/jf_perencana/', views.jf_perencana_dashboard, name='jf_perencana_dashboard'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('dashboard/jf-perencana/', views.jf_perencana_dashboard, name='jf_perencana_dashboard'),
    path('dashboard/jf-perencana/ahp-info/', views.ahp_info, name='ahp_info'),
    path('kriteria-perbandingan/', kriteria_dan_perbandingan, name='kriteria_perbandingan'),
    path('hasil-ahp/', hasil_ahp, name='hasil_ahp'),
  
]
