#!/usr/bin/env python3
"""Builds the README's SVG panels. Needs: fonttools, uharfbuzz, and the Google
fonts Cinzel, Cormorant Garamond. Text is outlined because GitHub serves SVGs
through <img>, where webfonts and viewers' local fonts are unavailable."""
import io
import math
import random
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

OUT = Path(__file__).parent
FONTS = Path.home() / ".local/share/fonts/google"

SLATE, DEEP, LINE = "#11171c", "#0c1116", "#2a3640"
TEAL, ROSE, CREAM, MUTED = "#8ab9b5", "#c48b8b", "#ece6da", "#9aa8ad"
W = 1200


class Face:
    def __init__(self, file, wght):
        font = instantiateVariableFont(TTFont(FONTS / file), {"wght": wght})
        buf = io.BytesIO()
        font.save(buf)
        self.font = TTFont(io.BytesIO(buf.getvalue()))
        self.glyphs = self.font.getGlyphSet()
        self.order = self.font.getGlyphOrder()
        self.upem = self.font["head"].unitsPerEm
        self.hb = hb.Font(hb.Face(buf.getvalue()))

    def shape(self, text):
        b = hb.Buffer()
        b.add_str(text)
        b.guess_segment_properties()
        hb.shape(self.hb, b, {"kern": True, "liga": True})
        return list(zip(b.glyph_infos, b.glyph_positions))

    def width(self, text, size, track=0):
        s = size / self.upem
        run = self.shape(text)
        return sum(p.x_advance for _, p in run) * s + track * (len(run) - 1)

    def path(self, text, x, y, size, track=0, anchor="start"):
        if anchor == "middle":
            x -= self.width(text, size, track) / 2
        elif anchor == "end":
            x -= self.width(text, size, track)
        s = size / self.upem
        pen = SVGPathPen(self.glyphs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
        for info, pos in self.shape(text):
            name = self.order[info.codepoint]
            self.glyphs[name].draw(
                TransformPen(pen, (s, 0, 0, -s, x + pos.x_offset * s, y))
            )
            x += pos.x_advance * s + track
        return pen.getCommands()


CINZEL = Face("Cinzel[wght].ttf", 500)
SERIF = Face("CormorantGaramond[wght].ttf", 500)
SERIF_LIGHT = Face("CormorantGaramond[wght].ttf", 400)
ITALIC = Face("CormorantGaramond-Italic[wght].ttf", 500)


def p(face, text, x, y, size, fill, track=0, anchor="start", extra=""):
    d = face.path(text, x, y, size, track, anchor)
    return f'<path fill="{fill}" d="{d}"{extra}/>'


def svg(h, title, body, style=""):
    style = f"<style>{style}</style>" if style else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" '
        f'width="{W}" height="{h}" role="img" aria-label="{title}"><title>{title}</title>'
        f'{style}<clipPath id="r"><rect width="{W}" height="{h}" rx="18"/></clipPath>'
        f'<g clip-path="url(#r)">{body}</g></svg>'
    )


def write(name, content):
    (OUT / name).write_text(content, encoding="utf-8")


def hero():
    H, WATER = 640, 400
    rng = random.Random(1999)
    name = "Maxence Osmond"
    name_path = SERIF_LIGHT.path(name, W / 2, WATER - 14, 146, 1.5, "middle")

    far, drops, rings = [], [], []
    for _ in range(46):
        x, y, l = rng.uniform(0, W), rng.uniform(-80, WATER - 60), rng.uniform(16, 36)
        dur, delay = rng.uniform(1.1, 1.9), rng.uniform(0, 2)
        far.append(
            f'<path class="f" style="animation-duration:{dur:.2f}s;animation-delay:-{delay:.2f}s" '
            f'd="M{x:.0f} {y:.0f}l-{l*.14:.1f} {l:.0f}"/>'
        )
    for _ in range(26):
        # Each drop lands somewhere on the water, and its ring opens on impact.
        x, land = rng.uniform(30, W - 30), rng.uniform(WATER + 16, H - 22)
        persp = (land - WATER) / (H - WATER)
        dur, delay = rng.uniform(2.6, 5.2), rng.uniform(0, 5.2)
        timing = f"animation-duration:{dur:.2f}s;animation-delay:-{delay:.2f}s"
        drift = land * 0.14
        drops.append(
            f'<g style="--x:{-drift:.0f}px;--y:{land + 50:.0f}px;{timing}" class="d">'
            f'<path d="M{x + drift:.0f} -50l-5.6 40"/></g>'
        )
        rx = 18 + persp * 54
        color = ROSE if rng.random() < 0.16 else TEAL
        rings.append(
            f'<ellipse class="r" style="{timing}" cx="{x:.0f}" cy="{land:.0f}" '
            f'rx="{rx:.0f}" ry="{rx * (.16 + persp * .12):.1f}" stroke="{color}"/>'
        )

    eyebrow = p(CINZEL, "AI & BACKEND DEVELOPER", W / 2, 176, 25, TEAL, 7.5, "middle")
    status = p(ITALIC, "Seeking a six-month internship in Data, AI or Game Development",
               W / 2, H - 46, 34, CREAM, 0.2, "middle")
    style = """
.f{stroke:#8ab9b5;stroke-width:1;opacity:.2;animation:fall linear infinite}
.d{animation:drop linear infinite}.d path{stroke:#cfe3df;stroke-width:1.3;stroke-linecap:round}
.r{fill:none;stroke-width:1.2;transform-box:fill-box;transform-origin:center;opacity:0;animation:ring ease-out infinite}
.b{animation:drift 9s ease-in-out infinite alternate}
.b2{animation:drift 13s ease-in-out infinite alternate-reverse}
@keyframes fall{from{transform:translateY(-90px)}to{transform:translateY(90px)}}
@keyframes drop{0%{transform:translate(0,0);opacity:.75}24%{transform:translate(var(--x),var(--y));opacity:.75}24.1%,100%{transform:translate(var(--x),var(--y));opacity:0}}
@keyframes ring{0%,24%{transform:scale(.05);opacity:0}26%{opacity:.8}100%{transform:scale(1);opacity:0}}
@keyframes drift{from{transform:translateX(-46px)}to{transform:translateX(46px)}}
@media (prefers-reduced-motion:reduce){.f,.d,.r,.b,.b2{animation:none}.d{opacity:0}.r{opacity:.3}}
"""
    glints = []
    for i in range(30):
        y = WATER + 10 + (i / 30) ** 1.3 * 122
        w = rng.uniform(70, 300)
        glints.append(
            f'<ellipse class="{"b" if i % 2 else "b2"}" cx="{rng.uniform(40, W - 40):.0f}" cy="{y:.0f}" '
            f'rx="{w / 2:.0f}" ry="{1 + i / 30 * 1.6:.1f}" fill="{DEEP}" opacity="{rng.uniform(.45, .8):.2f}"/>'
        )
    bands = "".join(glints)
    body = f"""<defs>
<linearGradient id="sky" x2="0" y2="1"><stop offset="0" stop-color="#0d1317"/><stop offset=".62" stop-color="{SLATE}"/><stop offset="1" stop-color="#1b2a30"/></linearGradient>
<linearGradient id="sea" x2="0" y2="1"><stop offset="0" stop-color="#17242a"/><stop offset="1" stop-color="{DEEP}"/></linearGradient>
<radialGradient id="glow"><stop offset="0" stop-color="{TEAL}" stop-opacity=".3"/><stop offset=".55" stop-color="{TEAL}" stop-opacity=".07"/><stop offset="1" stop-color="{TEAL}" stop-opacity="0"/></radialGradient>
<linearGradient id="ink" x2="0" y2="1"><stop offset="0" stop-color="#fbf7ee"/><stop offset="1" stop-color="#cfd9d4"/></linearGradient>
<linearGradient id="fade" gradientUnits="userSpaceOnUse" y1="{WATER}" x2="0" y2="{WATER + 128}"><stop offset="0" stop-color="#fff" stop-opacity=".46"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<mask id="m" maskUnits="userSpaceOnUse" x="0" y="{WATER}" width="{W}" height="{H - WATER}"><rect y="{WATER}" width="{W}" height="{H - WATER}" fill="url(#fade)"/></mask>
<filter id="wave" x="-5%" y="-20%" width="110%" height="140%"><feTurbulence type="fractalNoise" baseFrequency=".006 .09" numOctaves="2" seed="7"/><feDisplacementMap in="SourceGraphic" scale="15" xChannelSelector="R" yChannelSelector="G"/></filter>
<clipPath id="above"><rect width="{W}" height="{WATER}"/></clipPath>
</defs>
<rect width="{W}" height="{H}" fill="url(#sky)"/>
<rect y="{WATER}" width="{W}" height="{H - WATER}" fill="url(#sea)"/>
<ellipse cx="{W / 2}" cy="{WATER - 30}" rx="620" ry="250" fill="url(#glow)"/>
<g clip-path="url(#above)">{"".join(far)}</g>
{eyebrow}
<path fill="url(#ink)" d="{name_path}"/>
<rect x="0" y="{WATER}" width="{W}" height="1" fill="{TEAL}" opacity=".42"/>
<g mask="url(#m)"><g filter="url(#wave)"><path fill="{TEAL}" transform="matrix(1 0 0 -1 0 {2 * WATER - 28})" d="{name_path}"/></g></g>
{bands}
{"".join(rings)}
{status}
{"".join(drops)}"""
    write("hero.svg", svg(H, "Maxence Osmond, AI and Backend Developer", body, style))


def band(file, label, right=""):
    body = (
        f'<rect width="{W}" height="96" fill="{DEEP}"/>'
        + p(CINZEL, label, 56, 60, 24, TEAL, 6)
        + (p(ITALIC, right, W - 56, 60, 30, MUTED, 0, "end") if right else "")
    )
    write(file, svg(96, label.title(), body))


PROJECTS = [
    ("agent-smith", "Agent Smith", "An autonomous agent that writes and runs code in a sandbox", "Python · MCP · LLM API"),
    ("rage", "RAGe Against the Machine", "A full RAG pipeline for querying entire codebases", "Python · LLM · Indexing"),
    ("call-me-maybe", "Call Me Maybe", "Natural language into typed calls, by constrained decoding", "Python · PyTorch"),
    ("answer-protocol", "The Answer Protocol", "A real-time, shared-world text adventure over TCP", "Rust · Networking"),
    ("fly-in", "Fly-In", "Routing autonomous drones across dynamic networks", "Python · A* · MAPF"),
    ("thornwood", "Thornwood", "A solo roguelike deck-builder, 3rd at Oddward Jam", "Godot · GDScript"),
]


def row(file, n, title, text, stack, accent=TEAL):
    body = (
        f'<rect width="{W}" height="176" fill="{SLATE}"/>'
        + p(ITALIC, n, 56, 78, 40, accent)
        + p(SERIF, title, 134, 80, 58, CREAM, 0.3)
        + p(SERIF_LIGHT, text, 134, 134, 36, MUTED, 0.2)
        + p(CINZEL, stack.upper(), W - 56, 74, 16, accent, 2.4, "end")
    )
    write(file, svg(176, title, body))


def stack():
    groups = [
        ("LANGUAGES", "Python, Go, Rust, C, SQL, Shell"),
        ("AI / ML", "PyTorch, LLM APIs, RAG, MCP tools"),
        ("TOOLS", "Git, Docker (basics), REST APIs"),
    ]
    out = [f'<rect width="{W}" height="282" fill="{SLATE}"/>']
    for i, (label, value) in enumerate(groups):
        y = 74 + i * 76
        out.append(p(CINZEL, label, 56, y, 18, TEAL, 4))
        out.append(p(SERIF, value, 300, y + 6, 44, CREAM, 0.3))
        if i:
            out.append(f'<rect x="56" y="{y - 49}" width="{W - 112}" height="1" fill="{LINE}"/>')
    write("stack.svg", svg(282, "Stack", "".join(out)))


hero()
band("label-work.svg", "SELECTED WORK")
for i, (slug, title, text, tech) in enumerate(PROJECTS, 1):
    row(f"work-{slug}.svg", f"{i:02}", title, text, tech, ROSE if slug == "thornwood" else TEAL)
band("label-now.svg", "EXPERIENCE", "November 2025 to present")
row("now-vyni.svg", "Go", "Backend Developer at VyNi", "Photo chat, video calls and OAuth for a bike-repair chatbot", "In production", ROSE)
band("label-stack.svg", "STACK")
stack()
