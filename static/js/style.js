// Menggunakan event listener untuk menjalankan script setelah DOM siap
document.addEventListener("DOMContentLoaded", function() {
    // Menyiapkan grafik penjualan menggunakan Chart.js
    const ctx = document.getElementById('salesChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['January', 'February', 'March', 'April', 'May', 'June'],
            datasets: [{
                label: 'Penjualan Pulsa',
                data: [1000, 1200, 1500, 1800, 2200, 2500],
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Menangani form untuk menambahkan stok
    const stokForm = document.getElementById('stokForm');
    const stokTable = document.getElementById('stokTable').getElementsByTagName('tbody')[0];
    let stokList = []; // Array untuk menyimpan data stok

    // Fungsi untuk menambahkan data stok ke dalam tabel
    const addStokToTable = (stok) => {
        const row = stokTable.insertRow();
        const cellIndex = row.insertCell(0);
        const cellJenis = row.insertCell(1);
        const cellProvider = row.insertCell(2);
        const cellValue = row.insertCell(3);
        const cellJumlah = row.insertCell(4);

        cellIndex.textContent = stokList.length + 1; // Menampilkan nomor urut
        cellJenis.textContent = stok.jenis;
        cellProvider.textContent = stok.provider;
        cellValue.textContent = stok.value;
        cellJumlah.textContent = stok.jumlah;
    };

    // Event listener untuk menangani submit form
    stokForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const jenis = document.getElementById('jenis').value;
        const provider = document.getElementById('provider').value;
        const value = document.getElementById('value').value;
        const jumlah = document.getElementById('stok').value;

        // Validasi input sebelum ditambahkan ke tabel
        if (jenis && provider && value && jumlah) {
            const newStok = {
                jenis: jenis,
                provider: provider,
                value: value,
                jumlah: jumlah
            };

            stokList.push(newStok); // Menambahkan data ke array stokList
            addStokToTable(newStok); // Memasukkan data ke dalam tabel

            // Reset form setelah submit
            stokForm.reset();
        } else {
            alert('Harap isi semua bidang!');
        }
    });
});
