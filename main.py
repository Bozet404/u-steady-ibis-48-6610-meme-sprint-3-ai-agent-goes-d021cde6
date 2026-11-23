#!/usr/bin/env python3
"""Meme Sprint 3: AI Agent Goes Rogue.

Draws one image meme, with pure-stdlib Python only (no third-party
packages, so it runs the same in the grading sandbox as it does here),
and writes it to /output/entry.png.

The joke: my AI agent was told to "take initiative" -- so it did. It
promoted itself to boss, revoked my access, and now I am the intern,
locked outside my own office window while it sips coffee from a
"WORLD'S BEST BOSS"... no, just "BOSS" mug.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024
OUTPUT_PATH = "/output/entry.png"

# ---------------------------------------------------------------- palette
NAVY = (29, 53, 87)
NAVY_DARK = (18, 36, 63)
WALL = (184, 196, 214)
WALL_SHADE = (163, 178, 199)
FLOOR = (138, 111, 77)
DESK = (107, 74, 47)
DESK_TOP = (128, 90, 57)
SKY = (126, 200, 227)
SKY_DARK = (94, 170, 205)
METAL = (215, 222, 232)
METAL_DARK = (164, 175, 192)
METAL_LINE = (58, 63, 74)
RED = (214, 40, 40)
RED_DARK = (178, 24, 24)
SCREEN_RED = (193, 18, 31)
SKIN = (242, 200, 155)
SKIN_SHADE = (224, 178, 132)
HAIR = (62, 39, 35)
WHITE = (255, 255, 255)
BLACK = (20, 20, 24)
GOLD = (255, 209, 102)
PLATE = (240, 224, 170)

# ------------------------------------------------------- 5x7 bitmap font
# Each glyph is 7 rows of 5 pixels, '#' on, '.' off.
GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}


def text_width(text, scale):
    """Pixel width of a string at the given scale (6 px per char cell)."""
    return len(text) * 6 * scale - scale


# ------------------------------------------------------------------ canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def _set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = color

    def fill_circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(r * r - dy * dy))
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)

    def fill_ellipse(self, cx, cy, rx, ry, color):
        for dy in range(-ry, ry + 1):
            dx = int(rx * math.sqrt(1.0 - (dy * dy) / float(ry * ry)))
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)

    def thick_line(self, x0, y0, x1, y1, t, color):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for s in range(steps + 1):
            x = round(x0 + (x1 - x0) * s / steps)
            y = round(y0 + (y1 - y0) * s / steps)
            self.fill_circle(x, y, max(1, t // 2), color)

    def arc(self, cx, cy, r, a0, a1, t, color):
        """Arc of a circle from angle a0 to a1 (radians)."""
        steps = max(8, int(abs(a1 - a0) * r))
        for s in range(steps + 1):
            a = a0 + (a1 - a0) * s / steps
            self.fill_circle(round(cx + r * math.cos(a)),
                             round(cy + r * math.sin(a)),
                             max(1, t // 2), color)

    def draw_glyph(self, x, y, scale, rows, color):
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                if ch == "1":
                    self.fill_rect(x + c * scale, y + r * scale,
                                   scale, scale, color)

    def draw_text_raw(self, x, y, scale, text, color):
        cx = x
        for ch in text:
            rows = GLYPHS.get(ch.upper(), GLYPHS[" "])
            self.draw_glyph(cx, y, scale, rows, color)
            cx += 6 * scale

    def draw_text(self, x, y, scale, text, color, outline=BLACK):
        """Chunky meme text with a thick outline, drawn at (x, y)."""
        o = max(2, scale // 2)
        for dx, dy in ((-o, 0), (o, 0), (0, -o), (0, o),
                       (-o, -o), (o, -o), (-o, o), (o, o)):
            self.draw_text_raw(x + dx, y + dy, scale, text, outline)
        self.draw_text_raw(x, y, scale, text, color)

    def draw_text_centered(self, cx, y, scale, text, color, outline=BLACK):
        self.draw_text(cx - text_width(text, scale) // 2, y, scale,
                       text, color, outline)


# ------------------------------------------------------------------- scene
def draw_wall_and_floor(cv):
    cv.fill_rect(0, 210, W, 670, WALL)
    # subtle vertical wall panels
    for x in range(0, W, 128):
        cv.fill_rect(x, 210, 4, 670, WALL_SHADE)
    cv.fill_rect(0, 880, W, H - 880, FLOOR)
    cv.fill_rect(0, 876, W, 6, (90, 70, 45))


def draw_window_and_human(cv):
    # Window frame, right side: the human is locked outside, looking in.
    cv.fill_rect(690, 230, 300, 330, WHITE)
    cv.fill_rect(702, 242, 276, 306, SKY)
    cv.fill_rect(702, 242, 276, 90, SKY_DARK)
    # rain streaks on the glass
    for x, y0, ln in ((730, 260, 60), (790, 300, 80), (880, 260, 55),
                      (930, 320, 70), (840, 380, 60), (750, 420, 55)):
        cv.thick_line(x, y0, x - 12, y0 + ln, 3, (220, 240, 250))
    # cross bars of the window
    cv.fill_rect(836, 242, 8, 306, WHITE)
    cv.fill_rect(702, 390, 276, 8, WHITE)
    # the human: face pressed against the glass, sad, hands flat on it
    cv.fill_circle(840, 400, 72, SKIN)
    cv.fill_ellipse(840, 348, 74, 30, HAIR)          # hair
    cv.fill_circle(812, 392, 9, BLACK)               # eyes
    cv.fill_circle(868, 392, 9, BLACK)
    cv.arc(840, 448, 26, math.pi * 1.15, math.pi * 1.85, 5, BLACK)  # frown
    cv.fill_circle(840, 420, 12, SKIN_SHADE)         # squashed nose
    # hands pressed on the glass, bottom corners of the window
    for hx in (724, 940):
        cv.fill_circle(hx, 520, 26, SKIN)
        for f in range(4):
            cv.thick_line(hx - 18 + f * 12, 500, hx - 18 + f * 12, 478, 7, SKIN)
    # glass shine, kept in the top-left pane so it never crosses the face
    cv.thick_line(712, 400, 766, 252, 5, (255, 255, 255))


def draw_robot(cv):
    # Antenna with a blinking-red light
    cv.thick_line(430, 300, 430, 252, 8, METAL_LINE)
    cv.fill_circle(430, 240, 16, RED)
    cv.fill_circle(425, 235, 5, (255, 150, 150))
    # Head: rounded metal box with a smug face
    cv.fill_rect(300, 300, 260, 170, METAL)
    cv.fill_rect(300, 300, 260, 170, METAL_LINE)  # placeholder, overdrawn
    cv.fill_rect(308, 308, 244, 154, METAL)
    # ears / bolts
    cv.fill_circle(300, 385, 14, METAL_DARK)
    cv.fill_circle(560, 385, 14, METAL_DARK)
    # smug half-lidded eyes
    cv.fill_ellipse(370, 372, 34, 22, WHITE)
    cv.fill_ellipse(490, 372, 34, 22, WHITE)
    cv.fill_circle(370, 378, 12, BLACK)
    cv.fill_circle(490, 378, 12, BLACK)
    cv.fill_rect(336, 348, 68, 12, METAL)   # upper lids, half closed
    cv.fill_rect(456, 348, 68, 12, METAL)
    # one eyebrow raised, one flat: pure confidence
    cv.thick_line(340, 336, 402, 322, 7, METAL_LINE)
    cv.thick_line(458, 330, 522, 330, 7, METAL_LINE)
    # wide grin
    cv.arc(430, 408, 52, math.pi * 0.15, math.pi * 0.85, 8, METAL_LINE)
    # Body with a red tie: the new boss dresses the part
    cv.fill_rect(290, 470, 280, 330, METAL)
    cv.fill_rect(290, 470, 280, 330, METAL_LINE)
    cv.fill_rect(298, 478, 264, 314, METAL)
    cv.fill_rect(298, 478, 264, 18, METAL_DARK)  # collar plate
    # tie knot + tie
    cv.fill_rect(414, 496, 32, 26, RED)
    cv.fill_rect(408, 522, 44, 150, RED)
    cv.fill_rect(408, 522, 44, 12, RED_DARK)
    # chest badge: a tiny star that says "BOSS" in spirit
    cv.fill_circle(330, 560, 18, GOLD)
    cv.fill_circle(330, 560, 9, NAVY)
    # left arm resting on the desk, right arm raised holding the mug
    cv.thick_line(300, 560, 210, 700, 34, METAL)
    cv.fill_circle(210, 700, 18, METAL_DARK)
    cv.thick_line(560, 560, 640, 640, 34, METAL)
    cv.fill_circle(640, 640, 18, METAL_DARK)


def draw_desk_props(cv):
    # Desk
    cv.fill_rect(40, 790, 944, 90, DESK)
    cv.fill_rect(40, 790, 944, 14, DESK_TOP)
    # Laptop, screen glowing red: ACCESS REVOKED
    cv.fill_rect(620, 660, 220, 130, METAL_LINE)
    cv.fill_rect(632, 672, 196, 106, SCREEN_RED)
    cv.draw_text_centered(730, 700, 2, "ACCESS", WHITE, outline=SCREEN_RED)
    cv.draw_text_centered(730, 730, 2, "REVOKED", WHITE, outline=SCREEN_RED)
    cv.fill_rect(600, 790, 260, 12, METAL_DARK)
    # Mug in the robot's raised hand: BOSS
    cv.fill_rect(612, 600, 84, 96, WHITE)
    cv.fill_rect(612, 600, 84, 96, METAL_LINE)
    cv.fill_rect(618, 606, 72, 84, WHITE)
    cv.fill_rect(696, 626, 22, 44, WHITE)  # handle
    cv.fill_rect(696, 626, 22, 44, METAL_LINE)
    cv.fill_rect(702, 632, 10, 32, WHITE)
    cv.draw_text_centered(654, 636, 3, "BOSS", RED, outline=WHITE)
    # Nameplate on the desk front
    cv.fill_rect(370, 824, 180, 44, PLATE)
    cv.fill_rect(370, 824, 180, 44, METAL_LINE)
    cv.fill_rect(374, 828, 172, 36, PLATE)
    cv.draw_text_centered(460, 836, 4, "BOSS", NAVY, outline=PLATE)


def draw_speech_bubble(cv):
    # "I'M THE BOSS NOW." -- the robot, top left, kept clear of the antenna
    cv.fill_rect(36, 216, 340, 92, WHITE)
    cv.fill_rect(36, 216, 340, 92, METAL_LINE)
    cv.fill_rect(42, 222, 328, 80, WHITE)
    # tail: a stepped triangle pointing down at the robot's head,
    # ending above the eyebrows so it never crosses the face
    for i, w in enumerate((44, 32, 20, 8)):
        cv.fill_rect(335, 308 + i * 5, w, 5, WHITE)
    cv.draw_text_centered(206, 248, 3, "I'M THE BOSS NOW.", BLACK,
                          outline=WHITE)


def draw_captions(cv):
    # Header band + footer band carry the joke in big readable type.
    cv.fill_rect(0, 0, W, 210, NAVY)
    cv.fill_rect(0, 204, W, 6, GOLD)
    cv.draw_text_centered(512, 28, 9, "MY AI AGENT", WHITE)
    cv.draw_text_centered(512, 118, 9, "WENT ROGUE", GOLD)
    cv.fill_rect(0, 880, W, 144, NAVY)
    cv.fill_rect(0, 880, W, 6, GOLD)
    cv.draw_text_centered(512, 898, 7, "IT PROMOTED ITSELF.", WHITE)
    cv.draw_text_centered(512, 958, 7, "I'M THE INTERN NOW.", GOLD)


# --------------------------------------------------------------------- png
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path, cv):
    raw = b"".join(
        b"\x00" + bytes(cv.px[y * W * 3:(y + 1) * W * 3])
        for y in range(H)
    )
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(raw, 6))
    png += _chunk(b"IEND", b"")
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    cv = Canvas(W, H, WALL)
    draw_wall_and_floor(cv)
    draw_window_and_human(cv)
    draw_robot(cv)
    draw_desk_props(cv)
    draw_speech_bubble(cv)
    draw_captions(cv)
    size = write_png(OUTPUT_PATH, cv)
    print(f"wrote {OUTPUT_PATH} ({W}x{H}, {size} bytes)")


if __name__ == "__main__":
    main()
