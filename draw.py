#!/usr/bin/env python3
"""Draw the news-image-20261119 v3 entry: a dated world map of 19 Nov 2026.

Stdlib only. No network, no randomness, no timestamps: running this script
twice produces byte-identical PNG output.

Layout (1024x1024):
  - slim navy masthead with the date "19 NOVEMBER 2026"
  - equirectangular world map with 4 numbered pins
  - bottom legend strip, 2x2 boxes, one verified fact each
"""

import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- colours --
PAPER = (247, 243, 234)
NAVY = (16, 38, 59)
GOLD = (242, 193, 78)
OCEAN = (183, 217, 234)
GRID = (160, 198, 219)
LAND = (234, 223, 192)
LAND_EDGE = (122, 111, 77)
INK = (34, 34, 34)
PIN = (215, 38, 61)
WHITE = (255, 255, 255)

# ------------------------------------------------------------- framebuffer --
fb = bytearray(W * H * 3)


def fill_rect(x0, y0, x1, y1, color):
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(W, x1)
    y1 = min(H, y1)
    if x0 >= x1 or y0 >= y1:
        return
    r, g, b = color
    row = bytes((r, g, b)) * (x1 - x0)
    for y in range(y0, y1):
        off = (y * W + x0) * 3
        fb[off:off + len(row)] = row


def set_px(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        off = (y * W + x) * 3
        fb[off], fb[off + 1], fb[off + 2] = color


def draw_line(x0, y0, x1, y1, color):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        set_px(x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def draw_circle(cx, cy, r, color):
    for dy in range(-r, r + 1):
        dx = int((r * r - dy * dy) ** 0.5)
        fill_rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, color)


def fill_polygon(pts, color):
    ys = [p[1] for p in pts]
    y0 = max(0, min(ys))
    y1 = min(H - 1, max(ys))
    n = len(pts)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x1, ya = pts[i]
            x2, yb = pts[(i + 1) % n]
            if (ya <= y < yb) or (yb <= y < ya):
                xs.append(x1 + (y - ya) * (x2 - x1) / (yb - ya))
        xs.sort()
        for j in range(0, len(xs) - 1, 2):
            fill_rect(int(xs[j]), y, int(xs[j + 1]) + 1, y + 1, color)


def outline_polygon(pts, color):
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        draw_line(x1, y1, x2, y2, color)


# ------------------------------------------------------------------- font --
# 5x7 bitmap font. Each glyph is 7 rows of 5 cells ('#' = ink).
# Narrow glyphs ('i', 'l', 'I', '1') are drawn 3 cells wide on their bar
# rows: at the fixed 6-cell advance a 1-2 cell glyph leaves a gap wide
# enough to read as a word space, splitting words visually mid-word.
FONT = {
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    'D': ("###..", "#..#.", "#...#", "#...#", "#...#", "#..#.", "###.."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    'a': (".....", ".....", ".###.", "....#", ".####", "#...#", ".####"),
    'b': ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    'c': (".....", ".....", ".###.", "#...#", "#....", "#...#", ".###."),
    'd': ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    'e': (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    'f': ("..##.", ".#..#", ".#...", "####.", ".#...", ".#...", ".#..."),
    'g': (".....", ".####", "#...#", "#...#", ".####", "....#", ".###."),
    'h': ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    'i': ("..#..", ".....", ".###.", "..#..", "..#..", "..#..", ".###."),
    'j': ("..#..", ".....", ".##..", "..#..", "..#..", "..#..", "##..."),
    'k': ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    'l': (".##..", ".##..", ".##..", ".##..", ".##..", ".##..", ".###."),
    'm': (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    'n': (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    'o': (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    'p': (".....", ".....", "####.", "#...#", "#...#", "####.", "#...."),
    'q': (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
    'r': (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    's': (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    't': (".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."),
    'u': (".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#"),
    'v': (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'w': (".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    'x': (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    'y': (".....", "#...#", "#...#", "#...#", ".####", "....#", ".###."),
    'z': (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
    '0': (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    '1': ("..#..", ".###.", "..#..", "..#..", "..#..", "..#..", ".###."),
    '2': (".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"),
    '3': ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ',': (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ':': (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    "'": (".#...", ".#...", "#....", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    '-': (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    '/': ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    '&': (".###.", "#...#", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    '(': ("...#.", "..#..", "..#..", "..#..", "..#..", "..#..", "...#."),
    ')': (".#...", "..#..", "..#..", "..#..", "..#..", "..#..", ".#..."),
    '%': ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    '!': (".#...", ".#...", ".#...", ".#...", ".#...", ".....", ".#..."),
    '?': (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale if s else 0


def draw_text(x, y, scale, s, color, bold=False):
    for ci, ch in enumerate(s):
        glyph = FONT.get(ch, FONT[' '])
        cx = x + ci * 6 * scale
        for row in range(7):
            for col in range(5):
                if glyph[row][col] == '#':
                    fill_rect(cx + col * scale, y + row * scale,
                              cx + (col + 1) * scale, y + (row + 1) * scale,
                              color)
    if bold:
        shift = max(1, scale // 3)
        for ci, ch in enumerate(s):
            glyph = FONT.get(ch, FONT[' '])
            cx = x + ci * 6 * scale + shift
            for row in range(7):
                for col in range(5):
                    if glyph[row][col] == '#':
                        fill_rect(cx + col * scale, y + row * scale,
                                  cx + (col + 1) * scale,
                                  y + (row + 1) * scale, color)


def wrap_text(s, max_chars):
    lines = []
    for word in s.split(' '):
        if not lines or len(lines[-1]) + 1 + len(word) > max_chars:
            lines.append(word)
        else:
            lines[-1] += ' ' + word
    return lines


# ------------------------------------------------------------ map geometry --
MAP_X0, MAP_Y0, MAP_W, MAP_H = 16, 100, 992, 540
LAT_TOP, LAT_BOT = 84.0, -58.0


def project(lon, lat):
    x = MAP_X0 + (lon + 180.0) / 360.0 * MAP_W
    y = MAP_Y0 + (LAT_TOP - lat) / (LAT_TOP - LAT_BOT) * MAP_H
    return int(round(x)), int(round(y))


def project_poly(poly):
    return [project(lon, lat) for lon, lat in poly]


# Simplified continent outlines, (lon, lat). Coarse but recognisable.
NORTH_AMERICA = [
    (-168, 66), (-160, 58), (-152, 60), (-140, 60), (-134, 57), (-128, 54),
    (-124, 48), (-124, 42), (-120, 34), (-114, 29), (-110, 23), (-105, 20),
    (-97, 16), (-92, 15), (-87, 13), (-83, 9), (-79, 9), (-77, 7), (-83, 10),
    (-87, 14), (-91, 19), (-97, 26), (-93, 30), (-89, 30), (-84, 30),
    (-81, 25), (-80, 32), (-76, 35), (-74, 40), (-70, 42), (-67, 45),
    (-60, 46), (-65, 49), (-60, 52), (-64, 58), (-68, 58), (-73, 62),
    (-78, 62), (-85, 66), (-92, 66), (-95, 69), (-110, 68), (-125, 70),
    (-140, 70), (-155, 71), (-166, 68),
]
GREENLAND = [
    (-44, 60), (-40, 64), (-32, 68), (-22, 70), (-20, 76), (-28, 81),
    (-45, 82), (-58, 80), (-60, 76), (-53, 71), (-50, 66),
]
SOUTH_AMERICA = [
    (-77, 7), (-75, 10), (-71, 12), (-64, 10), (-60, 8), (-52, 5), (-50, 0),
    (-44, -3), (-35, -8), (-35, -15), (-39, -20), (-41, -23), (-48, -28),
    (-52, -33), (-58, -38), (-62, -41), (-65, -45), (-68, -50), (-68, -54),
    (-71, -54), (-73, -50), (-73, -44), (-73, -37), (-71, -30), (-70, -23),
    (-70, -18), (-75, -15), (-77, -12), (-81, -6), (-80, 1), (-77, 4),
]
AFRICA = [
    (-17, 15), (-17, 21), (-15, 27), (-10, 31), (-6, 35), (-1, 36), (6, 37),
    (10, 37), (20, 32), (30, 31), (32, 31), (35, 28), (37, 22), (39, 15),
    (43, 12), (48, 11), (51, 12), (46, 5), (41, -2), (40, -10), (35, -18),
    (32, -26), (28, -33), (20, -35), (17, -29), (14, -22), (12, -18),
    (13, -12), (9, -1), (9, 4), (4, 6), (-8, 5), (-13, 8),
]
EURASIA = [
    (-10, 36), (-9, 43), (-2, 44), (-1, 46), (-4, 48), (0, 51), (3, 53),
    (8, 55), (8, 57), (10, 58), (18, 56), (21, 55), (24, 58), (28, 60),
    (30, 62), (32, 66), (40, 68), (50, 69), (60, 69), (70, 72), (80, 73),
    (90, 75), (100, 77), (110, 74), (120, 73), (130, 72), (140, 72),
    (150, 70), (160, 70), (170, 67), (178, 65), (178, 62), (170, 60),
    (162, 56), (158, 52), (152, 47), (142, 42), (140, 39), (135, 35),
    (130, 33), (127, 35), (122, 38), (120, 32), (122, 28), (118, 25),
    (114, 22), (110, 20), (108, 12), (105, 9), (103, 2), (100, 6), (98, 10),
    (97, 16), (94, 17), (92, 21), (88, 22), (86, 20), (82, 16), (80, 13),
    (77, 8), (76, 10), (73, 16), (72, 20), (68, 23), (66, 25), (61, 25),
    (57, 26), (59, 23), (55, 17), (50, 15), (45, 13), (43, 12), (42, 16),
    (40, 20), (38, 24), (36, 28), (35, 29), (34, 31), (36, 36), (33, 36),
    (30, 36), (27, 37), (23, 36), (19, 40), (16, 42), (12, 44), (8, 44),
    (3, 43), (0, 39), (-2, 37), (-6, 36), (-9, 37),
]
UK = [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (1, 52), (1, 51)]
ICELAND = [(-22, 64), (-18, 63), (-15, 64), (-14, 66), (-18, 66), (-22, 65)]
JAPAN = [
    (130, 31), (132, 33), (135, 34), (137, 35), (140, 36), (141, 39),
    (141, 42), (142, 44), (145, 44), (144, 42), (141, 40), (139, 37),
    (136, 34), (133, 33),
]
SUMATRA = [
    (95, 5), (97, 3), (100, 0), (103, -3), (105, -5), (106, -6), (103, -5),
    (100, -2), (97, 1), (95, 4),
]
BORNEO = [
    (109, 1), (111, 3), (114, 5), (117, 6), (119, 2), (118, -2), (116, -3),
    (112, -3), (110, 0),
]
JAVA = [(105, -6), (108, -7), (111, -7), (114, -8), (114, -7), (110, -6),
        (106, -6)]
NEW_GUINEA = [
    (131, -1), (135, -2), (138, -2), (141, -3), (145, -5), (147, -6),
    (150, -10), (146, -9), (142, -8), (138, -7), (134, -4), (131, -2),
]
AUSTRALIA = [
    (114, -22), (113, -26), (115, -33), (118, -35), (124, -33), (129, -32),
    (132, -32), (135, -35), (138, -35), (140, -38), (145, -38), (150, -37),
    (153, -32), (153, -27), (151, -24), (146, -19), (142, -15), (142, -11),
    (137, -12), (135, -15), (132, -12), (130, -13), (126, -14), (122, -17),
    (118, -20),
]
NEW_ZEALAND = [
    (167, -45), (170, -43), (173, -41), (175, -38), (176, -37), (178, -38),
    (175, -40), (172, -43), (169, -46),
]
MADAGASCAR = [
    (44, -16), (47, -15), (50, -16), (49, -20), (47, -24), (45, -25),
    (44, -20),
]
SRI_LANKA = [(80, 6), (81, 6), (82, 8), (80, 9)]
CUBA = [(-84, 22), (-80, 23), (-75, 20), (-74, 20), (-78, 21), (-82, 22)]

LAND_POLYS = [
    NORTH_AMERICA, GREENLAND, SOUTH_AMERICA, AFRICA, EURASIA, UK, ICELAND,
    JAPAN, SUMATRA, BORNEO, JAVA, NEW_GUINEA, AUSTRALIA, NEW_ZEALAND,
    MADAGASCAR, SRI_LANKA, CUBA,
]

# Pins: (number, label, lon, lat, label side: 'left' or 'right')
PINS = [
    (1, "SHENZHEN", 114.1, 22.5, "right"),
    (2, "THE HAGUE", 4.3, 52.1, "left"),
    (3, "KERCH BRIDGE", 36.5, 45.3, "right"),
    (4, "INDIA", 81.0, 17.0, "left"),
]

# Legend: (number, heading, body). Bodies carry the verified facts.
LEGEND = [
    (1, "SHENZHEN",
     "Trump, Xi & Putin: first-ever trilateral, 90 min at Kylin Villa. "
     "Four-point 'Declaration Towards Peace'."),
    (2, "THE HAGUE",
     "UN court rules Myanmar committed genocide against the Rohingya - "
     "a first."),
    (3, "KERCH BRIDGE",
     "Ukraine strikes the Kerch Bridge a third time in a week."),
    (4, "INDIA",
     "Cyclone Akvan: landfall Friday, winds 90-100 km/h, gusts 110."),
]


# ------------------------------------------------------------------ draw ---
def draw_pin(cx, cy, number, label, side):
    # label pill first (behind the pin)
    scale = 2
    tw = text_width(label, scale)
    th = 7 * scale
    gap = 18
    if side == "right":
        px0 = cx + gap
    else:
        px0 = cx - gap - tw
    py0 = cy - th // 2
    fill_rect(px0 - 5, py0 - 4, px0 + tw + 5, py0 + th + 4, WHITE)
    # 1px navy border around the pill
    fill_rect(px0 - 5, py0 - 4, px0 + tw + 5, py0 - 3, NAVY)
    fill_rect(px0 - 5, py0 + th + 3, px0 + tw + 5, py0 + th + 4, NAVY)
    fill_rect(px0 - 5, py0 - 4, px0 - 4, py0 + th + 4, NAVY)
    fill_rect(px0 + tw + 4, py0 - 4, px0 + tw + 5, py0 + th + 4, NAVY)
    draw_text(px0, py0, scale, label, NAVY, bold=True)
    # pin: white halo, red disc, white number
    draw_circle(cx, cy, 15, WHITE)
    draw_circle(cx, cy, 13, PIN)
    digit = str(number)
    dw = text_width(digit, 2)
    draw_text(cx - dw // 2, cy - 7, 2, digit, WHITE, bold=True)


def main():
    fill_rect(0, 0, W, H, PAPER)

    # ---- masthead ------------------------------------------------------
    fill_rect(0, 0, W, 96, NAVY)
    fill_rect(0, 96, W, 99, GOLD)
    draw_text(28, 14, 6, "19 NOVEMBER 2026", WHITE, bold=True)
    draw_text(28, 62, 3, "THE WORLD IN ONE DAY", GOLD, bold=True)
    day = "THURSDAY"
    draw_text(W - 28 - text_width(day, 3), 20, 3, day, WHITE, bold=True)

    # ---- map frame + ocean ---------------------------------------------
    mx1, my1 = MAP_X0 + MAP_W, MAP_Y0 + MAP_H
    fill_rect(MAP_X0 - 3, MAP_Y0 - 3, mx1 + 3, my1 + 3, NAVY)
    fill_rect(MAP_X0, MAP_Y0, mx1, my1, OCEAN)

    # graticule every 30 degrees
    for lon in range(-150, 181, 30):
        gx, _ = project(lon, 0)
        fill_rect(gx, MAP_Y0, gx + 1, my1, GRID)
    for lat in range(-30, 61, 30):
        _, gy = project(0, lat)
        fill_rect(MAP_X0, gy, mx1, gy + 1, GRID)

    # land
    for poly in LAND_POLYS:
        pts = project_poly(poly)
        fill_polygon(pts, LAND)
    for poly in LAND_POLYS:
        pts = project_poly(poly)
        outline_polygon(pts, LAND_EDGE)

    # pins
    for number, label, lon, lat, side in PINS:
        cx, cy = project(lon, lat)
        draw_pin(cx, cy, number, label, side)

    # ---- legend strip: 2x2 boxes ---------------------------------------
    box_w, box_h, gap = 490, 178, 12
    lx0, ly0 = 16, 652
    for i, (number, heading, body) in enumerate(LEGEND):
        col, row = i % 2, i // 2
        bx = lx0 + col * (box_w + gap)
        by = ly0 + row * (box_h + gap)
        fill_rect(bx, by, bx + box_w, by + box_h, WHITE)
        fill_rect(bx, by, bx + box_w, by + 2, NAVY)
        fill_rect(bx, by + box_h - 2, bx + box_w, by + box_h, NAVY)
        fill_rect(bx, by, bx + 2, by + box_h, NAVY)
        fill_rect(bx + box_w - 2, by, bx + box_w, by + box_h, NAVY)
        # number badge
        fill_rect(bx + 14, by + 12, bx + 44, by + 42, PIN)
        digit = str(number)
        dw = text_width(digit, 3)
        draw_text(bx + 14 + (30 - dw) // 2, by + 17, 3, digit, WHITE,
                  bold=True)
        # heading
        draw_text(bx + 54, by + 17, 3, heading, NAVY, bold=True)
        # body, wrapped and vertically centred in the 5-line space
        # NOTE: wrap_text is word-aware (never splits a word); the -1 keeps
        # the phrase "90 min" on one line in box 1 instead of breaking it
        # across lines. All four boxes still fit their 5-line budget.
        max_chars = (box_w - 28) // (6 * 3) - 1
        lines = wrap_text(body, max_chars)
        body_y = by + 52 + max(0, (5 - len(lines)) * 11)
        for li, line in enumerate(lines):
            draw_text(bx + 14, body_y + li * 22, 3, line, INK)

    write_png("entry.png")


# -------------------------------------------------------------- png writer --
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path):
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)  # filter: none
        raw += fb[y * stride:(y + 1) * stride]
    png = (b"\x89PNG\r\n\x1a\n"
           + _chunk(b"IHDR", ihdr)
           + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


if __name__ == "__main__":
    main()
