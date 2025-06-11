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





@login_required
def kepala_dinas_dashboard(request):
    if request.user.role != 'kepala_dinas':
        messages.error(request, "Anda tidak memiliki izin mengakses halaman ini.")
        return redirect('login')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User berhasil ditambahkan.")
            return redirect('kepala_dinas_dashboard')
        else:
            messages.error(request, "Gagal menambahkan user. Periksa kembali formulir.")
            print(form.errors)  # Debugging jika ada error
    else:
        form = CustomUserCreationForm()

    user_list = CustomUser.objects.filter(role__in=['jf_perencana', 'admin_bidang'])

    return render(request, 'accounts/kepala_dinas_dashboard.html', {
        'form': form,
        'user_list': user_list
    })





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
        if 'submit_kegiatan' in request.POST:
            kegiatan_form = KegiatanForm(request.POST)
            if kegiatan_form.is_valid():
                kegiatan_form.save()
                messages.success(request, "Kegiatan berhasil ditambahkan.")
                return redirect('jf_perencana_dashboard')
            else:
                messages.error(request, "Gagal menambahkan kegiatan.")

        elif 'submit_subkegiatan' in request.POST:
            sub_kegiatan_form = SubKegiatanForm(request.POST)
            if sub_kegiatan_form.is_valid():
                subkegiatan = sub_kegiatan_form.save(commit=False)
                kegiatan_id = request.POST.get('kegiatan')
                if kegiatan_id:
                    subkegiatan.kegiatan = Kegiatan.objects.get(id=kegiatan_id)
                    subkegiatan.save()
                    messages.success(request, "Sub Kegiatan berhasil ditambahkan.")
                    return redirect('jf_perencana_dashboard')
                else:
                    messages.error(request, "Kegiatan tidak ditemukan untuk sub kegiatan.")
            else:
                messages.error(request, "Gagal menambahkan sub kegiatan.")

        elif 'submit_rekening' in request.POST:
            rekening_form = RekeningForm(request.POST)
            if rekening_form.is_valid():
                rekening = rekening_form.save(commit=False)
                sub_kegiatan_id = request.POST.get('sub_kegiatan')
                if sub_kegiatan_id:
                    rekening.sub_kegiatan = SubKegiatan.objects.get(id=sub_kegiatan_id)
                    rekening.save()
                    messages.success(request, "Rekening berhasil ditambahkan.")
                    return redirect('jf_perencana_dashboard')
                else:
                    messages.error(request, "Sub Kegiatan tidak ditemukan untuk rekening.")
            else:
                messages.error(request, "Gagal menambahkan rekening.")

        elif 'submit_penggunaan' in request.POST:
            penggunaan_form = PenggunaanBelanjaForm(request.POST)
            if penggunaan_form.is_valid():
                penggunaan = penggunaan_form.save(commit=False)
                rekening_id = request.POST.get('rekening')
                if rekening_id:
                    try:
                        penggunaan.rekening = Rekening.objects.get(id=rekening_id)
                        penggunaan.save()
                        messages.success(request, "Penggunaan Belanja berhasil ditambahkan.")
                        return redirect('jf_perencana_dashboard')
                    except Rekening.DoesNotExist:
                        messages.error(request, "Rekening tidak ditemukan untuk penggunaan belanja.")
                else:
                    messages.error(request, "Rekening tidak dipilih untuk penggunaan belanja.")
            else:
                messages.error(request, "Gagal menambahkan penggunaan belanja.")


    kegiatan_per_bidang = {}
    for kode, nama in Kegiatan.BIDANG_CHOICES:
       kegiatan_per_bidang[kode] = {
    'nama': nama,
    'kegiatan_list': Kegiatan.objects.filter(bidang=kode).prefetch_related('sub_kegiatans__rekenings__penggunaan_belanjas')
}


    context = {
        'kegiatan_form': kegiatan_form,
        'sub_kegiatan_form': sub_kegiatan_form,
        'penggunaan_form': penggunaan_form,
        'rekening_form': rekening_form,
        'kegiatan_per_bidang': kegiatan_per_bidang,
    }
    return render(request, 'accounts/jf_perencana_dashboard.html', context)

from django.shortcuts import render

def ahp_info(request):
    return render(request, 'accounts/ahp_info.html')


@login_required
def kriteria_dan_perbandingan(request):
    # Cek apakah user adalah JF Perencana
    if not hasattr(request.user, 'role') or request.user.role != 'jf_perencana':
        return HttpResponseForbidden("Anda tidak memiliki akses ke halaman ini.")

    # Form tambah kriteria
    if request.method == 'POST' and 'submit_kriteria' in request.POST:
        kriteria_form = KriteriaForm(request.POST)
        if kriteria_form.is_valid():
            kriteria_form.save()
            return redirect('kriteria_perbandingan')
    else:
        kriteria_form = KriteriaForm()

    # Form input perbandingan kriteria
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
                    # Resiprokal
                    PerbandinganKriteria.objects.create(
                        kriteria_1=kriteria[j],
                        kriteria_2=kriteria[i],
                        nilai=1/nilai
                    )
            return redirect('hasil_ahp')
    else:
        perbandingan_form = PerbandinganKriteriaForm()

    return render(request, 'accounts/kriteria_perbandingan.html', {
        'kriteria_form': kriteria_form,
        'perbandingan_form': perbandingan_form,
    })


def hasil_ahp(request):
    # Ambil semua kriteria dan perbandingan
    kriteria = Kriteria.objects.all()
    perbandingan = PerbandinganKriteria.objects.all()

    # Kamu bisa proses perhitungan AHP di sini sesuai kebutuhanmu

    context = {
        'kriteria': kriteria,
        'perbandingan': perbandingan,
        # tambahkan hasil perhitungan AHP kalau sudah diproses
    }
    return render(request, 'accounts/hasil_ahp.html', context)

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




