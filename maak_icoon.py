# -*- coding: utf-8 -*-
"""Tekent het app-icoon: een amberkleurige tent op leisteengrond.

Schrijft PNG's zonder externe bibliotheken, want Pillow staat er niet op.
Randen worden glad gemaakt door elke pixel 3x3 te bemonsteren.
"""
import struct
import zlib

GROND = (13, 18, 24)
TENT = (215, 162, 74)
MONSTERS = 3  # supersampling per as


def schrijf_png(pad, breedte, hoogte, pixels):
    """pixels is een bytes-object met RGBA, rij voor rij."""
    ruw = b"".join(
        b"\x00" + pixels[y * breedte * 4:(y + 1) * breedte * 4]
        for y in range(hoogte)
    )

    def blok(soort, data):
        kop = struct.pack(">I", len(data)) + soort + data
        return kop + struct.pack(">I", zlib.crc32(soort + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += blok(b"IHDR", struct.pack(">IIBBBBB", breedte, hoogte, 8, 6, 0, 0, 0))
    png += blok(b"IDAT", zlib.compress(ruw, 9))
    png += blok(b"IEND", b"")
    with open(pad, "wb") as f:
        f.write(png)


def _in_driehoek(px, py, a, b, c):
    def zijde(p1, p2):
        return (px - p2[0]) * (p1[1] - p2[1]) - (p1[0] - p2[0]) * (py - p2[1])
    d1, d2, d3 = zijde(a, b), zijde(b, c), zijde(c, a)
    neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    return not (neg and pos)


def _tent_dekking(x, y):
    """Geeft 0..1 terug: hoeveel van dit punt tent is (in eenheidscoordinaten)."""
    # Tentdoek.
    top = (0.50, 0.20)
    linksonder = (0.11, 0.79)
    rechtsonder = (0.89, 0.79)
    if not _in_driehoek(x, y, top, linksonder, rechtsonder):
        return 0.0
    # Ingang eruit knippen, zodat het als tent leest en niet als driehoek.
    ingang_top = (0.50, 0.37)
    ingang_links = (0.385, 0.79)
    ingang_rechts = (0.615, 0.79)
    if _in_driehoek(x, y, ingang_top, ingang_links, ingang_rechts):
        return 0.0
    return 1.0


def bouw(maat):
    rij = bytearray()
    for py in range(maat):
        for px in range(maat):
            raak = 0
            for sy in range(MONSTERS):
                for sx in range(MONSTERS):
                    x = (px + (sx + 0.5) / MONSTERS) / maat
                    y = (py + (sy + 0.5) / MONSTERS) / maat
                    raak += _tent_dekking(x, y)
            dekking = raak / (MONSTERS * MONSTERS)
            kleur = tuple(
                round(GROND[i] + (TENT[i] - GROND[i]) * dekking) for i in range(3)
            )
            rij += bytes(kleur) + b"\xff"
    return bytes(rij)


def main():
    for maat, naam in [(180, "icoon-180.png"), (192, "icoon-192.png"), (512, "icoon-512.png")]:
        schrijf_png(naam, maat, maat, bouw(maat))
        print(f"{naam} geschreven ({maat}x{maat})")


if __name__ == "__main__":
    main()
