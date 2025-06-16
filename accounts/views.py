from datetime import timedelta
import io
import numpy as np
import pdfkit
import tempfile
from itertools import combinations

from django.contrib import messages
from django.contrib.auth import logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Count, Sum, Avg
from django.http import (
    HttpResponse,
    JsonResponse,
    HttpResponseForbidden
)
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)
from django.template.loader import get_template, render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.timezone import now

from xhtml2pdf import pisa

from .models import (
    CustomUser,
    DPA,
    Kegiatan,
    SubKegiatan,
    Rekening,
    PenggunaanBelanja,
    PersetujuanPenggunaanBelanja,
    Kriteria,
    PerbandinganAlternatif,
    PerbandinganKriteria
)

from .forms import (
    CustomUserCreationForm,
    KegiatanForm,
    SubKegiatanForm,
    RekeningForm,
    PenggunaanBelanjaForm,
    KriteriaForm,
    PerbandinganKriteriaForm,
    PerbandinganAlternatifForm
)



class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        user = self.request.user

        if hasattr(user, 'role'):
            if user.role == 'superadmin' or user.role == 'kepala_dinas':
                return reverse_lazy('kepala_dinas_dashboard')
            elif user.role == 'admin_bidang':
                return reverse_lazy('info_admin_bidang')
            elif user.role == 'jf_perencana':
                return reverse_lazy('ahp_info')

        return reverse_lazy('login')


@login_required
def kepala_dinas_dashboard(request):
    if request.user.role != 'kepala_dinas':
        messages.error(request, "Anda tidak memiliki izin mengakses halaman ini.")
        return redirect('login')

    # Tambah atau ubah user
    if request.method == 'POST':
        if 'save_user' in request.POST:
            user_id = request.POST.get('user_id')
            if user_id:  # Update user
                user = get_object_or_404(CustomUser, id=user_id)
                form = CustomUserCreationForm(request.POST, instance=user)
                if form.is_valid():
                    form.save()
                    messages.success(request, "User berhasil diperbarui.")
                    return redirect('kepala_dinas_dashboard')
                else:
                    messages.error(request, "Gagal memperbarui user.")
            else:  # Tambah user baru
                form = CustomUserCreationForm(request.POST)
                if form.is_valid():
                    form.save()
                    messages.success(request, "User berhasil ditambahkan.")
                    return redirect('kepala_dinas_dashboard')
                else:
                    messages.error(request, "Gagal menambahkan user.")
        elif 'delete_user' in request.POST:
            user_id = request.POST.get('user_id')
            user = get_object_or_404(CustomUser, id=user_id)
            user.delete()
            messages.success(request, "User berhasil dihapus.")
            return redirect('kepala_dinas_dashboard')
    else:
        form = CustomUserCreationForm()

    user_list = CustomUser.objects.filter(role__in=['jf_perencana', 'admin_bidang'])

    return render(request, 'accounts/kepala_dinas_dashboard.html', {
        'form': form,
        'user_list': user_list
    })


@login_required
def statistik_kadis(request):
    if request.user.role != 'kepala_dinas':
        messages.error(request, "Anda tidak memiliki izin mengakses halaman ini.")
        return redirect('login')

    jumlah_user = CustomUser.objects.filter(role__in=['jf_perencana', 'admin_bidang']).count()
    jumlah_disetujui = PersetujuanPenggunaanBelanja.objects.filter(disetujui=True).count()
    jumlah_ditolak = PersetujuanPenggunaanBelanja.objects.filter(ditolak=True).count()

    context = {
        'jumlah_user': jumlah_user,
        'jumlah_disetujui': jumlah_disetujui,
        'jumlah_ditolak': jumlah_ditolak,
    }

    return render(request, 'accounts/statistik_kadis.html', context)




@login_required
def kepala_dinas_kegiatan_view(request):
    if request.user.role != 'kepala_dinas':
        messages.error(request, "Anda tidak memiliki izin mengakses halaman ini.")
        return redirect('login')

    kegiatan_list = Kegiatan.objects.all()

    return render(request, 'accounts/kepala_dinas_kegiatan.html', {
        'kegiatan_list': kegiatan_list
    })


@login_required
def persetujuan_kepala_dinas(request):
    if request.user.role != 'kepala_dinas':
        return HttpResponseForbidden("Tidak punya akses")

    persetujuan_list = PersetujuanPenggunaanBelanja.objects.all().order_by('-tanggal_persetujuan')

    penggunaan_belanja_belum_disetujui = PenggunaanBelanja.objects.exclude(
        id__in=persetujuan_list.values_list('penggunaan_belanja_id', flat=True)
    )

    if request.method == 'POST':
        disetujui_ids = request.POST.getlist('disetujui')
        ditolak_ids = request.POST.getlist('ditolak')

        for pb in penggunaan_belanja_belum_disetujui:
            if str(pb.id) in disetujui_ids or str(pb.id) in ditolak_ids:
                persetujuan = PersetujuanPenggunaanBelanja(
                    penggunaan_belanja_id=pb.id,
                    nama_penggunaan=pb.nama_penggunaan,
                    jumlah=pb.jumlah,
                    kode_rekening=pb.rekening.kode_rekening,
                    nama_rekening=pb.rekening.nama_rekening,
                    kode_sub_kegiatan=pb.rekening.sub_kegiatan.kode_sub_kegiatan,
                    nama_sub_kegiatan=pb.rekening.sub_kegiatan.nama_sub_kegiatan,
                    kode_kegiatan=pb.rekening.sub_kegiatan.kegiatan.kode_kegiatan,
                    nama_kegiatan=pb.rekening.sub_kegiatan.kegiatan.nama_kegiatan,
                    bidang=pb.rekening.sub_kegiatan.kegiatan.bidang,
                )
                if str(pb.id) in disetujui_ids:
                    persetujuan.set_approved()
                elif str(pb.id) in ditolak_ids:
                    persetujuan.set_rejected()

        messages.success(request, "Persetujuan dan penolakan berhasil disimpan.")
        return redirect('persetujuan_kepala_dinas')

    return render(request, 'accounts/persetujuan_kepala_dinas.html', {
        'penggunaan_belanja_belum_disetujui': penggunaan_belanja_belum_disetujui,
        'persetujuan_list': persetujuan_list
    })




@login_required
def view_dpa(request):
    if request.user.role != 'kepala_dinas':
        return HttpResponseForbidden("Tidak punya akses")

    # Filter berdasarkan field boolean 'disetujui'
    dpa_list = PersetujuanPenggunaanBelanja.objects.filter(disetujui=True).order_by('-tanggal_persetujuan')

    return render(request, 'accounts/view_dpa.html', {
        'dpa_list': dpa_list
    })


@login_required
def view_dpa_jf_perencana(request):
    if request.user.role != 'jf_perencana':
        return HttpResponseForbidden("Anda tidak memiliki akses sebagai JF Perencana.")

    # Hanya data yang disetujui
    dpa_list = PersetujuanPenggunaanBelanja.objects.filter(disetujui=True).order_by('-tanggal_persetujuan')

    return render(request, 'accounts/view_dpa_jf_perencana.html', {
        'dpa_list': dpa_list
    })
@login_required
def view_dpa_admin_bidang(request):
    user = request.user

    if user.role != 'admin_bidang':
        return HttpResponseForbidden("Anda tidak memiliki akses sebagai Admin Bidang.")

    if not user.bidang:
        return HttpResponseForbidden("Akun Anda belum memiliki bidang yang terkait.")

    # Asumsinya: `PersetujuanPenggunaanBelanja.bidang` adalah string yang cocok dengan user.bidang
    dpa_list = PersetujuanPenggunaanBelanja.objects.filter(
        disetujui=True,
        bidang=user.bidang
    ).order_by('-tanggal_persetujuan')

    return render(request, 'accounts/view_dpa_admin_bidang.html', {
        'dpa_list': dpa_list
    })


@login_required
def cetak_dpa_pdf(request):
    role = request.user.role

    if role == 'kepala_dinas' or role == 'jf_perencana':
        dpa_list = PersetujuanPenggunaanBelanja.objects.filter(disetujui=True)
    elif role == 'admin_bidang':
        if not request.user.bidang:
            return HttpResponseForbidden("Bidang belum diatur.")
        dpa_list = PersetujuanPenggunaanBelanja.objects.filter(disetujui=True, bidang=request.user.bidang)
    else:
        return HttpResponseForbidden("Anda tidak punya akses.")

    dpa_list = dpa_list.order_by('-tanggal_persetujuan')

    html_string = render_to_string('accounts/dpa_pdf_template.html', {
        'dpa_list': dpa_list,
        'user': request.user,  # kalau mau pakai role di template
    })

    path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    options = {'enable-local-file-access': None}

    pdf = pdfkit.from_string(html_string, False, configuration=config, options=options)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="dpa.pdf"'
    return response





from django.shortcuts import render
from .models import DPA




@login_required
def jf_perencana_dashboard(request):
    if request.user.role != 'jf_perencana':
        messages.error(request, "Anda tidak memiliki izin mengakses halaman ini!")
        return redirect('login')

    kegiatan_form = KegiatanForm()
    sub_kegiatan_form = SubKegiatanForm()
    rekening_form = RekeningForm()
    penggunaan_form = PenggunaanBelanjaForm()

    if request.method == 'POST':
        post = request.POST

        # ------------------------ KEGIATAN ------------------------
        if 'submit_kegiatan' in post:
            kegiatan_id = post.get('kegiatan_id')
            if kegiatan_id:
                kegiatan = get_object_or_404(Kegiatan, id=kegiatan_id)
                kegiatan_form = KegiatanForm(post, instance=kegiatan)
                if kegiatan_form.is_valid():
                    kegiatan_form.save()
                    messages.success(request, "Kegiatan berhasil diubah.")
                else:
                    messages.error(request, "Gagal mengubah kegiatan.")
            else:
                kegiatan_form = KegiatanForm(post)
                if kegiatan_form.is_valid():
                    kegiatan_form.save()
                    messages.success(request, "Kegiatan berhasil ditambahkan.")
                else:
                    messages.error(request, "Gagal menambahkan kegiatan.")
            return redirect('jf_perencana_dashboard')

        elif 'hapus_kegiatan' in post:
            kegiatan_id = post.get('kegiatan_id')
            try:
                Kegiatan.objects.get(id=kegiatan_id).delete()
                messages.success(request, "Kegiatan berhasil dihapus.")
            except Kegiatan.DoesNotExist:
                messages.error(request, "Kegiatan tidak ditemukan.")
            return redirect('jf_perencana_dashboard')

        # ------------------------ SUB KEGIATAN ------------------------
        elif 'submit_subkegiatan' in post:
            sub_id = post.get('subkegiatan_id')
            if sub_id:
                subkegiatan = get_object_or_404(SubKegiatan, id=sub_id)
                sub_kegiatan_form = SubKegiatanForm(post, instance=subkegiatan)
            else:
                sub_kegiatan_form = SubKegiatanForm(post)

            if sub_kegiatan_form.is_valid():
                subkegiatan = sub_kegiatan_form.save(commit=False)
                kegiatan_id = post.get('kegiatan')
                if kegiatan_id:
                    subkegiatan.kegiatan = get_object_or_404(Kegiatan, id=kegiatan_id)
                    subkegiatan.save()
                    messages.success(request, "Sub Kegiatan berhasil disimpan.")
                else:
                    messages.error(request, "Kegiatan tidak ditemukan.")
            else:
                messages.error(request, "Gagal menyimpan sub kegiatan.")
            return redirect('jf_perencana_dashboard')

        elif 'hapus_subkegiatan' in post:
            sub_id = post.get('subkegiatan_id')
            try:
                SubKegiatan.objects.get(id=sub_id).delete()
                messages.success(request, "Sub Kegiatan berhasil dihapus.")
            except SubKegiatan.DoesNotExist:
                messages.error(request, "Sub Kegiatan tidak ditemukan.")
            return redirect('jf_perencana_dashboard')

        # ------------------------ REKENING ------------------------
        elif 'submit_rekening' in post:
            rekening_id = post.get('rekening_id')
            if rekening_id:
                rekening = get_object_or_404(Rekening, id=rekening_id)
                rekening_form = RekeningForm(post, instance=rekening)
            else:
                rekening_form = RekeningForm(post)

            if rekening_form.is_valid():
                rekening = rekening_form.save(commit=False)
                sub_id = post.get('sub_kegiatan')
                if sub_id:
                    rekening.sub_kegiatan = get_object_or_404(SubKegiatan, id=sub_id)
                    rekening.save()
                    messages.success(request, "Rekening berhasil disimpan.")
                else:
                    messages.error(request, "Sub Kegiatan tidak ditemukan.")
            else:
                messages.error(request, "Gagal menyimpan rekening.")
            return redirect('jf_perencana_dashboard')

        elif 'hapus_rekening' in post:
            rekening_id = post.get('rekening_id')
            try:
                Rekening.objects.get(id=rekening_id).delete()
                messages.success(request, "Rekening berhasil dihapus.")
            except Rekening.DoesNotExist:
                messages.error(request, "Rekening tidak ditemukan.")
            return redirect('jf_perencana_dashboard')

        # ------------------------ PENGGUNAAN BELANJA ------------------------
        elif 'submit_penggunaan' in post:
            penggunaan_id = post.get('penggunaan_id')
            if penggunaan_id:
                penggunaan = get_object_or_404(PenggunaanBelanja, id=penggunaan_id)
                penggunaan_form = PenggunaanBelanjaForm(post, instance=penggunaan)
            else:
                penggunaan_form = PenggunaanBelanjaForm(post)

            if penggunaan_form.is_valid():
                penggunaan = penggunaan_form.save(commit=False)
                rekening_id = post.get('rekening')
                if rekening_id:
                    penggunaan.rekening = get_object_or_404(Rekening, id=rekening_id)
                    penggunaan.save()
                    messages.success(request, "Penggunaan Belanja berhasil disimpan.")
                else:
                    messages.error(request, "Rekening tidak ditemukan.")
            else:
                messages.error(request, "Gagal menyimpan penggunaan belanja.")
            return redirect('jf_perencana_dashboard')

        elif 'hapus_penggunaan' in post:
            penggunaan_id = post.get('penggunaan_id')
            try:
                PenggunaanBelanja.objects.get(id=penggunaan_id).delete()
                messages.success(request, "Penggunaan Belanja berhasil dihapus.")
            except PenggunaanBelanja.DoesNotExist:
                messages.error(request, "Penggunaan Belanja tidak ditemukan.")
            return redirect('jf_perencana_dashboard')

    # ------------------------ AMBIL DATA UNTUK DASHBOARD ------------------------
    kegiatan_per_bidang = {
        kode: {
            'nama': nama,
            'kegiatan_list': Kegiatan.objects.filter(bidang=kode).prefetch_related(
                'sub_kegiatans__rekenings__penggunaan_belanjas'
            )
        }
        for kode, nama in Kegiatan.BIDANG_CHOICES
    }

    context = {
        'kegiatan_form': kegiatan_form,
        'sub_kegiatan_form': sub_kegiatan_form,
        'rekening_form': rekening_form,
        'penggunaan_form': penggunaan_form,
        'kegiatan_per_bidang': kegiatan_per_bidang,
    }
    return render(request, 'accounts/jf_perencana_dashboard.html', context)

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

@login_required
def admin_bidang_kegiatan(request):
    if request.user.role != 'admin_bidang':
        messages.error(request, "Anda tidak memiliki izin mengakses halaman ini!")
        return redirect('login')

    penggunaan_form = PenggunaanBelanjaForm()

    if request.method == 'POST':
        post = request.POST

        if 'submit_penggunaan' in post:
            penggunaan_id = post.get('penggunaan_id')
            if penggunaan_id:
                penggunaan = get_object_or_404(PenggunaanBelanja, id=penggunaan_id)
                penggunaan_form = PenggunaanBelanjaForm(post, instance=penggunaan)
            else:
                penggunaan_form = PenggunaanBelanjaForm(post)

            if penggunaan_form.is_valid():
                penggunaan = penggunaan_form.save(commit=False)
                rekening_id = post.get('rekening')
                if rekening_id:
                    penggunaan.rekening = get_object_or_404(Rekening, id=rekening_id)
                    penggunaan.save()
                    messages.success(request, "Penggunaan Belanja berhasil disimpan.")
                else:
                    messages.error(request, "Rekening tidak ditemukan.")
            else:
                messages.error(request, "Gagal menyimpan penggunaan belanja.")
            return redirect('admin_bidang_kegiatan')

    bidang_user = getattr(request.user, 'bidang', None)
    if bidang_user:
        kegiatan_list = Kegiatan.objects.filter(bidang=bidang_user).prefetch_related(
            'sub_kegiatans__rekenings__penggunaan_belanjas'
        )
    else:
        kegiatan_list = Kegiatan.objects.none()

    context = {
        'penggunaan_form': penggunaan_form,
        'kegiatan_list': kegiatan_list,
    }
    return render(request, 'accounts/admin_bidang_dashboard.html', context)


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseForbidden

from .models import Kegiatan, SubKegiatan, Rekening, PenggunaanBelanja, PersetujuanPenggunaanBelanja

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponseForbidden
from .models import (
    Kegiatan, SubKegiatan, Rekening,
    PenggunaanBelanja, PersetujuanPenggunaanBelanja
)

@login_required
def info_admin_bidang(request):
    if request.user.role != 'admin_bidang':
        return HttpResponseForbidden("Anda tidak memiliki akses ke halaman ini.")

    # Ambil bidang dari user yang login
    bidang_user = request.user.bidang  # pastikan User model memiliki field ini

    # Filter data berdasarkan bidang user
    kegiatan_qs = Kegiatan.objects.filter(bidang=bidang_user)
    subkegiatan_qs = SubKegiatan.objects.filter(kegiatan__bidang=bidang_user)
    rekening_qs = Rekening.objects.filter(sub_kegiatan__kegiatan__bidang=bidang_user)
    penggunaan_qs = PenggunaanBelanja.objects.filter(rekening__sub_kegiatan__kegiatan__bidang=bidang_user)
    persetujuan_qs = PersetujuanPenggunaanBelanja.objects.filter(bidang=bidang_user)

    # Hitung jumlah data
    jumlah_kegiatan = kegiatan_qs.count()
    jumlah_subkegiatan = subkegiatan_qs.count()
    jumlah_rekening = rekening_qs.count()
    jumlah_penggunaan = penggunaan_qs.count()
    jumlah_disetujui = persetujuan_qs.filter(disetujui=True).count()
    jumlah_ditolak = persetujuan_qs.filter(ditolak=True).count()

    context = {
        'jumlah_kegiatan': jumlah_kegiatan,
        'jumlah_subkegiatan': jumlah_subkegiatan,
        'jumlah_rekening': jumlah_rekening,
        'jumlah_penggunaan': jumlah_penggunaan,
        'jumlah_disetujui': jumlah_disetujui,
        'jumlah_ditolak': jumlah_ditolak,
        'bidang': bidang_user,
    }

    return render(request, 'accounts/info_admin_bidang.html', context)


@login_required
def ahp_info(request):
    jumlah_kegiatan = Kegiatan.objects.count()
    jumlah_subkegiatan = SubKegiatan.objects.count()
    jumlah_rekening = Rekening.objects.count()
    jumlah_penggunaan = PenggunaanBelanja.objects.count()
    jumlah_kriteria = Kriteria.objects.count()

    penggunaan_data = PenggunaanBelanja.objects.values('nama_penggunaan').annotate(total=Sum('jumlah'))
    bobot_kriteria = BobotKriteria.objects.select_related('kriteria').all()

    context = {
        'jumlah_kegiatan': jumlah_kegiatan,
        'jumlah_subkegiatan': jumlah_subkegiatan,
        'jumlah_rekening': jumlah_rekening,
        'jumlah_penggunaan': jumlah_penggunaan,
        'jumlah_kriteria': jumlah_kriteria,
        'penggunaan_data': penggunaan_data,
        'bobot_kriteria': bobot_kriteria,
    }
    return render(request, 'accounts/ahp_info.html', context)




@login_required
def kriteria_dan_perbandingan(request):
    if not hasattr(request.user, 'role') or request.user.role != 'jf_perencana':
        return HttpResponseForbidden("Anda tidak memiliki akses ke halaman ini.")

    list_kriteria = Kriteria.objects.all().order_by('id')
    edit_kriteria = None

    # Hapus kriteria
    if 'hapus_kriteria' in request.GET:
        kriteria = get_object_or_404(Kriteria, id=request.GET.get('hapus_kriteria'))
        kriteria.delete()
        return redirect('kriteria_perbandingan')

    # Reset form perbandingan
    if 'reset_perbandingan' in request.GET:
        if 'perbandingan_data' in request.session:
            del request.session['perbandingan_data']
        messages.info(request, "Form perbandingan berhasil direset.")
        return redirect('kriteria_perbandingan')

    # Edit kriteria
    if 'edit_kriteria' in request.GET:
        edit_kriteria = get_object_or_404(Kriteria, id=request.GET.get('edit_kriteria'))

    # Tambah/Ubah kriteria
    if request.method == 'POST' and 'submit_kriteria' in request.POST:
        if request.POST.get('id'):
            kriteria = get_object_or_404(Kriteria, id=request.POST.get('id'))
            kriteria_form = KriteriaForm(request.POST, instance=kriteria)
        else:
            kriteria_form = KriteriaForm(request.POST)

        if kriteria_form.is_valid():
            kriteria_form.save()
            return redirect('kriteria_perbandingan')
    else:
        kriteria_form = KriteriaForm(instance=edit_kriteria)

    # === Form Perbandingan Kriteria ===
    perbandingan_data = request.session.get('perbandingan_data')

    if request.method == 'POST' and 'submit_perbandingan' in request.POST:
        perbandingan_form = PerbandinganKriteriaForm(request.POST)
        if perbandingan_form.is_valid():
            # Simpan ke database
            PerbandinganKriteria.objects.all().delete()
            kriteria = list(Kriteria.objects.all())
            for i in range(len(kriteria)):
                for j in range(i+1, len(kriteria)):
                    field_name = f'kriteria_{kriteria[i].id}_vs_{kriteria[j].id}'
                    nilai = float(perbandingan_form.cleaned_data[field_name])
                    PerbandinganKriteria.objects.create(
                        kriteria_1=kriteria[i],
                        kriteria_2=kriteria[j],
                        nilai=nilai
                    )
                    PerbandinganKriteria.objects.create(
                        kriteria_1=kriteria[j],
                        kriteria_2=kriteria[i],
                        nilai=1 / nilai
                    )
            # Simpan ke session
            request.session['perbandingan_data'] = request.POST
            messages.success(request, "Data perbandingan berhasil disimpan.")
        else:
            messages.error(request, "Terdapat kesalahan dalam form.")
    else:
        # Gunakan data dari session kalau ada
        if perbandingan_data:
            perbandingan_form = PerbandinganKriteriaForm(perbandingan_data)
        else:
            perbandingan_form = PerbandinganKriteriaForm()

    return render(request, 'accounts/kriteria_perbandingan.html', {
        'kriteria_form': kriteria_form,
        'perbandingan_form': perbandingan_form,
        'list_kriteria': list_kriteria,
        'edit_kriteria': edit_kriteria
    })







from django.shortcuts import render
from .models import Kriteria, PerbandinganKriteria, BobotKriteria
import numpy as np

def hasil_ahp(request):
    kriteria = list(Kriteria.objects.all())
    n = len(kriteria)

    # Matriks Perbandingan
    matrix = np.ones((n, n))

    for i in range(n):
        for j in range(n):
            if i != j:
                try:
                    nilai = PerbandinganKriteria.objects.get(kriteria_1=kriteria[i], kriteria_2=kriteria[j]).nilai
                    matrix[i][j] = nilai
                except PerbandinganKriteria.DoesNotExist:
                    matrix[i][j] = 1  # default jika tidak ditemukan
    # Normalisasi matriks dan hitung bobot
    row_geom_mean = np.prod(matrix, axis=1) ** (1/n)
    weights = row_geom_mean / np.sum(row_geom_mean)

    bobot_kriteria = []
    for i in range(n):
        bobot_kriteria.append({
            'kriteria': kriteria[i].nama,
            'bobot': round(weights[i], 4)
        })

    context = {
        'kriteria': kriteria,
        'perbandingan': PerbandinganKriteria.objects.all(),
        'bobot_kriteria': bobot_kriteria
    }
    return render(request, 'accounts/hasil_ahp.html', context)



@login_required
def perbandingan_alternatif(request):
    if request.user.role != 'jf_perencana':
        return HttpResponseForbidden("Tidak punya akses")

    kriteria_list = Kriteria.objects.all()
    alternatif_list = PenggunaanBelanja.objects.all()

    if request.method == 'POST':
        if 'reset' in request.POST:
            PerbandinganAlternatif.objects.all().delete()
            messages.success(request, "Data perbandingan alternatif berhasil direset.")
            return redirect('perbandingan_alternatif')

        form = PerbandinganAlternatifForm(request.POST)
        if form.is_valid():
            for field_name, value in form.cleaned_data.items():
                try:
                    # Parse field_name
                    parts = field_name.split('_')
                    kriteria_id = int(parts[1])
                    alt1_id = int(parts[3])
                    alt2_id = int(parts[5])
                    nilai = float(value)

                    # Simpan dua arah
                    PerbandinganAlternatif.objects.update_or_create(
                        kriteria_id=kriteria_id,
                        alternatif_1_id=alt1_id,
                        alternatif_2_id=alt2_id,
                        defaults={'nilai': nilai}
                    )
                    PerbandinganAlternatif.objects.update_or_create(
                        kriteria_id=kriteria_id,
                        alternatif_1_id=alt2_id,
                        alternatif_2_id=alt1_id,
                        defaults={'nilai': 1 / nilai}
                    )
                except Exception as e:
                    messages.error(request, f"Error saat menyimpan perbandingan: {e}")
            messages.success(request, "Perbandingan alternatif berhasil disimpan.")
            return redirect('perbandingan_alternatif')
    else:
        initial_data = {}
        for kriteria in kriteria_list:
            for i in range(len(alternatif_list)):
                for j in range(i + 1, len(alternatif_list)):
                    try:
                        obj = PerbandinganAlternatif.objects.get(
                            kriteria=kriteria,
                            alternatif_1=alternatif_list[i],
                            alternatif_2=alternatif_list[j]
                        )
                        key = f'kriteria_{kriteria.id}_alt_{alternatif_list[i].id}_vs_{alternatif_list[j].id}'
                        initial_data[key] = str(int(obj.nilai))
                    except PerbandinganAlternatif.DoesNotExist:
                        pass
        form = PerbandinganAlternatifForm(initial=initial_data)

    return render(request, 'accounts/perbandingan_alternatif.html', {
        'form': form,
        'kriteria_list': kriteria_list,
        'alternatif_list': alternatif_list,
    })


@login_required
def hasil_alternatif(request):
    if request.user.role != 'jf_perencana':
        return HttpResponseForbidden("Tidak punya akses")

    kriteria_list = Kriteria.objects.all()
    alternatif_list = PenggunaanBelanja.objects.all()

    alternatif_ids = [alt.id for alt in alternatif_list]
    alternatif_names = {alt.id: alt.nama_penggunaan for alt in alternatif_list}

    hasil_per_kriteria = []
    jumlah_kriteria = len(kriteria_list)
    if jumlah_kriteria == 0:
        messages.error(request, "Belum ada kriteria.")
        return render(request, 'accounts/hasil_alternatif.html', {})

    ranking_akhir = {alt.id: 0 for alt in alternatif_list}

    for kriteria in kriteria_list:
        n = len(alternatif_list)
        matriks = np.ones((n, n))

        # Buat matriks perbandingan
        for i in range(n):
            for j in range(i + 1, n):
                try:
                    nilai = PerbandinganAlternatif.objects.get(
                        kriteria=kriteria,
                        alternatif_1_id=alternatif_ids[i],
                        alternatif_2_id=alternatif_ids[j]
                    ).nilai
                    matriks[i][j] = nilai
                    matriks[j][i] = 1 / nilai
                except:
                    matriks[i][j] = 1
                    matriks[j][i] = 1

        # Normalisasi dan hitung bobot
        kolom_jumlah = np.sum(matriks, axis=0)
        matriks_normal = matriks / kolom_jumlah
        bobot_alternatif = np.mean(matriks_normal, axis=1)

        # Simpan ke hasil
        hasil = []
        for idx, alt in enumerate(alternatif_list):
            hasil.append({
                'alternatif': alternatif_names[alt.id],
                'bobot': round(bobot_alternatif[idx], 4)
            })
            ranking_akhir[alt.id] += bobot_alternatif[idx]

        hasil_per_kriteria.append({
            'kriteria': kriteria.nama,
            'hasil': hasil
        })

    # Hitung total dan ranking akhir
    total_bobot = []
    for alt in alternatif_list:
        total_bobot.append({
            'alternatif': alternatif_names[alt.id],
            'nilai': round(ranking_akhir[alt.id] / jumlah_kriteria, 4)
        })

    # Urutkan berdasarkan nilai tertinggi
    total_bobot = sorted(total_bobot, key=lambda x: x['nilai'], reverse=True)

    return render(request, 'accounts/hasil_alternatif.html', {
        'hasil_per_kriteria': hasil_per_kriteria,
        'ranking_akhir': total_bobot,
    })






@login_required
def admin_bidang_dashboard(request):
    if request.user.role != 'admin_bidang':
        messages.error(request, "Anda tidak memiliki izin mengakses halaman ini!")
        return redirect('login')

    penggunaan_form = PenggunaanBelanjaForm()

    if request.method == 'POST':
        post = request.POST
        penggunaan_id = post.get('penggunaan_id')

        if 'submit_penggunaan' in post:
            if penggunaan_id:
                penggunaan = get_object_or_404(PenggunaanBelanja, id=penggunaan_id)
                penggunaan_form = PenggunaanBelanjaForm(post, instance=penggunaan)
            else:
                penggunaan_form = PenggunaanBelanjaForm(post)

            if penggunaan_form.is_valid():
                penggunaan = penggunaan_form.save(commit=False)
                rekening_id = post.get('rekening')
                if rekening_id:
                    rekening = get_object_or_404(Rekening, id=rekening_id)
                    if rekening.sub_kegiatan.kegiatan.bidang == request.user.bidang:
                        penggunaan.rekening = rekening
                        penggunaan.save()
                        messages.success(request, "Penggunaan Belanja berhasil disimpan.")
                    else:
                        messages.error(request, "Anda tidak memiliki izin untuk rekening ini.")
                else:
                    messages.error(request, "Rekening tidak ditemukan.")
            else:
                messages.error(request, "Gagal menyimpan penggunaan belanja.")
            return redirect('admin_bidang_dashboard')

        elif 'hapus_penggunaan' in post:
            try:
                penggunaan = PenggunaanBelanja.objects.get(id=penggunaan_id)
                if penggunaan.rekening.sub_kegiatan.kegiatan.bidang == request.user.bidang:
                    penggunaan.delete()
                    messages.success(request, "Penggunaan Belanja berhasil dihapus.")
                else:
                    messages.error(request, "Anda tidak memiliki izin untuk menghapus data ini.")
            except PenggunaanBelanja.DoesNotExist:
                messages.error(request, "Data tidak ditemukan.")
            return redirect('admin_bidang_dashboard')

    kegiatan_list = Kegiatan.objects.filter(bidang=request.user.bidang).prefetch_related(
        'sub_kegiatans__rekenings__penggunaan_belanjas'
    )

    context = {
        'kegiatan_list': kegiatan_list,
        'penggunaan_form': penggunaan_form,
    }
    return render(request, 'accounts/admin_bidang_dashboard.html', context)





