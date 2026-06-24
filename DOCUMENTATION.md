# Dokumentasi Teknis — WarehouseBot

Simulasi Robot Pengantar Barang Otonom di Gudang menggunakan Algoritma **A\* (A-Star)**.
Projek Akhir Artificial Intelligence 2026 — kategori *AI untuk Searching & Planning / Robotics*.

---

## 1. Gambaran Umum

WarehouseBot memodelkan sebuah robot gudang otonom yang harus mengambil beberapa
barang dari rak lalu mengantarkannya ke titik *packing*. Robot tidak diberi rute;
ia **merencanakan rutenya sendiri** dengan dua lapis kecerdasan:

1. **Pencarian jalur (path search)** — menemukan jalur terpendek antar dua titik
   menggunakan algoritma A\*.
2. **Perencanaan tugas (task planning)** — menentukan urutan barang mana yang
   diambil lebih dulu menggunakan strategi *greedy nearest-neighbor*.

Seluruh proses divisualisasikan secara *real-time* dengan Pygame.

### Alur AI (Agent Loop)

```
            ┌──────────────┐      ┌─────────────────────┐      ┌──────────────────┐
  INPUT     │  Peta gudang │      │  PLANNING           │      │  OUTPUT          │
  ───────►  │  (grid)      │ ───► │  • urutan kunjungan │ ───► │  • rute optimal  │
            │  Daftar order│      │    (greedy NN)      │      │  • animasi gerak │
            │  Posisi awal │      │  • jalur tiap       │      │  • metrik kinerja│
            └──────────────┘      │    segmen (A*)      │      └──────────────────┘
                                  └─────────────────────┘
```

---

## 2. Arsitektur & Struktur File

| File             | Peran                      | Isi utama                                                |
|------------------|----------------------------|----------------------------------------------------------|
| `astar.py`       | **Inti AI**                | `heuristic()`, `get_neighbors()`, `astar()`              |
| `warehouse.py`   | **Lingkungan + Planner**   | `LAYOUT`, `build_grid()`, `plan_mission()`               |
| `main.py`        | **Simulasi & Visualisasi** | kelas `Simulation`, *loop* Pygame, *rendering*           |
| `requirements.txt` | Dependensi               | `pygame`                                                 |
| `README.md`      | Panduan singkat            | cara menjalankan & kontrol                               |
| `DOCUMENTATION.md` | Dokumentasi teknis (ini) | arsitektur, algoritma, evaluasi                          |

Ketiga modul Python bersifat **terpisah dan dapat diuji sendiri-sendiri**:
`astar.py` tidak tahu apa-apa soal gudang; `warehouse.py` tidak tahu apa-apa soal
Pygame. Ini memudahkan pengujian dan penggantian komponen.

---

## 3. Representasi Lingkungan

Gudang dimodelkan sebagai **grid 2 dimensi** berukuran 15 kolom × 11 baris.
Tiap sel bernilai:

- `0` — lorong (dapat dilewati robot)
- `1` — rak (obstacle, tidak dapat dilewati)

Layout ditulis sebagai daftar string di `warehouse.py` (`.` = lorong, `#` = rak),
lalu dikonversi `build_grid()` menjadi matriks angka.

Konfigurasi misi default:

| Elemen   | Posisi (baris, kolom) | Keterangan                       |
|----------|-----------------------|----------------------------------|
| START    | (10, 0)               | posisi awal robot (kiri bawah)   |
| DROP     | (10, 14)             | titik antar / packing (kanan bawah) |
| PICKUPS  | 5 titik di lorong     | lokasi barang yang harus diambil |

Robot bergerak **4 arah** (atas, bawah, kiri, kanan); diagonal tidak diizinkan,
sehingga jarak Manhattan menjadi heuristik yang tepat.

---

## 4. Algoritma A\* (`astar.py`)

A\* adalah *informed search* yang mengevaluasi node berdasarkan:

```
f(n) = g(n) + h(n)
```

- `g(n)` — biaya nyata dari titik awal ke node `n` (jumlah langkah).
- `h(n)` — estimasi biaya dari `n` ke tujuan, memakai **jarak Manhattan**:

  ```
  h((r1,c1), (r2,c2)) = |r1 - r2| + |c1 - c2|
  ```

### Pseudocode

```
fungsi astar(grid, start, goal):
    open ← priority queue berisi start, prioritas f(start)
    g[start] ← 0
    selama open tidak kosong:
        current ← node dengan f terkecil
        jika current == goal: rekonstruksi & kembalikan jalur
        untuk tiap tetangga valid dari current:
            g_baru ← g[current] + 1
            jika g_baru < g[tetangga]:
                came_from[tetangga] ← current
                g[tetangga] ← g_baru
                f ← g_baru + h(tetangga, goal)
                masukkan tetangga ke open
    kembalikan "gagal"   # tidak ada jalur
```

### Mengapa A\*, bukan yang lain?

| Algoritma   | Optimal? | Lengkap? | Efisiensi eksplorasi          |
|-------------|----------|----------|-------------------------------|
| DFS         | ❌       | ❌*      | bisa tersesat jauh            |
| BFS         | ✅ (unit) | ✅       | boros: menyebar ke segala arah |
| Dijkstra    | ✅       | ✅       | menyebar tanpa arah ke tujuan |
| **A\***     | ✅       | ✅       | **terarah** → paling sedikit  |

Karena heuristik Manhattan **admissible** (tak pernah melebih-lebihkan biaya
sebenarnya pada gerak 4-arah), A\* dijamin menemukan jalur **paling optimal**
sekaligus mengeksplorasi node lebih sedikit dibanding Dijkstra/BFS.

### Nilai kembalian `astar()`

```python
{
    "path": [...],          # daftar node start→goal (kosong jika gagal)
    "cost": int,            # panjang jalur (jumlah langkah)
    "explored": [...],      # urutan node yang dieksplorasi (untuk animasi)
    "explored_count": int,  # metrik efisiensi
    "success": bool,
}
```

---

## 5. Perencanaan Misi (`warehouse.py` → `plan_mission`)

Mengunjungi banyak barang lalu mengantar adalah varian **Travelling Salesman
Problem (TSP)** yang mahal jika dipecahkan secara optimal. Untuk simulasi yang
responsif, dipakai heuristik **greedy nearest-neighbor**:

1. Dari posisi robot saat ini, hitung jarak A\* ke setiap barang yang belum diambil.
2. Pilih barang dengan jarak A\* **terkecil**, pindah ke sana, tandai diambil.
3. Ulangi sampai semua barang diambil.
4. Terakhir, cari jalur A\* menuju titik antar (DROP).

Jarak antar target memakai **biaya A\* nyata** (bukan sekadar garis lurus), sehingga
keputusan urutan memperhitungkan rak yang menghalangi.

Keluaran `plan_mission()` menggabungkan seluruh segmen menjadi `full_path` (satu
daftar node mulus dari START sampai DROP) plus metrik total.

---

## 6. Simulasi & Visualisasi (`main.py`)

Kelas `Simulation` menyimpan state dan menjalankan *game loop* Pygame.

Elemen visual:

| Elemen            | Warna           | Makna                                  |
|-------------------|-----------------|----------------------------------------|
| Kotak abu tua     | abu             | rak (obstacle)                         |
| Sel biru muda     | biru            | node yang dieksplorasi A\*             |
| Garis kuning      | kuning          | jalur optimal terpilih                 |
| Lingkaran hijau   | hijau           | titik AMBIL barang (belum diambil)     |
| Lingkaran oranye  | oranye          | robot                                  |
| Kotak merah       | merah           | titik ANTAR (packing)                  |

Kontrol:

| Tombol  | Fungsi                              |
|---------|-------------------------------------|
| `SPASI` | jeda / lanjut animasi               |
| `R`     | acak ulang lokasi barang & jalankan |
| `ESC`/`Q` | keluar                            |

Animasi memajukan robot 1 sel tiap `MOVE_DELAY` frame, sambil menandai barang yang
dilewati sebagai "diambil".

---

## 7. Cara Menjalankan

```bash
# 1. Install dependensi
pip install -r requirements.txt

# 2. Jalankan simulasi
python main.py
```

Membutuhkan Python 3.8+ dan Pygame 2.x.

---

## 8. Evaluasi Keberhasilan

| Kriteria          | Cara ukur                                                            |
|-------------------|---------------------------------------------------------------------|
| **Optimalitas**   | panjang jalur A\* = jalur terpendek sebenarnya (≥ batas bawah Manhattan) |
| **Efisiensi**     | jumlah node dieksplorasi; A\* ≪ Dijkstra/BFS untuk jalur yang sama  |
| **Kelengkapan**   | seluruh barang berhasil diambil & diantar (delivered == jumlah order) |
| **Robustness**    | tetap menemukan rute valid untuk konfigurasi barang acak (tombol `R`) |

### Pengujian otomatis

Logika inti dapat diuji tanpa membuka jendela grafis (mode *headless*):

```python
from astar import astar
from warehouse import build_grid, plan_mission, START, PICKUPS, DROP

grid = build_grid()

# 1. A* menemukan jalur & valid (tidak menembus rak)
r = astar(grid, (10, 0), (10, 14))
assert r["success"] and r["cost"] == 14

# 2. Misi penuh: kontigu, semua barang dikunjungi, berakhir di DROP
m = plan_mission(grid, START, PICKUPS, DROP)
assert m["full_path"][0] == START and m["full_path"][-1] == DROP
for pk in PICKUPS:
    assert pk in m["full_path"]
```

Verifikasi yang dijalankan selama pengembangan: jalur valid untuk **200 pasang titik
acak**, biaya selalu ≥ batas bawah Manhattan, goal di atas rak mengembalikan
`success=False`, dan misi penuh selalu kontigu serta mengunjungi semua barang.

---

## 9. Kemungkinan Pengembangan

- Mengganti greedy NN dengan TSP optimal (mis. *held-karp*) untuk misi kecil.
- Menambah biaya gerak diagonal (heuristik *octile*) dan gerak 8-arah.
- Robot ganda dengan penghindaran tabrakan antar-agen.
- Rak dinamis / rintangan bergerak (*replanning* A\* tiap langkah).
- Membandingkan A\* vs Dijkstra vs BFS langsung di dalam UI.

---

## 10. Pembagian Tugas (template)

| Anggota       | Peran                | Tanggung jawab                                          |
|---------------|----------------------|---------------------------------------------------------|
| [Anggota 1]   | Algorithm Engineer   | Implementasi A\* (`astar.py`), heuristik, uji optimalitas |
| [Anggota 2]   | Simulation Developer | Lingkungan gudang & visualisasi (`warehouse.py`, `main.py`) |
| [Anggota 3]   | Planner & Evaluator  | Mission planner, metrik evaluasi, dokumentasi           |
| Bersama       | Presentasi & Laporan | Penyusunan PPT, uji coba akhir, latihan presentasi      |

> Ganti `[Anggota x]` dengan nama & NIM anggota kelompok Anda.
