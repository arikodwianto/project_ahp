from django.urls import path
from . import views 
from django.contrib.auth import views as auth_views
from .views import kriteria_dan_perbandingan, hasil_ahp, kepala_dinas_kegiatan_view, admin_bidang_kegiatan
from .views import view_dpa, cetak_dpa_pdf, statistik_kadis, view_dpa_jf_perencana, view_dpa_admin_bidang


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
    path('perbandingan/', views.perbandingan_alternatif, name='perbandingan_alternatif'),
    path('hasil-alternatif/', views.hasil_alternatif, name='hasil_alternatif'),

    path('kepala-dinas/kegiatan/', kepala_dinas_kegiatan_view, name='kepala_dinas_kegiatan'),
    
    path('persetujuan/', views.persetujuan_kepala_dinas, name='persetujuan_kepala_dinas'),
    path('dpa/', view_dpa, name='view_dpa'),
    path('dpa/cetak/', cetak_dpa_pdf, name='cetak_dpa_pdf'),
    path('dashboard/kadis/statistik/', statistik_kadis, name='statistik_kadis'),
    path('dpa/jf-perencana/', view_dpa_jf_perencana, name='view_dpa_jf_perencana'),
    path('dpa/admin-bidang/', view_dpa_admin_bidang, name='view_dpa_admin_bidang'),
    path('info-admin-bidang/', views.info_admin_bidang, name='info_admin_bidang'),
    path('admin-bidang/', admin_bidang_kegiatan, name='admin_bidang_kegiatan'),

    # Hasil Perhitungan AHP untuk Alternatif
    
]
