"""
warehouse.py
============
Definisi lingkungan (environment) gudang dan perencana misi (mission planner).

Lingkungan:
  - Peta grid: 0 = lorong (bisa dilewati), 1 = rak (obstacle).
  - Beberapa titik AMBIL (pickup) tempat barang berada di rak.
  - Satu titik ANTAR (packing/drop) tempat barang dikumpulkan.

Mission planner:
  - Robot harus mengambil sejumlah barang lalu mengantarnya ke titik antar.
  - Strategi perencanaan: greedy nearest-neighbor berdasarkan estimasi
    jarak A*. Robot selalu menuju target terdekat berikutnya.
  - Setiap segmen perjalanan dihitung jalurnya dengan A* (lihat astar.py).

Ini mendemonstrasikan alur AI lengkap:
  INPUT (peta + daftar order)  ->  PLANNING (urutan kunjungan + A*)  ->
  OUTPUT (rute optimal + metrik).
"""

from astar import astar, heuristic

# Layout gudang: setiap baris adalah string.
#   '.' = lorong kosong
#   '#' = rak (obstacle)
# Ukuran 15 kolom x 11 baris. Rak disusun seperti gudang nyata.
LAYOUT = [
    "...............",
    ".#.#.#.#.#.#.#.",
    ".#.#.#.#.#.#.#.",
    ".#.#.#.#.#.#.#.",
    "...............",
    ".#.#.#.#.#.#.#.",
    ".#.#.#.#.#.#.#.",
    ".#.#.#.#.#.#.#.",
    "...............",
    ".#.#.#.#.#.#.#.",
    "...............",
]


def build_grid(layout=LAYOUT):
    """Mengubah layout string menjadi grid angka (0 = kosong, 1 = rak)."""
    return [[0 if ch == "." else 1 for ch in row] for row in layout]


# Konfigurasi misi default.
# START  : posisi awal robot (pojok kiri bawah).
# DROP   : titik antar / packing station (pojok kanan bawah).
# PICKUPS: lokasi barang yang harus diambil (di lorong, dekat rak).
START = (10, 0)
DROP = (10, 14)
PICKUPS = [
    (4, 3),
    (0, 7),
    (8, 11),
    (4, 13),
    (8, 1),
]


def plan_mission(grid, start, pickups, drop):
    """Merencanakan urutan kunjungan + jalur lengkap untuk seluruh misi.

    Strategi: greedy nearest-neighbor.
      1. Dari posisi saat ini, pilih pickup yang JARAK A*-nya terkecil.
      2. Pindah ke sana, ambil barang, ulangi untuk pickup tersisa.
      3. Setelah semua barang diambil, menuju titik antar (drop).

    Mengembalikan dict berisi:
      - segments        : list segmen, tiap segmen = hasil astar() + label
      - order           : urutan target yang dikunjungi
      - full_path       : gabungan seluruh jalur (untuk animasi mulus)
      - total_cost      : total langkah seluruh misi
      - total_explored  : total node dieksplorasi seluruh segmen
    """
    remaining = list(pickups)
    current = start
    segments = []
    order = []
    total_cost = 0
    total_explored = 0
    full_path = [start]

    # Kunjungi semua pickup dengan greedy nearest-neighbor.
    while remaining:
        # Pilih target terdekat berdasar jalur A* nyata (bukan sekadar heuristik).
        best = None
        best_result = None
        for target in remaining:
            result = astar(grid, current, target)
            if not result["success"]:
                continue
            if best_result is None or result["cost"] < best_result["cost"]:
                best = target
                best_result = result

        if best is None:
            break  # ada target yang tak terjangkau

        best_result["label"] = "AMBIL"
        best_result["target"] = best
        segments.append(best_result)
        order.append(best)
        total_cost += best_result["cost"]
        total_explored += best_result["explored_count"]
        full_path.extend(best_result["path"][1:])

        current = best
        remaining.remove(best)

    # Segmen terakhir: menuju titik antar.
    final = astar(grid, current, drop)
    if final["success"]:
        final["label"] = "ANTAR"
        final["target"] = drop
        segments.append(final)
        order.append(drop)
        total_cost += final["cost"]
        total_explored += final["explored_count"]
        full_path.extend(final["path"][1:])

    return {
        "segments": segments,
        "order": order,
        "full_path": full_path,
        "total_cost": total_cost,
        "total_explored": total_explored,
    }
