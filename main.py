#!/usr/bin/env python3
"""Sum up Wednesday 25 November 2026 world news in one image.

Pure Python 3 standard library only (os, zlib, struct, binascii).
No network, no randomness, no clock: the same input always writes the
same bytes to /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).

The image is a newspaper front page for 25 November 2026, drawn with a
hand-written 5x7 bitmap font and simple geometric pictograms. Every
headline below was reported by Reuters, AP or the BBC on 25 November
2026 (in at least one time zone); see NEWS.md for the sources.
"""
import binascii
import os
import struct
import zlib

W, H = 1024, 1024

# --- palette (newspaper front page) -------------------------------------
PAPER = (247, 243, 232)
INK = (20, 33, 61)
NAVY = (20, 33, 61)
RED = (178, 34, 34)
TEAL = (14, 110, 110)
AMBER = (176, 124, 18)
GREEN = (34, 110, 60)
GREY = (90, 96, 104)
LIGHT = (232, 226, 210)
WHITE = (255, 255, 255)
BLACK = (15, 15, 15)

# --- 5x7 bitmap font: each glyph is 7 rows, each row a 5-bit value -------
# Bit 4 is the leftmost pixel. Only the characters the page uses are here.
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x15, 0x0A),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 0x0C, 0x0C),
    ",": (0, 0, 0, 0, 0x0C, 0x04, 0x08),
    ":": (0, 0x0C, 0x0C, 0, 0x0C, 0x0C, 0),
    ";": (0, 0x0C, 0x0C, 0, 0x0C, 0x04, 0x08),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x06, 0x04, 0, 0x04),
    "-": (0, 0, 0, 0x0E, 0, 0, 0),
    "'": (0x04, 0x04, 0x08, 0, 0, 0, 0),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "%": (0x19, 0x1A, 0x02, 0x04, 0x08, 0x0B, 0x13),
    "/": (0x01, 0x02, 0x02, 0x04, 0x08, 0x08, 0x10),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "+": (0, 0x04, 0x04, 0x1F, 0x04, 0x04, 0),
    "=": (0, 0, 0x1F, 0, 0x1F, 0, 0),
    "*": (0, 0x04, 0x15, 0x0E, 0x15, 0x04, 0),
    "•": (0, 0, 0x0C, 0x0C, 0x0C, 0, 0),
}


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def hline(self, x, y, w, c, t=1):
        self.rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.rect(x0, y0, t, t, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill and d2 <= r * r:
                    self.set(xx, yy, c)
                elif not fill and abs(d2 - r * r) <= r * 2:
                    self.set(xx, yy, c)

    def poly(self, pts, c):
        # scanline fill for a simple polygon
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            for i in range(len(pts)):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % len(pts)]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(int(xs[i]), int(xs[i + 1]) + 1):
                    self.set(x, y, c)

    def text(self, x, y, s, scale, c):
        s = s.upper()
        cx = x
        for ch in s:
            g = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = g[row]
                for col in range(5):
                    if bits & (1 << (4 - col)):
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, c)
            cx += 6 * scale
        return cx

    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale

    def wrap(self, s, scale, max_w):
        words = s.upper().split(" ")
        lines, cur = [], ""
        for wd in words:
            trial = (cur + " " + wd).strip()
            if self.text_w(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        return lines


def write_png(path, cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        out += struct.pack(">I", binascii.crc32(typ + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# --- pictograms (simple, readable at small size) -------------------------
def icon_ship(cv, x, y, s, c):
    # hull, mast, flag, waves
    cv.poly([(x, y + 52 * s), (x + 88 * s, y + 52 * s),
             (x + 76 * s, y + 72 * s),
             (x + 12 * s, y + 72 * s)], c)
    cv.vline(x + 44 * s, y + 8 * s, 46 * s, c, 3)
    cv.poly([(x + 44 * s, y + 10 * s),
             (x + 72 * s, y + 22 * s),
             (x + 44 * s, y + 34 * s)], RED)
    for wy in (78, 86):
        for wx in range(0, 90, 18):
            cv.line(x + wx * s, y + wy * s,
                    x + (wx + 10) * s, y + wy * s, c, 2)


def icon_tower(cv, x, y, s, c):
    cv.rect(x + 30 * s, y + 6 * s, 30 * s, 78 * s, c)
    cv.rect(x + 38 * s, y, 14 * s, 8 * s, c)
    for wy in range(14, 78, 12):
        for wx in (36, 48):
            cv.rect(x + wx * s, y + wy * s, 6 * s,
                    6 * s, PAPER)
    for a in range(8):
        dx = [-26, -18, 0, 18, 26, -18, 18, 0][a]
        dy = [-26, -26, -30, -26, -26, -12, -12, -8][a]
        cv.line(x + 45 * s, y + 10 * s,
                x + (45 + dx) * s, y + (10 + dy) * s, RED, 2)
    cv.circle(x + 45 * s, y + 10 * s, 4, RED)


def icon_chip(cv, x, y, s, c):
    cv.rect(x + 22 * s, y + 22 * s, 46 * s, 46 * s, c)
    cv.rect(x + 34 * s, y + 34 * s, 22 * s, 22 * s,
            PAPER)
    cv.rect(x + 40 * s, y + 40 * s, 10 * s, 10 * s, c)
    for i in range(3):
        px = x + (30 + i * 15) * s
        cv.vline(px, y + 8 * s, 14 * s, c, 3)
        cv.vline(px, y + 68 * s, 14 * s, c, 3)
        py = y + (30 + i * 15) * s
        cv.hline(x + 8 * s, py, 14 * s, c, 3)
        cv.hline(x + 68 * s, py, 14 * s, c, 3)


def icon_medal(cv, x, y, s, c):
    cv.poly([(x + 34 * s, y + 6 * s),
             (x + 56 * s, y + 6 * s),
             (x + 48 * s, y + 34 * s),
             (x + 42 * s, y + 34 * s)], RED)
    cv.circle(x + 45 * s, y + 58 * s, 26 * s, c)
    cv.circle(x + 45 * s, y + 58 * s, 18 * s, PAPER)
    cv.text(x + 38 * s, y + 48 * s, "1", 2, c)


def icon_chart(cv, x, y, s, c):
    cv.hline(x + 8 * s, y + 78 * s, 74 * s, c, 3)
    cv.vline(x + 8 * s, y + 10 * s, 70 * s, c, 3)
    pts = [(12, 22), (28, 34), (44, 28), (60, 52), (76, 66)]
    for i in range(len(pts) - 1):
        cv.line(x + pts[i][0] * s, y + pts[i][1] * s,
                x + pts[i + 1][0] * s, y + pts[i + 1][1] * s,
                RED, 3)
    for px, py in pts:
        cv.circle(x + px * s, y + py * s, 3, RED)


def icon_trophy(cv, x, y, s, c):
    cv.poly([(x + 26 * s, y + 10 * s),
             (x + 64 * s, y + 10 * s),
             (x + 58 * s, y + 44 * s),
             (x + 32 * s, y + 44 * s)], c)
    cv.line(x + 26 * s, y + 14 * s, x + 12 * s,
            y + 30 * s, c, 3)
    cv.line(x + 64 * s, y + 14 * s, x + 78 * s,
            y + 30 * s, c, 3)
    cv.vline(x + 43 * s, y + 44 * s, 22 * s, c, 4)
    cv.hline(x + 30 * s, y + 66 * s, 30 * s, c, 4)
    cv.text(x + 38 * s, y + 20 * s, "1", 2, PAPER)


def icon_blast(cv, x, y, s, c):
    # factory + blast star, for the lead story
    cv.rect(x + 6 * s, y + 44 * s, 78 * s, 40 * s, c)
    cv.rect(x + 12 * s, y + 18 * s, 10 * s, 28 * s, c)
    cv.rect(x + 30 * s, y + 26 * s, 10 * s, 20 * s, c)
    for wy in (54, 66):
        for wx in (14, 30, 46, 62):
            cv.rect(x + wx * s, y + wy * s, 8 * s,
                    8 * s, PAPER)
    for a in range(10):
        ang = a * 36
        import math
        dx = int(30 * math.cos(math.radians(ang)))
        dy = int(30 * math.sin(math.radians(ang)))
        cv.line(x + 118 * s, y + 34 * s,
                x + (118 + dx) * s, y + (34 + dy) * s, RED, 3)
    cv.circle(x + 118 * s, y + 34 * s, 12, RED)


ICONS = {"ship": icon_ship, "tower": icon_tower, "chip": icon_chip,
         "medal": icon_medal, "chart": icon_chart, "trophy": icon_trophy,
         "blast": icon_blast}


def card(cv, x, y, w, h, tag, tag_c, headline, body, icon, icon_c):
    cv.rect(x, y, w, h, WHITE)
    cv.rect(x, y, w, 4, tag_c)
    cv.rect(x, y + 10, 108, 108, LIGHT)
    ICONS[icon](cv, x + 9, y + 16, 1, icon_c)
    tx = x + 126
    tw = w - 126 - 14
    cv.text(tx, y + 14, tag, 2, tag_c)
    lines = cv.wrap(headline, 3, tw)
    ly = y + 38
    for ln in lines[:3]:
        cv.text(tx, ly, ln, 3, INK)
        ly += 24
    blines = cv.wrap(body, 2, tw)
    by = ly + 4
    for ln in blines[:4]:
        cv.text(tx, by, ln, 2, GREY)
        by += 16


def main():
    cv = Canvas(W, H, PAPER)
    # --- header -----------------------------------------------------------
    cv.rect(0, 0, W, 148, NAVY)
    cv.rect(0, 148, W, 6, RED)
    cv.text(24, 18, "THE WORLD IN ONE DAY", 3, (255, 255, 255))
    cv.text(24, 48, "WEDNESDAY", 7, (255, 255, 255))
    cv.text(24, 106, "25 NOVEMBER 2026", 4, (255, 214, 90))
    cv.text(700, 30, "SIX STORIES", 2, (200, 210, 230))
    cv.text(700, 52, "FROM EVERY", 2, (200, 210, 230))
    cv.text(700, 74, "CORNER OF", 2, (200, 210, 230))
    cv.text(700, 96, "THE GLOBE", 2, (200, 210, 230))
    cv.text(700, 122, "REUTERS - AP - BBC", 2, (255, 214, 90))

    # --- lead story: Iowa -------------------------------------------------
    lx, ly, lw, lh = 24, 168, 976, 168
    cv.rect(lx, ly, lw, lh, WHITE)
    cv.rect(lx, ly, lw, 4, RED)
    cv.rect(lx + 12, ly + 14, 150, 140, LIGHT)
    icon_blast(cv, lx + 18, ly + 30, 1, NAVY)
    tx = lx + 180
    cv.text(tx, ly + 16, "LEAD  -  UNITED STATES", 2, RED)
    cv.text(tx, ly + 40, "IOWA SET FOR ARMY BLAST", 4, INK)
    cv.text(tx, ly + 72, "OF 5 TONS OF EXPLOSIVES", 4, INK)
    cv.text(tx, ly + 108, "CONTROLLED BLAST OF DEGRADED LEAD AZIDE DUE", 2, GREY)
    cv.text(tx, ly + 126, "9 A.M. IN MIDDLETOWN. LEAD DUST MAY DRIFT", 2, GREY)
    cv.text(tx, ly + 144, "100 MILES. RESIDENTS TOLD TO STAY INDOORS.", 2, GREY)

    # --- six stories, 2 columns x 3 rows ---------------------------------
    stories = [
        ("UKRAINE", RED,
         "ZELENSKYY: UKRAINE HIT RUSSIAN SHIP",
         "KYIV CONFIRMS SPARTA II STRIKE IN THE GULF OF FINLAND. LIBYA ATTACKS WERE SELF-DEFENCE.",
         "ship", NAVY),
        ("SAUDI ARABIA", TEAL,
         "HOUTHIS HIT RIYADH'S TALLEST TOWER",
         "11 HURT IN SECOND STRIKE ON PIF TOWER IN FIVE DAYS, SAUDI CIVIL DEFENCE SAYS.",
         "tower", TEAL),
        ("UNITED STATES", AMBER,
         "HUAWEI GUILTY OF STEALING TRADE SECRETS",
         "JURY CONVICTS ON 10 OF 12 COUNTS, INCLUDING BANK FRAUD. ACQUITTED OF RACKETEERING.",
         "chip", AMBER),
        ("UNITED STATES", NAVY,
         "TRUMP GIVES GIULIANI MEDAL OF FREEDOM",
         "HIGHEST CIVILIAN HONOUR FOR EX-NEW YORK MAYOR. TURKEYS FREEDOM AND FEATHERS PARDONED.",
         "medal", NAVY),
        ("MARKETS", RED,
         "NVIDIA SLIDES AS TRUMP ROLE QUESTIONED",
         "AI STOCKS DRAG US MARKETS DOWN A DAY AFTER JENSEN HUANG WAS REINSTATED AS CEO.",
         "chart", RED),
        ("SPORT", GREEN,
         "SENEGAL GET AFCON TITLE BACK",
         "CAS OVERTURNS CAF DECISION, RESTORES 1-0 FINAL WIN OVER MOROCCO.",
         "trophy", GREEN),
    ]
    gx, gy = 24, 352
    cw, ch, gap = 482, 196, 12
    for i, (tag, tc, head, body, icon, ic) in enumerate(stories):
        x = gx + (i % 2) * (cw + gap)
        y = gy + (i // 2) * (ch + gap)
        card(cv, x, y, cw, ch, tag, tc, head, body, icon, ic)

    # --- footer strip ------------------------------------------------------
    fy = 964
    cv.rect(0, fy, W, 60, NAVY)
    cv.text(24, fy + 10, "ALSO TODAY: CARTAGENA HOSTAGE SIEGE  •  DR CONGO PLANE MISSING", 2, (255, 214, 90))
    cv.text(24, fy + 32, "POPE FRANCIS DIARY RELEASED  •  SOURCES: REUTERS, AP, BBC", 2, WHITE)

    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = write_png(path, cv)
    print("wrote %s (%d bytes, %dx%d)" % (path, size, W, H))


if __name__ == "__main__":
    main()
