"""Generate the Girlypop cybersigilism background tiles in a hand-drawn ink style.

Run:  python3 design/sigils/generate.py

Writes into this folder:
  mosaic.svg      960 x 960. All motifs mixed on one tile, plus scattered small fillers.
                  This is the default page background.
  thorn.svg, needle.svg, cathedral.svg, filigree.svg
                  360 x 360 single-motif tiles.
  preview.html    Every tile repeated, in light and dark, plus an "in use" example.

Drawing style
  - Pen pressure: main strokes are filled outlines whose width swells and tapers.
  - Hand wobble: every stroke is bent by smooth, low-frequency noise.
  - Overdraw: major strokes get a second, thinner pass slightly off the first.
  - Construction lines: faint pencil guides (35 % alpha) are left under the ink.
  - Texture: stipple, bead chains, ball-ended scrolls and four-point sparkles.
  Every motif instance is drawn separately, so repeated motifs never look identical.

Seamless tiling: each tile's content is drawn nine times, shifted by one tile in every
direction, so anything that crosses an edge continues on the opposite edge.
Tiles are black on transparent because the theme uses them as CSS masks.
"""
from __future__ import annotations

import math
import random
import re
import urllib.parse
from pathlib import Path
from typing import Callable

OUT = Path(__file__).parent
Pt = tuple[float, float]
Pts = list[Pt]


# ------------------------------------------------------------------ numbers and paths

def fmt(v: float) -> str:
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    if s in ("", "-0"):
        return "0"
    if s.startswith("0."):
        return s[1:]
    if s.startswith("-0."):
        return "-" + s[2:]
    return s


def join(vals) -> str:
    out = ""
    for v in vals:
        t = fmt(v)
        if out and not t.startswith("-"):
            out += " "
        out += t
    return out


def d_of(pts: Pts, closed: bool = False) -> str:
    """Compact path data with relative coordinates."""
    x0, y0 = round(pts[0][0], 1), round(pts[0][1], 1)
    vals: list[float] = []
    px, py = x0, y0
    for x, y in pts[1:]:
        rx, ry = round(x, 1), round(y, 1)
        if rx == px and ry == py:
            continue
        vals += [rx - px, ry - py]
        px, py = rx, ry
    d = "M" + join([x0, y0])
    if vals:
        d += "l" + join(vals)
    return d + ("z" if closed else "")


def signed_area(pts: Pts) -> float:
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1])) / 2


# ------------------------------------------------------------------ geometry

def dist(a: Pt, b: Pt) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def lerp(a: Pt, b: Pt, t: float) -> Pt:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def seg(a: Pt, b: Pt, step: float = 4.0) -> Pts:
    n = max(2, int(dist(a, b) / step))
    return [lerp(a, b, i / n) for i in range(n + 1)]


def cubic(p0: Pt, p1: Pt, p2: Pt, p3: Pt, step: float = 3.5) -> Pts:
    n = max(6, int((dist(p0, p1) + dist(p1, p2) + dist(p2, p3)) / step))
    pts = []
    for i in range(n + 1):
        t = i / n
        m = 1 - t
        a, b, c, d = m * m * m, 3 * m * m * t, 3 * m * t * t, t * t * t
        pts.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                    a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return pts


def quad(p0: Pt, p1: Pt, p2: Pt, step: float = 3.5) -> Pts:
    return cubic(p0, lerp(p0, p1, 2 / 3), lerp(p2, p1, 2 / 3), p2, step)


def arc(c: Pt, r: float, a0: float, a1: float, step: float = 3.5) -> Pts:
    n = max(8, int(abs(math.radians(a1 - a0)) * r / step))
    return [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def spiral(c: Pt, r: float, start: float, turns: float = 1.35, cw: bool = True, shrink: float = 6.0) -> Pts:
    """Logarithmic C-scroll from its outer end inward. Angles in degrees, SVG orientation."""
    total = turns * 2 * math.pi
    b = math.log(shrink) / total
    n = max(14, int(total * r / 5))
    pts = []
    for i in range(n + 1):
        t = total * i / n
        a = math.radians(start) + (t if cw else -t)
        rr = r * math.exp(-b * t)
        pts.append((c[0] + rr * math.cos(a), c[1] + rr * math.sin(a)))
    return pts


def wave(a: Pt, b: Pt, amp: float, waves: float, phase: float = 0.0, step: float = 3.5) -> Pts:
    """Wavy line from a to b that starts calm at its root."""
    L = dist(a, b)
    n = max(8, int(L / step))
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    pts = []
    for i in range(n + 1):
        t = i / n
        o = amp * math.sin(t * waves * 2 * math.pi + phase) * min(1.0, t * 4)
        pts.append((a[0] + (b[0] - a[0]) * t - uy * o, a[1] + (b[1] - a[1]) * t + ux * o))
    return pts


def barb(base: Pt, tip: Pt, bend: float = 0.25) -> Pts:
    """Curved thorn from base to tip; bend > 0 bows it to the left of travel."""
    m = lerp(base, tip, 0.5)
    dx, dy = tip[0] - base[0], tip[1] - base[1]
    return quad(base, (m[0] - dy * bend, m[1] + dx * bend), tip, 2.5)


def normal_at(pts: Pts, i: int) -> Pt:
    a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
    L = dist(a, b) or 1.0
    return (-(b[1] - a[1]) / L, (b[0] - a[0]) / L)


def point_on(pts: Pts, t: float) -> tuple[Pt, Pt]:
    i = min(len(pts) - 1, max(0, round(t * (len(pts) - 1))))
    return pts[i], normal_at(pts, i)


def mirror(s: int, x0: float = 0.0) -> Callable[[Pts], Pts]:
    return lambda pts: [(x0 + (x - x0) * s, y) for x, y in pts]


def quadrant(sx: int, sy: int) -> Callable[[Pts], Pts]:
    return lambda pts: [(x * sx, y * sy) for x, y in pts]


def placement(x: float, y: float, scale: float, rot: float, flip: int) -> Callable[[Pt], Pt]:
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))

    def f(p: Pt) -> Pt:
        px, py = p[0] * scale * flip, p[1] * scale
        return (px * c - py * s + x, px * s + py * c + y)
    return f


# ------------------------------------------------------------------ the pen

class Pen:
    """Collects ink in three layers: pen strokes (filled), hairlines and faint pencil guides.

    Motifs draw in their own local coordinates; `xf` places them in the tile and `ws`
    scales line widths (by the square root of the placement scale, so small motifs stay legible).
    """

    def __init__(self, seed: int) -> None:
        self.r = random.Random(seed)
        self.fills: list[str] = []
        self.hair: dict[float, list[str]] = {}
        self.guides: list[str] = []
        self.xf: Callable[[Pt], Pt] = lambda p: p
        self.ws = 1.0

    def place(self, pts: Pts, gap: float = 1.6) -> Pts:
        q = [self.xf(p) for p in pts]
        if len(q) < 3:
            return q
        out = [q[0]]
        for p in q[1:-1]:
            if dist(out[-1], p) >= gap:
                out.append(p)
        out.append(q[-1])
        return out

    def wobble(self, pts: Pts, amt: float) -> Pts:
        if amt <= 0 or len(pts) < 3:
            return pts
        k1 = 2 * math.pi / self.r.uniform(35, 80)
        k2 = 2 * math.pi / self.r.uniform(12, 24)
        p1, p2 = self.r.uniform(0, 6.3), self.r.uniform(0, 6.3)
        out, L = [], 0.0
        for i, p in enumerate(pts):
            if i:
                L += dist(pts[i - 1], p)
            nx, ny = normal_at(pts, i)
            o = amt * (0.75 * math.sin(L * k1 + p1) + 0.25 * math.sin(L * k2 + p2))
            out.append((p[0] + nx * o, p[1] + ny * o))
        return out

    def ink(self, pts: Pts, w: float = 2.0, start: float = 0.3, end: float = 0.3, wob: float = 0.5,
            ball: float = 0.0, over: bool = False, pw: float = 0.6) -> None:
        """Pen stroke whose width swells and tapers like pen pressure."""
        pts = self.wobble(self.place(pts), wob)
        if len(pts) < 2:
            return
        w *= self.ws
        cum = [0.0]
        for a, b in zip(pts, pts[1:]):
            cum.append(cum[-1] + dist(a, b))
        tot = cum[-1] or 1.0
        k, ph = 2 * math.pi / self.r.uniform(20, 45), self.r.uniform(0, 6.3)
        left, right = [], []
        for i, p in enumerate(pts):
            t = cum[i] / tot
            prof = 1.0
            if start > 0:
                prof = min(prof, t / start)
            if end > 0:
                prof = min(prof, (1 - t) / end)
            hw = w * max(0.08, prof) ** pw * (1 + 0.12 * math.sin(cum[i] * k + ph)) / 2
            nx, ny = normal_at(pts, i)
            left.append((p[0] + nx * hw, p[1] + ny * hw))
            right.append((p[0] - nx * hw, p[1] - ny * hw))
        self._fill(left + right[::-1])
        if ball:
            self._dot(pts[-1], ball * self.ws)
        if over and len(pts) > 6:
            n = len(pts)
            a, b = int(n * self.r.uniform(0.05, 0.25)), int(n * self.r.uniform(0.7, 0.95))
            off = self.r.choice((-1, 1)) * self.r.uniform(0.55, 0.9) * w * 0.5
            sub = []
            for i in range(a, b):
                nx, ny = normal_at(pts, i)
                sub.append((pts[i][0] + nx * off, pts[i][1] + ny * off))
            if len(sub) > 2:
                self._hair(self.wobble(sub, 0.5), max(0.5, w * 0.28))

    def line(self, pts: Pts, w: float = 0.8, wob: float = 0.4) -> None:
        """Hairline of constant width."""
        self._hair(self.wobble(self.place(pts), wob), w * self.ws)

    def pencil(self, pts: Pts) -> None:
        """Faint construction line, left visible under the ink."""
        self.guides.append(d_of(self.wobble(self.place(pts), 0.3)))

    def poly(self, pts: Pts, wob: float = 0.0) -> None:
        self._fill(self.wobble(self.place(pts, 0.5), wob))

    def dot(self, c: Pt, r: float) -> None:
        self._dot(self.xf(c), r * self.ws)

    def _fill(self, pts: Pts) -> None:
        if signed_area(pts) < 0:  # same winding everywhere, so overlaps merge instead of cancelling
            pts = pts[::-1]
        self.fills.append(d_of(pts, closed=True))

    def _dot(self, c: Pt, r: float) -> None:
        r *= self.r.uniform(0.85, 1.15)
        a = f"a{join([r, r])} 0 1 1 "
        self.fills.append(f"M{join([c[0] - r, c[1]])}{a}{join([2 * r, 0])}{a}{join([-2 * r, 0])}z")

    def _hair(self, pts: Pts, w: float) -> None:
        self.hair.setdefault(round(w, 1), []).append(d_of(pts))

    def svg(self) -> str:
        out = []
        if self.guides:
            out.append(f'<path d="{"".join(self.guides)}" fill="none" stroke="#000" stroke-width=".6" '
                       f'stroke-linecap="round" opacity=".35"/>')
        for w, ds in sorted(self.hair.items()):
            out.append(f'<path d="{"".join(ds)}" fill="none" stroke="#000" stroke-width="{fmt(w)}" '
                       f'stroke-linecap="round" stroke-linejoin="round"/>')
        if self.fills:
            out.append(f'<path d="{"".join(self.fills)}"/>')
        return "".join(out)


# ------------------------------------------------------------------ ornaments

def spark(p: Pen, c: Pt, r: float, ratio: float = 0.55) -> None:
    """Four-point star: four pen strokes tapering from the centre, plus small diagonal flicks."""
    x, y = c
    w = max(1.4, r * 0.24)
    for dx, dy, L in ((0, -1, r), (0, 1, r), (1, 0, r * ratio), (-1, 0, r * ratio)):
        p.ink(seg((x - dx * w * 0.2, y - dy * w * 0.2), (x + dx * L, y + dy * L), 2.0), w, 0, 1.0, wob=0.12, pw=1.5)
    for ang in (45, 135, 225, 315):
        a = math.radians(ang)
        p.line(seg((x + math.cos(a) * r * 0.16, y + math.sin(a) * r * 0.16),
                   (x + math.cos(a) * r * 0.4, y + math.sin(a) * r * 0.4), 2.0), 0.6, wob=0)


def scroll(p: Pen, pts: Pts, w: float = 1.4) -> None:
    p.ink(pts, w, 0.05, 0.4, wob=0.2, ball=w * 0.95)


def beads(p: Pen, p0: Pt, p1: Pt, p2: Pt, n: int, r: float = 1.5) -> None:
    pts = quad(p0, p1, p2, 0.8)
    for i in range(n):
        p.dot(pts[round(i * (len(pts) - 1) / (n - 1))], r)


def drop(p: Pen, c: Pt, s: float) -> None:
    x, y = c
    outline = (cubic((x, y), (x + s, y + s * 1.4), (x + s * 0.7, y + s * 2.4), (x, y + s * 2.4), 1.2)
               + cubic((x, y + s * 2.4), (x - s * 0.7, y + s * 2.4), (x - s, y + s * 1.4), (x, y), 1.2)[1:])
    p.poly(outline, 0.1)


def diamond(p: Pen, c: Pt, h: float, ratio: float = 0.45) -> None:
    x, y = c
    p.poly([(x, y - h), (x + h * ratio, y), (x, y + h), (x - h * ratio, y)])


def stipple(p: Pen, inside: Callable[[Pt], bool], box: tuple[float, float, float, float], n: int) -> None:
    x0, y0, x1, y1 = box
    placed = tries = 0
    while placed < n and tries < n * 40:
        tries += 1
        q = (p.r.uniform(x0, x1), p.r.uniform(y0, y1))
        if inside(q):
            p.dot(q, p.r.uniform(0.5, 1.1))
            placed += 1


def vine(p: Pen, pts: Pts, every: float = 16.0, size: float = 6.0, skip: float = 0.1, w: float = 1.2) -> None:
    """Ornament along a stroke: alternating thorns and small scrolls on both sides (like crockets)."""
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + dist(a, b))
    tot = cum[-1]
    s, k, idx = every * 0.5, 0, 0
    while s < tot * (1 - skip):
        if s > tot * skip:
            while idx < len(cum) - 1 and cum[idx] < s:
                idx += 1
            q, n = pts[idx], normal_at(pts, idx)
            tg = (n[1], -n[0])
            side = 1 if k % 2 == 0 else -1
            nn = (n[0] * side, n[1] * side)
            if k % 3 == 2:
                c = (q[0] + nn[0] * size * 0.9, q[1] + nn[1] * size * 0.9)
                start = math.degrees(math.atan2(q[1] - c[1], q[0] - c[0]))
                scroll(p, spiral(c, size * 0.7, start, 1.2, side > 0), w * 0.85)
            else:
                tip = (q[0] + nn[0] * size * 1.6 + tg[0] * size * 0.6, q[1] + nn[1] * size * 1.6 + tg[1] * size * 0.6)
                p.ink(barb(q, tip, 0.25 * side), w, 0, 0.9, wob=0.08)
            k += 1
        s += every


def curl_cluster(p: Pen, c: Pt, r: float, ang: float = -90.0, flip: int = 1, w: float = 1.4) -> None:
    """A stem ending in a fan of three ball-ended scrolls of falling size. `ang` is the stem direction."""
    th = math.radians(ang + 90)
    ca, sa = math.cos(th), math.sin(th)

    def R(pts: Pts) -> Pts:
        return [(c[0] + x * flip * ca - y * sa, c[1] + x * flip * sa + y * ca) for x, y in pts]

    p.ink(R(cubic((0, 0), (2, -r * 0.4), (-2, -r * 0.8), (0, -r * 1.2))), w, 0.1, 0.25, wob=0.12)
    scroll(p, R(spiral((r * 0.45, -r * 1.2), r * 0.45, 180, 1.35, True)), w)
    scroll(p, R(spiral((-r * 0.36, -r * 0.78), r * 0.33, 0, 1.3, False)), w * 0.85)
    scroll(p, R(spiral((r * 0.3, -r * 0.42), r * 0.22, 180, 1.25, False)), w * 0.7)
    p.dot(R([(-r * 0.1, -r * 1.75)])[0], w * 0.7)


# ------------------------------------------------------------------ motifs (local coordinates)

def draw_thorn(p: Pen) -> None:
    """Winged symmetrical sigil: spine, three tiers of sweeping spikes, outer arcs, curls, beads."""
    p.pencil(seg((0, -214), (0, 214), 6))
    p.pencil(arc((0, -10), 150, -150, -30))
    p.pencil(arc((0, -10), 112, 20, 160))
    p.ink(seg((0, -170), (0, 170)), 3.4, 0.45, 0.45, wob=0.35, over=True)
    vine(p, seg((0, -160), (0, -106)), 12, 4.5, 0.05, 1.0)
    vine(p, seg((0, 112), (0, 160)), 12, 4, 0.05, 1.0)
    for y, hh in ((-125, 10), (-62, 6), (8, 7), (78, 8)):
        diamond(p, (0, y), hh)
    spark(p, (0, -192), 20)
    p.line(seg((0, 170), (0, 176), 2), 0.7, 0)
    drop(p, (0, 176), 4)
    spark(p, (0, 208), 8)
    tiers = (((0, -96), (26, -110), (52, -140), (66, -184), 3.0, 0.0),
             ((0, -30), (46, -40), (98, -72), (126, -130), 3.9, 0.55),
             ((0, 42), (42, 32), (86, 12), (110, -26), 3.2, 0.5))
    for s in (1, -1):
        X = mirror(s)
        for p0, c1, c2, tip, w, cl in tiers:
            wing = cubic(p0, c1, c2, tip)
            p.ink(X(wing), w, 0, 0.9, wob=0.3, over=True)
            vine(p, X(wing), 12, 4.2, 0.22, 1.0)
            if cl:
                q, n = point_on(wing, cl)
                if n[1] < 0:
                    n = (-n[0], -n[1])
                ang = math.degrees(math.atan2(n[1], n[0]))
                curl_cluster(p, X([q])[0], 11, ang if s > 0 else 180 - ang, s, 1.2)
        spark(p, X([(68, -192)])[0], 9)
        spark(p, X([(130, -140)])[0], 8)
        p.line(X(cubic((126, -130), (142, -84), (132, -44), (110, -26))), 0.8)
        p.line(X(cubic((66, -184), (82, -200), (100, -194), (104, -178))), 0.8)
        scroll(p, X(spiral((98, -172), 6, 300, 1.25, True)), 1.1)
        down = cubic((0, 96), (22, 110), (40, 142), (44, 198))
        p.ink(X(down), 2.6, 0, 0.9, wob=0.3)
        p.ink(X(barb((30, 126), (48, 118), -0.3)), 1.3, 0, 0.9)
        p.ink(X(barb((40, 160), (58, 166), 0.3)), 1.3, 0, 0.9)
        outer = arc((0, -10), 150, -58, 48)
        p.ink(X(outer), 2.0, 0.4, 0.4, wob=0.4, over=True)
        for t, L in ((0.18, 9), (0.36, 14), (0.54, 10), (0.72, 14), (0.88, 8)):
            q, n = point_on(outer, t)
            if n[0] < 0:
                n = (-n[0], -n[1])
            p.ink(X(barb(q, (q[0] + n[0] * L, q[1] + n[1] * L - L * 0.3), 0.25)), 1.3, 0, 0.9, wob=0.1)
        spark(p, X([outer[0]])[0], 7)
        scroll(p, X(spiral((outer[-1][0] - 8, outer[-1][1] + 2), 8, 0, 1.3, True)), 1.3)
        p.line(X(arc((0, -10), 138, -40, 30)), 0.6)
        scroll(p, X(spiral((14, -62), 7, 180, 1.3, True)), 1.3)
        scroll(p, X(spiral((14, 8), 7, 180, 1.3, False)), 1.3)
        scroll(p, X(spiral((12, 78), 6, 180, 1.3, True)), 1.2)
        beads(p, X([(8, 140)])[0], X([(44, 176)])[0], X([(76, 150)])[0], 9)
        beads(p, X([(30, -56)])[0], X([(60, -30)])[0], X([(92, -66)])[0], 7, 1.3)
        for q in ((150, 70), (160, -20), (112, 90), (40, -168), (90, -112)):
            p.dot(X([q])[0], 1.2)


def draw_needle(p: Pen) -> None:
    """Needles with sparkles and curls, a barbed arc, bead swags and pendants."""
    C, R = (-30, 235), 245
    p.pencil(arc(C, R + 18, -108, -38))
    p.pencil(seg((0, -206), (0, 176), 6))
    A = arc(C, R, -104, -44)
    p.ink(A, 2.3, 0.2, 0.2, wob=0.45, over=True)
    p.line(arc(C, R - 10, -100, -48), 0.7)
    for i, a in enumerate(range(-100, -46, 6)):
        ra = math.radians(a)
        n = (math.cos(ra), math.sin(ra))
        q = (C[0] + R * n[0], C[1] + R * n[1])
        if i % 3 == 2:
            scroll(p, spiral((q[0] + n[0] * 8, q[1] + n[1] * 8), 6, a + 180, 1.15, True), 1.1)
        else:
            L = 15 if i % 2 else 9
            tip = (q[0] + n[0] * L - n[1] * L * 0.35, q[1] + n[1] * L + n[0] * L * 0.35)
            p.ink(barb(q, tip, 0.25), 1.5, 0, 0.9, wob=0.1)
    scroll(p, spiral((A[0][0] + 8, A[0][1] + 4), 8, 200, 1.35, False), 1.5)
    scroll(p, spiral((A[-1][0] - 4, A[-1][1] + 8), 8, 290, 1.35, True), 1.5)
    needles = [(0, -168, 142, -72, 27), (-58, -122, 72, -38, 15), (54, -102, 112, 4, 19),
               (-104, -56, 48, -8, 10), (98, -148, -18, -94, 11), (-30, 60, 128, 92, 7)]
    for x, y1, y2, sy, sr in needles:
        big = sr >= 15
        p.ink(seg((x, y1), (x, y2)), 2.4 if big else 1.6, 0.35, 0.35, wob=0.25, over=big)
        spark(p, (x, sy), sr)
        g = sr * 0.55
        for s in (1, -1):
            X = mirror(s, x)
            scroll(p, X(spiral((x + g * 0.75, sy + sr * 0.85), g * 0.55, 200, 1.3, False)), 1.2)
            scroll(p, X(spiral((x + 7, y2 - 8), 6, 180, 1.2, False)), 1.1)
            if big:
                p.ink(X(barb((x, sy - sr * 1.6), (x + sr * 0.5, sy - sr * 2.2), 0.3)), 1.3, 0, 0.9, wob=0.1)
                ym = (sy + sr * 1.4 + y2) / 2
                curl_cluster(p, (x + s * 2, ym), sr * 0.55, -20 if s > 0 else -160, s, 1.1)
        if big:
            vine(p, seg((x, sy + sr * 1.3), (x, y2 - 14)), 12, 4, 0.05, 1.0)
            vine(p, seg((x, y1 + 10), (x, sy - sr * 1.1)), 11, 3.5, 0.05, 0.9)
        p.line(seg((x, y2), (x, y2 + 4), 2), 0.7, 0)
        drop(p, (x, y2 + 4), 3.0 if big else 2.4)
    beads(p, (0, -14), (-30, 22), (-58, 2), 8)
    spark(p, (-29, 18), 6)
    beads(p, (0, 30), (28, 72), (54, 50), 8)
    drop(p, (27, 57), 3)
    beads(p, (54, -40), (78, -10), (98, -30), 6, 1.3)
    for x, y1, L in ((-104, 48, 34), (98, -18, 26)):
        p.line(seg((x, y1), (x, y1 + L), 2.5), 0.7)
        diamond(p, (x, y1 + L + 5), 5)
    for q in ((-80, -100), (30, -150), (78, 90), (-130, 20), (120, -60)):
        p.dot(q, 1.2)


def draw_cathedral(p: Pen) -> None:
    """Pointed gothic arch with crockets, tracery and a rose window, framing a jellyfish."""
    p.pencil(seg((0, -218), (0, 176), 6))
    p.pencil(arc((0, -20), 112, 180, 360))
    for s in (1, -1):
        X = mirror(s)
        curve = cubic((96, -20), (96, -92), (52, -134), (0, -158))
        p.ink(X(seg((96, 162), (96, -20)) + curve[1:]), 2.7, 0.04, 0.12, wob=0.35, over=True)
        p.line(X(seg((82, 162), (82, -18)) + cubic((82, -18), (82, -80), (44, -118), (0, -138))[1:]), 0.9)
        p.line(X(seg((108, 162), (108, 10))), 0.6)
        vine(p, X(seg((82, 150), (82, -10))), 15, 4.5, 0.05, 1.0)
        curl_cluster(p, X([(96, 162)])[0], 12, -20 if s > 0 else -160, s, 1.2)
        for t in (0.12, 0.32, 0.52, 0.72, 0.9):
            q, n = point_on(curve, t)
            if n[0] + -n[1] < 0:
                n = (-n[0], -n[1])
            c = (q[0] + n[0] * 8, q[1] + n[1] * 8)
            start = math.degrees(math.atan2(q[1] - c[1], q[0] - c[0]))
            scroll(p, X(spiral(c, 6.5, start, 1.25, True)), 1.2)
        for y in (30, 70, 110):
            p.ink(X(barb((96, y), (112, y - 12), 0.3)), 1.4, 0, 0.9, wob=0.1)
        spark(p, X([(96, -20)])[0], 16)
        scroll(p, X(spiral((106, -4), 7, 200, 1.25, False)), 1.2)
        scroll(p, X(spiral((106, 150), 8, 160, 1.3, True)), 1.4)
        spark(p, X([(118, 168)])[0], 7)
        p.line(X(cubic((44, -56), (44, -90), (22, -106), (0, -114))), 0.8)
        p.line(X(cubic((70, -6), (70, -40), (52, -60), (36, -66))), 0.7)
        scroll(p, X(spiral((22, -150), 6, 180, 1.2, False)), 1.1)
    p.line(arc((0, -84), 12, 0, 360), 0.9)
    p.line(arc((0, -84), 5, 0, 360), 0.6)
    for a in range(0, 360, 60):
        ra = math.radians(a)
        p.line(seg((math.cos(ra) * 5, -84 + math.sin(ra) * 5), (math.cos(ra) * 12, -84 + math.sin(ra) * 12), 2), 0.5, 0)
    p.ink(seg((0, -218), (0, -150)), 1.9, 0.4, 0.2, wob=0.15)
    spark(p, (0, -186), 21)
    # jellyfish
    p.ink(cubic((-38, 0), (-40, -50), (40, -50), (38, 0)), 2.5, 0.1, 0.1, wob=0.2, over=True)
    p.line(cubic((-28, -5), (-30, -38), (30, -38), (28, -5)), 0.7)
    rim: Pts = []
    for i in range(8):
        x0 = -38 + i * 9.5
        rim += quad((x0, 0), (x0 + 4.75, 7), (x0 + 9.5, 0), 1.5)[(1 if i else 0):]
    p.ink(rim, 1.3, 0, 0, wob=0.1)
    stipple(p, lambda q: (q[0] / 34) ** 2 + ((q[1] + 2) / 36) ** 2 < 1 and q[1] < -6, (-34, -38, 34, -6), 30)
    for x0, ph in ((-9, 0.0), (0, 1.8), (9, 3.4)):
        p.ink(wave((x0, 5), (x0 * 1.6, 122), 5, 2.6, ph), 2.1, 0, 0.7, wob=0.2)
        p.line(wave((x0 + 3, 12), (x0 * 1.6 + 3, 112), 4, 3.2, ph + 1), 0.6)
    for x0 in (-34, -29, -24, -18, 18, 24, 29, 34):
        p.line(wave((x0, 5), (x0 * 1.3, 152 + abs(x0)), 3.5, 2.2, x0 * 0.3), 0.8, wob=0.3)
    for x0 in (-22, -4, 14):
        p.line(wave((x0, 6), (x0 * 1.1 + 6, 96), 2.5, 4.0, x0 * 0.2), 0.5, wob=0.2)
    for c, r in (((-56, -40), 4), ((58, -62), 3), ((-62, 32), 2.5), ((52, 12), 3.5), ((-48, 96), 2)):
        p.line(arc(c, r, 0, 360, 1.5), 0.7, 0)


def draw_filigree(p: Pen) -> None:
    """Four-way symmetric rosette of ball-ended scrolls, blades, whiskers and dot rings."""
    p.pencil(arc((0, 0), 100, 0, 360))
    p.pencil(arc((0, 0), 58, 0, 360))
    p.ink(seg((0, -152), (0, 152)), 2.9, 0.4, 0.4, wob=0.3, over=True)
    p.ink(seg((-132, 0), (132, 0)), 2.1, 0.4, 0.4, wob=0.3)
    spark(p, (0, 0), 27)
    for sx in (1, -1):
        for sy in (1, -1):
            Q = quadrant(sx, sy)
            scroll(p, Q(spiral((30, 30), 17, 225, 1.45, True)), 1.9)
            scroll(p, Q(spiral((58, 17), 10, 200, 1.35, False)), 1.4)
            scroll(p, Q(spiral((17, 58), 10, 250, 1.35, True)), 1.4)
            scroll(p, Q(spiral((68, 66), 8, 225, 1.25, True)), 1.2)
            blade = cubic((12, 12), (34, 44), (60, 74), (94, 94))
            p.ink(Q(blade), 3.1, 0, 0.9, wob=0.25, over=True)
            vine(p, Q(blade), 13, 4, 0.25, 1.0)
            cx, cy = Q([(104, 44)])[0]
            curl_cluster(p, (cx, cy), 12, math.degrees(math.atan2(cy, cx)), sx * sy, 1.2)
            for a in range(8, 88, 9):
                ra = math.radians(a)
                p.dot(Q([(116 * math.cos(ra), 116 * math.sin(ra))])[0], 0.9)
            for t, side in ((0.45, 1), (0.65, -1)):
                q, n = point_on(blade, t)
                n = (n[0] * side, n[1] * side)
                p.ink(Q(barb(q, (q[0] + n[0] * 12 + 4, q[1] + n[1] * 12 + 4), 0.3 * side)), 1.3, 0, 0.9, wob=0.1)
            for a, b in (((44, 22), (128, 36)), ((22, 44), (36, 128))):
                ctrl1 = (a[0] + 28, a[1] - 14) if a[0] > a[1] else (a[0] - 14, a[1] + 28)
                ctrl2 = (b[0] - 24, b[1] - 22) if a[0] > a[1] else (b[0] - 22, b[1] - 24)
                p.line(Q(cubic(a, ctrl1, ctrl2, b)), 0.8)
                p.dot(Q([b])[0], 1.4)
            p.line(Q(cubic((72, 42), (100, 46), (118, 62), (134, 86))), 0.6)
            for a in range(10, 85, 12):
                ra = math.radians(a)
                p.dot(Q([(78 * math.cos(ra), 78 * math.sin(ra))])[0], 1.3)
            p.ink(Q(barb((0, 92), (12, 108), -0.3)), 1.4, 0, 0.9, wob=0.1)
            p.ink(Q(barb((92, 0), (108, 12), 0.3)), 1.3, 0, 0.9, wob=0.1)
            diamond(p, Q([(0, 140)])[0] if sx > 0 else Q([(124, 0)])[0], 6)


def draw_arc(p: Pen) -> None:
    """Large barbed arc with curls, bead swags and hanging pendants."""
    C, R = (0, 260), 300
    p.pencil(arc(C, R + 22, -134, -46))
    A = arc(C, R, -128, -52)
    p.ink(A, 3.1, 0.25, 0.25, wob=0.5, over=True)
    p.line(arc(C, R - 12, -124, -56), 0.8)
    vine(p, arc(C, R - 12, -122, -58), 18, 4, 0.03, 0.9)

    def at(a: float, rr: float) -> Pt:
        return (C[0] + rr * math.cos(math.radians(a)), C[1] + rr * math.sin(math.radians(a)))

    for i, a in enumerate(range(-122, -55, 5)):
        q = at(a, R)
        n = (math.cos(math.radians(a)), math.sin(math.radians(a)))
        if i % 4 == 1:
            scroll(p, spiral((q[0] + n[0] * 9, q[1] + n[1] * 9), 7, a + 180, 1.2, i % 8 == 1), 1.2)
        elif i % 4 == 3:
            spark(p, (q[0] + n[0] * 14, q[1] + n[1] * 14), 7)
        else:
            L = 16 if i % 2 else 10
            p.ink(barb(q, (q[0] + n[0] * L + n[1] * L * 0.3, q[1] + n[1] * L - n[0] * L * 0.3), 0.25), 1.5, 0, 0.9, wob=0.1)
    for a0, a1 in ((-124, -106), (-106, -90), (-90, -74), (-74, -56)):
        q0, q1 = at(a0, R - 14), at(a1, R - 14)
        mid = lerp(q0, q1, 0.5)
        beads(p, q0, (mid[0], mid[1] + 26), q1, 10, 1.4)
    for a, L in ((-106, 46), (-90, 66), (-74, 46)):
        q = at(a, R - 14)
        p.line(seg(q, (q[0], q[1] + L), 3), 0.7)
        drop(p, (q[0], q[1] + L), 3.2)
        spark(p, (q[0], q[1] + L + 18), 8)
    e0, e1 = A[0], A[-1]
    scroll(p, spiral((e0[0] + 2, e0[1] + 10), 10, 270, 1.4, False), 1.8)
    scroll(p, spiral((e1[0] - 2, e1[1] + 10), 10, 270, 1.4, True), 1.8)
    spark(p, (e0[0] - 14, e0[1] - 10), 11)
    spark(p, (e1[0] + 14, e1[1] - 10), 11)


def draw_glyph(p: Pen) -> None:
    """Small symmetric sigil used to fill gaps. Proportions vary per instance."""
    H = p.r.uniform(50, 66)
    p.ink(seg((0, -H), (0, H)), 2.0, 0.4, 0.4, wob=0.2, over=True)
    spark(p, (0, -H * 0.55), p.r.uniform(9, 13))
    y = p.r.uniform(-0.05, 0.2) * H
    for s in (1, -1):
        X = mirror(s)
        curl_cluster(p, X([(3, y)])[0], p.r.uniform(13, 17), -35 if s > 0 else -145, s, 1.3)
        p.ink(X(barb((0, H * 0.45), (14, H * 0.72), 0.3)), 1.3, 0, 0.9, wob=0.1)
        p.ink(X(barb((0, -H * 0.15), (10, -H * 0.3), -0.3)), 1.1, 0, 0.9, wob=0.1)
    diamond(p, (0, H * 0.88), 5)
    beads(p, (-18, y + 16), (0, y + 32), (18, y + 16), 7, 1.2)


def draw_filler(p: Pen, kind: int, size: float) -> None:
    if kind == 0:
        spark(p, (0, 0), size)
        for a in (45, 135, 225, 315):
            p.dot((math.cos(math.radians(a)) * size * 0.9, math.sin(math.radians(a)) * size * 0.9), 1.1)
    elif kind == 1:
        p.ink(seg((0, -size * 2.2), (0, size * 2.2)), 1.5, 0.4, 0.4, wob=0.15)
        spark(p, (0, -size * 0.6), size * 0.8)
        for s in (1, -1):
            scroll(p, mirror(s)(spiral((5, size * 1.6), 5, 180, 1.2, False)), 1.1)
    elif kind == 2:
        for a in (-90, 30, 150):
            p.dot((math.cos(math.radians(a)) * size * 0.5, math.sin(math.radians(a)) * size * 0.5), 1.5)
        diamond(p, (0, 0), 3.5)
    elif kind == 3:
        curl_cluster(p, (0, size * 0.8), size, -90 + p.r.uniform(-25, 25), p.r.choice((1, -1)), 1.2)
    else:
        beads(p, (-size, 0), (0, size * 1.1), (size, 0), 8, 1.2)
        p.line(seg((0, size * 0.55), (0, size * 1.1), 2), 0.6, 0)
        drop(p, (0, size * 1.1), 2.2)
        spark(p, (0, -size * 0.2), size * 0.55)


FILLER_REACH = {0: 1.2, 1: 2.4, 2: 0.8, 3: 1.9, 4: 1.5}

# name -> (draw function, footprint circles (x, y, r) in local units, used for layout)
MOTIFS: dict[str, tuple[Callable[[Pen], None], list[tuple[float, float, float]]]] = {
    "thorn": (draw_thorn, [(0, -140, 96), (0, -10, 150), (0, 130, 96), (0, 205, 22), (0, -198, 26)]),
    "needle": (draw_needle, [(0, -72, 118), (0, 52, 112)]),
    "cathedral": (draw_cathedral, [(0, -165, 58), (0, -48, 112), (0, 88, 108)]),
    "filigree": (draw_filigree, [(0, 0, 144)]),
    "glyph": (draw_glyph, [(0, 0, 78)]),
    "arc": (draw_arc, [(-150, 20, 55), (-80, -14, 52), (0, -24, 52), (80, -14, 52), (150, 20, 55), (0, 64, 46)]),
}


# ------------------------------------------------------------------ tiles

def tdist(a: Pt, b: Pt, T: float) -> float:
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
    return math.hypot(min(dx, T - dx), min(dy, T - dy))


def build(name: str, T: int, places: list[tuple[str, float, float, float, float, int]],
          fillers: int, seed: int, note: str, glyphs: int = 0) -> str:
    p = Pen(seed)
    feet: list[list[tuple[float, float, float]]] = []
    for motif, x, y, scale, rot, flip in places:
        fn, foot = MOTIFS[motif]
        p.xf, p.ws = placement(x, y, scale, rot, flip), scale ** 0.5
        fn(p)
        feet.append([(*p.xf((cx, cy)), cr * scale) for cx, cy, cr in foot])
    obstacles = [c for f in feet for c in f]
    # warn when two motifs' footprints overlap (toroidally, so across tile edges too)
    for i in range(len(feet)):
        for j in range(i + 1, len(feet)):
            gap = min(tdist(a[:2], b[:2], T) - a[2] - b[2] for a in feet[i] for b in feet[j])
            if gap < 0:
                print(f"  {name}: {places[i][0]}@{places[i][1:3]} overlaps {places[j][0]}@{places[j][1:3]} by {-gap:.0f}")
    r = random.Random(seed * 7 + 1)
    # stage 1: small glyph sigils in the larger gaps
    placed: list[tuple[float, float, float]] = []
    tries = 0
    while len(placed) < glyphs and tries < 4000:
        tries += 1
        sc = r.uniform(0.7, 0.95)
        c = (r.uniform(0, T), r.uniform(0, T))
        if all(tdist(c, (ox, oy), T) > orr + 78 * sc + 8 for ox, oy, orr in obstacles + placed):
            placed.append((c[0], c[1], 78 * sc))
            p.xf, p.ws = placement(c[0], c[1], sc, r.uniform(-10, 10), r.choice((1, -1))), sc ** 0.5
            draw_glyph(p)
    obstacles += placed
    n_glyphs = len(placed)
    # stage 2: small fillers in what is left
    placed = []
    tries = 0
    while len(placed) < fillers and tries < fillers * 600:
        tries += 1
        kind = r.choice((0, 0, 1, 2, 2, 3, 3, 4))
        size = r.uniform(6, 12) if kind == 0 else r.uniform(6, 9)
        reach = size * FILLER_REACH[kind]
        c = (r.uniform(0, T), r.uniform(0, T))
        if all(tdist(c, (ox, oy), T) > orr + reach + 12 for ox, oy, orr in obstacles + placed):
            placed.append((c[0], c[1], reach))
            p.xf, p.ws = placement(c[0], c[1], 1.0, r.uniform(-12, 12), 1), 1.0
            draw_filler(p, kind, size)
    uses = "".join(f'<use href="#m" xlink:href="#m" transform="translate({dx} {dy})"/>'
                   for dx in (-T, 0, T) for dy in (-T, 0, T))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
           f'width="{T}" height="{T}" viewBox="0 0 {T} {T}">'
           f'<!-- Girlypop cybersigilism tile: {note}. Generated by generate.py; edit that, not this file. -->'
           f'<defs><g id="m">{p.svg()}</g></defs>{uses}</svg>\n')
    (OUT / f"{name}.svg").write_text(svg, encoding="utf-8")
    print(f"wrote {name}.svg  {len(svg) / 1024:.0f} KB  ({n_glyphs} glyphs, {len(placed)} fillers)")
    return svg


SINGLE = 360
MOSAIC = 960

MOSAIC_LAYOUT = [
    ("thorn", 150, 240, 1.0, -4, 1),
    ("cathedral", 480, 250, 1.0, 0, 1),
    ("needle", 800, 225, 1.0, 5, 1),
    ("filigree", 290, 705, 1.0, 8, 1),
    ("arc", 640, 650, 0.95, -5, 1),
    ("thorn", 925, 725, 0.62, 9, -1),
    ("filigree", 610, 915, 0.45, 0, 1),
]


def data_uri(svg: str) -> str:
    s = re.sub(r"<!--.*?-->", "", svg, flags=re.S)
    s = re.sub(r"\s+", " ", s).replace('"', "'").strip()
    return "data:image/svg+xml," + urllib.parse.quote(s, safe=" :/='-.,()")


def preview(tiles: dict[str, str]) -> None:
    """Write preview.html. Tiles are inlined as data URIs because browsers block CSS masks
    loaded from file:// URLs."""
    defs = "\n".join(f'  .t-{n} {{ --u: url("{data_uri(svg)}"); }}' for n, svg in tiles.items())
    singles = "".join(
        f'<figure class="{mode}"><div class="pat strong t-{n}" style="--s:240px"></div>'
        f'<figcaption>{n} &middot; {mode}</figcaption></figure>'
        for n in tiles if n != "mosaic" for mode in ("light", "dark"))
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sigil Backgrounds</title>
<style>
{defs}
  body {{ margin: 0; padding: 24px 16px 48px; background: oklch(0.985 0.008 350); color: oklch(0.24 0.04 340);
    font: 15px/21px -apple-system, BlinkMacSystemFont, "Inter", system-ui, sans-serif; }}
  main {{ max-width: 1200px; margin: 0 auto; }}
  h1 {{ font: 700 28px/34px ui-rounded, "Nunito", system-ui, sans-serif; margin: 0 0 4px; letter-spacing: -0.01em; }}
  h2 {{ font: 600 17px/22px system-ui, sans-serif; margin: 32px 0 12px; }}
  p {{ margin: 0 0 16px; color: oklch(0.52 0.03 340); max-width: 720px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; }}
  .pair {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; }}
  figure {{ position: relative; margin: 0; border-radius: 16px; overflow: hidden; border: 1px solid oklch(0.91 0.025 350); }}
  figure.light {{ background: oklch(0.985 0.008 350); --fill: linear-gradient(160deg, oklch(0.57 0.2 352), oklch(0.45 0.12 300)); }}
  figure.dark {{ background: oklch(0.17 0.03 330); --fill: linear-gradient(160deg, oklch(0.8 0.15 352), oklch(0.78 0.1 300)); }}
  .pat {{ height: 300px; background: var(--fill); opacity: var(--o, .12);
    -webkit-mask: var(--u) 0 0 / var(--s) var(--s) repeat; mask: var(--u) 0 0 / var(--s) var(--s) repeat; }}
  .pat.strong {{ --o: .6; }}
  .pat.tall {{ height: 620px; }}
  figcaption {{ padding: 8px 12px; font-weight: 600; background: oklch(1 0 0 / .85); }}
  figure.dark figcaption {{ background: oklch(0.21 0.035 330); color: oklch(0.96 0.015 350); }}
  .demo {{ position: absolute; left: 24px; right: 24px; top: 24px; max-width: 360px; padding: 20px; border-radius: 16px;
    background: oklch(1 0 0); box-shadow: 0 1px 2px oklch(0.6 0.15 352 / .08), 0 8px 24px oklch(0.6 0.15 352 / .12); }}
  figure.dark .demo {{ background: oklch(0.21 0.035 330); color: oklch(0.96 0.015 350); box-shadow: 0 8px 24px oklch(0 0 0 / .35); }}
  .demo b {{ display: block; font-size: 17px; margin-bottom: 4px; }}
  .demo span {{ display: inline-block; margin-top: 10px; padding: 2px 10px; border-radius: 999px; font-size: 13px; font-weight: 600;
    background: oklch(0.94 0.04 20); color: oklch(0.46 0.17 25); }}
  figure.dark .demo span {{ background: oklch(0.32 0.08 22); color: oklch(0.86 0.08 20); }}
</style></head><body><main>
<h1>Sigil backgrounds</h1>
<p>Hand-drawn cybersigilism tiles for the Girlypop theme. Every tile repeats seamlessly. The mosaic mixes all motifs and is the default page background.</p>
<h2>Mosaic: drawing detail (60 % strength, 640 px tile)</h2>
<div class="pair">
  <figure class="light"><div class="pat strong tall t-mosaic" style="--s:640px"></div><figcaption>mosaic &middot; light</figcaption></figure>
  <figure class="dark"><div class="pat strong tall t-mosaic" style="--s:640px"></div><figcaption>mosaic &middot; dark</figcaption></figure>
</div>
<h2>Mosaic in use (product strength, 720 px tile)</h2>
<div class="pair">
  <figure class="light"><div class="pat tall t-mosaic" style="--s:720px;--o:.16"></div><div class="demo"><b>Filing ABC-SAT-2</b>Downlink 10.7–11.7 GHz overlaps 2 protected assets in southern Finland.<br><span>High &middot; 82</span></div><figcaption>light &middot; 16 %</figcaption></figure>
  <figure class="dark"><div class="pat tall t-mosaic" style="--s:720px;--o:.2"></div><div class="demo"><b>Filing ABC-SAT-2</b>Downlink 10.7–11.7 GHz overlaps 2 protected assets in southern Finland.<br><span>High &middot; 82</span></div><figcaption>dark &middot; 20 %</figcaption></figure>
</div>
<h2>Single motifs (60 % strength, 240 px tile)</h2>
<div class="grid">{singles}</div>
</main></body></html>
"""
    (OUT / "preview.html").write_text(html, encoding="utf-8")
    print(f"wrote preview.html  {len(html) / 1024:.0f} KB")


if __name__ == "__main__":
    tiles = {
        "mosaic": build("mosaic", MOSAIC, MOSAIC_LAYOUT, 40, 11, "all motifs mixed, with glyphs and fillers in the gaps", glyphs=10),
        "thorn": build("thorn", SINGLE, [("thorn", 180, 180, 0.8, 0, 1)], 6, 21, "symmetrical thorn sigil"),
        "needle": build("needle", SINGLE, [("needle", 186, 176, 0.86, 0, 1)], 6, 31, "needles, sparkles, barbed arc, bead swags"),
        "cathedral": build("cathedral", SINGLE, [("cathedral", 180, 196, 0.8, 0, 1)], 6, 41, "gothic arch framing a jellyfish"),
        "filigree": build("filigree", SINGLE, [("filigree", 180, 180, 0.95, 0, 1)], 6, 51, "four-way scroll rosette"),
    }
    preview(tiles)
