from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.timezone import now

from .forms import (
    CustomUserCreationForm,
    KegiatanForm,
    SubKegiatanForm,
    RekeningForm,
    PenggunaanBelanjaForm
)
from .models import (
    CustomUser,
    Kegiatan,
    SubKegiatan,
    Rekening,
    PenggunaanBelanja,
    Kriteria,
    PerbandinganKriteria
)
from .forms import (
    KriteriaForm,
    PerbandinganKriteriaForm
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
                return reverse_lazy('admin_bidang_dashboard')
            elif user.role == 'jf_perencana':
                return reverse_lazy('ahp_info')

        return reverse_lazy('login')





from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import CustomUserCreationForm
from .models import CustomUser

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






from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Kegiatan, SubKegiatan, Rekening, PenggunaanBelanja
from .forms import KegiatanForm, SubKegiatanForm, RekeningForm, PenggunaanBelanjaForm

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import KegiatanForm, SubKegiatanForm, RekeningForm, PenggunaanBelanjaForm
from .models import Kegiatan, SubKegiatan, Rekening, PenggunaanBelanja


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



from django.shortcuts import render

def ahp_info(request):
    return render(request, 'accounts/ahp_info.html')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Kriteria, PerbandinganKriteria
from .forms import KriteriaForm, PerbandinganKriteriaForm

@login_required
def kriteria_dan_perbandingan(request):
    # Akses hanya untuk JF Perencana
    if not hasattr(request.user, 'role') or request.user.role != 'jf_perencana':
        return HttpResponseForbidden("Anda tidak memiliki akses ke halaman ini.")

    # Ambil semua kriteria
    list_kriteria = Kriteria.objects.all().order_by('id')
    edit_kriteria = None

    # === Hapus Kriteria ===
    if 'hapus_kriteria' in request.GET:
        kriteria = get_object_or_404(Kriteria, id=request.GET.get('hapus_kriteria'))
        kriteria.delete()
        return redirect('kriteria_perbandingan')

    # === Edit Kriteria ===
    if 'edit_kriteria' in request.GET:
        edit_kriteria = get_object_or_404(Kriteria, id=request.GET.get('edit_kriteria'))

    # === Tambah/Ubah Kriteria ===
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
    if request.method == 'POST' and 'submit_perbandingan' in request.POST:
        perbandingan_form = PerbandinganKriteriaForm(request.POST)
        if perbandingan_form.is_valid():
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
            return redirect('hasil_ahp')
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

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Kriteria, Alternatif, PerbandinganAlternatif
from itertools import combinations

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from itertools import combinations

from .models import Kriteria, Alternatif, PerbandinganAlternatif

@login_required
def perbandingan_alternatif(request):
    if request.user.role != 'jf_perencana':
        messages.error(request, "Anda tidak memiliki izin mengakses halaman ini!")
        return redirect('login')

    kriteria_list = Kriteria.objects.all()
    alternatif_list = Alternatif.objects.all().select_related('penggunaan')

    context = {
        'kriteria_list': kriteria_list,
        'alternatif_list': alternatif_list,
    }
    return render(request, 'accounts/perbandingan_alternatif.html', context)


import numpy as np
from .models import Kriteria, Alternatif, PerbandinganAlternatif

def hasil_ahp_alternatif(request):
    kriteria_list = Kriteria.objects.all()
    alternatif_list = Alternatif.objects.select_related('penggunaan').all()
    hasil_akhir = []

    for kriteria in kriteria_list:
        n = len(alternatif_list)
        matrix = np.ones((n, n))

        for i in range(n):
            for j in range(n):
                if i != j:
                    try:
                        nilai = PerbandinganAlternatif.objects.get(
                            kriteria=kriteria,
                            alternatif_1=alternatif_list[i],
                            alternatif_2=alternatif_list[j]
                        ).nilai
                        matrix[i][j] = nilai
                    except:
                        matrix[i][j] = 1

        # Normalisasi dan bobot
        row_geom_mean = np.prod(matrix, axis=1) ** (1/n)
        weights = row_geom_mean / np.sum(row_geom_mean)

        hasil_akhir.append({
            'kriteria': kriteria,
            'weights': list(zip(alternatif_list, weights))
        })

    return render(request, 'accounts/hasil_ahp_alternatif.html', {
        'hasil_akhir': hasil_akhir,
        'alternatif_list': alternatif_list,
        'kriteria_list': kriteria_list,
    })




@login_required
def admin_bidang_dashboard(request):
    if request.user.role != 'admin_bidang':
        messages.error(request, "Anda tidak memiliki izin mengakses halaman ini!")
        return redirect('login')

    kegiatan_list = Kegiatan.objects.filter(bidang=request.user.bidang)

    context = {
        'kegiatan_list': kegiatan_list,
    }
    return render(request, 'accounts/admin_bidang_dashboard.html', context)




