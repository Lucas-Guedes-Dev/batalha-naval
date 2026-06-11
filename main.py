import pygame
import math
import random
from classes.navio import Ship
from classes.tabuleiro import Board


try:
    from menu import run_menu
    HAS_MENU = True
except ImportError:
    HAS_MENU = False

GRID_SIZE = 10
CELL_SIZE = 50
MARGIN = 2
UI_HEIGHT = 56
SIDE_W = 120

WIDTH = GRID_SIZE * CELL_SIZE + SIDE_W
HEIGHT = GRID_SIZE * CELL_SIZE + UI_HEIGHT

TERRAIN_DARK = (30,  45,  20)
TERRAIN_MID = (50,  70,  30)
TERRAIN_LIGHT = (75, 100,  45)
TERRAIN_DUST = (140, 130,  90)
SAND = (190, 175, 120)
WHITE = (255, 255, 255)
OFF_WHITE = (220, 225, 200)
GOLD = (220, 185,  55)
GOLD_DARK = (160, 120,  20)
RED_HIT = (210,  45,  45)
RED_GLOW = (255, 100,  60)
SMOKE_BLUE = (120, 130, 150)
GRAY_DARK = (50,   55,  40)
GRAY_MID = (100, 110,  80)
GREEN_OK = (80,  180,  70)
YELLOW = (255, 220,  50)
ORANGE_FIRE = (230, 120,  20)
BLACK = (0,    0,   0)
ARMY_GREEN = (60,   90,  40)
ARMY_TAN = (160, 145,  90)
CAMO_1 = (55,   75,  35)
CAMO_2 = (80,   65,  30)
DIRT = (100,  80,  50)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Guerra Territorial")

font_hud = pygame.font.SysFont("consolas", 18, bold=True)
font_big = pygame.font.SysFont("consolas", 38, bold=True)
font_mid = pygame.font.SysFont("consolas", 24, bold=True)
font_small = pygame.font.SysFont("consolas", 16)
font_tiny = pygame.font.SysFont("consolas", 13)

board_p1 = Board()
board_p2 = Board()

fleet = [1, 2, 3, 4, 5]
setup_index = 0
setup_rotation = "H"
current_player = 1
GAME_STATE = "SETUP_P1"

transition_start_time = 0
last_attack_time = 0
RESULT_DURATION = 1100

winner = None
hits_p1 = hits_p2 = 0
misses_p1 = misses_p2 = 0
sectors_p1 = [0, 0, 0, 0]
sectors_p2 = [0, 0, 0, 0]
SECTOR_LABELS = ["Sup. Esq.", "Sup. Dir.", "Inf. Esq.", "Inf. Dir."]

# ── nomes dos alvos ────────────────────────────────────────────────────────
TARGET_NAMES = {
    5: "Bunker",
    4: "Tanque",
    3: "Quartel",
    2: "Torre Rádio",
    1: "Soldado",
}

# ── ícones ASCII para cada alvo ────────────────────────────────────────────
TARGET_ICONS = {
    5: "▣",   # bunker
    4: "◉",   # tanque
    3: "⌂",   # quartel
    2: "▲",   # torre
    1: "☺",   # soldado
}

# ── cores de camuflagem por tipo ──────────────────────────────────────────
TARGET_COLORS = {
    1: ((160, 170, 130), (80,  90,  60)),   # soldado – verde oliva
    2: ((100, 140, 100), (50,  80,  50)),   # torre    – verde médio
    3: ((90,  110,  60), (50,  65,  30)),   # quartel  – verde exército
    4: ((80,   80,  50), (45,  45,  25)),   # tanque   – verde-acinzentado
    5: ((60,   65,  45), (30,  35,  20)),   # bunker   – verde-cinza escuro
}

# ── partículas ─────────────────────────────────────────────────────────────
particles = []


def spawn_particles(x, y, kind="hit"):
    count = 30 if kind == "hit" else 12
    for _ in range(count):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1.5, 6.0) if kind == "hit" \
            else random.uniform(0.5, 2.5)
        if kind == "hit":
            color = random.choice([RED_HIT, RED_GLOW, ORANGE_FIRE,
                                   YELLOW, (80, 70, 50)])
        else:
            color = random.choice([TERRAIN_DUST, SAND, (160, 155, 120),
                                   GRAY_MID])
        size = random.randint(2, 6) if kind == "hit" else random.randint(2, 4)
        life = random.randint(30, 60)
        particles.append({
            "x": x, "y": y,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed - random.uniform(0, 2.5),
            "color": color, "size": size,
            "life": life, "max_life": life,
        })


def update_draw_particles():
    dead = []
    for p in particles:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.14
        p["life"] -= 1
        ratio = p["life"] / p["max_life"]
        alpha = int(255 * ratio)
        r, g, b = p["color"]
        s = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (r, g, b, alpha),
                           (p["size"], p["size"]), p["size"])
        screen.blit(s, (int(p["x"]) - p["size"], int(p["y"]) - p["size"]))
        if p["life"] <= 0:
            dead.append(p)
    for p in dead:
        particles.remove(p)


# ── animação do terreno ────────────────────────────────────────────────────
def terrain_color(col, row, t):
    """Cor levemente animada para cada célula vazia (terreno)."""
    w = (math.sin(col * 0.5 + row * 0.4 + t * 0.3) + 1) / 2
    r = int(TERRAIN_DARK[0] + (TERRAIN_MID[0] - TERRAIN_DARK[0]) * w)
    g = int(TERRAIN_DARK[1] + (TERRAIN_MID[1] - TERRAIN_DARK[1]) * w)
    b = int(TERRAIN_DARK[2] + (TERRAIN_MID[2] - TERRAIN_DARK[2]) * w)
    return (r, g, b)


def draw_camo_patch(surface, col, row, t, cell_x, cell_y):
    """Manchas de camuflagem animadas sutis em cada célula."""
    phase = col * 1.3 + row * 0.8
    alpha = int(30 + 15 * math.sin(phase + t * 0.5))
    patch_w = int(CELL_SIZE * 0.35 + math.cos(phase + t * 0.3) * 4)
    patch_h = int(CELL_SIZE * 0.25)
    px = cell_x + int((CELL_SIZE - patch_w) * 0.3)
    py = cell_y + int(CELL_SIZE * 0.4)
    s = pygame.Surface((patch_w, patch_h), pygame.SRCALPHA)
    s.fill((40, 55, 20, alpha))
    surface.blit(s, (px, py))


# ── grade ──────────────────────────────────────────────────────────────────
GRID_X = 0
GRID_Y = UI_HEIGHT


def cell_rect(col, row):
    return pygame.Rect(
        GRID_X + col * CELL_SIZE,
        GRID_Y + row * CELL_SIZE,
        CELL_SIZE - MARGIN,
        CELL_SIZE - MARGIN
    )


def draw_board_terrain(board, t, reveal_targets=False):
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            rect = cell_rect(col, row)
            state = board.get_cell_state((row, col))

            if state == "empty":
                color = terrain_color(col, row, t)
                pygame.draw.rect(screen, color, rect, border_radius=2)
                draw_camo_patch(screen, col, row, t, rect.x, rect.y)

                rim = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                pygame.draw.rect(rim, (255, 255, 200, 10),
                                 (0, 0, rect.w, rect.h), border_radius=2)
                pygame.draw.rect(rim, (80, 100, 40, 30),
                                 (0, 0, rect.w, rect.h), 1, border_radius=2)
                screen.blit(rim, rect.topleft)

            elif state == "miss":
                # impacto no solo – poeira / cratera
                pygame.draw.rect(screen, TERRAIN_DARK, rect, border_radius=2)
                cx2, cy2 = rect.centerx, rect.centery
                # cratera
                pygame.draw.circle(screen, DIRT, (cx2, cy2), 10)
                pygame.draw.circle(screen, (70, 55, 35), (cx2, cy2), 10, 2)
                pygame.draw.circle(screen, (100, 85, 55), (cx2, cy2), 5)

            elif state == "hit":
                # explosão / incêndio
                pygame.draw.rect(screen, (60, 20, 10), rect, border_radius=2)
                cx2, cy2 = rect.centerx, rect.centery
                flicker = int(6 * math.sin(t * 9 + col * 2.5 + row * 1.8))
                fire = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                pygame.draw.circle(
                    fire, (220, 80, 10, 140 + flicker * 3),
                    (rect.w // 2, rect.h // 2), 15)
                pygame.draw.circle(
                    fire, (255, 180, 30, 100 + flicker * 2),
                    (rect.w // 2, rect.h // 2), 8)
                screen.blit(fire, rect.topleft)
                pygame.draw.rect(screen, RED_HIT, rect, 2, border_radius=2)

    if reveal_targets:
        for ship in board.ships:
            _blit_target(ship)


def draw_setup_board(board, t):
    """Desenha a grade durante o posicionamento dos alvos."""
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            rect = cell_rect(col, row)
            color = terrain_color(col, row, t)
            pygame.draw.rect(screen, color, rect, border_radius=2)
            draw_camo_patch(screen, col, row, t, rect.x, rect.y)
            rim = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            pygame.draw.rect(rim, (80, 100, 40, 25),
                             (0, 0, rect.w, rect.h), 1, border_radius=2)
            screen.blit(rim, rect.topleft)

    for ship in board.ships:
        _blit_target(ship)


def _draw_target_vector(surf, x, y, size, is_h, color_body, color_dark,
                        target_size, alpha=255):
    """
    Desenha um alvo militar com aparência específica por tipo.
    target_size: tamanho em células (1-5).
    """
    W = size * CELL_SIZE - MARGIN
    H = CELL_SIZE - MARGIN
    s = pygame.Surface((W, H), pygame.SRCALPHA)

    pygame.draw.rect(s, (*color_body, alpha), (0, 0, W, H), border_radius=3)

    random.seed(target_size * 100 + x + y)

    random.seed()

    pad = 5
    inner_h = H - pad * 2
    mid_y = H // 2

    if target_size == 5:  # Bunker – forma retangular reforçada
        pygame.draw.rect(s, (*color_dark, alpha),
                         (pad, pad, W - pad * 2, inner_h), border_radius=2)
        # seta de entrada
        pygame.draw.rect(s, (30, 30, 20, alpha),
                         (W // 2 - 8, pad + 2, 16, inner_h - 4),
                         border_radius=1)
        # teto reforçado
        pygame.draw.rect(s, (*color_dark, min(alpha, 200)),
                         (pad, pad, W - pad * 2, 6), border_radius=2)
        lbl = font_tiny.render("BUNKER", True, (*OFF_WHITE, alpha))

    elif target_size == 4:  # Tanque – corpo com canhão
        body_w = int(W * 0.55)
        body_x = (W - body_w) // 2
        # lagarta esquerda
        pygame.draw.rect(s, (*color_dark, alpha),
                         (body_x - 8, mid_y - 8, 8, 16), border_radius=2)
        # lagarta direita
        pygame.draw.rect(s, (*color_dark, alpha),
                         (body_x + body_w, mid_y - 8, 8, 16), border_radius=2)
        # corpo principal
        pygame.draw.rect(s, (*color_dark, alpha),
                         (body_x, mid_y - 7, body_w, 14), border_radius=3)
        # torre
        tower_w = max(int(body_w * 0.5), 10)
        tower_x = body_x + (body_w - tower_w) // 2
        pygame.draw.rect(s, (*color_body, alpha),
                         (tower_x, mid_y - 5, tower_w, 10), border_radius=2)
        # canhão
        cannon_len = int(W * 0.28)
        pygame.draw.rect(s, (*color_dark, alpha),
                         (tower_x + tower_w, mid_y - 2, cannon_len, 4),
                         border_radius=1)
        lbl = font_tiny.render("TANQUE", True, (*OFF_WHITE, alpha))

    elif target_size == 3:  # Quartel – prédio com janelas
        pygame.draw.rect(s, (*color_dark, alpha),
                         (pad + 4, pad, W - (pad + 4) * 2, inner_h),
                         border_radius=2)
        # janelas
        win_cols = max(size, 2)
        for wi in range(win_cols):
            wx = pad + 8 + wi * ((W - (pad + 8) * 2) // max(win_cols - 1, 1))
            pygame.draw.rect(s, (200, 220, 180, min(alpha, 200)),
                             (wx - 4, mid_y - 5, 8, 6), border_radius=1)
        # telhado triangular
        roof_pts = [(pad + 2, pad + 1), (W // 2, 2), (W - pad - 2, pad + 1)]
        pygame.draw.polygon(s, (*color_body, alpha), roof_pts)
        lbl = font_tiny.render("QUARTEL", True, (*OFF_WHITE, alpha))

    elif target_size == 2:  # Torre de Rádio – mastro e antenas
        mid_x = W // 2
        # base
        pygame.draw.rect(s, (*color_dark, alpha),
                         (mid_x - 6, mid_y, 12, H - mid_y - pad),
                         border_radius=1)
        # poste
        pygame.draw.rect(s, (*color_dark, alpha),
                         (mid_x - 2, pad, 4, H - pad * 2), border_radius=1)
        # antenas
        pygame.draw.line(s, (*OFF_WHITE, alpha),
                         (mid_x, pad + 4), (mid_x - 14, mid_y - 4), 2)
        pygame.draw.line(s, (*OFF_WHITE, alpha),
                         (mid_x, pad + 4), (mid_x + 14, mid_y - 4), 2)
        # luz pulsante (estática)
        pygame.draw.circle(s, (255, 80, 80, alpha), (mid_x, pad + 2), 3)
        lbl = font_tiny.render("TORRE", True, (*OFF_WHITE, alpha))

    else:  # Soldado (size==1) – figura humana estilizada
        mid_x = W // 2
        # capacete
        pygame.draw.circle(s, (*color_dark, alpha), (mid_x, pad + 5), 6)
        # corpo
        pygame.draw.rect(s, (*color_dark, alpha),
                         (mid_x - 5, pad + 10, 10, 12), border_radius=1)
        # pernas
        pygame.draw.line(s, (*color_dark, alpha),
                         (mid_x - 2, pad + 22), (mid_x - 4, H - pad), 2)
        pygame.draw.line(s, (*color_dark, alpha),
                         (mid_x + 2, pad + 22), (mid_x + 4, H - pad), 2)
        # rifle
        pygame.draw.line(s, (*color_dark, alpha),
                         (mid_x + 5, pad + 12), (mid_x + W // 3, pad + 8), 2)
        lbl = font_tiny.render("SOLD.", True, (*OFF_WHITE, alpha))

    # borda tática
    pygame.draw.rect(s, (*color_dark, min(alpha, 200)), (0, 0, W, H), 1,
                     border_radius=3)

    if is_h:
        surf.blit(s, (x, y))
    else:
        rotated = pygame.transform.rotate(s, -90)
        surf.blit(rotated, (x, y))


def _blit_target(ship, alpha=255):
    rows = [p[0] for p in ship.positions]
    cols = [p[1] for p in ship.positions]
    min_row, min_col = min(rows), min(cols)
    px = GRID_X + min_col * CELL_SIZE
    py = GRID_Y + min_row * CELL_SIZE
    is_h = len(set(rows)) == 1
    color_body, color_dark = TARGET_COLORS[ship.size]
    _draw_target_vector(screen, px, py, ship.size, is_h,
                        color_body, color_dark, ship.size, alpha)


def draw_preview(row, col, size, rotation, t):
    """Pré-visualização fantasma durante o posicionamento."""
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
    cell_color = (80, 200, 70) if valid else (200, 50, 50)

    for (r, c) in positions:
        if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
            rect = cell_rect(c, r)
            bg = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            bg.fill((*cell_color, 45 + int(25 * abs(math.sin(t * 3)))))
            pygame.draw.rect(bg, (*cell_color, pulse_a),
                             (0, 0, rect.w, rect.h), 2, border_radius=2)
            screen.blit(bg, rect.topleft)

    if positions:
        r0, c0 = positions[0]
        if all(0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE
               for r, c in positions):
            px = GRID_X + c0 * CELL_SIZE
            py = GRID_Y + r0 * CELL_SIZE
            color_body, color_dark = TARGET_COLORS[size]
            ghost_alpha = 160 if valid else 70
            _draw_target_vector(screen, px, py, size, is_h,
                                color_body, color_dark, size, ghost_alpha)


def draw_top_bar(state, t):
    bar = pygame.Surface((WIDTH, UI_HEIGHT), pygame.SRCALPHA)
    bar.fill((20, 30, 12, 245))
    screen.blit(bar, (0, 0))
    pygame.draw.line(screen, GOLD, (0, UI_HEIGHT - 1),
                     (WIDTH, UI_HEIGHT - 1), 1)

    cx = (WIDTH - SIDE_W) // 2

    if state in ("SETUP_P1", "SETUP_P2"):
        player = 1 if state == "SETUP_P1" else 2
        tgt_name = TARGET_NAMES[fleet[setup_index]]
        label = f"COMANDANTE {player}  ·  POSICIONE: {tgt_name}"
        hint = "Seta ↓ para girar  |  Click para posicionar"
        rot_icon = "━━" if setup_rotation == "H" else "┃"
        rot_text = font_tiny.render(f"ROT: {rot_icon}", True, GOLD)
        text = font_hud.render(label, True, OFF_WHITE)
        screen.blit(text, (cx - text.get_width() // 2, 8))
        hint_s = font_tiny.render(hint, True, GRAY_MID)
        screen.blit(hint_s, (cx - hint_s.get_width() // 2, 32))
        screen.blit(rot_text, (WIDTH - SIDE_W - rot_text.get_width() - 8, 20))

    elif state == "PLAYING":
        label = f"COMANDANTE {current_player}  ·  ATAQUE!"
        pulse = int(180 + 75 * abs(math.sin(t * 2.5)))
        color = (pulse, 220, 120) if current_player == 1 else (
            255, pulse // 2 + 80, 80)
        text = font_hud.render(label, True, color)
        screen.blit(text, (cx - text.get_width() // 2, 16))

    elif state == "SHOW_RESULT":
        label = f"COMANDANTE {current_player}  ·  ATAQUE!"
        text = font_hud.render(label, True, GOLD)
        screen.blit(text, (cx - text.get_width() // 2, 16))


def draw_side_panel(t):
    sx = GRID_SIZE * CELL_SIZE
    panel = pygame.Surface((SIDE_W, HEIGHT - UI_HEIGHT), pygame.SRCALPHA)
    panel.fill((18, 28, 10, 245))
    screen.blit(panel, (sx, UI_HEIGHT))
    pygame.draw.line(screen, GOLD, (sx, UI_HEIGHT), (sx, HEIGHT), 1)

    def label(txt, y, color=GRAY_MID, f=font_tiny):
        s = f.render(txt, True, color)
        screen.blit(s, (sx + SIDE_W // 2 - s.get_width() // 2, y))

    if GAME_STATE in ("SETUP_P1", "SETUP_P2"):
        label("── ALVOS ──", UI_HEIGHT + 14, GOLD, font_tiny)
        for i, sz in enumerate(fleet):
            y_item = UI_HEIGHT + 36 + i * 36
            cb, cd = TARGET_COLORS[sz]
            is_done = i < setup_index
            is_curr = i == setup_index

            swatch_x, swatch_y = sx + 10, y_item
            swatch_w, swatch_h = 10, 10

            if is_done:
                sw_col = (30, 45, 20)
                border = (60, 100, 40)
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
            ns = font_tiny.render(TARGET_NAMES[sz], True, name_color)
            screen.blit(ns, (swatch_x + 14, swatch_y - 1))

            pip_x = swatch_x
            pip_y = swatch_y + 13
            for p in range(sz):
                pip_col = cd if is_curr else (
                    GRAY_DARK if is_done else GRAY_MID)
                pygame.draw.rect(screen, pip_col,
                                 (pip_x + p * 8, pip_y, 6, 4), border_radius=1)

            if is_done:
                ck = font_tiny.render("✓", True, (80, 180, 60))
                screen.blit(ck, (sx + SIDE_W - 18, swatch_y - 1))
            if is_curr:
                pulse_x = int(3 * abs(math.sin(t * 5)))
                arr = font_tiny.render("▶", True, GOLD)
                screen.blit(arr, (sx + SIDE_W - 18 - pulse_x, swatch_y - 1))

    else:
        label("── PLACAR ──", UI_HEIGHT + 14, GOLD, font_tiny)
        label(f"C1  {hits_p1} acertos", UI_HEIGHT + 38, (120, 210, 100))
        label(f"C2  {hits_p2} acertos", UI_HEIGHT + 58, (255, 130, 100))

        label("── INIMIGO ──", UI_HEIGHT + 96, GOLD, font_tiny)
        for i, sz in enumerate(fleet):
            board = board_p2 if current_player == 1 else board_p1
            ship_obj = next((s for s in board.ships if s.size == sz), None)
            y_item = UI_HEIGHT + 116 + i * 22
            cb, cd = TARGET_COLORS[sz]

            if ship_obj and ship_obj.is_sunk():
                swatch = pygame.Surface((8, 8), pygame.SRCALPHA)
                swatch.fill((120, 30, 30, 200))
                screen.blit(swatch, (sx + 10, y_item + 1))
                icon_s = font_tiny.render(
                    "✕ " + TARGET_NAMES[sz][:6], True, (150, 50, 50))
            else:
                swatch = pygame.Surface((8, 8), pygame.SRCALPHA)
                swatch.fill((*cb, 200))
                screen.blit(swatch, (sx + 10, y_item + 1))
                icon_s = font_tiny.render(
                    "■ " + TARGET_NAMES[sz][:6], True, (120, 180, 100))
            screen.blit(icon_s, (sx + 22, y_item))

    # bússola tática
    cx2 = sx + SIDE_W // 2
    cy2 = HEIGHT - 50
    r = 20
    pulse = 0.7 + 0.3 * abs(math.sin(t * 1.2))
    for ang, lbl_txt in [(0, "N"), (90, "L"), (180, "S"), (270, "O")]:
        rad = math.radians(ang - 90)
        tx2 = cx2 + int(r * math.cos(rad))
        ty2 = cy2 + int(r * math.sin(rad))
        col_c = GOLD if lbl_txt == "N" else GRAY_MID
        s = font_tiny.render(lbl_txt, True, col_c)
        screen.blit(s, (tx2 - s.get_width() // 2, ty2 - s.get_height() // 2))
    pygame.draw.circle(screen, GRAY_DARK, (cx2, cy2), int(r * pulse), 1)
    pygame.draw.circle(screen, GOLD, (cx2, cy2), 3)


def draw_transition(t):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((10, 18, 6, 225))
    screen.blit(overlay, (0, 0))

    next_p = 2 if current_player == 1 else 1
    elapsed = (pygame.time.get_ticks() - transition_start_time) / 1000.0
    progress = min(elapsed / 3.0, 1.0)

    scan_y = int(HEIGHT * progress)
    pygame.draw.line(screen, GOLD, (0, scan_y), (WIDTH, scan_y), 1)

    cy = HEIGHT // 2
    pulse = abs(math.sin(t * 3)) * 6

    lines = [
        (font_mid, f"COMANDANTE {current_player} ATACOU", GRAY_MID, cy - 64),
        (font_big, "PASSANDO O TURNO",                    GOLD,     cy - 10),
        (font_mid, f"VEZ DO COMANDANTE {next_p}",
         (120, 200, 100), cy + 58 + int(pulse)),
    ]
    for font, text, color, y in lines:
        s = font.render(text, True, color)
        screen.blit(s, (WIDTH // 2 - s.get_width() // 2, y))

    bar_w = int((WIDTH - 80) * (1 - progress))
    pygame.draw.rect(screen, GRAY_DARK, (40, HEIGHT - 30, WIDTH - 80, 8),
                     border_radius=4)
    pygame.draw.rect(screen, GOLD,      (40, HEIGHT - 30, bar_w, 8),
                     border_radius=4)


def _draw_sector_heatmap(cx, cy, size, sectors, color_main, t):
    half = size // 2
    gap = 3
    max_s = max(sectors) if max(sectors) > 0 else 1
    quadrants = [
        (cx - half,  cy - half,  sectors[0]),
        (cx + gap,   cy - half,  sectors[1]),
        (cx - half,  cy + gap,   sectors[2]),
        (cx + gap,   cy + gap,   sectors[3]),
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
            screen.blit(cs, (qx + qw // 2 - cs.get_width() // 2,
                             qy + qw // 2 - cs.get_height() // 2))

    labels = [("O", cx - half - 14, cy),
              ("L", cx + half + gap + 2, cy),
              ("↑", cx, cy - half - 14),
              ("↓", cx, cy + half + gap + 2)]
    for lbl, lx, ly in labels:
        ls = font_tiny.render(lbl, True, GRAY_MID)
        screen.blit(ls, (lx - ls.get_width() // 2, ly - ls.get_height() // 2))


def draw_win_screen(t):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((10, 18, 6, 240))
    screen.blit(overlay, (0, 0))

    pulse = abs(math.sin(t * 2.5)) * 6

    h1, h2 = hits_p1, hits_p2
    m1, m2 = misses_p1, misses_p2
    t1, t2 = h1 + m1, h2 + m2
    acc1 = int(100 * h1 / t1) if t1 > 0 else 0
    acc2 = int(100 * h2 / t2) if t2 > 0 else 0

    cx = WIDTH // 2

    # estrela de vitória
    dy = int(pulse)
    star_y = 28
    star_cx = cx
    star_cy = star_y + 18 - dy
    pts = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        radius = 20 if i % 2 == 0 else 9
        pts.append((star_cx + int(radius * math.cos(angle)),
                    star_cy + int(radius * math.sin(angle))))
    pygame.draw.polygon(screen, GOLD, pts)
    pygame.draw.polygon(screen, WHITE, pts, 1)

    title_y = star_y + 44
    ts = font_big.render(f"COMANDANTE {winner} VENCEU!", True, GOLD)
    shadow = font_big.render(f"COMANDANTE {winner} VENCEU!", True, (60, 40, 0))
    screen.blit(shadow, (cx - ts.get_width() // 2 + 2, title_y + 2))
    screen.blit(ts,     (cx - ts.get_width() // 2,     title_y))

    div_y = title_y + ts.get_height() + 8
    pygame.draw.line(screen, GOLD, (40, div_y), (WIDTH - 40, div_y), 1)

    col1_x = cx - 4
    col2_x = cx + 4
    col_w = cx - 50
    stats_y = div_y + 14

    c1_col = (120, 210, 100)
    c2_col = (255, 130, 100)
    w_col = GOLD

    def center_text(txt, font, color, x_center, y):
        s = font.render(txt, True, color)
        screen.blit(s, (x_center - s.get_width() // 2, y))

    j1_cx = col1_x - col_w // 2
    j2_cx = col2_x + col_w // 2

    center_text("COMANDANTE 1", font_small,
                w_col if winner == 1 else c1_col, j1_cx, stats_y)
    center_text("COMANDANTE 2", font_small,
                w_col if winner == 2 else c2_col, j2_cx, stats_y)

    # coroa do vencedor
    crown_cx = j1_cx if winner == 1 else j2_cx
    crown_y = stats_y - 14
    crown_pts = [
        (crown_cx - 12, crown_y + 10), (crown_cx - 12, crown_y),
        (crown_cx - 6,  crown_y + 6),  (crown_cx,      crown_y),
        (crown_cx + 6,  crown_y + 6),  (crown_cx + 12, crown_y),
        (crown_cx + 12, crown_y + 10),
    ]
    pygame.draw.polygon(screen, GOLD, crown_pts)

    row_y = stats_y + 20
    bar_h = 10
    bar_w = col_w - 30
    lbl_off = 26

    def stat_row(lbl_text, v1, v2, max_v, c1, c2, y):
        lbl_s = font_tiny.render(lbl_text, True, GRAY_MID)
        screen.blit(lbl_s, (cx - lbl_s.get_width() // 2, y))
        bx1 = col1_x - bar_w - lbl_off
        pygame.draw.rect(screen, GRAY_DARK, (bx1, y + 14, bar_w, bar_h),
                         border_radius=3)
        fw1 = int(bar_w * v1 / max_v) if max_v > 0 else 0
        if fw1:
            pygame.draw.rect(screen, c1, (bx1, y + 14, fw1, bar_h),
                             border_radius=3)
        vs1 = font_tiny.render(str(v1), True, c1)
        screen.blit(vs1, (bx1 - vs1.get_width() - 4, y + 13))

        bx2 = col2_x + lbl_off
        pygame.draw.rect(screen, GRAY_DARK, (bx2, y + 14, bar_w, bar_h),
                         border_radius=3)
        fw2 = int(bar_w * v2 / max_v) if max_v > 0 else 0
        if fw2:
            pygame.draw.rect(screen, c2, (bx2, y + 14, fw2, bar_h),
                             border_radius=3)
        vs2 = font_tiny.render(str(v2), True, c2)
        screen.blit(vs2, (bx2 + bar_w + 4, y + 13))

    max_t = max(t1, t2, 1)
    max_h = max(h1, h2, 1)
    max_m = max(m1, m2, 1)

    stat_row("DISPAROS",  t1, t2, max_t, c1_col, c2_col, row_y)
    stat_row("ACERTOS",   h1, h2, max_h, GREEN_OK, GREEN_OK, row_y + 32)
    stat_row("ERROS",     m1, m2, max_m, RED_HIT, RED_HIT,   row_y + 64)

    acc_y = row_y + 90
    center_text(f"Precisão: {acc1}%", font_tiny, c1_col, j1_cx, acc_y)
    center_text(f"Precisão: {acc2}%", font_tiny, c2_col, j2_cx, acc_y)

    pygame.draw.line(screen, GRAY_DARK,
                     (40, acc_y + 18), (WIDTH - 40, acc_y + 18), 1)

    heat_y = acc_y + 30
    hmap_lbl = font_tiny.render("ZONAS MAIS BOMBARDEADAS", True, GOLD)
    screen.blit(hmap_lbl, (cx - hmap_lbl.get_width() // 2, heat_y))

    hmap_size = 88
    _draw_sector_heatmap(j1_cx, heat_y + 60, hmap_size, sectors_p1, c1_col, t)
    _draw_sector_heatmap(j2_cx, heat_y + 60, hmap_size, sectors_p2, c2_col, t)

    def hottest_label(sectors, x_center, y):
        if max(sectors) == 0:
            return
        idx = sectors.index(max(sectors))
        s = font_tiny.render(f"▲ {SECTOR_LABELS[idx]}", True, GOLD)
        screen.blit(s, (x_center - s.get_width() // 2, y))

    hottest_label(sectors_p1, j1_cx, heat_y + 110)
    hottest_label(sectors_p2, j2_cx, heat_y + 110)

    prompt_y = HEIGHT - 22
    pa = int(160 + 95 * abs(math.sin(t * 2)))
    ps = font_tiny.render(
        "ENTER  →  nova missão     ESC  →  retirada", True, (pa, pa, pa))
    screen.blit(ps, (cx - ps.get_width() // 2, prompt_y))

    # faíscas de explosão aleatórias
    if random.random() < 0.20:
        sx2 = random.randint(20, WIDTH - 20)
        sy2 = random.randint(20, HEIGHT // 3)
        spawn_particles(sx2, sy2, "hit")


# ── lógica de jogo ─────────────────────────────────────────────────────────
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


def place_target_manual(board, row, col, size, rotation):
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

    if HAS_MENU:
        action = run_menu(screen, WIDTH, HEIGHT)
        if action == "quit":
            pygame.quit()
            return

    running = True
    while running:
        t = pygame.time.get_ticks() / 1000.0
        screen.fill(TERRAIN_DARK)

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

                if GAME_STATE in ("SETUP_P1", "SETUP_P2"):
                    board = board_p1 if GAME_STATE == "SETUP_P1" else board_p2
                    size = fleet[setup_index]
                    if place_target_manual(board, row, col, size, setup_rotation):
                        spawn_particles(
                            GRID_X + col * CELL_SIZE + CELL_SIZE // 2,
                            GRID_Y + row * CELL_SIZE + CELL_SIZE // 2,
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

        # ── renderização ──────────────────────────────────────────────────
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
            draw_board_terrain(get_enemy_board(), t)
            draw_top_bar("PLAYING", t)
            draw_side_panel(t)

        elif GAME_STATE == "SHOW_RESULT":
            handle_show_result()
            draw_board_terrain(get_enemy_board(), t)
            draw_top_bar("SHOW_RESULT", t)
            draw_side_panel(t)

        elif GAME_STATE == "TRANSITION":
            handle_transition()
            draw_board_terrain(get_enemy_board(), t)
            draw_transition(t)

        elif GAME_STATE == "WIN":
            draw_board_terrain(get_enemy_board(), t, reveal_targets=True)
            draw_win_screen(t)

        update_draw_particles()
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
