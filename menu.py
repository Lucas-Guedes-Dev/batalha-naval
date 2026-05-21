import pygame
import math
import random

WHITE = (255, 255, 255)
BLACK = (0,   0,   0)
BLUE = (0,  80, 160)
DARK_BLUE = (0,  30,  80)
NAVY = (10,  20,  60)
LIGHT_BLUE = (100, 180, 255)
GOLD = (220, 180,  60)
RED = (200,  40,  40)
GRAY = (160, 160, 180)
DARK_GRAY = (60,  60,  80)


def draw_wave(surface, W, H, t, y_base, amplitude, color, alpha=180):
    wave_surf = pygame.Surface((W, H), pygame.SRCALPHA)
    points = [(0, H)]
    for x in range(W + 1):
        y = y_base + math.sin((x / 80.0) + t) * amplitude
        points.append((x, int(y)))
    points.append((W, H))
    pygame.draw.polygon(wave_surf, (*color, alpha), points)
    surface.blit(wave_surf, (0, 0))


def draw_ship_silhouette(surface, x, y, scale=1.0):
    hull = [
        (x - int(60 * scale), y),
        (x - int(70 * scale), y + int(12 * scale)),
        (x + int(70 * scale), y + int(12 * scale)),
        (x + int(60 * scale), y),
    ]
    pygame.draw.polygon(surface, DARK_GRAY, hull)

    pygame.draw.rect(surface, DARK_GRAY,
                     (x - int(20 * scale), y - int(22 * scale),
                      int(30 * scale), int(22 * scale)))

    pygame.draw.rect(surface, GRAY,
                     (x + int(10 * scale), y - int(14 * scale),
                      int(8 * scale), int(14 * scale)))

    pygame.draw.line(surface, GRAY,
                     (x - int(5 * scale), y - int(30 * scale)),
                     (x + int(40 * scale), y - int(10 * scale)), 2)

    pygame.draw.line(surface, GRAY,
                     (x - int(5 * scale), y - int(30 * scale)),
                     (x - int(5 * scale), y - int(22 * scale)), 2)


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


class Button:
    def __init__(self, x, y, w, h, text, font):
        self.rect = pygame.Rect(x - w // 2, y - h // 2, w, h)
        self.text = text
        self.font = font
        self.hovered = False
        self.border_anim = 0

    def draw(self, surface, t):
        self.border_anim = t

        if self.hovered:
            bg_color = (0, 60, 130)
            border_color = GOLD
            text_color = GOLD
            border_w = 2
        else:
            bg_color = (0, 30, 80, 200)
            border_color = LIGHT_BLUE
            text_color = WHITE
            border_w = 1

        btn_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(
            btn_surf, (*bg_color[:3], 220), (0, 0, self.rect.w, self.rect.h), border_radius=4)
        pygame.draw.rect(btn_surf, border_color, (0, 0,
                         self.rect.w, self.rect.h), border_w, border_radius=4)
        surface.blit(btn_surf, self.rect.topleft)

        text_surf = self.font.render(self.text, True, text_color)
        tr = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, tr)

        if self.hovered:
            corner_len = 8
            cx, cy, cw, ch = self.rect
            for dx, dy, sx, sy in [(-2, -2, 1, 1), (cw + 2, -2, -1, 1),
                                   (-2, ch + 2, 1, -1), (cw + 2, ch + 2, -1, -1)]:
                px, py = cx + dx, cy + dy
                pygame.draw.line(surface, GOLD, (px, py),
                                 (px + sx * corner_len, py), 2)
                pygame.draw.line(surface, GOLD, (px, py),
                                 (px, py + sy * corner_len), 2)

    def check_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)
        return self.hovered

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


def run_menu(screen, WIDTH, HEIGHT):
    font_title = pygame.font.SysFont("consolas", 48, bold=True)
    font_sub = pygame.font.SysFont("consolas", 18)
    font_btn = pygame.font.SysFont("consolas", 22, bold=True)

    btn_play = Button(WIDTH // 2, HEIGHT // 2 + 20,
                      220, 48, "JOGAR", font_btn)
    btn_quit = Button(WIDTH // 2, HEIGHT // 2 + 84,
                      220, 48, "SAIR",  font_btn)

    clock = pygame.time.Clock()
    ship_x = -100.0
    running = True

    WAVE_TOP = HEIGHT * 0.62

    while running:
        t = pygame.time.get_ticks() / 1000.0
        screen.fill(NAVY)

        for row in range(HEIGHT // 20 + 1):
            alpha = 15 + (row % 2) * 8
            s = pygame.Surface((WIDTH, 20), pygame.SRCALPHA)
            pygame.draw.rect(s, (255, 255, 255, alpha), (0, 0, WIDTH, 20))
            screen.blit(s, (0, row * 20))

        deep_y = int(WAVE_TOP - 20)
        pygame.draw.rect(screen, (0, 40, 100),
                         (0, deep_y, WIDTH, HEIGHT - deep_y))

        draw_wave(screen, WIDTH, HEIGHT, t * 0.8,
                  HEIGHT * 0.62, 14, (0,  50, 120), alpha=230)
        draw_wave(screen, WIDTH, HEIGHT, t * 0.6 + 1.2,
                  HEIGHT * 0.65, 10, (0,  80, 160), alpha=210)
        draw_wave(screen, WIDTH, HEIGHT, t * 1.0 + 2.5,
                  HEIGHT * 0.68,  7, (0, 100, 180), alpha=190)

        ship_x += 0.4
        if ship_x > WIDTH + 100:
            ship_x = -120.0
        ship_y = HEIGHT * 0.62 + math.sin(t * 0.8) * 4
        draw_ship_silhouette(screen, int(ship_x), int(ship_y), scale=0.9)

        draw_crosshair(screen, WIDTH - 60, 60,        30, GOLD, alpha=160)
        draw_crosshair(screen, 50,         HEIGHT - 70, 20, RED,  alpha=120)

        for i in range(3):
            px = int(70 + i * 180 + math.sin(t + i) * 5)
            py = int(HEIGHT * 0.58 - i * 6 + math.cos(t * 1.2 + i) * 4)
            pygame.draw.circle(screen, (*LIGHT_BLUE, 80), (px, py), 3 + i)

        title_text = "BATALHA NAVAL"
        title_surf = font_title.render(title_text, True, GOLD)
        shadow_surf = font_title.render(title_text, True, (80, 50, 0))
        tx = WIDTH // 2 - title_surf.get_width() // 2
        ty = HEIGHT // 4 - title_surf.get_height() // 2
        screen.blit(shadow_surf, (tx + 3, ty + 3))
        screen.blit(title_surf,  (tx, ty))

        dash = "─" * 28
        dash_surf = font_sub.render(dash, True, LIGHT_BLUE)
        screen.blit(dash_surf, (WIDTH // 2 - dash_surf.get_width() // 2,
                                ty + title_surf.get_height() + 4))

        sub_surf = font_sub.render("2 JOGADORES  •  TURNO A TURNO", True, GRAY)
        screen.blit(sub_surf, (WIDTH // 2 - sub_surf.get_width() // 2,
                               ty + title_surf.get_height() + 24))

        mouse_pos = pygame.mouse.get_pos()
        btn_play.check_hover(mouse_pos)
        btn_quit.check_hover(mouse_pos)
        btn_play.draw(screen, t)
        btn_quit.draw(screen, t)

        version_surf = font_sub.render("v1.0", True, DARK_GRAY)
        screen.blit(version_surf, (WIDTH - version_surf.get_width() - 10,
                                   HEIGHT - version_surf.get_height() - 8))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_play.is_clicked(mouse_pos):
                    return "play"
                if btn_quit.is_clicked(mouse_pos):
                    return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return "play"
                if event.key == pygame.K_ESCAPE:
                    return "quit"

        pygame.display.flip()
        clock.tick(60)

    return "quit"
