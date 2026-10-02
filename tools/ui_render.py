"""Splatoon 3 레이아웃 정적 렌더 시험 (해석 검증용, 원본 화면 대조 아님).

mpj tools/ui_render.py 의 좌표·원점·알파·재질 규칙을 옮기고 Splatoon 3 에 맞게 바꿨다.
  - 파츠(prt1)는 같은 SARC 가 아니라 romfs/Layout/<이름>.Nin_NX_NVN.blarc.zs 별도 아카이브에서 읽는다.
  - 텍스처 디코드는 web/tools/graphics_bntx.py([graphics] 도구, 수정 없이 import).
  - BFLAN FLEU(확장 사용자 데이터 float) 트랙을 페인 userData 에 적용한다.
  - 재질 bit20 사용자 셰이더 "MeterAction" 은 __CUS_Float_0 을 원 둘레 비율(0~1)로 보는 각도 마스크로 근사한다 [추정].
  - txt1 은 MSBT(LayoutMsg/<레이아웃>.json) 문자열을 복호화 OTF/TTF(PIL ImageFont)로 그린다(가운데 정렬 근사).

사용:
  ui_render.py <레이아웃> <out.png> [레이아웃:애니=프레임]... [페인=문자열]... [--meter-start=top|left] [--meter-dir=cw|ccw]
  예) ui_render.py VS_MainTV_00 out.png SuperGaugeTV_00:Gauge=37.5 T_Time_00=3:00
"""
import copy
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import graphics_bntx  # noqa: E402
import ui_lyt  # noqa: E402
import ui_sarc  # noqa: E402

ROOT = Path(r"C:/dev/splatoon3")
LAYOUT_DIR = ROOT / "extracted/romfs/Layout"
MSG_DIR = ROOT / "analysis/ui/msbt_KRko/LayoutMsg"
FONT_LATIN = ROOT / "analysis/ui/font/BlitzMain.otf"
FONT_ASIA = ROOT / "analysis/ui/font/AsiaKERIN-M.ttf"

_ARCH = {}
_FCPX = {}


def fcpx_base(font_name):
    """FCPX +0x1C f32 = 기준 글자 크기(BlitzMain_S 40, _L 100) [데이터]. 페인 fontSize 는 이 값에 곱하는 배율로 본다 [추정]."""
    if not _FCPX:
        import struct
        for n, b in ui_sarc.read_files(ROOT / "extracted/romfs/Font/Font_KRko.Nin_NX_NVN.bfarc.zs").items():
            if b[:4] == b"FCPX":
                _FCPX[Path(n).stem] = struct.unpack_from("<f", b, 0x1C)[0]
    return _FCPX.get(font_name.rsplit(".", 1)[0], 40.0)


def archive(name):
    if name not in _ARCH:
        files = ui_sarc.read_files(LAYOUT_DIR / f"{name}.Nin_NX_NVN.blarc.zs")
        texs = {}
        for n, b in files.items():
            if b[:4] == b"BNTX":
                for t in graphics_bntx.parse(b):
                    texs[t.name] = t
        anims = {Path(n).stem.replace(name + "_", "", 1): b for n, b in files.items() if b[:4] == b"FLAN"}
        _ARCH[name] = {"files": files, "tex": texs, "img": {}, "anims": anims,
                       "lay": ui_lyt.parse_bflyt(files[f"blyt/{name}.bflyt"])}
    return _ARCH[name]


def tex_image(arc, name):
    if name in arc["img"]:
        return arc["img"][name]
    t = arc["tex"].get(name)
    img = None
    if t is not None:
        try:
            img = graphics_bntx.apply_comp(graphics_bntx.decode_layer(t), t.comp)
        except Exception:  # noqa: BLE001
            img = None
    arc["img"][name] = img
    return img


# ---------------------------------------------------------------- 애니

def hermite(keys, f):
    if not keys:
        return None
    if f <= keys[0][0]:
        return keys[0][1]
    if f >= keys[-1][0]:
        return keys[-1][1]
    for k0, k1 in zip(keys, keys[1:]):
        if k0[0] <= f <= k1[0]:
            t0, v0, s0 = k0[0], k0[1], k0[2] if len(k0) > 2 else 0
            t1, v1, s1 = k1[0], k1[1], k1[2] if len(k1) > 2 else 0
            d = t1 - t0
            if d == 0:
                return v1
            t = (f - t0) / d
            return ((2 * t ** 3 - 3 * t ** 2 + 1) * v0 + (t ** 3 - 2 * t ** 2 + t) * d * s0
                    + (-2 * t ** 3 + 3 * t ** 2) * v1 + (t ** 3 - t ** 2) * d * s1)
    return keys[-1][1]


def step(keys, f):
    v = keys[0][1]
    for k in keys:
        if k[0] <= f:
            v = k[1]
    return v


def apply_anim(lay, anim, frame):
    panes = {}
    stack = [lay["root"]]
    while stack:
        n = stack.pop()
        panes[n["name"]] = n
        stack.extend(n["children"])
    mats = {m["name"]: m for m in lay["materials"]}
    for e in anim.get("entries", []):
        for tag in e["tags"]:
            for tr in tag["tracks"]:
                v = hermite(tr["keys"], frame) if tr["curve"] == "hermite" else step(tr["keys"], frame)
                if v is None:
                    continue
                if e["target"] in ("pane", "user") and e["name"] in panes:
                    p = panes[e["name"]]
                    tg = tag["tag"]
                    k = tr["target"]
                    if tg == "FLPA":
                        if k < 3:
                            p["translate"][k] = v
                        elif k < 6:
                            p["rotate"][k - 3] = v
                        elif k < 8:
                            p["scale"][k - 6] = v
                        elif k < 10:
                            p["size"][k - 8] = v
                    elif tg == "FLVC":
                        if k == 16:
                            p["alpha"] = max(0, min(255, round(v)))
                        elif k < 16 and "vtxColors" in p:
                            cols = [bytearray.fromhex(c[1:]) for c in p["vtxColors"]]
                            cols[k // 4][k % 4] = max(0, min(255, round(v)))
                            p["vtxColors"] = ["#" + c.hex() for c in cols]
                    elif tg == "FLVI":
                        p["visible"] = bool(round(v))
                    elif tg == "FLEU":
                        # 확장 사용자 데이터: 트랙 index 가 userData 의 몇 번째인지는 [미확정]. 관측 데이터는 __CUS_Float_0 하나뿐
                        p.setdefault("userData", {})["__CUS_Float_0"] = [v]
                elif e["target"] == "material" and e["name"] in mats:
                    m = mats[e["name"]]
                    k = tr["target"]
                    if tag["tag"] == "FLMC" and k < 8:
                        key = "black" if k < 4 else "white"
                        c = bytearray.fromhex(m[key][1:])
                        c[k % 4] = max(0, min(255, round(v)))
                        m[key] = "#" + c.hex()
                    elif tag["tag"] == "FLTP":
                        idx = int(round(v))
                        tl = anim.get("textures", [])
                        if m["texMaps"] and 0 <= idx < len(tl):
                            m["texMaps"][tr["index"]]["tex"] = tl[idx]


# ---------------------------------------------------------------- 기하

def mat3_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def pane_local(p):
    tx, ty = p["translate"][0], p["translate"][1]
    rz = math.radians(p["rotate"][2])
    sx, sy = p["scale"]
    c, s = math.cos(rz), math.sin(rz)
    return [[c * sx, -s * sy, tx], [s * sx, c * sy, ty], [0, 0, 1]]


def rect_of(p):
    w, h = p["size"]
    ox, oy = p["origin"]
    x0 = {"center": -w / 2, "left": 0, "right": -w}.get(ox, -w / 2)
    y1 = {"center": h / 2, "top": 0, "bottom": h}.get(oy, h / 2)
    return x0, y1 - h, x0 + w, y1


def parent_anchor(parent, child):
    if parent is None:
        return 0.0, 0.0
    l, b, r, t = rect_of(parent)
    px, py = child["parentOrigin"]
    ax = {"center": (l + r) / 2, "left": l, "right": r}.get(px, (l + r) / 2)
    ay = {"center": (b + t) / 2, "top": t, "bottom": b}.get(py, (b + t) / 2)
    return ax, ay


def hexc(s):
    return tuple(bytes.fromhex(s[1:]))


def meter_mask(img, value, start="top", direction="cw"):
    """MeterAction 근사: 텍스처 중심 기준 각도가 value(원 둘레 비율) 이하인 픽셀만 남긴다 [추정]."""
    a = np.asarray(img).copy()
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    dx = xx + 0.5 - w / 2
    dy = h / 2 - (yy + 0.5)
    ang = np.degrees(np.arctan2(dx, dy)) % 360  # 위=0, 시계방향 +
    if start == "left":
        ang = (ang - 270) % 360
    if direction == "ccw":
        ang = (360 - ang) % 360
    a[..., 3] = np.where(ang / 360.0 <= value, a[..., 3], 0)
    return Image.fromarray(a, "RGBA")


class Renderer:
    def __init__(self, W, H, texts, opts):
        self.W, self.H = W, H
        self.texts = texts
        self.opts = opts
        self.img = Image.new("RGBA", (W, H), (40, 40, 48, 255))
        self.draw = ImageDraw.Draw(self.img)
        self.log = []
        self.fonts = {}
        self.captures = {}

    def to_screen(self, m, x, y):
        return m[0][0] * x + m[0][1] * y + m[0][2] + self.W / 2, self.H / 2 - (m[1][0] * x + m[1][1] * y + m[1][2])

    def font(self, path, size):
        key = (path, size)
        if key not in self.fonts:
            self.fonts[key] = ImageFont.truetype(str(path), size)
        return self.fonts[key]

    def text_image(self, p, lay, text, alpha):
        base = fcpx_base(p["font"]) if isinstance(p["font"], str) else 40.0
        size = max(4, int(round(p["fontSize"][1] * base)))
        mats = {mm["name"]: mm for mm in lay["materials"]}
        mat = mats.get(p["material"]) if isinstance(p["material"], str) else None
        white = hexc(mat["white"]) if mat else (255, 255, 255, 255)
        top = hexc(p["colorTop"])
        col = tuple(white[i] * top[i] // 255 for i in range(3)) + (white[3] * top[3] * alpha // (255 * 255),)
        widths = []
        for ch in text:
            asia = ord(ch) >= 0x1100
            f = self.font(FONT_ASIA if asia else FONT_LATIN, int(size * 1.1) if asia else size)
            widths.append((ch, f, f.getlength(ch)))
        W = int(sum(w for _, _, w in widths)) + 4
        img = Image.new("RGBA", (max(1, W), size + size // 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        x = 2
        for ch, f, w in widths:
            d.text((x, 0), ch, font=f, fill=col)
            x += w
        return img

    def material_image(self, arc, mat, uvs, w, h, vtx, alpha, ud):
        black, white = hexc(mat["black"]), hexc(mat["white"])
        if mat["texMaps"]:
            name = mat["texMaps"][0]["tex"]
            t = tex_image(arc, name)
            cap = (ud or {}).get("CaptureUseName") or (ud or {}).get("DynamicCaptureUseName")
            if cap:
                ci = ((ud or {}).get("CaptureUseIndex") or (ud or {}).get("DynamicCaptureUseIndex") or [0])[0]
                c = self.captures.get(cap)
                if c is None:
                    self.log.append(f"capture missing {cap}")
                elif ci == 0 or t is None:
                    t = c
                else:
                    # 텍스처 슬롯 ci 를 캡처로 바꾼 다단 컴바이너를 '캡처 × 슬롯0 알파' 로 근사 [추정]
                    c = c.resize(t.size, Image.BILINEAR)
                    ca = np.asarray(c).copy()
                    ca[..., 3] = (ca[..., 3].astype(np.uint16) * np.asarray(t)[..., 3] // 255).astype(np.uint8)
                    t = Image.fromarray(ca, "RGBA")
                uvs = None
            if t is None:
                self.log.append(f"tex missing {name}")
                t = Image.new("RGBA", (4, 4), (255, 0, 255, 255))
            if uvs:
                u = uvs[0]
                us, vs = [u[0], u[2], u[4], u[6]], [u[1], u[3], u[5], u[7]]
                tw, th = t.size
                x0, x1, y0, y1 = min(us) * tw, max(us) * tw, min(vs) * th, max(vs) * th
                if 0 <= x0 and x1 <= tw and 0 <= y0 and y1 <= th and (x1 - x0) >= 1 and (y1 - y0) >= 1:
                    t = t.crop((int(x0), int(y0), int(math.ceil(x1)), int(math.ceil(y1))))
                if u[0] > u[2]:
                    t = t.transpose(Image.FLIP_LEFT_RIGHT)
                if u[1] > u[5]:
                    t = t.transpose(Image.FLIP_TOP_BOTTOM)
            cus = mat.get("combinerUserShader", {}).get("name")
            if cus == "MeterAction":
                v = (ud or {}).get("__CUS_Float_0", [0.0])[0]
                t = meter_mask(t, v, self.opts.get("meter-start", "top"), self.opts.get("meter-dir", "cw"))
            elif cus:
                self.log.append(f"user shader {cus} ignored")
            t = t.resize((max(1, int(round(w))), max(1, int(round(h)))), Image.BILINEAR)
            chans = [ch.point(lambda v, lo=black[i], hi=white[i]: lo + (hi - lo) * v // 255) for i, ch in enumerate(t.split())]
            t = Image.merge("RGBA", chans)
        else:
            t = Image.new("RGBA", (max(1, int(round(w))), max(1, int(round(h)))), white)
        avg = tuple(sum(c[i] for c in vtx) // 4 for i in range(4))
        if avg != (255, 255, 255, 255) or alpha != 255:
            k = (avg[0], avg[1], avg[2], avg[3] * alpha // 255)
            t = Image.merge("RGBA", [ch.point(lambda v, kk=kk: v * kk // 255) for ch, kk in zip(t.split(), k)])
        return t

    def blit(self, m, rect, img):
        l, b, r, t = rect
        corners = [self.to_screen(m, x, y) for x, y in ((l, t), (r, t), (r, b), (l, b))]
        w, h = img.size
        (x0, y0), (x1, y1), _, (x3, y3) = corners
        ax, ay = (x1 - x0) / w, (y1 - y0) / w
        bx, by = (x3 - x0) / h, (y3 - y0) / h
        det = ax * by - ay * bx
        if abs(det) < 1e-9:
            return
        coef = (by / det, -bx / det, (bx * y0 - by * x0) / det, -ay / det, ax / det, (ay * x0 - ax * y0) / det)
        self.img.alpha_composite(img.transform((self.W, self.H), Image.AFFINE, coef, Image.BILINEAR))

    def pane(self, p, lay, arc, parent_m, parent, alpha, msg, prefix):
        if not p["visible"]:
            return
        ud = p.get("userData") or {}
        if ("CaptureOn" in ud or "DynamicCaptureOn" in ud) and not getattr(self, "_capturing", False):
            # 캡처 원본: 페인 크기 캔버스에 자식들을 그려 텍스처로 보관하고 화면에는 그리지 않는다 [추정: ui2d 캡처 규칙]
            w, h = (max(1, int(round(v))) for v in p["size"])
            sub = Renderer(w, h, self.texts, self.opts)
            sub.img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            sub.captures = self.captures
            sub._capturing = True
            for c in p["children"]:
                sub.pane(c, lay, arc, [[1, 0, 0], [0, 1, 0], [0, 0, 1]], p, p["alpha"], msg, prefix)
            self.captures[p["name"]] = sub.img
            self.log.extend(sub.log)
            return
        ax, ay = parent_anchor(parent, p)
        m = mat3_mul(mat3_mul(parent_m, [[1, 0, ax], [0, 1, ay], [0, 0, 1]]), pane_local(p))
        my_alpha = alpha * p["alpha"] // 255
        rect = rect_of(p)
        typ = p["type"]
        if typ == "pic1" and isinstance(p.get("materialIndex"), int):
            mat = lay["materials"][p["materialIndex"]]
            img = self.material_image(arc, mat, p["uvs"], abs(rect[2] - rect[0]), abs(rect[3] - rect[1]),
                                      [hexc(c) for c in p["vtxColors"]], my_alpha, p.get("userData"))
            self.blit(m, rect, img)
        elif typ == "wnd1":
            mats = {x["name"]: x for x in lay["materials"]}
            mat = mats.get(p["content"]["material"])
            if mat:
                img = self.material_image(arc, mat, p["content"]["uvs"], abs(rect[2] - rect[0]), abs(rect[3] - rect[1]),
                                          [hexc(c) for c in p["content"]["vtxColors"]], my_alpha, None)
                self.blit(m, rect, img)
        elif typ == "txt1":
            key = prefix + p["name"]
            text = self.texts.get(p["name"], self.texts.get(key, msg.get(key, msg.get(p["name"], p.get("text", "")))))
            if text:
                img = self.text_image(p, lay, text, my_alpha)
                l, b, r, t = rect
                cx, cy = (l + r) / 2, (b + t) / 2
                w, h = img.size
                self.blit(m, (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), img)
        elif typ == "prt1":
            sub = archive(p["layoutFile"])
            sl = sub["lay_inst"] if "lay_inst" in sub else sub["lay"]
            mm = mat3_mul(m, [[p["magnify"][0], 0, 0], [0, p["magnify"][1], 0], [0, 0, 1]])
            self.pane(sl["root"], sl, sub, mm, None, my_alpha, msg, prefix + p["name"] + "-")
        child_alpha = my_alpha if p["influencedAlpha"] else alpha
        for c in p["children"]:
            self.pane(c, lay, arc, m, p, child_alpha, msg, prefix)


def render(name, out_png, anims, texts, opts):
    arc = archive(name)
    lay = copy.deepcopy(arc["lay"])
    for (ln, an), fr in anims:
        a = archive(ln)
        if ln == name:
            apply_anim(lay, ui_lyt.parse_bflan(a["anims"][an]), fr)
        else:
            inst = a.setdefault("lay_inst", copy.deepcopy(a["lay"]))
            apply_anim(inst, ui_lyt.parse_bflan(a["anims"][an]), fr)
    mp = MSG_DIR / f"{name}.json"
    msg = json.loads(mp.read_text(encoding="utf-8")) if mp.exists() else {}
    W, H = (int(v) for v in lay["layout"]["size"])
    r = Renderer(W, H, texts, opts)
    r.pane(lay["root"], lay, arc, [[1, 0, 0], [0, 1, 0], [0, 0, 1]], None, 255, msg, "")
    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    r.img.save(out_png)
    return r.log


if __name__ == "__main__":
    name, out = sys.argv[1], sys.argv[2]
    anims, texts, opts = [], {}, {}
    for x in sys.argv[3:]:
        if x.startswith("--"):
            k, v = x[2:].split("=", 1)
            opts[k] = v
        elif ":" in x.split("=", 1)[0]:
            lhs, fr = x.rsplit("=", 1)
            ln, an = lhs.split(":", 1)
            anims.append(((ln, an), float(fr)))
        elif "=" in x:
            k, v = x.split("=", 1)
            texts[k] = v
    log = render(name, out, anims, texts, opts)
    print("\n".join(sorted(set(log))) or "ok")
