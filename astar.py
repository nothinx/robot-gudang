"""
astar.py
========
Implementasi algoritma A* (A-Star) untuk pencarian jalur (pathfinding)
pada peta gudang berbasis grid.

A* dipilih karena merupakan algoritma informed search yang OPTIMAL dan
COMPLETE selama heuristik yang digunakan admissible (tidak pernah
melebih-lebihkan biaya sesungguhnya). Pada grid dengan gerak 4-arah,
jarak Manhattan adalah heuristik admissible yang ideal.

f(n) = g(n) + h(n)
  g(n) = biaya nyata dari titik awal ke node n
  h(n) = estimasi biaya dari node n ke tujuan (heuristik Manhattan)
"""

import heapq


def heuristic(a, b):
    """Heuristik jarak Manhattan antara dua titik (baris, kolom).

    Cocok untuk gerak 4-arah (atas/bawah/kiri/kanan) dan bersifat
    admissible sehingga menjamin A* menemukan jalur paling optimal.
    """
    (r1, c1), (r2, c2) = a, b
    return abs(r1 - r2) + abs(c1 - c2)


def get_neighbors(node, grid):
    """Mengembalikan tetangga yang valid (bukan rak/obstacle, di dalam peta).

    grid: list 2D. 0 = jalur kosong, 1 = rak (obstacle / tidak bisa dilewati).
    Gerakan terbatas 4 arah: atas, bawah, kiri, kanan.
    """
    rows, cols = len(grid), len(grid[0])
    r, c = node
    neighbors = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0:
            neighbors.append((nr, nc))
    return neighbors


def astar(grid, start, goal):
    """Mencari jalur terpendek dari start ke goal menggunakan A*.

    Mengembalikan dict berisi:
      - path           : list node dari start ke goal (kosong jika gagal)
      - cost            : panjang jalur (jumlah langkah)
      - explored        : list node yang sempat dieksplorasi (untuk visualisasi)
      - explored_count  : jumlah node yang dieksplorasi (metrik efisiensi)
      - success         : True/False apakah jalur ditemukan
    """
    # Antrian prioritas (min-heap) berisi tuple (f_score, counter, node).
    # counter dipakai sebagai tie-breaker agar heap stabil.
    counter = 0
    open_heap = [(heuristic(start, goal), counter, start)]

    came_from = {}                 # untuk merekonstruksi jalur
    g_score = {start: 0}           # biaya nyata terbaik yang diketahui
    explored = []                  # urutan node yang ditutup (untuk animasi)
    in_open = {start}              # set node yang masih di open list

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        in_open.discard(current)

        # Tujuan tercapai -> rekonstruksi jalur dengan menelusuri came_from
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return {
                "path": path,
                "cost": len(path) - 1,
                "explored": explored,
                "explored_count": len(explored),
                "success": True,
            }

        explored.append(current)

        for neighbor in get_neighbors(current, grid):
            tentative_g = g_score[current] + 1  # biaya antar sel = 1
            if tentative_g < g_score.get(neighbor, float("inf")):
                # Jalur baru ke tetangga ini lebih baik -> catat
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f = tentative_g + heuristic(neighbor, goal)
                if neighbor not in in_open:
                    counter += 1
                    heapq.heappush(open_heap, (f, counter, neighbor))
                    in_open.add(neighbor)

    # Open list habis tanpa mencapai goal -> tidak ada jalur
    return {
        "path": [],
        "cost": float("inf"),
        "explored": explored,
        "explored_count": len(explored),
        "success": False,
    }
