"""AAMP(v2, agl 파라미터 아카이브: .baglenv/.bglght/.bgsdw …) 덤프. 이름은 CRC32 라 알려진 이름 사전으로 되돌린다.
사용: PY web/tools/render_aamp.py <파일.bagl*> [이름 ...]
  추가 이름을 인자로 주면 사전에 더한다. 모르는 해시는 0x........ 로 출력.
형식(공개 AAMP v2): 헤더 0x30 + 타입 문자열, ResParameterList{crc, u16 리스트상대오프셋/4, u16 수, u16 객체상대오프셋/4, u16 수},
ResParameterObj{crc, u16 파라미터상대오프셋/4, u16 수}, ResParameter{crc, u24 데이터상대오프셋/4, u8 형식}.
"""
import binascii
import struct
import sys

NAMES = """param_root enable DiffuseColor SpecularColor BacksideColor Intensity Direction ViewCoordinate Enable Name name
AmbientLight HemisphereLight DirectionalLight PointLight SpotLight Fog Group group EnvObjSet env_obj_ref_array
SkyColor GroundColor Color color Intensity intensity Pos Position Radius Angle Range Rotate Scale Translate
HemiSphereLight Hemisphere Sky Ground Lat Lon Latitude Longitude data param_list setting config default
UseCubeMap CubeMapIntens IsUseCubeMapIntens MainLight SubLight Light light Dir dir Type type Layer layer
DirectionalLight0 DirectionalLight1 AmbientLight0 HemisphereLight0 Fog0 PointLight0 SpotLight0 enable_mip0 enable_mip1
""".split()
TYPES = {0: "bool", 1: "f32", 2: "int", 3: "vec2", 4: "vec3", 5: "vec4", 6: "color", 7: "str32", 8: "str64",
         9: "curve1", 10: "curve2", 11: "curve3", 12: "curve4", 13: "bufInt", 14: "bufF32", 15: "str256", 16: "quat",
         17: "u32", 18: "bufU32", 19: "bufBin", 20: "strRef"}


def names(extra=()):
    d = {}
    for n in list(NAMES) + list(extra):
        d[binascii.crc32(n.encode()) & 0xFFFFFFFF] = n
        for i in range(8):
            d[binascii.crc32((n + str(i)).encode()) & 0xFFFFFFFF] = n + str(i)
    return d


def dump(path, extra=()):
    d = open(path, "rb").read()
    assert d[:4] == b"AAMP", "AAMP 아님"
    ver, flags, size, pio_ver, pio_off = struct.unpack_from("<5I", d, 4)
    nm = names(extra)
    N = lambda c: nm.get(c, "0x%08x" % c)
    root = 0x30 + pio_off
    out = []

    def val(p, t):
        if t == 0:
            return bool(struct.unpack_from("<I", d, p)[0])
        if t == 1:
            return round(struct.unpack_from("<f", d, p)[0], 6)
        if t in (2, 17):
            return struct.unpack_from("<i" if t == 2 else "<I", d, p)[0]
        if t in (3, 4, 5, 6, 16):
            n = {3: 2, 4: 3, 5: 4, 6: 4, 16: 4}[t]
            return [round(x, 6) for x in struct.unpack_from("<%df" % n, d, p)]
        if t in (7, 8, 15, 20):
            e = d.index(b"\0", p)
            return d[p:e].decode("utf8", "replace")
        return "(%s)" % TYPES.get(t, t)

    def plist(p, depth):
        crc, a, b = struct.unpack_from("<3I", d, p)
        lo, ln, oo, on = (a & 0xFFFF) * 4, a >> 16, (b & 0xFFFF) * 4, b >> 16
        out.append("  " * depth + "[list] " + N(crc))
        for i in range(on):
            q = p + oo + i * 8
            ocrc, w = struct.unpack_from("<2I", d, q)
            po, pn = (w & 0xFFFF) * 4, w >> 16
            out.append("  " * (depth + 1) + "{obj} " + N(ocrc))
            for j in range(pn):
                r = q + po + j * 8
                pcrc, w2 = struct.unpack_from("<2I", d, r)
                doff, t = (w2 & 0xFFFFFF) * 4, w2 >> 24
                out.append("  " * (depth + 2) + "%s : %s = %s" % (N(pcrc), TYPES.get(t, t), val(r + doff, t)))
        for i in range(ln):
            plist(p + lo + i * 12, depth + 1)

    plist(root, 0)
    return out


if __name__ == "__main__":
    print("\n".join(dump(sys.argv[1], sys.argv[2:])))
