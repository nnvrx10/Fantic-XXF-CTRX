#!/usr/bin/env python3
"""Turn the setup sheets in setups/ into MX Bikes .stp files.

A .stp stores every setting as a position in that bike's option list, tagged
with the bike's internal ID. Neither is in the sheets, so a conversion needs:

  * a template .stp saved from the garage for that bike (ID, version, gears)
  * a garage file giving the range the garage offers for each setting

The .stp layout used here is reverse-engineered and has not been checked
against the game (see README). Two checks guard against it being wrong: the
file length must fit the layout exactly, and each setting's stored position
must agree with the value the garage showed for the template.
"""

import argparse
import configparser
import glob
import re
import struct
import sys
from fractions import Fraction
from pathlib import Path

MAGIC = 0x459353C8
VERSIONS = (0x115, 0x116)  # 0x116 adds a 2-byte bike subversion to the header

# The settings, in file order, as 32-bit positions. The gearbox sits between
# the two groups, one slot per gear.
PRE = [
    "FrontTyre", "RearTyre", "FrontPressure", "RearPressure", "Fuel",
    "ForkSpring", "ForkPreload", "ForkOil", "ForkHeight", "ForkCompression",
    "ForkRebound", "ShockSpring", "ShockPreload", "RodLength",
    "ShockLowSpeedCompression", "ShockHighSpeedCompression", "ShockRebound",
    "SwingarmLength", "ForkOffset", "RearSprocket",
]
POST = [
    "FrontSprocket", "Unknown1", "FrontTyreSet", "RearTyreSet",
    "FrontBrakeLeverage", "FrontMasterCylinder", "FrontDisc", "EngineMap",
    "RearMasterCylinder", "RearDisc", "Unknown2",
] + [f"Geometry{i}" for i in range(13)]

# Sheet (section, key) -> (slot name, stored position counts down as the value goes up).
# The second item is only the fallback when the template cannot settle it.
FIELDS = {
    ("Drivetrain", "FrontSprocket"): ("FrontSprocket", False),
    ("Drivetrain", "RearSprocket"): ("RearSprocket", False),
    ("FrontSuspension", "SpringRate"): ("ForkSpring", False),
    ("FrontSuspension", "Preload"): ("ForkPreload", False),
    ("FrontSuspension", "OilLevel"): ("ForkOil", False),
    ("FrontSuspension", "Compression"): ("ForkCompression", True),
    ("FrontSuspension", "Rebound"): ("ForkRebound", True),
    ("FrontSuspension", "ForkHeight"): ("ForkHeight", True),
    ("FrontSuspension", "ForkOffset"): ("ForkOffset", False),
    ("RearSuspension", "SpringRate"): ("ShockSpring", False),
    ("RearSuspension", "Preload"): ("ShockPreload", False),
    ("RearSuspension", "LowSpeedCompression"): ("ShockLowSpeedCompression", True),
    ("RearSuspension", "HighSpeedCompression"): ("ShockHighSpeedCompression", True),
    ("RearSuspension", "Rebound"): ("ShockRebound", True),
    ("RearSuspension", "RodLength"): ("RodLength", False),
    ("Tyres", "FrontPressure"): ("FrontPressure", False),
    ("Tyres", "RearPressure"): ("RearPressure", False),
}

# [GarageLimits] keys -> the sheet field they push to the garage limit.
LIMITS = {
    "ForkSpringRate": ("FrontSuspension", "SpringRate"),
    "ForkOilLevel": ("FrontSuspension", "OilLevel"),
    "ForkHeight": ("FrontSuspension", "ForkHeight"),
    "ForkOffset": ("FrontSuspension", "ForkOffset"),
    "ShockSpringRate": ("RearSuspension", "SpringRate"),
    "RodLength": ("RearSuspension", "RodLength"),
}


class Fail(Exception):
    """A problem to report to the user without a traceback."""


class Stp:
    def __init__(self, version, bike, subversion, pre, gears, post, notes):
        self.version, self.bike, self.subversion = version, bike, subversion
        self.pre, self.gears, self.post, self.notes = pre, gears, post, notes

    @classmethod
    def load(cls, path, gears=None):
        try:
            data = Path(path).read_bytes()
        except OSError as e:
            raise Fail(f"{path}: {e.strerror}")
        try:
            return cls.parse(data, gears)
        except Fail as e:
            raise Fail(f"{path}: {e}")

    @classmethod
    def parse(cls, data, gears=None):
        if len(data) < 40 or struct.unpack_from("<I", data)[0] != MAGIC:
            raise Fail("not an MX Bikes .stp file")
        (version,) = struct.unpack_from("<H", data, 4)
        if version not in VERSIONS:
            raise Fail(f"unsupported .stp version {version:#x}")
        bike, start, subversion = data[6:38], 38, None
        if version == 0x116:
            (subversion,) = struct.unpack_from("<H", data, 38)
            start = 40

        # The gear count is not stored. Find the one that makes the notes
        # block end exactly at the end of the file.
        fits = []
        for g in range(11) if gears is None else [gears]:
            end = start + 4 * (len(PRE) + g + len(POST))
            if end + 4 <= len(data) and end + 4 + struct.unpack_from("<I", data, end)[0] == len(data):
                fits.append(g)
        if not fits:
            raise Fail("file length does not fit the known .stp layout" + ("" if gears is None else f" with {gears} gears"))
        if len(fits) > 1:
            raise Fail(f"gear count is ambiguous ({', '.join(map(str, fits))}); pass --gears")
        g = fits[0]
        count = len(PRE) + g + len(POST)
        values = list(struct.unpack_from(f"<{count}I", data, start))
        return cls(version, bike, subversion, values[:len(PRE)], values[len(PRE):len(PRE) + g],
                   values[len(PRE) + g:], data[start + 4 * count + 4:])

    def encode(self):
        out = struct.pack("<IH", MAGIC, self.version) + self.bike
        if self.subversion is not None:
            out += struct.pack("<H", self.subversion)
        values = self.pre + self.gears + self.post
        return out + struct.pack(f"<{len(values)}I", *values) + struct.pack("<I", len(self.notes)) + self.notes

    def copy(self):
        return Stp(self.version, self.bike, self.subversion, list(self.pre), list(self.gears), list(self.post), self.notes)

    @property
    def bike_id(self):
        return self.bike.split(b"\0")[0].decode("latin-1")

    def slots(self):
        """Every stored position as (name, value), in file order."""
        gears = [(f"Gear{i + 1}", v) for i, v in enumerate(self.gears)]
        return list(zip(PRE, self.pre)) + gears + list(zip(POST, self.post))

    def get(self, name):
        return self.pre[PRE.index(name)] if name in PRE else self.post[POST.index(name)]

    def set(self, name, value):
        if name in PRE:
            self.pre[PRE.index(name)] = value
        else:
            self.post[POST.index(name)] = value

    def set_notes(self, text):
        # The game writes notes with a trailing NUL. Follow the template if it differs.
        nul = b"" if self.notes and not self.notes.endswith(b"\0") else b"\0"
        self.notes = text.encode("latin-1", "replace") + nul


def number(text):
    """A garage value: 5.0, 13, 3/4 or 1-1/4 (the garage's turns format)."""
    text = text.strip()
    mixed = re.fullmatch(r"(\d+)-(\d+)/(\d+)", text)
    try:
        if mixed:
            return int(mixed[1]) + Fraction(int(mixed[2]), int(mixed[3]))
        return Fraction(text)
    except (ValueError, ZeroDivisionError):
        raise Fail(f"'{text}' is not a number")


def show(value):
    return f"{float(value):g}"


class Range:
    """One setting's options as the garage shows them, plus the template's reading."""

    def __init__(self, name, text):
        self.name = name
        parts = text.split(",")
        if len(parts) != 4:
            raise Fail(f"{name}: expected 'lowest, highest, step, template value'")
        try:
            self.lo, self.hi, self.step, self.template = map(number, parts)
        except Fail as e:
            raise Fail(f"{name}: {e}")
        if self.step <= 0 or self.hi < self.lo:
            raise Fail(f"{name}: step must be positive and highest must not be below lowest")
        if ((self.hi - self.lo) / self.step).denominator != 1:
            raise Fail(f"{name}: lowest to highest is not a whole number of steps")
        self.count = int((self.hi - self.lo) / self.step) + 1
        if not self.lo <= self.template <= self.hi or self.place(self.template).denominator != 1:
            raise Fail(f"{name}: template value {show(self.template)} is not one of the options")

    def place(self, value):
        return (value - self.lo) / self.step

    def reversed(self, stored, fallback):
        """Whether stored positions count down as the value goes up, read from the template."""
        up = int(self.place(self.template))
        down = self.count - 1 - up
        if stored not in (up, down):
            raise Fail(
                f"{self.name}: the garage file says the template shows {show(self.template)} "
                f"(position {up} or {down} of {self.count}), but the template stores {stored}. "
                "Check the range, or the .stp layout does not match this bike."
            )
        return fallback if up == down else stored == down


def read_ini(path):
    ini = configparser.ConfigParser(interpolation=None, comment_prefixes=(";", "#"))
    ini.optionxform = str
    try:
        with open(path, encoding="utf-8") as f:
            ini.read_file(f)
    except OSError as e:
        raise Fail(f"{path}: {e.strerror}")
    except (configparser.Error, UnicodeDecodeError) as e:
        raise Fail(f"{path}: {e}")
    return ini


def convert(sheet, garage, template):
    """Apply one sheet to a copy of the template. Returns (stp, report lines)."""
    out = template.copy()
    limits = {}
    for key, value in (sheet["GarageLimits"].items() if sheet.has_section("GarageLimits") else []):
        if key not in LIMITS or value.strip().upper() not in ("MIN", "MAX"):
            raise Fail(f"[GarageLimits] {key}={value}: expected one of {', '.join(LIMITS)} set to MIN or MAX")
        limits[LIMITS[key]] = value.strip().upper()

    lines, kept = [], []
    for (section, key), (slot, fallback) in FIELDS.items():
        name = f"{section}.{key}"
        if not sheet.has_option(section, key) and (section, key) not in limits:
            continue
        text = garage.get(section, key, fallback="?")
        if "?" in text:
            kept.append(name)
            continue
        rng = Range(name, text)
        stored = template.get(slot)
        down = rng.reversed(stored, fallback)

        limit = limits.get((section, key))
        if limit:
            value, remark = (rng.hi if limit == "MAX" else rng.lo), f"garage limit {limit}"
        else:
            try:
                asked = number(sheet.get(section, key))
            except Fail as e:
                raise Fail(f"{name}: {e}")
            value = min(max(asked, rng.lo), rng.hi)
            value = rng.lo + rng.step * int(rng.place(value) + Fraction(1, 2))
            remark = "" if value == asked else f"sheet has {show(asked)}, nearest option used"
        place = int(rng.place(value))
        new = rng.count - 1 - place if down else place
        out.set(slot, new)
        lines.append(f"  {name:<37} {show(value):>7}   position {stored:>3} -> {new:<3} {remark}".rstrip())

    if kept:
        lines.append("  kept from template (no range in the garage file): " + ", ".join(kept))
    return out, lines


def cmd_dump(args):
    stp = Stp.load(args.file, args.gears)
    sub = "none" if stp.subversion is None else stp.subversion
    print(f"bike id: {stp.bike_id}   version: {stp.version:#x}   subversion: {sub}   gears: {len(stp.gears)}")
    for name, value in stp.slots():
        print(f"  {name:<26} {value}")
    notes = stp.notes.rstrip(b"\0").decode("latin-1")
    print(f"  notes: {notes!r}")


def cmd_diff(args):
    a, b = Stp.load(args.a, args.gears), Stp.load(args.b, args.gears)
    if (a.bike, a.version, a.subversion, len(a.gears)) != (b.bike, b.version, b.subversion, len(b.gears)):
        raise Fail(f"the files are for different bikes or versions ({a.bike_id} and {b.bike_id})")
    changed = [(n, x, y) for (n, x), (_, y) in zip(a.slots(), b.slots()) if x != y]
    for name, x, y in changed:
        print(f"  {name:<26} {x} -> {y}")
    if not changed:
        print("  no setting differs")


def cmd_init(args):
    stp = Stp.load(args.template, args.gears)
    out = Path(args.output)
    if out.exists() and not args.force:
        raise Fail(f"{out} exists; pass --force to overwrite")
    lines = [
        f"; Garage ranges for bike id '{stp.bike_id}', read off the garage with {Path(args.template).name} loaded.",
        "; Each line:  lowest value, highest value, step, value shown for that setup",
        "; Use the sheets' units (see the README key). Turns may be written as 1-1/4.",
        "; A line left as ? keeps the template's setting.",
    ]
    section = None
    for (sec, key), (slot, _) in FIELDS.items():
        if sec != section:
            lines += ["", f"[{sec}]"]
            section = sec
        lines.append(f"{key} = ?, ?, ?, ?")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}")


def cmd_build(args):
    template = Stp.load(args.template, args.gears)
    garage = read_ini(args.garage)
    out_dir = Path(args.out_dir)
    jobs = []
    # Expand wildcards here: the Windows shells pass them through untouched.
    sheets = [name for arg in args.sheets for name in (sorted(glob.glob(arg)) if glob.has_magic(arg) else [arg])]
    if not sheets:
        raise Fail("no sheet matches " + " ".join(args.sheets))
    for path in map(Path, sheets):
        target = out_dir / (path.stem + ".stp")
        if target.exists() and not args.force:
            raise Fail(f"{target} exists; pass --force to overwrite")
        try:
            stp, lines = convert(read_ini(path), garage, template)
        except Fail as e:
            raise Fail(f"{path.name}: {e}")
        if args.notes is not None:
            stp.set_notes(args.notes)
        jobs.append((path, target, stp, lines))

    # Nothing is written unless every sheet converted.
    out_dir.mkdir(parents=True, exist_ok=True)
    for path, target, stp, lines in jobs:
        target.write_bytes(stp.encode())
        print(f"{path.name} -> {target}   (bike id: {stp.bike_id})")
        print("\n".join(lines))
    print("Not stored in a setup: Map (kept from the template) and RaceSag "
          "(a readout: adjust rear preload in the garage until it matches).")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    gears = argparse.ArgumentParser(add_help=False)
    gears.add_argument("--gears", type=int, help="gear count, if it cannot be worked out from the file")

    p = sub.add_parser("dump", parents=[gears], help="print every stored position in a .stp")
    p.add_argument("file")
    p.set_defaults(run=cmd_dump)

    p = sub.add_parser("diff", parents=[gears], help="list the positions that differ between two .stp files")
    p.add_argument("a")
    p.add_argument("b")
    p.set_defaults(run=cmd_diff)

    p = sub.add_parser("init", parents=[gears], help="write an empty garage file for a template .stp")
    p.add_argument("template")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--force", action="store_true")
    p.set_defaults(run=cmd_init)

    p = sub.add_parser("build", parents=[gears], help="convert sheets to .stp files")
    p.add_argument("sheets", nargs="+")
    p.add_argument("--template", required=True, help=".stp saved from the garage for this bike")
    p.add_argument("--garage", required=True, help="garage file for this bike (see init)")
    p.add_argument("--out-dir", default="stp_out")
    p.add_argument("--notes", help="text for the setup's notes box (default: keep the template's)")
    p.add_argument("--force", action="store_true", help="overwrite existing output files")
    p.set_defaults(run=cmd_build)

    args = parser.parse_args(argv)
    try:
        args.run(args)
    except Fail as e:
        sys.exit(f"error: {e}")


if __name__ == "__main__":
    main()
