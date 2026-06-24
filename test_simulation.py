"""
test_simulation.py
==================
Pengujian otomatis (headless, tanpa jendela grafis) untuk logika inti AI:
algoritma A* dan perencana misi. Jalankan dengan:

    python test_simulation.py

Semua pengujian harus lulus ("ALL TESTS PASSED").
"""

import random

from astar import astar
from warehouse import build_grid, plan_mission, START, PICKUPS, DROP


def test_basic_path():
    """A* menemukan jalur lurus di baris bawah dengan biaya yang benar."""
    grid = build_grid()
    r = astar(grid, (10, 0), (10, 14))
    assert r["success"], "seharusnya menemukan jalur di baris bawah"
    assert r["cost"] == 14, f"diharapkan 14, dapat {r['cost']}"
    # jalur kontigu & tidak menembus rak
    for a, b in zip(r["path"], r["path"][1:]):
        assert abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1
        assert grid[b[0]][b[1]] == 0
    print("test_basic_path OK")


def test_optimality_random():
    """200 pasang titik acak: selalu menemukan jalur valid >= batas bawah Manhattan."""
    grid = build_grid()
    rows, cols = len(grid), len(grid[0])
    free = [(i, j) for i in range(rows) for j in range(cols) if grid[i][j] == 0]
    random.seed(1)
    for _ in range(200):
        s, g = random.sample(free, 2)
        res = astar(grid, s, g)
        assert res["success"], f"tidak ada jalur {s}->{g}"
        lower_bound = abs(s[0] - g[0]) + abs(s[1] - g[1])
        assert res["cost"] >= lower_bound, "biaya di bawah batas bawah Manhattan"
        for a, b in zip(res["path"], res["path"][1:]):
            assert grid[b[0]][b[1]] == 0
    print("test_optimality_random OK")


def test_unreachable_goal():
    """Tujuan di atas rak harus mengembalikan success=False."""
    grid = build_grid()
    res = astar(grid, (10, 0), (1, 1))  # (1,1) adalah rak
    assert not res["success"]
    print("test_unreachable_goal OK")


def test_full_mission():
    """Misi penuh: kontigu, semua barang dikunjungi, berakhir di DROP."""
    grid = build_grid()
    m = plan_mission(grid, START, PICKUPS, DROP)
    assert len(m["segments"]) == len(PICKUPS) + 1
    assert m["full_path"][0] == START
    assert m["full_path"][-1] == DROP
    for a, b in zip(m["full_path"], m["full_path"][1:]):
        assert abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1, f"ada celah {a}->{b}"
    for pk in PICKUPS:
        assert pk in m["full_path"], f"barang {pk} tidak dikunjungi"
    print("test_full_mission OK")


if __name__ == "__main__":
    test_basic_path()
    test_optimality_random()
    test_unreachable_goal()
    test_full_mission()
    print("\nALL TESTS PASSED")
