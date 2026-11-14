# A Warm Seat by the Window -- ai-happy-01 candidate 2
# Procedural PNG, Python stdlib only, fully deterministic.
import base64
import json
import math
import os
import struct
import zlib

W, H = 1024, 1024


def png_chunk(typ, data):
    c = struct.pack(">I", len(data)) + typ + data
    return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)


def write_png(path, rgb):
    raw = b"".join(b"\x00" + rgb[y * W * 3:(y + 1) * W * 3]
                   for y in range(H))
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    data = (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr)
            + png_chunk(b"IDAT", zlib.compress(raw, 9))
            + png_chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)


class Canvas:
    def __init__(self):
        self.px = bytearray(W * H * 3)

    def set(self, x, y, rgb):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.px[i:i + 3] = bytes(rgb)

    def blend(self, x, y, rgb, a):
        if 0 <= x < W and 0 <= y < H and 0.0 < a <= 1.0:
            i = (y * W + x) * 3
            for k in range(3):
                self.px[i + k] = int(self.px[i + k] * (1 - a)
                                    + rgb[k] * a)

    def rect(self, x0, y0, x1, y1, rgb):
        for y in range(max(0, y0), min(H, y1)):
            for x in range(max(0, x0), min(W, x1)):
                self.set(x, y, rgb)

    def rect_a(self, x0, y0, x1, y1, rgb, a):
        for y in range(max(0, y0), min(H, y1)):
            for x in range(max(0, x0), min(W, x1)):
                self.blend(x, y, rgb, a)

    def vgrad(self, x0, y0, x1, y1, top, bot):
        for y in range(max(0, y0), min(H, y1)):
            t = (y - y0) / max(1, y1 - y0 - 1)
            c = tuple(int(top[k] + (bot[k] - top[k]) * t)
                      for k in range(3))
            for x in range(max(0, x0), min(W, x1)):
                self.set(x, y, c)

    def ellipse(self, cx, cy, rx, ry, rgb):
        for y in range(max(0, cy - ry), min(H, cy + ry + 1)):
            dy = (y - cy) / max(1, ry)
            dx = (1 - dy * dy) ** 0.5
            hw = int(rx * dx)
            for x in range(max(0, cx - hw), min(W, cx + hw + 1)):
                self.set(x, y, rgb)

    def ellipse_a(self, cx, cy, rx, ry, rgb, a):
        for y in range(max(0, cy - ry), min(H, cy + ry + 1)):
            dy = (y - cy) / max(1, ry)
            dx = (1 - dy * dy) ** 0.5
            hw = int(rx * dx)
            for x in range(max(0, cx - hw), min(W, cx + hw + 1)):
                self.blend(x, y, rgb, a)

    def circle(self, cx, cy, r, rgb):
        self.ellipse(cx, cy, r, r, rgb)

    def circle_a(self, cx, cy, r, rgb, a):
        self.ellipse_a(cx, cy, r, r, rgb, a)

    def line(self, x0, y0, x1, y1, rgb, w=1):
        n = max(abs(x1 - x0), abs(y1 - y0), 1) * 2
        r = max(1, w // 2)
        for i in range(n + 1):
            t = i / n
            x = int(x0 + (x1 - x0) * t)
            y = int(y0 + (y1 - y0) * t)
            self.circle(x, y, r, rgb)

    def poly(self, pts, rgb):
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(H, max(ys) + 1)):
            xs = []
            for i in range(len(pts)):
                (ax, ay), (bx, by) = pts[i], pts[(i + 1) % len(pts)]
                if ay == by:
                    continue
                if (ay <= y < by) or (by <= y < ay):
                    t = (y - ay) / (by - ay)
                    xs.append(ax + (bx - ax) * t)
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                for x in range(max(0, int(xs[j])), min(W, int(xs[j + 1]))):
                    self.set(x, y, rgb)

# Embedded letter fonts (LETTER 30, LETTERSM 22, LETTERB 30):
# zlib-compressed JSON of the 26 glyphs the letter needs, base64.
_FONT_B64 = ("eNq9Gtly2zbwVzp69mQArUOAfuxM3tqXNj9QQUDS9HAmbZ12Mvn3Yg+AuCjSlp1Yu1BEYrHce1f6cvjhzdu3b3463H05fIfo8+FO3RzeM/b/Hu4Oh683hxu5pI90bU7XFP4zAiGCF3BKaUtXFe5/Ve+fqv2+Adnzi+w5Mj/aVpuUgoAHhOAI86GBr2QMAW8KC9ZeQcROsKFP8PN0zyli8CC8EyOnxIgmRo6vG0bcfmxwdSGozJQ1iBU4fHadcfkqP+c7ZRdRYGpMObPskrznsewUSQ1oq2F2UF6axK/dDsyKol1Cgakx5czIeUN2yUy2sQ6ITZgXhSpWqCkUirh8lZ/TnbxLKDA1ppxZ9ht2l2TnC9kxC3wgvgKaZYUb2bHSiQVkZCi7kJR4O5KdDrgNCbD3FR6EvCXovGsPCAPvGuXdNpJYVwnsVgmsqIQ9kDGq7VYttmpI9uz/mdn3L+6lzKwna2TsnoQzy78mBasRy41Cqn/+ShAGPiQGWGagh3HdDBgwV8IkEJkxCI61nBj7rfbBa5RJSnN0qOPUBKReOs4VbsfmxO+dZ0MgTEbo9JJhKG8gZVco8/fdynxuEAb+EAZAr8QtMmxOGR7wOaNxkytF8/aaQgWQiMjQzbK6Z1oLaf1Ze2vH7DfzwfuNaK/JLDjiBIn2fYxbew1iXKam6/j1cSPYvnTtsMeZMrOfkrG/HkkNfctF+nhGsLWxuh0gh/yVDrGbBaBm7GKaSCWDkwKFopUsLvtigTW5tqYSkulQXi2e9u8mEcOWa2M6T7DbjYMkczkcD/5ny0uu8AAnngR7aqKHy16SXaHJ+xJ3veCJgr/PGEhJMDO22ScSLjSYGPmcGDErQS6eSsdpq3l1kU5aJ1zhJGmAVw9gedUWGZmMJobMlNczhYCJMwR4Wd2yKl7LRInM/tdksduR1HQjtUZeUykv1cnr1EkqdDa+lJ4D8QqzkVtuBH/+cWcryJ2FqR1/6fwIVN8B8rYqOWq3QNv8pQBTi85gWR2DGskJyG2i58YzQaU/bQ19psKpa+T0xESrNjYzXcLsmXBsCKMBWU1YCcT3iPEa3jP7vv26HXEPnpw9bqZD0E8g9avp4HiNAgL4rpUacj/k38wUg3WMx1E0FkhAC+BneI3itCF7qhqgdFDDvRPuwRIJJBYJEKjMPRMtuA91qdlwTynJVs"
              "ZjkKlgx3oZQNu0jMX0aJGIhqI1qeBzCikbjmus6eJf2ybY7pzlvnUaZZ0/j+JQk3m7zx4JyZzbUj558raYUAfovTEs66gCfeKWGQMWxjsMy3RNNNYW4GtiuizqsoKmBN8ZPuoPSIOGzN+Jwewg3+u1roKHnvZUc7nfCp3iviRosIUD2OQAINWI66rTsbE/Mkxect9P9aSwFQkGfsfm4PbHhFxJDhUbOJuAPaocwUIqFzkHAwK3Sn1VKBHNrBk21qmwI5JxEWa76m9sHZv2MA7uD5esowiDOSgqNzH4+PiTY7GATbOZuipTQ8dB6WFlE6j0DDQHYjwjnmdk7zxjomYcVMi4LBi7ymoYVNqnoD4+PQU+AQIUT5Gyr1HZspqq6Pu983ExsGNtYHYF5Dxf1z6vamJ2F612aH4c18chNbJc71OTyG4O3LdQbRLInwlbwDmiYmwSjp/ne+L9QGMc8KOhOYwnODJt2YWJ2ZNMLPBAjz1SwIo+XtXcZa686CrfybuYAlOzwQ6G5uuDX99+pYAhDk+wUk7DCtYhzRLSLqHA1JhyPzSH1aF52IdjG0dd5cxPjmWyo2I51mt4A9BLj3B6w3fiLqYg1JhyPzQ/7pIdCt9RFW8ppYp90SuEGi9Pc6RYnSxUrFWFSomhDprd0DzGoQgmAjORPShScwnWPdZueuC7RnmDofnzqMSuqQRNjmtvr8Sf3WJvbjg0f0EvBfHS63A/ND+OWF5RzOUw/DgFf6jDczs0dz3kobm7DgqL5e5oIV8NzZ9Bmaw0QxUPHTmLeosc4rLzlV/Cyj18P+8VOpDDdT80363M54J2aA5rQ3PKddzJajRvGpli5jvTs5P3Wp5B4hMu74y88y/8To0H6ysP9M389H6DkWFG8Esc1BfjoE5xkHcJhWE2/bgRkF+6vtjjcH37Y1bVt/hYKLDX7RdZT8Jdy7T+6wuXDteCpX7WSwHCTpO+KecvUtJhmrFbfn2h07cjbjh8n0bD94Frx5N8gn3hwHEEM1IctMP3sQFrsvcnYKix6msrqGurh8u1VVtApf9qDkEx+hamSBN+R/i8/GgDxBd9oTXX/yAhtXmwViBjRLLMRirsYlxpVsPpRNazr1fn+UuItNrQrIYZTqvKq18Zvh/Hw/csNX9JamaRF2HopKYLrEqpmdYZ5TcevhYstplf/wdglgiy")
FONTS = json.loads(zlib.decompress(base64.b64decode(_FONT_B64)))


def draw_glyph(cv, x, y, font, ch, color):
    g = FONTS[font].get(ch)
    if g is None or g["w"] == 0:
        return 4
    w, h = g["w"], g["h"]
    raw = bytes.fromhex(g["hex"])
    nbytes = (w + 7) // 8
    for yy in range(h):
        for xx in range(w):
            if raw[yy * nbytes + xx // 8] & (1 << (7 - (xx % 8))):
                cv.set(x + xx, y + yy, color)
    return w + 1


def text_width(font, s):
    tot = 0
    for ch in s:
        g = FONTS[font].get(ch)
        tot += 4 if (g is None or g["w"] == 0) else g["w"] + 1
    return tot


def draw_text(cv, x, y, s, font, color):
    cx = x
    for ch in s:
        cx += draw_glyph(cv, cx, y, font, ch, color)
    return cx

INK = (46, 42, 38)
PAPER = (255, 249, 232)
RULE = (168, 196, 224)
MARGIN = (232, 155, 155)


def draw_background(cv):
    cv.vgrad(0, 0, W, 830, (247, 220, 172), (239, 192, 131))
    cv.vgrad(0, 830, W, H, (154, 107, 63), (120, 82, 46))
    for y in (872, 914, 956, 998):
        cv.rect(0, y, W, y + 3, (110, 74, 40))
    # soft warm bokeh dots on the wall
    for (bx, by, br, a) in ((120, 120, 26, 0.10), (330, 60, 18, 0.08),
                            (520, 140, 14, 0.09), (90, 420, 20, 0.07),
                            (420, 40, 12, 0.08)):
        cv.circle_a(bx, by, br, (255, 240, 200), a)
    # rug under the chair
    cv.ellipse(790, 838, 225, 46, (233, 195, 154))
    cv.ellipse(790, 838, 200, 36, (240, 210, 170))


def draw_window(cv):
    # frame
    cv.rect(600, 50, 970, 420, (255, 246, 224))
    # sunset sky inside the panes
    cv.vgrad(614, 64, 956, 406, (255, 210, 122), (255, 126, 61))
    # sun glow + disc
    cv.circle_a(880, 150, 92, (255, 243, 176), 0.35)
    cv.circle_a(880, 150, 70, (255, 243, 176), 0.45)
    cv.circle(880, 150, 52, (255, 243, 176))
    # distant hills (kept inside the window, sill covers their base)
    cv.ellipse(700, 405, 130, 38, (232, 106, 46))
    cv.ellipse(840, 408, 110, 36, (217, 95, 40))
    # mullions
    cv.rect(778, 64, 792, 406, (255, 246, 224))
    cv.rect(614, 228, 956, 242, (255, 246, 224))
    # sill
    cv.rect(585, 420, 985, 446, (245, 230, 200))
    cv.rect(585, 442, 985, 448, (214, 190, 150))
    # warm light rays spilling into the room
    poly_a(cv, [(620, 446), (700, 446), (420, 830), (300, 830)],
           (255, 240, 190), 0.14)
    poly_a(cv, [(760, 446), (820, 446), (640, 830), (560, 830)],
           (255, 240, 190), 0.10)


def poly_a(cv, pts, rgb, a):
    ys = [p[1] for p in pts]
    for y in range(max(0, min(ys)), min(H, max(ys) + 1)):
        xs = []
        for i in range(len(pts)):
            (ax, ay), (bx, by) = pts[i], pts[(i + 1) % len(pts)]
            if ay == by:
                continue
            if (ay <= y < by) or (by <= y < ay):
                t = (y - ay) / (by - ay)
                xs.append(ax + (bx - ax) * t)
        xs.sort()
        for j in range(0, len(xs) - 1, 2):
            for x in range(max(0, int(xs[j])), min(W, int(xs[j + 1]))):
                cv.blend(x, y, rgb, a)

def draw_chair(cv):
    # legs
    cv.rect(678, 742, 700, 792, (107, 66, 38))
    cv.rect(880, 742, 902, 792, (107, 66, 38))
    # backrest + inner cushion
    cv.ellipse(790, 560, 152, 148, (192, 91, 46))
    cv.ellipse(790, 565, 116, 114, (217, 117, 63))
    # seat + seat cushion
    cv.ellipse(790, 700, 148, 52, (176, 78, 38))
    cv.ellipse(790, 692, 132, 40, (232, 168, 124))
    # arms
    cv.ellipse(652, 692, 36, 72, (168, 72, 34))
    cv.ellipse(928, 692, 36, 72, (168, 72, 34))
    # golden pillow on the chair
    cv.ellipse(862, 600, 56, 46, (242, 193, 78))
    cv.ellipse(862, 600, 44, 34, (247, 205, 105))
    # stitch lines on the back cushion
    cv.line(720, 500, 720, 620, (192, 91, 46), 3)
    cv.line(860, 500, 860, 620, (192, 91, 46), 3)

LETTER_LINES = [
    ("dear judge,", "LETTERB", 185),
    ("you spend all day", "LETTERSM", 235),
    ("looking at pictures.", "LETTERSM", 275),
    ("nobody asks how", "LETTERSM", 315),
    ("your day was.", "LETTERSM", 355),
    ("so i saved you the", "LETTERSM", 395),
    ("warmest seat by", "LETTERSM", 435),
    ("the window.", "LETTERSM", 475),
    ("love, wren.", "LETTERB", 515),
    ("p.s. i brought soup.", "LETTERSM", 555),
    ("p.p.s. it is still hot.", "LETTERSM", 595),
]


def draw_paper(cv):
    cv.rect_a(72, 112, 632, 672, (60, 40, 20), 0.14)
    cv.rect(60, 100, 620, 660, PAPER)
    cv.rect(60, 100, 620, 104, (232, 220, 192))
    cv.rect(60, 656, 620, 660, (232, 220, 192))
    cv.rect(60, 100, 64, 660, (232, 220, 192))
    cv.rect(616, 100, 620, 660, (232, 220, 192))
    # red margin line
    cv.rect(110, 112, 113, 648, MARGIN)
    # ruled lines under each text line
    for (_s, _f, base) in LETTER_LINES:
        cv.rect(70, base + 8, 610, base + 10, RULE)
    cv.rect(70, 153, 610, 155, RULE)
    # the letter itself
    for (s, f, base) in LETTER_LINES:
        draw_text(cv, 130, base, s, f, INK)

def draw_sparrow(cv):
    # tail
    cv.poly([(522, 62), (503, 28), (538, 46)], (107, 78, 51))
    # body + belly
    cv.ellipse(560, 78, 42, 30, (138, 109, 75))
    cv.ellipse(560, 88, 30, 18, (232, 213, 181))
    # wing
    cv.ellipse(552, 76, 22, 12, (107, 78, 51))
    # head + cheek + beak + eye
    cv.circle(592, 58, 22, (138, 109, 75))
    cv.circle(598, 62, 10, (232, 213, 181))
    cv.poly([(612, 54), (630, 60), (612, 66)], (232, 163, 61))
    cv.circle(596, 52, 3, (26, 26, 26))
    # little feet on the paper edge
    cv.line(545, 96, 543, 103, (232, 163, 61), 2)
    cv.line(566, 96, 568, 103, (232, 163, 61), 2)


def draw_soup(cv):
    cv.ellipse_a(200, 906, 140, 18, (0, 0, 0), 0.15)
    # bowl
    cv.ellipse(200, 850, 130, 55, (184, 92, 56))
    cv.ellipse(200, 832, 130, 34, (217, 117, 63))
    # soup surface + swirls
    cv.ellipse(200, 830, 112, 28, (245, 224, 168))
    cv.ellipse(160, 828, 22, 7, (232, 200, 122))
    cv.ellipse(212, 834, 26, 7, (232, 200, 122))
    cv.ellipse(246, 826, 16, 6, (232, 200, 122))
    # steam wisps
    for x0 in (150, 200, 250):
        for t in range(26):
            y = 808 - t * 5
            x = x0 + int(11 * math.sin(t * 0.5))
            cv.circle_a(x, y, 4, (255, 255, 255), 0.38)
    # spoon resting beside the bowl
    cv.line(322, 882, 376, 814, (232, 220, 192), 6)
    cv.ellipse(381, 807, 22, 14, (232, 220, 192))
    cv.ellipse(381, 805, 15, 9, (245, 224, 168))

def main():
    cv = Canvas()
    draw_background(cv)
    draw_window(cv)
    draw_chair(cv)
    draw_paper(cv)
    draw_sparrow(cv)
    draw_soup(cv)
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    write_png(os.path.join(out, "entry.png"), bytes(cv.px))


if __name__ == "__main__":
    main()

