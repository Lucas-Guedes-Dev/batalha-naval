from menu import run_menu
import pygame
import math
import random
from classes.navio import Ship
from classes.tabuleiro import Board

GRID_SIZE = 10
CELL_SIZE = 50
MARGIN = 2
UI_HEIGHT = 56
SIDE_W = 120

WIDTH = GRID_SIZE * CELL_SIZE + SIDE_W
HEIGHT = GRID_SIZE * CELL_SIZE + UI_HEIGHT


NAVY = (8,  18,  52)
OCEAN_DARK = (0,  48, 110)
OCEAN_MID = (0,  80, 160)
OCEAN_LIGHT = (30, 130, 210)
OCEAN_FOAM = (140, 200, 240)
WHITE = (255, 255, 255)
OFF_WHITE = (220, 230, 245)
GOLD = (220, 185,  55)
GOLD_DARK = (160, 120,  20)
RED_HIT = (210,  45,  45)
RED_GLOW = (255, 100,  60)
MISS_BLUE = (60, 160, 220)
GRAY_DARK = (50,  60,  80)
GRAY_MID = (100, 115, 140)
GREEN_OK = (50, 200, 100)
YELLOW = (255, 220,  50)
BLACK = (0,   0,   0)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Batalha Naval")

font_hud = pygame.font.SysFont("consolas", 18, bold=True)
font_big = pygame.font.SysFont("consolas", 38, bold=True)
font_mid = pygame.font.SysFont("consolas", 24, bold=True)
font_small = pygame.font.SysFont("consolas", 16)
font_tiny = pygame.font.SysFont("consolas", 13)


board_p1 = Board()
board_p2 = Board()

fleet = [1]
setup_index = 0
setup_rotation = "H"
current_player = 1
GAME_STATE = "SETUP_P1"

transition_start_time = 0
last_attack_time = 0
RESULT_DURATION = 1100

winner = None
hits_p1 = 0
hits_p2 = 0
misses_p1 = 0
misses_p2 = 0


sectors_p1 = [0, 0, 0, 0]
sectors_p2 = [0, 0, 0, 0]
SECTOR_LABELS = ["Sup. Esq.", "Sup. Dir.", "Inf. Esq.", "Inf. Dir."]


SHIP_COLORS = {
    1: ((180, 190, 210), (100, 110, 135)),
    2: ((100, 160, 200), (50,  90, 140)),
    3: ((80, 180, 140), (30, 100,  80)),
    4: ((200, 150,  50), (130,  85,  20)),
    5: ((190,  70,  60), (110,  30,  25)),
}


particles = []


def spawn_particles(x, y, kind="hit"):
    for _ in range(22 if kind == "hit" else 10):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(
            1.2, 5.0) if kind == "hit" else random.uniform(0.5, 2.5)
        color = random.choice([RED_HIT, RED_GLOW, GOLD, WHITE]) if kind == "hit" \
            else random.choice([MISS_BLUE, OCEAN_FOAM, OFF_WHITE])
        size = random.randint(2, 5) if kind == "hit" else random.randint(2, 4)
        life = random.randint(28, 55)
        particles.append({
            "x": x, "y": y,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed - random.uniform(0, 2),
            "color": color, "size": size,
            "life": life, "max_life": life,
        })


def update_draw_particles():
    dead = []
    for p in particles:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.12
        p["life"] -= 1
        ratio = p["life"] / p["max_life"]
        alpha = int(255 * ratio)
        r, g, b = p["color"]
        s = pygame.Surface((p["size"]*2, p["size"]*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (r, g, b, alpha),
                           (p["size"], p["size"]), p["size"])
        screen.blit(s, (int(p["x"]) - p["size"], int(p["y"]) - p["size"]))
        if p["life"] <= 0:
            dead.append(p)
    for p in dead:
        particles.remove(p)


def wave_offset(col, row, t, amplitude=3.0, freq=0.35, speed=1.1):
    """Per-cell vertical sine displacement for the ocean shimmer."""
    return math.sin(col * freq + row * 0.4 + t * speed) * amplitude


def ocean_color(col, row, t):
    """Subtle animated tint for each empty cell."""
    w = (math.sin(col * 0.4 + row * 0.3 + t * 0.9) + 1) / 2
    r = int(OCEAN_DARK[0] + (OCEAN_MID[0] - OCEAN_DARK[0]) * w)
    g = int(OCEAN_DARK[1] + (OCEAN_MID[1] - OCEAN_DARK[1]) * w)
    b = int(OCEAN_DARK[2] + (OCEAN_MID[2] - OCEAN_DARK[2]) * w)
    return (r, g, b)


def draw_foam_line(surface, col, row, t, cell_x, cell_y):
    """A single animated foam streak inside an ocean cell."""
    phase = col * 1.7 + row * 0.9
    offset_y = int(CELL_SIZE * 0.35 + math.sin(phase + t * 1.4)
                   * CELL_SIZE * 0.12)
    alpha = int(55 + 30 * math.sin(phase + t * 2.1))
    length = int(CELL_SIZE * 0.45 + math.cos(phase + t) * CELL_SIZE * 0.15)
    start_x = cell_x + (CELL_SIZE - MARGIN - length) // 2
    s = pygame.Surface((length, 2), pygame.SRCALPHA)
    s.fill((200, 230, 255, alpha))
    surface.blit(s, (start_x, cell_y + offset_y))


GRID_X = 0
GRID_Y = UI_HEIGHT


def cell_rect(col, row):
    return pygame.Rect(
        GRID_X + col * CELL_SIZE,
        GRID_Y + row * CELL_SIZE,
        CELL_SIZE - MARGIN,
        CELL_SIZE - MARGIN
    )


def draw_board_ocean(board, t, reveal_ships=False):
    """Draw the attack board with animated ocean cells."""
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            rect = cell_rect(col, row)
            state = board.get_cell_state((row, col))

            if state == "empty":
                color = ocean_color(col, row, t)
                pygame.draw.rect(screen, color, rect, border_radius=3)
                draw_foam_line(screen, col, row, t, rect.x, rect.y)

                rim = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                pygame.draw.rect(rim, (255, 255, 255, 14),
                                 (0, 0, rect.w, rect.h), border_radius=3)
                pygame.draw.rect(rim, (255, 255, 255, 22),
                                 (0, 0, rect.w, rect.h), 1, border_radius=3)
                screen.blit(rim, rect.topleft)

            elif state == "miss":

                pygame.draw.rect(screen, OCEAN_DARK, rect, border_radius=3)
                cx, cy = rect.centerx, rect.centery
                pulse = int(4 + 2 * math.sin(t * 3 + col + row))
                pygame.draw.circle(screen, MISS_BLUE, (cx, cy), pulse + 8, 2)
                pygame.draw.circle(screen, OCEAN_FOAM, (cx, cy), pulse + 3, 1)

                dot_s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                pygame.draw.circle(dot_s, (140, 200, 255, 80),
                                   (rect.w//2, rect.h//2), 10)
                screen.blit(dot_s, rect.topleft)

            elif state == "hit":

                pygame.draw.rect(screen, (80, 15, 15), rect, border_radius=3)
                cx, cy = rect.centerx, rect.centery
                flicker = int(6 * math.sin(t * 8 + col * 2.3 + row * 1.7))
                fire_s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                pygame.draw.circle(
                    fire_s, (220, 60, 20, 130 + flicker*3), (rect.w//2, rect.h//2), 14)
                pygame.draw.circle(
                    fire_s, (255, 160, 30, 90 + flicker*2), (rect.w//2, rect.h//2), 8)
                screen.blit(fire_s, rect.topleft)
                pygame.draw.rect(screen, RED_HIT, rect, 2, border_radius=3)

    if reveal_ships:
        for ship in board.ships:
            _blit_ship(ship)


def draw_setup_board(board, t):
    """Draw grid during placement phase (your own board)."""
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            rect = cell_rect(col, row)
            color = ocean_color(col, row, t)
            pygame.draw.rect(screen, color, rect, border_radius=3)
            draw_foam_line(screen, col, row, t, rect.x, rect.y)
            rim = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            pygame.draw.rect(rim, (255, 255, 255, 20),
                             (0, 0, rect.w, rect.h), 1, border_radius=3)
            screen.blit(rim, rect.topleft)

    for ship in board.ships:
        _blit_ship(ship)


def _draw_ship_vector(surf, x, y, size, is_h, color_body, color_dark, alpha=255):
    """
    Draw a sleek geometric warship onto `surf` at pixel position (x, y).
    The ship always points right / down depending on is_h.
    Dimensions: size*CELL_SIZE long, CELL_SIZE tall (before any rotation).
    """
    W = size * CELL_SIZE - MARGIN
    H = CELL_SIZE - MARGIN
    pad = 6
    inner_h = H - pad * 2
    body_y = pad

    s = pygame.Surface((W, H), pygame.SRCALPHA)

    tip_w = max(inner_h // 2, 8)

    bow_pts = [
        (W - tip_w, body_y),
        (W,         body_y + inner_h // 2),
        (W - tip_w, body_y + inner_h),
    ]

    stern_inset = inner_h // 5
    hull_pts = [
        (0,         body_y + stern_inset),
        (W - tip_w, body_y),
        (W,         body_y + inner_h // 2),
        (W - tip_w, body_y + inner_h),
        (0,         body_y + inner_h - stern_inset),
    ]
    pygame.draw.polygon(s, (*color_body, alpha), hull_pts)

    deck_y = body_y + inner_h // 2 - 2
    pygame.draw.rect(s, (*color_dark, min(alpha, 180)),
                     (2, deck_y, W - tip_w - 2, 4))

    tower_w = max(inner_h - 2, 6)
    tower_h = inner_h - 6
    tower_x = int(W * 0.22)
    tower_y = body_y + 3
    pygame.draw.rect(s, (*color_dark, alpha),
                     (tower_x, tower_y, tower_w, tower_h),
                     border_radius=2)

    win_y = tower_y + tower_h // 3
    pygame.draw.rect(s, (200, 230, 255, min(alpha, 200)),
                     (tower_x + 3, win_y, tower_w - 6, 3),
                     border_radius=1)

    barrel_y = body_y + inner_h // 2 - 1
    barrel_x0 = tower_x + tower_w
    barrel_x1 = int(W * 0.58)
    pygame.draw.line(s, (*color_dark, alpha),
                     (barrel_x0, barrel_y), (barrel_x1, barrel_y), 3)
    pygame.draw.circle(s, (*color_dark, alpha), (barrel_x1, barrel_y), 3)

    pygame.draw.polygon(s, (*color_dark, min(alpha, 220)), hull_pts, 1)

    if is_h:
        surf.blit(s, (x, y))
    else:

        rotated = pygame.transform.rotate(s, -90)
        surf.blit(rotated, (x, y))


def _blit_ship(ship, alpha=255):
    rows = [p[0] for p in ship.positions]
    cols = [p[1] for p in ship.positions]
    min_row, min_col = min(rows), min(cols)
    px = GRID_X + min_col * CELL_SIZE
    py = GRID_Y + min_row * CELL_SIZE
    is_h = len(set(rows)) == 1
    color_body, color_dark = SHIP_COLORS[ship.size]
    _draw_ship_vector(screen, px, py, ship.size, is_h,
                      color_body, color_dark, alpha)


def draw_preview(row, col, size, rotation, t):
    """Ghost ship preview that follows the mouse during placement."""
    board = board_p1 if GAME_STATE == "SETUP_P1" else board_p2
    is_h = rotation == "H"

    positions = []
    valid = True
    for i in range(size):
        r, c = (row, col + i) if is_h else (row + i, col)
        positions.append((r, c))
        if r < 0 or r >= GRID_SIZE or c < 0 or c >= GRID_SIZE \
                or not board.is_valid_position((r, c)):
            valid = False

    pulse_a = int(140 + 80 * abs(math.sin(t * 4)))
    cell_color = (50, 200, 100) if valid else (200, 50, 50)

    for (r, c) in positions:
        if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
            rect = cell_rect(c, r)
            bg = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            bg.fill((*cell_color, 45 + int(25 * abs(math.sin(t * 3)))))
            pygame.draw.rect(bg, (*cell_color, pulse_a),
                             (0, 0, rect.w, rect.h), 2, border_radius=3)
            screen.blit(bg, rect.topleft)

    if positions:
        r0, c0 = positions[0]
        if all(0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE for r, c in positions):
            px = GRID_X + c0 * CELL_SIZE
            py = GRID_Y + r0 * CELL_SIZE
            color_body, color_dark = SHIP_COLORS[size]
            ghost_alpha = 170 if valid else 80
            _draw_ship_vector(screen, px, py, size, is_h,
                              color_body, color_dark, ghost_alpha)


def draw_top_bar(state, t):

    bar = pygame.Surface((WIDTH, UI_HEIGHT), pygame.SRCALPHA)
    bar.fill((8, 20, 55, 240))
    screen.blit(bar, (0, 0))
    pygame.draw.line(screen, GOLD, (0, UI_HEIGHT - 1),
                     (WIDTH, UI_HEIGHT - 1), 1)

    cx = (WIDTH - SIDE_W) // 2

    if state in ("SETUP_P1", "SETUP_P2"):
        player = 1 if state == "SETUP_P1" else 2
        ship_size = fleet[setup_index]
        label = f"JOGADOR {player}  ·  POSICIONE O NAVIO [{ship_size}]"
        hint = "Seta ↓ para girar  |  Click para colocar"
        rot_icon = "━━" if setup_rotation == "H" else "┃"
        rot_text = font_tiny.render(f"ROT: {rot_icon}", True, GOLD)

        text = font_hud.render(label, True, OFF_WHITE)
        screen.blit(text, (cx - text.get_width()//2, 8))
        hint_s = font_tiny.render(hint, True, GRAY_MID)
        screen.blit(hint_s, (cx - hint_s.get_width()//2, 32))
        screen.blit(rot_text, (WIDTH - SIDE_W - rot_text.get_width() - 8, 20))

    elif state == "PLAYING":
        label = f"JOGADOR {current_player}  ·  SUA VEZ"
        pulse = int(180 + 75 * abs(math.sin(t * 2.5)))
        color = (pulse, 220, 255) if current_player == 1 else (
            255, pulse // 2 + 80, 80)
        text = font_hud.render(label, True, color)
        screen.blit(text, (cx - text.get_width()//2, 16))

    elif state == "SHOW_RESULT":
        label = f"JOGADOR {current_player}  ·  SUA VEZ"
        text = font_hud.render(label, True, GOLD)
        screen.blit(text, (cx - text.get_width()//2, 16))


SHIP_NAMES = {1: "Scout", 2: "Patrulha",
              3: "Cruzador", 4: "Porta-aviões", 5: "Couraçado"}


def draw_side_panel(t):
    sx = GRID_SIZE * CELL_SIZE
    panel = pygame.Surface((SIDE_W, HEIGHT - UI_HEIGHT), pygame.SRCALPHA)
    panel.fill((8, 22, 58, 240))
    screen.blit(panel, (sx, UI_HEIGHT))
    pygame.draw.line(screen, GOLD, (sx, UI_HEIGHT), (sx, HEIGHT), 1)

    def label(txt, y, color=GRAY_MID, f=font_tiny):
        s = f.render(txt, True, color)
        screen.blit(s, (sx + SIDE_W//2 - s.get_width()//2, y))

    if GAME_STATE in ("SETUP_P1", "SETUP_P2"):
        label("── FROTA ──", UI_HEIGHT + 14, GOLD, font_tiny)
        names_short = {1: "Scout", 2: "Patrulha", 3: "Cruzador",
                       4: "Carrier", 5: "Encouraç."}
        for i, sz in enumerate(fleet):
            y_item = UI_HEIGHT + 36 + i * 36
            cb, cd = SHIP_COLORS[sz]
            is_done = i < setup_index
            is_curr = i == setup_index

            swatch_x = sx + 10
            swatch_y = y_item
            swatch_w, swatch_h = 10, 10
            if is_done:
                sw_col = (40, 60, 40)
                border = (60, 120, 60)
            elif is_curr:

                pa = int(200 + 55 * abs(math.sin(t * 4)))
                sw_col = (*cb, pa)
                border = GOLD
            else:
                sw_col = (*cb, 80)
                border = (*cd, 120)

            sw_surf = pygame.Surface((swatch_w, swatch_h), pygame.SRCALPHA)
            sw_surf.fill(sw_col if len(sw_col) == 4 else (*sw_col, 255))
            screen.blit(sw_surf, (swatch_x, swatch_y))
            pygame.draw.rect(screen, border,
                             (swatch_x, swatch_y, swatch_w, swatch_h), 1)

            name_color = GOLD if is_curr else (
                GRAY_MID if is_done else OFF_WHITE)
            ns = font_tiny.render(names_short[sz], True, name_color)
            screen.blit(ns, (swatch_x + 14, swatch_y - 1))

            pip_x = swatch_x
            pip_y = swatch_y + 13
            for p in range(sz):
                pip_col = cd if is_curr else (
                    GRAY_DARK if is_done else GRAY_MID)
                pygame.draw.rect(screen, pip_col,
                                 (pip_x + p * 8, pip_y, 6, 4),
                                 border_radius=1)

            if is_done:
                ck = font_tiny.render("✓", True, (60, 180, 80))
                screen.blit(ck, (sx + SIDE_W - 18, swatch_y - 1))

            if is_curr:
                pulse_x = int(3 * abs(math.sin(t * 5)))
                arr = font_tiny.render("▶", True, GOLD)
                screen.blit(arr, (sx + SIDE_W - 18 - pulse_x, swatch_y - 1))

    else:
        label("── PLACAR ──", UI_HEIGHT + 14, GOLD, font_tiny)
        label(f"J1  {hits_p1} acertos", UI_HEIGHT + 38, (100, 200, 255))
        label(f"J2  {hits_p2} acertos", UI_HEIGHT + 58, (255, 130, 100))

        label("── FROTA ──", UI_HEIGHT + 96, GOLD, font_tiny)
        for i, sz in enumerate(fleet):
            board = board_p2 if current_player == 1 else board_p1
            ship_obj = next((s for s in board.ships if s.size == sz), None)
            y_item = UI_HEIGHT + 116 + i * 22

            cb, cd = SHIP_COLORS[sz]
            if ship_obj and ship_obj.is_sunk():

                swatch = pygame.Surface((8, 8), pygame.SRCALPHA)
                swatch.fill((120, 30, 30, 200))
                screen.blit(swatch, (sx + 10, y_item + 1))
                icon_s = font_tiny.render("✕ " + "─" * sz, True, (150, 50, 50))
            else:
                swatch = pygame.Surface((8, 8), pygame.SRCALPHA)
                swatch.fill((*cb, 200))
                screen.blit(swatch, (sx + 10, y_item + 1))
                icon_s = font_tiny.render("■" * sz, True, OCEAN_FOAM)

            screen.blit(icon_s, (sx + 22, y_item))

    cx2 = sx + SIDE_W // 2
    cy2 = HEIGHT - 50
    r = 20
    pulse = 0.7 + 0.3 * abs(math.sin(t * 1.2))
    for ang, lbl in [(0, "N"), (90, "E"), (180, "S"), (270, "W")]:
        rad = math.radians(ang - 90)
        tx2 = cx2 + int(r * math.cos(rad))
        ty2 = cy2 + int(r * math.sin(rad))
        col_c = GOLD if lbl == "N" else GRAY_MID
        s = font_tiny.render(lbl, True, col_c)
        screen.blit(s, (tx2 - s.get_width()//2, ty2 - s.get_height()//2))
    pygame.draw.circle(screen, GRAY_DARK, (cx2, cy2), int(r * pulse), 1)
    pygame.draw.circle(screen, GOLD, (cx2, cy2), 3)


def draw_transition(t):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((5, 12, 40, 220))
    screen.blit(overlay, (0, 0))

    next_p = 2 if current_player == 1 else 1
    elapsed = (pygame.time.get_ticks() - transition_start_time) / 1000.0
    progress = min(elapsed / 3.0, 1.0)

    scan_y = int(HEIGHT * progress)
    pygame.draw.line(screen, GOLD, (0, scan_y), (WIDTH, scan_y), 1)

    cy = HEIGHT // 2
    pulse = abs(math.sin(t * 3)) * 6

    lines = [
        (font_mid, f"JOGADOR {current_player} TERMINOU", GRAY_MID, cy - 64),
        (font_big, "PASSANDO O TURNO", GOLD,     cy - 10),
        (font_mid, f"VEZ DO JOGADOR {next_p}",
         OCEAN_FOAM, cy + 58 + int(pulse)),
    ]
    for font, text, color, y in lines:
        s = font.render(text, True, color)
        screen.blit(s, (WIDTH//2 - s.get_width()//2, y))

    bar_w = int((WIDTH - 80) * (1 - progress))
    pygame.draw.rect(screen, GRAY_DARK, (40, HEIGHT -
                     30, WIDTH - 80, 8), border_radius=4)
    pygame.draw.rect(screen, GOLD,      (40, HEIGHT - 30,
                     bar_w, 8),       border_radius=4)


def _draw_sector_heatmap(cx, cy, size, sectors, color_main, t):
    """Draw a 2×2 mini-grid heatmap showing which sectors were attacked most."""
    half = size // 2
    gap = 3
    max_s = max(sectors) if max(sectors) > 0 else 1
    quadrants = [
        (cx - half,      cy - half,      sectors[0]),
        (cx + gap,       cy - half,      sectors[1]),
        (cx - half,      cy + gap,       sectors[2]),
        (cx + gap,       cy + gap,       sectors[3]),
    ]
    hottest = sectors.index(max(sectors))
    for i, (qx, qy, count) in enumerate(quadrants):
        intensity = count / max_s
        r = int(color_main[0] * intensity)
        g = int(color_main[1] * intensity)
        b = int(color_main[2] * intensity)
        base_col = (max(r, 20), max(g, 20), max(b, 20))
        qw = half - gap
        pygame.draw.rect(screen, base_col,
                         (qx, qy, qw, qw), border_radius=3)

        if i == hottest and count > 0:
            pulse_a = int(180 + 75 * abs(math.sin(t * 3)))
            outline = pygame.Surface((qw, qw), pygame.SRCALPHA)
            pygame.draw.rect(outline, (255, 220, 80, pulse_a),
                             (0, 0, qw, qw), 2, border_radius=3)
            screen.blit(outline, (qx, qy))

        if count > 0:
            cs = font_tiny.render(str(count), True, WHITE)
            screen.blit(cs, (qx + qw//2 - cs.get_width()//2,
                             qy + qw//2 - cs.get_height()//2))

    labels = [("E", cx - half - 14, cy),
              ("D", cx + half + gap + 2, cy),
              ("↑", cx, cy - half - 14),
              ("↓", cx, cy + half + gap + 2)]
    for lbl, lx, ly in labels:
        ls = font_tiny.render(lbl, True, GRAY_MID)
        screen.blit(ls, (lx - ls.get_width()//2, ly - ls.get_height()//2))


def _draw_stat_bar(x, y, w, h, value, max_val, color, label, count_label):
    """Horizontal bar for accuracy/misses stats."""
    ratio = value / max_val if max_val > 0 else 0

    pygame.draw.rect(screen, GRAY_DARK, (x, y, w, h), border_radius=3)

    fill_w = int(w * ratio)
    if fill_w > 0:
        pygame.draw.rect(screen, color, (x, y, fill_w, h), border_radius=3)

    ls = font_tiny.render(label, True, GRAY_MID)
    screen.blit(ls, (x - ls.get_width() - 6, y + h//2 - ls.get_height()//2))

    cs = font_tiny.render(count_label, True, OFF_WHITE)
    screen.blit(cs, (x + w + 5, y + h//2 - cs.get_height()//2))


def draw_win_screen(t):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((5, 12, 40, 235))
    screen.blit(overlay, (0, 0))

    loser = 2 if winner == 1 else 1
    pulse = abs(math.sin(t * 2.5)) * 6

    h1 = hits_p1
    h2 = hits_p2
    m1 = misses_p1
    m2 = misses_p2
    t1 = h1 + m1
    t2 = h2 + m2
    acc1 = int(100 * h1 / t1) if t1 > 0 else 0
    acc2 = int(100 * h2 / t2) if t2 > 0 else 0

    cx = WIDTH // 2

    dy = int(pulse)
    trophy_y = 28
    dpts = [
        (cx,      trophy_y - dy),
        (cx + 22, trophy_y + 18 - dy),
        (cx,      trophy_y + 36 - dy),
        (cx - 22, trophy_y + 18 - dy),
    ]
    pygame.draw.polygon(screen, GOLD, dpts)
    pygame.draw.polygon(screen, WHITE, dpts, 1)

    title_y = trophy_y + 44
    ts = font_big.render(f"JOGADOR {winner} VENCEU!", True, GOLD)
    shadow = font_big.render(f"JOGADOR {winner} VENCEU!", True, (80, 50, 0))
    screen.blit(shadow, (cx - ts.get_width()//2 + 2, title_y + 2))
    screen.blit(ts,     (cx - ts.get_width()//2,     title_y))

    div_y = title_y + ts.get_height() + 8
    pygame.draw.line(screen, GOLD, (40, div_y), (WIDTH - 40, div_y), 1)

    col1_x = cx - 4
    col2_x = cx + 4
    col_w = cx - 50

    stats_y = div_y + 14

    j1_col = (100, 200, 255)
    j2_col = (255, 130, 100)
    w_col = GOLD

    def center_text(txt, font, color, x_center, y):
        s = font.render(txt, True, color)
        screen.blit(s, (x_center - s.get_width()//2, y))

    j1_cx = col1_x - col_w // 2
    j2_cx = col2_x + col_w // 2

    center_text("JOGADOR 1", font_small,
                w_col if winner == 1 else j1_col, j1_cx, stats_y)
    center_text("JOGADOR 2", font_small,
                w_col if winner == 2 else j2_col, j2_cx, stats_y)

    crown_cx = j1_cx if winner == 1 else j2_cx
    crown_y = stats_y - 14
    crown_pts = [
        (crown_cx - 12, crown_y + 10),
        (crown_cx - 12, crown_y),
        (crown_cx - 6,  crown_y + 6),
        (crown_cx,      crown_y),
        (crown_cx + 6,  crown_y + 6),
        (crown_cx + 12, crown_y),
        (crown_cx + 12, crown_y + 10),
    ]
    pygame.draw.polygon(screen, GOLD, crown_pts)

    row_y = stats_y + 20

    bar_h = 10
    bar_w = col_w - 30
    lbl_off = 26

    def stat_row(label, v1, v2, max_v, c1, c2, y):
        lbl_s = font_tiny.render(label, True, GRAY_MID)
        screen.blit(lbl_s, (cx - lbl_s.get_width()//2, y))

        bx1 = col1_x - bar_w - lbl_off
        pygame.draw.rect(screen, GRAY_DARK,  (bx1, y + 14,
                         bar_w, bar_h), border_radius=3)
        fw1 = int(bar_w * v1 / max_v) if max_v > 0 else 0
        if fw1:
            pygame.draw.rect(
                screen, c1, (bx1, y + 14, fw1, bar_h), border_radius=3)
        vs1 = font_tiny.render(str(v1), True, c1)
        screen.blit(vs1, (bx1 - vs1.get_width() - 4, y + 13))

        bx2 = col2_x + lbl_off
        pygame.draw.rect(screen, GRAY_DARK,  (bx2, y + 14,
                         bar_w, bar_h), border_radius=3)
        fw2 = int(bar_w * v2 / max_v) if max_v > 0 else 0
        if fw2:
            pygame.draw.rect(
                screen, c2, (bx2, y + 14, fw2, bar_h), border_radius=3)
        vs2 = font_tiny.render(str(v2), True, c2)
        screen.blit(vs2, (bx2 + bar_w + 4, y + 13))

    max_t = max(t1, t2, 1)
    max_h = max(h1, h2, 1)
    max_m = max(m1, m2, 1)

    stat_row("TIROS",   t1, t2, max_t, j1_col, j2_col, row_y)
    stat_row("ACERTOS", h1, h2, max_h, GREEN_OK, GREEN_OK, row_y + 32)
    stat_row("ERROS",   m1, m2, max_m, RED_HIT, RED_HIT,   row_y + 64)

    acc_y = row_y + 90
    center_text(f"Precisão: {acc1}%", font_tiny, j1_col, j1_cx, acc_y)
    center_text(f"Precisão: {acc2}%", font_tiny, j2_col, j2_cx, acc_y)

    pygame.draw.line(screen, GRAY_DARK,
                     (40, acc_y + 18), (WIDTH - 40, acc_y + 18), 1)

    heat_y = acc_y + 30
    hmap_lbl = font_tiny.render("SETORES MAIS ATACADOS", True, GOLD)
    screen.blit(hmap_lbl, (cx - hmap_lbl.get_width()//2, heat_y))

    hmap_size = 88
    _draw_sector_heatmap(j1_cx, heat_y + 60, hmap_size, sectors_p1, j1_col, t)
    _draw_sector_heatmap(j2_cx, heat_y + 60, hmap_size, sectors_p2, j2_col, t)

    def hottest_label(sectors, x_center, y):
        if max(sectors) == 0:
            return
        idx = sectors.index(max(sectors))
        s = font_tiny.render(f"▲ {SECTOR_LABELS[idx]}", True, GOLD)
        screen.blit(s, (x_center - s.get_width()//2, y))

    hottest_label(sectors_p1, j1_cx, heat_y + 110)
    hottest_label(sectors_p2, j2_cx, heat_y + 110)

    prompt_y = HEIGHT - 22
    pa = int(160 + 95 * abs(math.sin(t * 2)))
    ps = font_tiny.render(
        "ENTER  →  novo jogo     ESC  →  sair", True, (pa, pa, pa))
    screen.blit(ps, (cx - ps.get_width()//2, prompt_y))

    if random.random() < 0.20:
        sx2 = random.randint(20, WIDTH - 20)
        sy2 = random.randint(20, HEIGHT // 3)
        spawn_particles(sx2, sy2, "hit")


def get_enemy_board():
    return board_p2 if current_player == 1 else board_p1


def start_transition():
    global GAME_STATE, transition_start_time
    GAME_STATE = "TRANSITION"
    transition_start_time = pygame.time.get_ticks()


def handle_transition():
    global GAME_STATE, current_player
    if pygame.time.get_ticks() - transition_start_time >= 3000:
        current_player = 2 if current_player == 1 else 1
        GAME_STATE = "PLAYING"


def start_show_result():
    global GAME_STATE, last_attack_time
    GAME_STATE = "SHOW_RESULT"
    last_attack_time = pygame.time.get_ticks()


def handle_show_result():
    if pygame.time.get_ticks() - last_attack_time >= RESULT_DURATION:
        start_transition()


def next_setup():
    global setup_index, GAME_STATE
    setup_index += 1
    if setup_index >= len(fleet):
        setup_index = 0
        if GAME_STATE == "SETUP_P1":
            GAME_STATE = "SETUP_P2"
        elif GAME_STATE == "SETUP_P2":
            GAME_STATE = "PLAYING"


def place_ship_manual(board, row, col, size, rotation):
    positions = []
    for i in range(size):
        pos = (row, col + i) if rotation == "H" else (row + i, col)
        if not board.is_valid_position(pos):
            return False
        positions.append(pos)
    ship = Ship(size)
    ship.place(positions)
    board.ships.append(ship)
    return True


def reset_game():
    global board_p1, board_p2, setup_index, setup_rotation
    global current_player, GAME_STATE, winner, hits_p1, hits_p2, particles
    global misses_p1, misses_p2, sectors_p1, sectors_p2
    board_p1 = Board()
    board_p2 = Board()
    setup_index = 0
    setup_rotation = "H"
    current_player = 1
    GAME_STATE = "SETUP_P1"
    winner = None
    hits_p1 = hits_p2 = 0
    misses_p1 = misses_p2 = 0
    sectors_p1 = [0, 0, 0, 0]
    sectors_p2 = [0, 0, 0, 0]
    particles.clear()


def main():
    global GAME_STATE, setup_rotation, winner, hits_p1, hits_p2, current_player
    global misses_p1, misses_p2, sectors_p1, sectors_p2

    clock = pygame.time.Clock()

    action = run_menu(screen, WIDTH, HEIGHT)
    if action == "quit":
        pygame.quit()
        return

    running = True

    while running:
        t = pygame.time.get_ticks() / 1000.0

        screen.fill(NAVY)

        mouse_x, mouse_y = pygame.mouse.get_pos()
        col = (mouse_x - GRID_X) // CELL_SIZE
        row = (mouse_y - GRID_Y) // CELL_SIZE

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    setup_rotation = "V" if setup_rotation == "H" else "H"
                if event.key == pygame.K_RETURN and GAME_STATE == "WIN":
                    reset_game()
                if event.key == pygame.K_ESCAPE and GAME_STATE == "WIN":
                    running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:

                if GAME_STATE == "SETUP_P1":
                    size = fleet[setup_index]
                    if place_ship_manual(board_p1, row, col, size, setup_rotation):
                        spawn_particles(
                            GRID_X + col * CELL_SIZE + CELL_SIZE//2,
                            GRID_Y + row * CELL_SIZE + CELL_SIZE//2,
                            "miss"
                        )
                        next_setup()

                elif GAME_STATE == "SETUP_P2":
                    size = fleet[setup_index]
                    if place_ship_manual(board_p2, row, col, size, setup_rotation):
                        spawn_particles(
                            GRID_X + col * CELL_SIZE + CELL_SIZE//2,
                            GRID_Y + row * CELL_SIZE + CELL_SIZE//2,
                            "miss"
                        )
                        next_setup()

                elif GAME_STATE == "PLAYING":
                    enemy_board = get_enemy_board()
                    result = enemy_board.attack((row, col))

                    if result is not None:
                        px = GRID_X + col * CELL_SIZE + CELL_SIZE // 2
                        py = GRID_Y + row * CELL_SIZE + CELL_SIZE // 2
                        spawn_particles(px, py, result)

                        sec_r = 0 if row < GRID_SIZE // 2 else 2
                        sec_c = 0 if col < GRID_SIZE // 2 else 1
                        sec_idx = sec_r + sec_c

                        if current_player == 1:
                            sectors_p1[sec_idx] += 1
                            if result == "hit":
                                hits_p1 += 1
                            else:
                                misses_p1 += 1
                        else:
                            sectors_p2[sec_idx] += 1
                            if result == "hit":
                                hits_p2 += 1
                            else:
                                misses_p2 += 1

                        if enemy_board.all_sunk():
                            winner = current_player
                            GAME_STATE = "WIN"
                        else:
                            start_show_result()

        if GAME_STATE == "SETUP_P1":
            draw_setup_board(board_p1, t)
            draw_preview(row, col, fleet[setup_index], setup_rotation, t)
            draw_top_bar("SETUP_P1", t)
            draw_side_panel(t)

        elif GAME_STATE == "SETUP_P2":
            draw_setup_board(board_p2, t)
            draw_preview(row, col, fleet[setup_index], setup_rotation, t)
            draw_top_bar("SETUP_P2", t)
            draw_side_panel(t)

        elif GAME_STATE == "PLAYING":
            draw_board_ocean(get_enemy_board(), t)
            draw_top_bar("PLAYING", t)
            draw_side_panel(t)

        elif GAME_STATE == "SHOW_RESULT":
            handle_show_result()
            draw_board_ocean(get_enemy_board(), t)
            draw_top_bar("SHOW_RESULT", t)
            draw_side_panel(t)

        elif GAME_STATE == "TRANSITION":
            handle_transition()
            draw_board_ocean(get_enemy_board(), t)
            draw_transition(t)

        elif GAME_STATE == "WIN":
            draw_board_ocean(get_enemy_board(), t)
            draw_win_screen(t)

        update_draw_particles()
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
