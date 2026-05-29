import pygame
import math
import random

WHITE = (255, 255, 255)
BLACK = (0,   0,   0)
TERRAIN_DARK = (30,  45,  20)
TERRAIN_MID = (50,  70,  30)
TERRAIN_LIGHT = (75, 100,  45)
ARMY_GREEN = (60,  90,  40)
ARMY_TAN = (160, 145,  90)
GOLD = (220, 185,  55)
RED = (200,  40,  40)
GRAY = (130, 140, 110)
DARK_GRAY = (50,  55,  40)
SAND = (190, 175, 120)
SMOKE = (100, 105,  85)
ORANGE_FIRE = (230, 120,  20)
OFF_WHITE = (220, 225, 200)


# ── regras do jogo ─────────────────────────────────────────────────────────
RULES_SECTIONS = [
    ("OBJETIVO",
     "Destrua todos os alvos militares do inimigo antes\n"
     "que ele destrua os seus. O primeiro comandante a\n"
     "eliminar toda a frota inimiga vence a guerra."),

    ("FASE DE POSICIONAMENTO",
     "Cada comandante posiciona seus 5 alvos no mapa:\n"
     "  [B] Bunker       (5 casas)\n"
     "  [T] Tanque       (4 casas)\n"
     "  [Q] Quartel      (3 casas)\n"
     "  [R] Torre Radio  (2 casas)\n"
     "  [S] Soldado      (1 casa)\n"
     "Use SETA BAIXO para girar o alvo (horiz/vert).\n"
     "Clique no mapa para confirmar a posicao."),

    ("FASE DE ATAQUE",
     "Os comandantes se alternam atacando o mapa inimigo.\n"
     "Clique em qualquer celula para disparar:\n"
     "  >> ACERTO  - celula pega fogo (vermelho)\n"
     "  >> ERRO    - cratera no solo (marrom)\n"
     "Nao e possivel atacar a mesma celula duas vezes.\n"
     "Apos cada disparo o turno passa automaticamente."),

    ("CONTROLES",
     "  Mouse       -  mirar e atirar / posicionar alvos\n"
     "  Seta Baixo  -  girar alvo (posicionamento)\n"
     "  ENTER       -  nova missao (tela de vitoria)\n"
     "  ESC         -  retirada (tela de vitoria)"),

    ("VITORIA",
     "Quando todos os alvos do inimigo forem destruidos\n"
     "a tela de vitoria exibe o placar completo:\n"
     "  - Total de disparos de cada comandante\n"
     "  - Acertos e erros\n"
     "  - Precisao percentual\n"
     "  - Mapa de calor das zonas mais bombardeadas"),
]


def draw_terrain_strip(surface, W, H, t, y_base, amplitude, color, alpha=200):
    wave_surf = pygame.Surface((W, H), pygame.SRCALPHA)
    points = [(0, H)]
    for x in range(W + 1):
        y = y_base + math.sin((x / 90.0) + t * 0.4) * amplitude \
                   + math.sin((x / 40.0) + t * 0.25) * (amplitude * 0.4)
        points.append((x, int(y)))
    points.append((W, H))
    pygame.draw.polygon(wave_surf, (*color, alpha), points)
    surface.blit(wave_surf, (0, 0))


def draw_tank_silhouette(surface, x, y, scale=1.0, facing_right=True):
    flip = 1 if facing_right else -1

    track_w = int(110 * scale)
    track_h = int(18 * scale)
    pygame.draw.rect(surface, DARK_GRAY,
                     (x - int(55 * scale), y - int(9 * scale),
                      track_w, track_h), border_radius=int(6 * scale))
    for i in range(5):
        wx = x - int(44 * scale) + i * int(22 * scale)
        pygame.draw.circle(surface, SMOKE, (wx, y), int(7 * scale))
        pygame.draw.circle(surface, DARK_GRAY, (wx, y), int(4 * scale))

    hull_pts = [
        (x - int(48 * scale), y - int(9 * scale)),
        (x - int(42 * scale), y - int(22 * scale)),
        (x + int(42 * scale), y - int(22 * scale)),
        (x + int(48 * scale), y - int(9 * scale)),
    ]
    pygame.draw.polygon(surface, ARMY_GREEN, hull_pts)

    turret_w = int(46 * scale)
    turret_h = int(16 * scale)
    turret_x = x - int(10 * scale) - int(flip * 4 * scale)
    turret_y = y - int(22 * scale) - turret_h
    pygame.draw.rect(surface, DARK_GRAY,
                     (turret_x - turret_w // 2, turret_y,
                      turret_w, turret_h), border_radius=int(4 * scale))

    cannon_len = int(52 * scale)
    cannon_x = turret_x + flip * (turret_w // 2)
    cannon_y = turret_y + turret_h // 2
    pygame.draw.rect(surface, SMOKE,
                     (cannon_x if facing_right else cannon_x - cannon_len,
                      cannon_y - int(3 * scale),
                      cannon_len, int(6 * scale)),
                     border_radius=int(2 * scale))

    pygame.draw.circle(surface, SMOKE,
                       (turret_x, turret_y + turret_h // 2), int(5 * scale))


def draw_explosion_particles(surface, particles):
    for p in particles:
        ratio = p["life"] / p["max_life"]
        alpha = int(255 * ratio)
        r, g, b = p["color"]
        s = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (r, g, b, alpha),
                           (p["size"], p["size"]), p["size"])
        surface.blit(s, (int(p["x"]) - p["size"], int(p["y"]) - p["size"]))


def draw_crosshair(surface, x, y, size, color, alpha=200):
    s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    cx, cy = size, size
    pygame.draw.circle(s, (*color, alpha), (cx, cy), size, 2)
    pygame.draw.circle(s, (*color, alpha), (cx, cy), size // 3, 2)
    gap = size // 3
    pygame.draw.line(s, (*color, alpha), (cx - size, cy), (cx - gap, cy), 2)
    pygame.draw.line(s, (*color, alpha), (cx + gap, cy), (cx + size, cy), 2)
    pygame.draw.line(s, (*color, alpha), (cx, cy - size), (cx, cy - gap), 2)
    pygame.draw.line(s, (*color, alpha), (cx, cy + gap), (cx, cy + size), 2)
    surface.blit(s, (x - size, y - size))


def draw_camo_bg(surface, W, H, t):
    surface.fill(TERRAIN_DARK)
    for row in range(H // 22 + 1):
        alpha = 10 + (row % 2) * 6
        s = pygame.Surface((W, 22), pygame.SRCALPHA)
        pygame.draw.rect(s, (80, 100, 40, alpha), (0, 0, W, 22))
        surface.blit(s, (0, row * 22))
    random.seed(42)
    for _ in range(18):
        px = random.randint(0, W)
        py = random.randint(0, H)
        rw = random.randint(40, 120)
        rh = random.randint(20, 60)
        alpha = random.randint(12, 28)
        col = random.choice([(40, 60, 20), (60, 80, 30), (25, 40, 15)])
        patch = pygame.Surface((rw, rh), pygame.SRCALPHA)
        pygame.draw.ellipse(patch, (*col, alpha), (0, 0, rw, rh))
        surface.blit(patch, (px - rw // 2, py - rh // 2))
    random.seed()


class Button:
    def __init__(self, x, y, w, h, text, font):
        self.rect = pygame.Rect(x - w // 2, y - h // 2, w, h)
        self.text = text
        self.font = font
        self.hovered = False

    def draw(self, surface, t):
        if self.hovered:
            bg_color = (50, 80, 25)
            border_color = GOLD
            text_color = GOLD
            border_w = 2
        else:
            bg_color = (25, 40, 12)
            border_color = (100, 140, 60)
            text_color = OFF_WHITE
            border_w = 1

        btn_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(btn_surf, (*bg_color, 220),
                         (0, 0, self.rect.w, self.rect.h), border_radius=4)
        pygame.draw.rect(btn_surf, border_color,
                         (0, 0, self.rect.w, self.rect.h),
                         border_w, border_radius=4)
        surface.blit(btn_surf, self.rect.topleft)

        text_surf = self.font.render(self.text, True, text_color)
        tr = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, tr)

        if self.hovered:
            corner_len = 8
            cx, cy, cw, ch = self.rect
            for dx, dy, sx, sy in [(-2, -2, 1, 1), (cw + 2, -2, -1, 1),
                                   (-2, ch + 2, 1, -1), (cw + 2, ch + 2, -1, -1)]:
                px2, py2 = cx + dx, cy + dy
                pygame.draw.line(surface, GOLD, (px2, py2),
                                 (px2 + sx * corner_len, py2), 2)
                pygame.draw.line(surface, GOLD, (px2, py2),
                                 (px2, py2 + sy * corner_len), 2)

    def check_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


# ── modal de regras ────────────────────────────────────────────────────────
def draw_rules_modal(screen, WIDTH, HEIGHT, t,
                     font_title, font_body, font_tiny, font_btn,
                     scroll_y, btn_close):
    """Desenha o modal de regras sobre o menu."""

    # sombra escura por cima do menu
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((5, 10, 3, 210))
    screen.blit(overlay, (0, 0))

    # dimensões do painel
    M_W = min(WIDTH - 60, 560)
    M_H = min(HEIGHT - 60, 520)
    M_X = (WIDTH - M_W) // 2
    M_Y = (HEIGHT - M_H) // 2

    # fundo do painel
    panel = pygame.Surface((M_W, M_H), pygame.SRCALPHA)
    pygame.draw.rect(panel, (12, 22, 8, 248),
                     (0, 0, M_W, M_H), border_radius=6)
    pygame.draw.rect(panel, GOLD,              (0, 0,
                     M_W, M_H), 2, border_radius=6)

    # listras camo internas
    random.seed(99)
    for _ in range(8):
        px2 = random.randint(0, M_W)
        py2 = random.randint(0, M_H)
        rw2 = random.randint(60, 160)
        rh2 = random.randint(20, 50)
        pat = pygame.Surface((rw2, rh2), pygame.SRCALPHA)
        pygame.draw.ellipse(pat, (30, 50, 15, 18), (0, 0, rw2, rh2))
        panel.blit(pat, (px2 - rw2 // 2, py2 - rh2 // 2))
    random.seed()

    screen.blit(panel, (M_X, M_Y))

    # ── cantos decorativos ─────────────────────────────────────────────
    corner = 14
    for dx, dy, sx, sy in [(0, 0, 1, 1), (M_W, 0, -1, 1),
                           (0, M_H, 1, -1), (M_W, M_H, -1, -1)]:
        bx, by = M_X + dx, M_Y + dy
        pygame.draw.line(screen, GOLD, (bx, by), (bx + sx * corner, by), 2)
        pygame.draw.line(screen, GOLD, (bx, by), (bx, by + sy * corner), 2)

    # ── cabeçalho ─────────────────────────────────────────────────────
    HDR_H = 48
    hdr = pygame.Surface((M_W - 4, HDR_H), pygame.SRCALPHA)
    pygame.draw.rect(hdr, (25, 45, 12, 220),
                     (0, 0, M_W - 4, HDR_H), border_radius=4)
    screen.blit(hdr, (M_X + 2, M_Y + 2))

    pulse = int(180 + 75 * abs(math.sin(t * 2.2)))
    title_s = font_title.render("[ BRIEFING DE MISSAO ]", True,
                                (pulse, int(pulse * 0.85), 50))
    if title_s.get_width() > M_W - 20:
        scale_f = (M_W - 20) / title_s.get_width()
        title_s = pygame.transform.smoothscale(
            title_s,
            (int(title_s.get_width() * scale_f),
             int(title_s.get_height() * scale_f)))
    screen.blit(title_s,
                (M_X + M_W // 2 - title_s.get_width() // 2, M_Y + 12))

    pygame.draw.line(screen, GOLD,
                     (M_X + 10, M_Y + HDR_H + 2),
                     (M_X + M_W - 10, M_Y + HDR_H + 2), 1)

    CONTENT_TOP = M_Y + HDR_H + 12
    CONTENT_BOT = M_Y + M_H - 54
    CONTENT_H = CONTENT_BOT - CONTENT_TOP
    PAD_X = 18

    clip_surf = pygame.Surface((M_W, CONTENT_H), pygame.SRCALPHA)
    cy_cur = -scroll_y                   # posição vertical dentro do clip

    for section_title, body_text in RULES_SECTIONS:
        # título da seção
        sec_s = font_body.render(f">> {section_title}", True, GOLD)
        if 0 <= cy_cur < CONTENT_H:
            clip_surf.blit(sec_s, (PAD_X, cy_cur))
        cy_cur += sec_s.get_height() + 4

        # linhas do corpo
        for line in body_text.split("\n"):
            line_s = font_tiny.render(line, True, OFF_WHITE)
            if -line_s.get_height() <= cy_cur < CONTENT_H:
                clip_surf.blit(line_s, (PAD_X + 10, cy_cur))
            cy_cur += line_s.get_height() + 2

        cy_cur += 10   # espaço entre seções

    # total de conteúdo para scroll
    total_content_h = cy_cur + scroll_y

    screen.blit(clip_surf, (M_X, CONTENT_TOP))

    # ── gradientes de fade (topo/baixo da área de conteúdo) ───────────
    for i in range(18):
        alpha_f = int(200 * (1 - i / 18))
        fade_s = pygame.Surface((M_W, 1), pygame.SRCALPHA)
        fade_s.fill((12, 22, 8, alpha_f))
        screen.blit(fade_s, (M_X, CONTENT_TOP + i))
        screen.blit(fade_s, (M_X, CONTENT_BOT - i))

    # ── barra de scroll ────────────────────────────────────────────────
    if total_content_h > CONTENT_H:
        sb_x = M_X + M_W - 10
        sb_top = CONTENT_TOP + 4
        sb_bot = CONTENT_BOT - 4
        sb_h = sb_bot - sb_top
        thumb_ratio = min(CONTENT_H / total_content_h, 1.0)
        thumb_h = max(int(sb_h * thumb_ratio), 20)
        scroll_ratio = scroll_y / max(total_content_h - CONTENT_H, 1)
        thumb_y = sb_top + int((sb_h - thumb_h) * scroll_ratio)
        pygame.draw.rect(screen, DARK_GRAY, (sb_x, sb_top, 4, sb_h),
                         border_radius=2)
        pygame.draw.rect(screen, GOLD, (sb_x, thumb_y, 4, thumb_h),
                         border_radius=2)

    # ── dica de scroll ─────────────────────────────────────────────────
    hint_s = font_tiny.render("↑↓ scroll  •  ESC para fechar", True, GRAY)
    screen.blit(hint_s,
                (M_X + M_W // 2 - hint_s.get_width() // 2, CONTENT_BOT + 6))

    # ── botão fechar ───────────────────────────────────────────────────
    btn_close.rect.topleft = (M_X + M_W // 2 - btn_close.rect.w // 2,
                              M_Y + M_H - 44)
    btn_close.check_hover(pygame.mouse.get_pos())
    btn_close.draw(screen, t)

    return total_content_h, CONTENT_H


def run_menu(screen, WIDTH, HEIGHT):
    font_title = pygame.font.SysFont("consolas", 46, bold=True)
    font_modal = pygame.font.SysFont("consolas", 15, bold=True)
    font_sub = pygame.font.SysFont("consolas", 17)
    font_btn = pygame.font.SysFont("consolas", 22, bold=True)
    font_btn_sm = pygame.font.SysFont("consolas", 16, bold=True)
    font_tiny = pygame.font.SysFont("consolas", 13)
    font_body = pygame.font.SysFont("consolas", 14, bold=True)

    btn_play = Button(WIDTH // 2, HEIGHT // 2 + 10,  230,
                      46, "INICIAR MISSÃO", font_btn)
    btn_rules = Button(WIDTH // 2, HEIGHT // 2 + 66,  230,
                       40, "REGRAS",         font_btn)
    btn_quit = Button(WIDTH // 2, HEIGHT // 2 + 116, 230,
                      40, "RETIRADA",       font_btn)
    btn_close = Button(
        0, 0, 180, 36, "FECHAR  [ESC]", font_btn_sm)   # pos. dinâmica

    clock = pygame.time.Clock()
    tank_x = -130.0
    tank_x2 = WIDTH + 130.0

    HORIZON_Y = HEIGHT * 0.60

    menu_particles = []

    def spawn_menu_smoke(x, y):
        for _ in range(6):
            angle = random.uniform(-math.pi, 0)
            speed = random.uniform(0.3, 1.2)
            menu_particles.append({
                "x": x, "y": y,
                "vx": math.cos(angle) * speed * 0.5,
                "vy": math.sin(angle) * speed - 0.2,
                "color": random.choice([SMOKE, DARK_GRAY, (80, 80, 60)]),
                "size": random.randint(3, 7),
                "life": random.randint(40, 80),
                "max_life": 80,
            })

    show_rules = False
    rules_scroll = 0
    SCROLL_STEP = 22

    running = True
    while running:
        t = pygame.time.get_ticks() / 1000.0

        # ── fundo ──────────────────────────────────────────────────────
        draw_camo_bg(screen, WIDTH, HEIGHT, t)

        draw_terrain_strip(screen, WIDTH, HEIGHT, t,
                           HORIZON_Y + 30, 22, (25, 40, 15), alpha=240)
        draw_terrain_strip(screen, WIDTH, HEIGHT, t + 1.5,
                           HORIZON_Y + 55, 16, (35, 55, 20), alpha=230)
        draw_terrain_strip(screen, WIDTH, HEIGHT, t + 3.0,
                           HORIZON_Y + 80, 10, (45, 68, 28), alpha=220)

        pygame.draw.rect(screen, (30, 48, 18),
                         (0, int(HORIZON_Y + 90), WIDTH, HEIGHT))

        # tanques
        tank_x += 0.5
        if tank_x > WIDTH + 140:
            tank_x = -140.0
        ty1 = HORIZON_Y + 72 + math.sin(t * 0.9) * 2
        draw_tank_silhouette(screen, int(tank_x), int(ty1),
                             scale=0.85, facing_right=True)
        if random.random() < 0.08:
            spawn_menu_smoke(int(tank_x) - 50, int(ty1) - 24)

        tank_x2 -= 0.35
        if tank_x2 < -140:
            tank_x2 = WIDTH + 140.0
        ty2 = HORIZON_Y + 58 + math.sin(t * 0.7 + 1.3) * 2
        draw_tank_silhouette(screen, int(tank_x2), int(ty2),
                             scale=0.55, facing_right=False)

        draw_crosshair(screen, WIDTH - 58, 55,          28, GOLD, alpha=150)
        draw_crosshair(screen, 48,         HEIGHT - 68, 18, RED,  alpha=110)

        # partículas
        dead = []
        for p in menu_particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] -= 0.01
            p["life"] -= 1
            if p["life"] <= 0:
                dead.append(p)
        for p in dead:
            menu_particles.remove(p)
        draw_explosion_particles(screen, menu_particles)

        # ── título ─────────────────────────────────────────────────────
        title_text = "GUERRA TERRITORIAL"
        title_surf = font_title.render(title_text, True, GOLD)
        shadow_surf = font_title.render(title_text, True, (50, 35, 0))
        tx = WIDTH // 2 - title_surf.get_width() // 2
        ty_title = int(HEIGHT * 0.16) - title_surf.get_height() // 2

        plate_pad = 14
        plate_surf = pygame.Surface(
            (title_surf.get_width() + plate_pad * 2,
             title_surf.get_height() + plate_pad), pygame.SRCALPHA)
        pygame.draw.rect(plate_surf, (10, 20, 6, 190),
                         (0, 0, plate_surf.get_width(), plate_surf.get_height()),
                         border_radius=4)
        pygame.draw.rect(plate_surf, (*GOLD, 160),
                         (0, 0, plate_surf.get_width(), plate_surf.get_height()),
                         1, border_radius=4)
        screen.blit(plate_surf, (tx - plate_pad, ty_title - plate_pad // 2))
        screen.blit(shadow_surf, (tx + 3, ty_title + 3))
        screen.blit(title_surf,  (tx,     ty_title))

        dash = "─" * 30
        dash_surf = font_sub.render(dash, True, (100, 140, 60))
        screen.blit(dash_surf,
                    (WIDTH // 2 - dash_surf.get_width() // 2,
                     ty_title + title_surf.get_height() + 4))

        sub_surf = font_sub.render(
            "2 COMANDANTES  •  TURNO A TURNO", True, GRAY)
        screen.blit(sub_surf,
                    (WIDTH // 2 - sub_surf.get_width() // 2,
                     ty_title + title_surf.get_height() + 26))

        targets = [
            ("[B] Bunker",      (80,  85,  55)),
            ("[T] Tanque",      (70,  90,  45)),
            ("[Q] Quartel",     (90, 110,  50)),
            ("[R] Torre Radio", (85, 100,  48)),
            ("[S] Soldado",     (95, 115,  55)),
        ]
        legend_y = ty_title + title_surf.get_height() + 50
        for i, (lbl, col) in enumerate(targets):
            ls = font_tiny.render(lbl, True, col)
            lx = WIDTH // 2 - (len(targets) * 92) // 2 + i * 92
            screen.blit(ls, (lx, legend_y))

        # ── botões do menu ─────────────────────────────────────────────
        mouse_pos = pygame.mouse.get_pos()
        btn_play.check_hover(mouse_pos)
        btn_rules.check_hover(mouse_pos)
        btn_quit.check_hover(mouse_pos)
        btn_play.draw(screen, t)
        btn_rules.draw(screen, t)
        btn_quit.draw(screen, t)

        ver_surf = font_tiny.render("v1.0", True, DARK_GRAY)
        screen.blit(ver_surf,
                    (WIDTH - ver_surf.get_width() - 10,
                     HEIGHT - ver_surf.get_height() - 8))

        # ── modal de regras ────────────────────────────────────────────
        total_content_h = 0
        visible_h = 1
        if show_rules:
            total_content_h, visible_h = draw_rules_modal(
                screen, WIDTH, HEIGHT, t,
                font_modal, font_body, font_tiny, font_btn_sm,
                rules_scroll, btn_close)

        # ── eventos ────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.KEYDOWN:
                if show_rules:
                    if event.key == pygame.K_ESCAPE:
                        show_rules = False
                        rules_scroll = 0
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        max_scroll = max(total_content_h - visible_h, 0)
                        rules_scroll = min(
                            rules_scroll + SCROLL_STEP, max_scroll)
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        rules_scroll = max(rules_scroll - SCROLL_STEP, 0)
                else:
                    if event.key == pygame.K_RETURN:
                        return "play"
                    if event.key == pygame.K_ESCAPE:
                        return "quit"

            if event.type == pygame.MOUSEWHEEL and show_rules:
                max_scroll = max(total_content_h - visible_h, 0)
                rules_scroll = max(0, min(rules_scroll - event.y * SCROLL_STEP,
                                          max_scroll))

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if show_rules:
                    if btn_close.is_clicked(mouse_pos):
                        show_rules = False
                        rules_scroll = 0
                else:
                    if btn_play.is_clicked(mouse_pos):
                        return "play"
                    if btn_rules.is_clicked(mouse_pos):
                        show_rules = True
                        rules_scroll = 0
                    if btn_quit.is_clicked(mouse_pos):
                        return "quit"

        pygame.display.flip()
        clock.tick(60)

    return "quit"
