"""Tests for ini2stp. Run with: python -m unittest discover tools

These check the script against the documented layout and against itself.
They cannot check it against the game: no real .stp was available.
"""

import configparser
import contextlib
import io
import struct
import tempfile
import unittest
from pathlib import Path

import ini2stp
from ini2stp import Fail, Stp

ROOT = Path(__file__).resolve().parent.parent

# Positions for a made-up template, written out field by field in file order
# so the fixture does not depend on the script's own tables.
PRE = [
    1, 1,      # front tyre, rear tyre
    4, 3,      # front pressure, rear pressure
    2,         # fuel
    6, 5, 2,   # fork spring, preload, oil
    3,         # fork height
    10, 10,    # fork compression, rebound
    3, 10,     # shock spring, preload
    2,         # rod length
    10, 7, 9,  # shock low-speed, high-speed, rebound
    1,         # swingarm length
    2,         # fork offset
    2,         # rear sprocket
]
POST = [1, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0] + [0] * 13  # front sprocket first, engine map eighth


def template_bytes(gears=(0, 1, 2, 3, 4), version=0x116, notes=b"stock\0"):
    out = struct.pack("<I", 0x459353C8) + struct.pack("<H", version)
    out += b"fantic_xxf450_2023".ljust(32, b"\0")
    if version == 0x116:
        out += struct.pack("<H", 3)
    for value in PRE + list(gears) + POST:
        out += struct.pack("<I", value)
    return out + struct.pack("<I", len(notes)) + notes


# What the garage would show for that template: lowest, highest, step, template value.
GARAGE = """
[Drivetrain]
FrontSprocket = 12, 15, 1, 13
RearSprocket = 47, 53, 1, 49
[FrontSuspension]
SpringRate = 4.4, 5.4, 0.1, 5.0
Preload = 0, 10, 1, 5
OilLevel = 90, 130, 10, 110
Compression = 0, 20, 1, 10
Rebound = 0, 20, 1, 10
ForkHeight = 0, 8, 1, 5
ForkOffset = 20, 24, 1, 22
[RearSuspension]
SpringRate = 52, 64, 2, 58
Preload = 0, 20, 1, 10
LowSpeedCompression = 0, 20, 1, 10
HighSpeedCompression = 0, 3, 1/4, 1-1/4
Rebound = 0, 20, 1, 11
RodLength = 142, 144, 0.5, 143
[Tyres]
FrontPressure = 0.70, 1.20, 0.05, 0.90
RearPressure = 0.70, 1.20, 0.05, 0.85
"""


def run(args):
    with contextlib.redirect_stdout(io.StringIO()):
        ini2stp.main(args)


def ini(text):
    parsed = configparser.ConfigParser(interpolation=None)
    parsed.optionxform = str
    parsed.read_string(text)
    return parsed


class Layout(unittest.TestCase):
    def test_fields_land_in_named_slots_and_reencode(self):
        data = template_bytes()
        stp = Stp.parse(data)
        self.assertEqual(stp.bike_id, "fantic_xxf450_2023")
        self.assertEqual((stp.version, stp.subversion, stp.gears), (0x116, 3, [0, 1, 2, 3, 4]))
        self.assertEqual(stp.get("ForkSpring"), 6)
        self.assertEqual(stp.get("ShockHighSpeedCompression"), 7)
        self.assertEqual(stp.get("RearSprocket"), 2)
        self.assertEqual(stp.get("FrontSprocket"), 1)
        self.assertEqual(stp.get("EngineMap"), 1)
        self.assertEqual(stp.notes, b"stock\0")
        self.assertEqual(stp.encode(), data)

    def test_gear_count_and_old_header(self):
        self.assertEqual(len(Stp.parse(template_bytes(gears=(0,) * 6)).gears), 6)
        old = Stp.parse(template_bytes(version=0x115))
        self.assertIsNone(old.subversion)
        self.assertEqual(old.encode(), template_bytes(version=0x115))

    def test_rejects_files_that_do_not_fit(self):
        data = template_bytes()
        for bad in (b"[Bike]\nName=x\n" * 20, data[:-1], data + b"\0", data[:4] + b"\x99\x01" + data[6:]):
            with self.assertRaises(Fail):
                Stp.parse(bad)
        with self.assertRaises(Fail):
            Stp.parse(data, gears=6)


class Convert(unittest.TestCase):
    def setUp(self):
        self.template = Stp.parse(template_bytes())

    def build(self, sheet, garage=GARAGE):
        return ini2stp.convert(ini(sheet), ini(garage), self.template)

    def test_values_become_positions(self):
        out, _ = self.build("""
[Drivetrain]
FrontSprocket=13
RearSprocket=50
[FrontSuspension]
SpringRate=5.2
Compression=4
ForkHeight=0.0
[RearSuspension]
HighSpeedCompression=0.75
RodLength=144.0
[Tyres]
RearPressure=1.00
""")
        self.assertEqual(out.get("RearSprocket"), 3)               # 47..53, up
        self.assertEqual(out.get("FrontSprocket"), 1)
        self.assertEqual(out.get("ForkSpring"), 8)                 # 4.4 + 8 * 0.1
        self.assertEqual(out.get("ForkCompression"), 16)           # clicks count down
        self.assertEqual(out.get("ForkHeight"), 8)                 # shown reversed
        self.assertEqual(out.get("ShockHighSpeedCompression"), 9)  # 12 - 3 quarter turns
        self.assertEqual(out.get("RodLength"), 4)
        self.assertEqual(out.get("RearPressure"), 6)

    def test_everything_else_is_left_alone(self):
        out, _ = self.build("[FrontSuspension]\nRebound=8\n")
        changed = [n for (n, a), (_, b) in zip(self.template.slots(), out.slots()) if a != b]
        self.assertEqual(changed, ["ForkRebound"])
        self.assertEqual((out.bike, out.version, out.subversion, out.notes),
                         (self.template.bike, 0x116, 3, b"stock\0"))

    def test_garage_limits_override_the_sheet_number(self):
        out, lines = self.build("""
[FrontSuspension]
SpringRate=9.9
OilLevel=50
ForkHeight=3.0
[RearSuspension]
RodLength=150
[GarageLimits]
ForkSpringRate=MAX
ForkOilLevel=MIN
ForkHeight=MIN
RodLength=MAX
""")
        self.assertEqual(out.get("ForkSpring"), 10)
        self.assertEqual(out.get("ForkOil"), 0)
        self.assertEqual(out.get("ForkHeight"), 8)
        self.assertEqual(out.get("RodLength"), 4)
        self.assertEqual(sum("garage limit" in line for line in lines), 4)

    def test_off_grid_and_out_of_range_values_snap_and_say_so(self):
        out, lines = self.build("[FrontSuspension]\nSpringRate=5.26\nOilLevel=40\nPreload=5.0\n")
        self.assertEqual(out.get("ForkSpring"), 9)   # 5.3
        self.assertEqual(out.get("ForkOil"), 0)      # clamped to 90
        self.assertEqual(sum("nearest option used" in line for line in lines), 2)

    def test_template_reading_must_match_stored_position(self):
        wrong = GARAGE.replace("SpringRate = 4.4, 5.4, 0.1, 5.0", "SpringRate = 4.4, 5.4, 0.1, 4.7")
        with self.assertRaises(Fail):
            self.build("[FrontSuspension]\nSpringRate=5.0\n", wrong)

    def test_direction_is_read_from_the_template(self):
        # A bike whose fork height is stored counting up: template shows 3 at position 3.
        garage = GARAGE.replace("ForkHeight = 0, 8, 1, 5", "ForkHeight = 0, 8, 1, 3")
        out, _ = self.build("[FrontSuspension]\nForkHeight=2.0\n", garage)
        self.assertEqual(out.get("ForkHeight"), 2)

    def test_uncalibrated_fields_keep_the_template_setting(self):
        garage = GARAGE.replace("Preload = 0, 10, 1, 5", "Preload = ?, ?, ?, ?")
        out, lines = self.build("[FrontSuspension]\nPreload=9.0\n", garage)
        self.assertEqual(out.get("ForkPreload"), 5)
        self.assertIn("FrontSuspension.Preload", lines[-1])

    def test_bad_garage_lines_are_rejected(self):
        for bad in ("4.4, 5.4, 0.1", "4.4, 5.4, 0.3, 5.0", "5.4, 4.4, 0.1, 5.0", "4.4, 5.4, 0, 5.0", "a, b, c, d"):
            with self.assertRaises(Fail):
                self.build("[FrontSuspension]\nSpringRate=5.0\n",
                           GARAGE.replace("4.4, 5.4, 0.1, 5.0", bad))


class CommandLine(unittest.TestCase):
    def test_build_converts_every_sheet_in_the_pack(self):
        sheets = sorted(str(p) for p in (ROOT / "setups").glob("*/*.ini"))
        self.assertEqual(len(sheets), 8)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "t.stp").write_bytes(template_bytes())
            (tmp / "g.ini").write_text(GARAGE)
            args = ["build", *sheets, "--template", str(tmp / "t.stp"), "--garage", str(tmp / "g.ini"),
                    "--out-dir", str(tmp / "out"), "--notes", "from sheet"]
            run(args)
            built = sorted((tmp / "out").glob("*.stp"))
            self.assertEqual(len(built), 8)
            sx = Stp.load(tmp / "out" / "XXF450_SX.stp")
            self.assertEqual((sx.get("ForkSpring"), sx.get("ForkOil"), sx.get("RodLength")), (10, 0, 4))
            self.assertEqual((sx.bike_id, sx.notes), ("fantic_xxf450_2023", b"from sheet\0"))
            with self.assertRaises(SystemExit):   # refuses to overwrite
                run(args)

    def test_init_writes_a_file_build_accepts(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "t.stp").write_bytes(template_bytes())
            run(["init", str(tmp / "t.stp"), "-o", str(tmp / "g.ini")])
            run(["build", str(ROOT / "setups/XXF450/XXF450_MX.ini"), "--template", str(tmp / "t.stp"),
                          "--garage", str(tmp / "g.ini"), "--out-dir", str(tmp / "out")])
            # Nothing calibrated, so the output is the template unchanged.
            self.assertEqual((tmp / "out" / "XXF450_MX.stp").read_bytes(), template_bytes())


if __name__ == "__main__":
    unittest.main()
