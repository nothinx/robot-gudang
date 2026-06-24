# WarehouseBot — Simulasi Robot Pengantar Barang Otonom di Gudang (A\*)

Projek Akhir Artificial Intelligence 2026 — kategori **AI untuk Searching & Planning / Robotics**.

Sebuah robot gudang otonom bertugas mengambil beberapa barang dari rak lalu
mengantarnya ke titik *packing*. Robot merencanakan urutan kunjungan dan mencari
jalur paling optimal menggunakan algoritma **A\* (A-Star)**, lalu mengeksekusinya
dalam simulasi visual (Pygame).

![Tampilan simulasi WarehouseBot](screenshot_simulasi.png)

## Alur AI

```
INPUT                    PLANNING                         OUTPUT
peta gudang (grid)  -->  urutan kunjungan (greedy NN) -->  rute optimal
daftar order             + jalur tiap segmen (A*)          + animasi gerak robot
                                                           + metrik (jarak, node)
```

## Struktur File

| File             | Isi                                                            |
|------------------|---------------------------------------------------------------|
| `astar.py`       | Algoritma A\* + heuristik Manhattan (inti AI).                 |
| `warehouse.py`   | Peta gudang + perencana misi (greedy nearest-neighbor).       |
| `main.py`        | Simulasi & visualisasi Pygame.                                |
| `requirements.txt` | Dependensi (pygame).                                         |

## Cara Menjalankan

1. Pastikan Python 3.8+ terpasang.
2. Install dependensi:

   ```bash
   pip install -r requirements.txt
   ```

3. Jalankan simulasi:

   ```bash
   python main.py
   ```

## Kontrol

| Tombol  | Fungsi                              |
|---------|-------------------------------------|
| `SPASI` | Jeda / lanjut animasi               |
| `R`     | Acak ulang lokasi barang & jalankan |
| `ESC` / `Q` | Keluar                          |

## Keterangan Visual

- **Kotak abu tua** — rak (obstacle, tidak bisa dilewati).
- **Sel biru muda** — node yang dieksplorasi A\* (cara AI "berpikir").
- **Garis kuning** — jalur optimal yang dipilih.
- **Lingkaran hijau** — titik AMBIL barang.
- **Kotak merah** — titik ANTAR (packing station).
- **Lingkaran oranye** — robot.

## Algoritma A\*

`f(n) = g(n) + h(n)`, dengan `g(n)` = biaya nyata dari titik awal dan
`h(n)` = jarak Manhattan ke tujuan. Karena heuristik Manhattan *admissible*
pada grid gerak 4-arah, A\* dijamin menemukan jalur **paling optimal**
(complete & optimal) sekaligus lebih efisien daripada BFS/Dijkstra karena
pencariannya terarah ke tujuan.

## Evaluasi Keberhasilan

- **Optimalitas** — panjang jalur sama dengan jalur terpendek sebenarnya.
- **Efisiensi** — jumlah node yang dieksplorasi (lebih sedikit = lebih baik).
- **Kelengkapan misi** — seluruh barang berhasil diambil & diantar.
- **Robustness** — tetap menemukan jalur untuk konfigurasi barang acak (tombol `R`).
