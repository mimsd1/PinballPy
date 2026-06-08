#PinballPy is a simple simulator/game based around the Pinball Slot Machine, using Pygame
#Made by D Mims
#Last updated 06/08/2026

import os
import random
import pygame as pg


# Screen and gameplay constants
GAME_FPS = 60
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
VISIBLE_ROWS = 3
REEL_COUNT = 3
SYMBOL_SIZE = (150, 150)

BG_COLOR = (15, 43, 56)
PANEL_COLOR = (236, 227, 200)
FRAME_COLOR = (43, 27, 21)
TEXT_COLOR = (24, 22, 18)
BUTTON_COLOR = (205, 63, 57)
BUTTON_DISABLED = (145, 145, 145)


# Symbol definitions: name -> (filename, weight, three-of-a-kind payout)
SYMBOL_DEFS = {
    "CHERRY": ("Cherry.png", 28, 20),
    "LEMON": ("Lemon.png", 24, 15),
    "BAR": ("Bar.png", 20, 35),
    "BAR2": ("2Bar.png", 16, 35),
    "BAR3": ("3Bar.png", 12, 35),
    "SEVEN": ("Seven.png", 16, 50),
    "COIN": ("Coin.png", 12, 80),
    "DIAMOND": ("Gem.png", 8, 100),
    "PINBALL": ("Pinball.png", 4, 150),
}


main_dir = os.path.split(os.path.abspath(__file__))[0]
data_dir = os.path.join(main_dir, "data")


def weighted_pick(k=1):
    names = list(SYMBOL_DEFS.keys())
    weights = [SYMBOL_DEFS[name][1] for name in names]
    return random.choices(names, weights=weights, k=k)


def load_symbol_images(symbol_size, fallback_font):
    images = {}
    fallback_colors = {
        "CHERRY": (203, 30, 56),
        "LEMON": (237, 212, 72),
        "BAR": (36, 35, 35),
        "BAR2": (50, 50, 50),
        "BAR3": (70, 70, 70),
        "SEVEN": (35, 160, 68),
        "COIN": (220, 148, 41),
        "DIAMOND": (0, 255, 255),
        "PINBALL": (255, 0, 255),
    }

    for name, (filename, _weight, _payout) in SYMBOL_DEFS.items():
        path = os.path.join(data_dir, filename)
        if os.path.exists(path):
            image = pg.image.load(path).convert_alpha()
            image = pg.transform.smoothscale(image, symbol_size)
            images[name] = image
            continue

        # Fallback art keeps the game playable if assets are not ready yet.
        surf = pg.Surface(symbol_size, pg.SRCALPHA)
        color = fallback_colors.get(name, (100, 100, 100))
        surf.fill((245, 242, 232))
        pg.draw.rect(surf, color, surf.get_rect().inflate(-14, -14), border_radius=16)
        text = fallback_font.render(name, True, (246, 246, 246))
        text_rect = text.get_rect(center=surf.get_rect().center)
        surf.blit(text, text_rect)
        images[name] = surf

    return images


def make_reel_strip(length=26):
    # Make a weighted strip so reels look random while still using predictable symbols.
    strip = weighted_pick(k=length)
    random.shuffle(strip)
    return strip


class Reel:
    def __init__(self, x, y, symbol_w, symbol_h, visible_rows=3):
        self.x = x
        self.y = y
        self.symbol_w = symbol_w
        self.symbol_h = symbol_h
        self.visible_rows = visible_rows
        self.strip = make_reel_strip()
        self.strip_px = len(self.strip) * self.symbol_h
        self.offset_px = random.uniform(0.0, self.strip_px)

        self.spinning = False
        self.speed = 0.0
        self.decel = 0.0
        self.spin_until_ms = 0

        self.target_symbol = None
        self.target_offset_px = None
        self.slam_stopping = False
        self.slam_until_ms = 0

    @property
    def rect(self):
        return pg.Rect(
            self.x,
            self.y,
            self.symbol_w,
            self.symbol_h * self.visible_rows,
        )

    def start_spin(self, now_ms, target_symbol, min_spin_ms):
        self.spinning = True
        self.slam_stopping = False
        self.slam_until_ms = 0
        self.speed = random.uniform(2200.0, 2700.0)
        self.decel = random.uniform(2200.0, 2800.0)
        self.spin_until_ms = now_ms + min_spin_ms
        self.target_symbol = target_symbol
        self.target_offset_px = None

    def start_slam_stop(self, now_ms, slam_ms=140):
        if not self.spinning:
            return

        if self.target_offset_px is None:
            self._compute_target_offset()

        self.slam_stopping = True
        self.slam_until_ms = now_ms + slam_ms
        # Force the reel into a quick braking phase.
        self.spin_until_ms = now_ms
        self.decel = max(self.decel, 6400.0)

    def _compute_target_offset(self):
        candidates = []
        n = len(self.strip)
        current = self.offset_px % self.strip_px

        for idx, symbol_name in enumerate(self.strip):
            if symbol_name == self.target_symbol:
                # Center row is row index 1, so top row should be (target - 1).
                top_index = (idx - 1) % n
                candidate = float(top_index * self.symbol_h)
                distance = (candidate - current) % self.strip_px
                candidates.append((distance, candidate))

        if not candidates:
            self.target_offset_px = current
            return

        # Avoid very short snap by preferring a candidate at least a few symbols ahead.
        min_forward = self.symbol_h * 3
        valid = [item for item in candidates if item[0] >= min_forward]
        if valid:
            chosen = min(valid, key=lambda item: item[0])
        else:
            chosen = min(candidates, key=lambda item: item[0])

        self.target_offset_px = chosen[1]

    def update(self, dt, now_ms):
        if not self.spinning:
            return

        self.offset_px = (self.offset_px + self.speed * dt) % self.strip_px

        if now_ms < self.spin_until_ms:
            return

        self.speed = max(280.0, self.speed - self.decel * dt)

        if self.target_offset_px is None and self.speed <= 750.0:
            self._compute_target_offset()

        if self.target_offset_px is None:
            return

        if self.slam_stopping and now_ms < self.slam_until_ms:
            return

        if self.slam_stopping:
            # End slam stop by locking directly to the precomputed landing position.
            self.offset_px = self.target_offset_px
            self.speed = 0.0
            self.spinning = False
            self.slam_stopping = False
            return

        snap_speed = 920.0
        current = self.offset_px % self.strip_px
        distance = (self.target_offset_px - current) % self.strip_px

        if distance <= 2.0:
            self.offset_px = self.target_offset_px
            self.speed = 0.0
            self.spinning = False
            return

        step = min(distance, snap_speed * dt)
        self.offset_px = (self.offset_px + step) % self.strip_px

    def force_stop(self):
        if not self.spinning:
            return

        if self.target_offset_px is None:
            self._compute_target_offset()

        if self.target_offset_px is not None:
            self.offset_px = self.target_offset_px

        self.speed = 0.0
        self.spinning = False
        self.slam_stopping = False

    def draw(self, screen, symbol_images):
        reel_rect = self.rect
        original_clip = screen.get_clip()
        screen.set_clip(reel_rect)

        base_index = int(self.offset_px // self.symbol_h)
        sub_offset = self.offset_px % self.symbol_h
        start_y = self.y - sub_offset

        rows_to_draw = self.visible_rows + 2
        for row in range(rows_to_draw):
            symbol_name = self.strip[(base_index + row) % len(self.strip)]
            symbol_img = symbol_images[symbol_name]
            screen.blit(symbol_img, (self.x, start_y + row * self.symbol_h))

        screen.set_clip(original_clip)
        pg.draw.rect(screen, FRAME_COLOR, reel_rect, width=6, border_radius=12)

    def center_symbol(self):
        top_index = int(self.offset_px // self.symbol_h)
        center_index = (top_index + 1) % len(self.strip)
        return self.strip[center_index]


def evaluate_payout(center_symbols):
    a, b, c = center_symbols

    if a == b == c:
        return SYMBOL_DEFS[a][2], f"JACKPOT: {a} x3"
    if a == b or b == c or a == c:
        return 8, "Pair match"
    return 0, "No win"


def draw_ui(screen, big_font, small_font, credits, bet, last_win, status_text, can_spin, spin_button):
    title = big_font.render("PINBALLPY SLOT", True, PANEL_COLOR)
    screen.blit(title, (40, 26))

    stats = small_font.render(
        f"Credits: {credits}   Bet: {bet}   Last Win: {last_win}",
        True,
        PANEL_COLOR,
    )
    screen.blit(stats, (40, 84))

    status = small_font.render(status_text, True, PANEL_COLOR)
    screen.blit(status, (40, 118))

    button_color = BUTTON_COLOR if can_spin else BUTTON_DISABLED
    pg.draw.rect(screen, button_color, spin_button, border_radius=12)
    pg.draw.rect(screen, FRAME_COLOR, spin_button, width=3, border_radius=12)
    label = small_font.render("SPIN (SPACE)", True, (245, 245, 245))
    label_rect = label.get_rect(center=spin_button.center)
    screen.blit(label, label_rect)


def main():
    pg.init()
    pg.display.set_caption("PinballPy")

    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SCALED)
    clock = pg.time.Clock()

    fallback_font = pg.font.Font(None, 28)
    big_font = pg.font.Font(None, 66)
    small_font = pg.font.Font(None, 38)

    symbol_images = load_symbol_images(SYMBOL_SIZE, fallback_font)

    symbol_w, symbol_h = SYMBOL_SIZE
    gap = 42
    total_w = REEL_COUNT * symbol_w + (REEL_COUNT - 1) * gap
    start_x = (SCREEN_WIDTH - total_w) // 2
    start_y = 220

    reels = []
    for i in range(REEL_COUNT):
        x = start_x + i * (symbol_w + gap)
        reels.append(Reel(x=x, y=start_y, symbol_w=symbol_w, symbol_h=symbol_h, visible_rows=VISIBLE_ROWS))

    spin_button = pg.Rect(SCREEN_WIDTH - 260, 72, 200, 70)

    credits = 100
    bet = 2
    last_win = 0
    status_text = "Press SPACE or click SPIN"
    spinning_round = False

    def start_round(now_ms):
        nonlocal credits, spinning_round, status_text
        credits -= bet
        targets = weighted_pick(k=REEL_COUNT)
        for idx, reel in enumerate(reels):
            reel.start_spin(now_ms, targets[idx], min_spin_ms=360 + idx * 180)
        spinning_round = True
        status_text = "Spinning..."

    def quick_stop_round():
        nonlocal status_text
        for reel in reels:
            reel.start_slam_stop(now_ms)
        status_text = "Slam stop!"

    running = True
    while running:
        dt = clock.tick(GAME_FPS) / 1000.0
        now_ms = pg.time.get_ticks()

        can_spin = (not spinning_round) and (credits >= bet)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    running = False
                elif event.key == pg.K_SPACE:
                    if spinning_round:
                        quick_stop_round()
                    elif can_spin:
                        start_round(now_ms)
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                if spin_button.collidepoint(event.pos):
                    if spinning_round:
                        quick_stop_round()
                    elif can_spin:
                        start_round(now_ms)

        for reel in reels:
            reel.update(dt, now_ms)

        if spinning_round and all(not reel.spinning for reel in reels):
            center_symbols = [reel.center_symbol() for reel in reels]
            payout, message = evaluate_payout(center_symbols)
            credits += payout
            last_win = payout
            spinning_round = False
            status_text = f"{message} -> {' - '.join(center_symbols)}"

        screen.fill(BG_COLOR)

        machine_panel = pg.Rect(start_x - 24, start_y - 20, total_w + 48, symbol_h * VISIBLE_ROWS + 40)
        pg.draw.rect(screen, PANEL_COLOR, machine_panel, border_radius=20)
        pg.draw.rect(screen, FRAME_COLOR, machine_panel, width=8, border_radius=20)

        for reel in reels:
            reel.draw(screen, symbol_images)

        # Payline highlight (center row)
        payline_y = start_y + symbol_h + symbol_h // 2
        pg.draw.line(screen, (220, 70, 52), (start_x - 8, payline_y), (start_x + total_w + 8, payline_y), 5)

        draw_ui(
            screen,
            big_font,
            small_font,
            credits,
            bet,
            last_win,
            status_text,
            can_spin,
            spin_button,
        )

        pg.display.flip()

    pg.quit()


if __name__ == "__main__":
    main()

#Lifes a Gamble
