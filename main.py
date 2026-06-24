"""
main.py
=======
WarehouseBot — Simulasi Robot Pengantar Barang Otonom di Gudang
menggunakan algoritma A* (Searching & Planning / Robotics).

Robot otonom harus mengambil beberapa barang dari rak lalu mengantarnya
ke titik packing. Robot:
  1. Merencanakan urutan kunjungan (greedy nearest-neighbor).
  2. Mencari jalur optimal tiap segmen dengan A*.
  3. Mengeksekusi dan menganimasikan pergerakan.

Visualisasi (Pygame):
  - Sel biru muda  : node yang DIEKSPLORASI A* (cara AI "berpikir").
  - Garis kuning   : jalur optimal yang dipilih.
  - Kotak abu tua  : rak (obstacle).
  - Lingkaran hijau: titik AMBIL barang.
  - Kotak merah    : titik ANTAR (packing).
  - Robot oranye   : agen yang bergerak.

KONTROL:
  SPASI  -> jeda / lanjut animasi
  R      -> acak ulang lokasi barang dan jalankan ulang
  ESC/Q  -> keluar

Jalankan:  python main.py
"""

import sys
import random
import pygame

from astar import astar
from warehouse import build_grid, plan_mission, START, DROP, PICKUPS

# ----------------------------- Konfigurasi tampilan -----------------------------
CELL = 48                      # ukuran piksel tiap sel grid
MARGIN_TOP = 90                # ruang untuk panel info di atas
FPS = 60
MOVE_DELAY = 6                 # frame per langkah robot (semakin kecil semakin cepat)

# Warna (R, G, B)
C_BG = (24, 26, 32)
C_GRID = (44, 48, 58)
C_RACK = (70, 74, 88)
C_RACK_TOP = (90, 95, 112)
C_FLOOR = (32, 35, 43)
C_EXPLORED = (52, 84, 120)
C_PATH = (240, 200, 60)
C_PICKUP = (60, 200, 120)
C_PICKUP_DONE = (70, 90, 80)
C_DROP = (220, 70, 70)
C_ROBOT = (255, 150, 40)
C_ROBOT_EDGE = (255, 200, 130)
C_TEXT = (235, 238, 245)
C_TEXT_DIM = (150, 156, 170)
C_BADGE = (40, 44, 54)


def cell_rect(r, c):
    """Persegi piksel untuk sel (baris r, kolom c)."""
    return pygame.Rect(c * CELL, MARGIN_TOP + r * CELL, CELL, CELL)


def cell_center(r, c):
    rect = cell_rect(r, c)
    return rect.center


class Simulation:
    def __init__(self):
        self.grid = build_grid()
        self.rows = len(self.grid)
        self.cols = len(self.grid[0])
        self.start = START
        self.drop = DROP
        self.pickups = list(PICKUPS)
        self.reset_plan()

    def random_pickups(self, n=5):
        """Acak lokasi pickup pada sel lorong yang valid (bukan rak/start/drop)."""
        free = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if self.grid[r][c] == 0 and (r, c) not in (self.start, self.drop)
        ]
        self.pickups = random.sample(free, min(n, len(free)))

    def reset_plan(self):
        """Hitung ulang rencana misi dan siapkan state animasi."""
        self.mission = plan_mission(self.grid, self.start, self.pickups, self.drop)
        self.full_path = self.mission["full_path"]
        self.path_index = 0
        self.move_timer = 0
        self.paused = False
        self.delivered = 0
        # Set node yang dieksplorasi (gabungan semua segmen) untuk "jejak berpikir".
        self.explored_set = set()
        for seg in self.mission["segments"]:
            self.explored_set.update(seg["explored"])
        # Set lokasi pickup yang sudah diambil saat animasi berjalan.
        self.collected = set()

    # ----------------------------- Update logika -----------------------------
    def update(self):
        if self.paused:
            return
        if self.path_index >= len(self.full_path) - 1:
            return
        self.move_timer += 1
        if self.move_timer >= MOVE_DELAY:
            self.move_timer = 0
            self.path_index += 1
            pos = self.full_path[self.path_index]
            # Tandai pickup yang dilewati sebagai sudah diambil.
            if pos in self.pickups and pos not in self.collected:
                self.collected.add(pos)
                self.delivered += 1

    # ----------------------------- Render -----------------------------
    def draw(self, screen, font, big, small):
        screen.fill(C_BG)
        self._draw_floor_and_racks(screen)
        self._draw_explored(screen)
        self._draw_path(screen)
        self._draw_points(screen, small)
        self._draw_robot(screen)
        self._draw_panel(screen, font, big, small)

    def _draw_floor_and_racks(self, screen):
        for r in range(self.rows):
            for c in range(self.cols):
                rect = cell_rect(r, c)
                if self.grid[r][c] == 1:
                    pygame.draw.rect(screen, C_RACK, rect)
                    top = pygame.Rect(rect.x, rect.y, rect.width, 8)
                    pygame.draw.rect(screen, C_RACK_TOP, top)
                else:
                    pygame.draw.rect(screen, C_FLOOR, rect)
                pygame.draw.rect(screen, C_GRID, rect, 1)

    def _draw_explored(self, screen):
        # Hanya gambar node yang sudah "tercapai" oleh progres animasi
        # agar terlihat proses pencariannya berkembang.
        for node in self.explored_set:
            rect = cell_rect(*node).inflate(-CELL * 0.5, -CELL * 0.5)
            pygame.draw.rect(screen, C_EXPLORED, rect, border_radius=4)

    def _draw_path(self, screen):
        if len(self.full_path) < 2:
            return
        pts = [cell_center(*p) for p in self.full_path]
        pygame.draw.lines(screen, C_PATH, False, pts, 4)

    def _draw_points(self, screen, small):
        # Titik antar (drop).
        drect = cell_rect(*self.drop).inflate(-10, -10)
        pygame.draw.rect(screen, C_DROP, drect, border_radius=6)
        self._label(screen, small, "ANTAR", self.drop)
        # Titik ambil (pickup).
        for p in self.pickups:
            color = C_PICKUP_DONE if p in self.collected else C_PICKUP
            pygame.draw.circle(screen, color, cell_center(*p), CELL // 3)
            if p not in self.collected:
                self._label(screen, small, "ambil", p)
        # Titik start.
        srect = cell_rect(*self.start).inflate(-18, -18)
        pygame.draw.rect(screen, (120, 130, 150), srect, border_radius=4)

    def _label(self, screen, small, text, node):
        rect = cell_rect(*node)
        img = small.render(text, True, C_TEXT)
        screen.blit(img, (rect.centerx - img.get_width() // 2, rect.bottom - 16))

    def _draw_robot(self, screen):
        pos = self.full_path[self.path_index]
        center = cell_center(*pos)
        pygame.draw.circle(screen, C_ROBOT, center, CELL // 3 + 2)
        pygame.draw.circle(screen, C_ROBOT_EDGE, center, CELL // 3 + 2, 3)
        # "mata" arah robot
        pygame.draw.circle(screen, (40, 30, 20), center, 5)

    def _draw_panel(self, screen, font, big, small):
        title = big.render("WarehouseBot — Simulasi Robot Gudang (A*)", True, C_TEXT)
        screen.blit(title, (12, 12))

        steps_done = self.path_index
        steps_total = len(self.full_path) - 1
        info = (
            f"Barang diambil: {self.delivered}/{len(self.pickups)}    "
            f"Langkah: {steps_done}/{steps_total}    "
            f"Total jalur (A*): {self.mission['total_cost']}    "
            f"Node dieksplorasi: {self.mission['total_explored']}"
        )
        screen.blit(font.render(info, True, C_TEXT_DIM), (12, 46))

        hint = "SPASI: jeda/lanjut   R: acak ulang   ESC: keluar"
        h = small.render(hint, True, C_TEXT_DIM)
        screen.blit(h, (screen.get_width() - h.get_width() - 12, 16))

        if self.path_index >= len(self.full_path) - 1 and steps_total > 0:
            done = font.render("MISI SELESAI — semua barang terantar!", True, C_PICKUP)
            screen.blit(done, (12, 64))
        elif self.paused:
            screen.blit(font.render("[ JEDA ]", True, C_PATH), (12, 64))


def main():
    pygame.init()
    sim = Simulation()
    width = sim.cols * CELL
    height = MARGIN_TOP + sim.rows * CELL
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("WarehouseBot — A* Pathfinding Simulation")
    clock = pygame.time.Clock()

    big = pygame.font.SysFont("Arial", 24, bold=True)
    font = pygame.font.SysFont("Arial", 18)
    small = pygame.font.SysFont("Arial", 13)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key == pygame.K_SPACE:
                    sim.paused = not sim.paused
                elif event.key == pygame.K_r:
                    sim.random_pickups(5)
                    sim.reset_plan()

        sim.update()
        sim.draw(screen, font, big, small)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
