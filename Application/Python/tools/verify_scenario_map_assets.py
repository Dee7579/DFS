from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

EXPECTED = {
  "ambush.png": {
    "height": 938,
    "sha256": "c1269c2abf8f3948ebd0cf6dd5935ce56e880f28cc9728738157dd28b0ab5d41",
    "width": 1343
  },
  "annihilation.png": {
    "height": 1009,
    "sha256": "1b3dda8efd794dd9553dc524f846704cf413ac567212cd751364293693af74a5",
    "width": 1445
  },
  "assassination.png": {
    "height": 931,
    "sha256": "a9f902588469a9e9f15ae4b9672999b0253bb92438800988aaae6e08bdf3ecba",
    "width": 1329
  },
  "assault-on-ragesh-3.png": {
    "height": 810,
    "sha256": "05ff44715d4185dbba88c3a6ef2099b14a67ca101927f46915dcff70ac6c04b5",
    "width": 1160
  },
  "automaton-recovery.png": {
    "height": 1048,
    "sha256": "a2e3835a45bc1036968fe370911ce8127cf905b3725563ce66f8dd57958d55d9",
    "width": 1461
  },
  "battle-of-the-line.png": {
    "height": 784,
    "sha256": "73689045f7225063425be1acdb579beee3d4917d0380b23c33d9b3b908c9b507",
    "width": 1101
  },
  "between-darkness-and-light.png": {
    "height": 769,
    "sha256": "155cbbc5bdbb0b75fc3f2d33a7751fa1f248c39f787bbe49b64d5ff50e46388a",
    "width": 1100
  },
  "blockade.png": {
    "height": 956,
    "sha256": "7847fbe6d3ca77dea687ff2dadf0b04a03453f0bc941eb3fccbe656b7b8816c3",
    "width": 1370
  },
  "border-dispute.png": {
    "height": 790,
    "sha256": "bfb37485a40a3f5c51fbf4b5041e344636c51ba63382b040f5994067fcf41892",
    "width": 1128
  },
  "call-to-arms.png": {
    "height": 1009,
    "sha256": "4fc2cebdfda28015d0ec95a7970a0386f6de976a9dc1d5cb74db3f0158341162",
    "width": 1445
  },
  "carrier-clash.png": {
    "height": 1008,
    "sha256": "eef1c0bcaba694c1b0379a5787b4250698b4c8dfa4184f620b9e57fe4e024d1f",
    "width": 1443
  },
  "convoy-duty.png": {
    "height": 866,
    "sha256": "a52b4e9cc32aacff0db47e9fd7d5ff36c387ad64f1f6dda20395404efa9d283c",
    "width": 1238
  },
  "fall-of-night.png": {
    "height": 821,
    "sha256": "3c2fb2f201ee870770a1798050d532dfa05f4bb0fd3e1806c49b63a68b779197",
    "width": 1174
  },
  "first-strike.png": {
    "height": 1025,
    "sha256": "c51971fb6400ae89c53b16f8399113963efd229ad346e7208a22f454a30496e0",
    "width": 1469
  },
  "flee-to-jump-gate.png": {
    "height": 960,
    "sha256": "df7f0d3b0bbc0866c1cc3d27e4923d1e890ae7c86c27305404789ccf48c2d397",
    "width": 1373
  },
  "gravity-well.png": {
    "height": 1041,
    "sha256": "52d9ec3fc74d2e146dae591a99aa3e941435aa69896249209951c1bf903fd9c8",
    "width": 1461
  },
  "hunting-the-hunters.png": {
    "height": 997,
    "sha256": "5efe55b5421a1c5b438a198c7fc854edd819929f417aac6d7762f1bdf944f268",
    "width": 1429
  },
  "initial-contact.png": {
    "height": 1019,
    "sha256": "405ff46a694cf9f59b577d34df7f8f7dbc851913e90f0d882749f910122d7b5a",
    "width": 1460
  },
  "interludes-and-examinations.png": {
    "height": 812,
    "sha256": "45cd478dd6630d5e7205415400d3f93b612493a29d4185db51d942cf5aeade80",
    "width": 1158
  },
  "into-the-fire.png": {
    "height": 803,
    "sha256": "0150261e957ccaeeb3f544e6ccc38f19177f8b22a88202f89510d329f63fa2c6",
    "width": 1148
  },
  "king-of-the-jump-gate.png": {
    "height": 1040,
    "sha256": "0d2262f7f823b44eeebf3e5656ef85d4d729e7e27e55cabf747b3d2292ff3ad0",
    "width": 1463
  },
  "long-twilight-struggle.png": {
    "height": 821,
    "sha256": "1bdaadb1075a6fdf1c78e8e62b91472637932709939648c36cec0446edace285",
    "width": 1175
  },
  "on-the-back-foot.png": {
    "height": 1043,
    "sha256": "cb93531c72d281b6e2b23ee2f943b7859c12c2cc7f9dbc3de0db89143ff8604f",
    "width": 1460
  },
  "planetary-assault.png": {
    "height": 912,
    "sha256": "39fbe3b0e38ebbc7d68dc4ddefd6a40ee1265dcd2a8b8cfa884393a2e6d2a9bc",
    "width": 1306
  },
  "planetfall.png": {
    "height": 1019,
    "sha256": "10536b26c79daceba342b4f13ccc6f3920be0d60a8afb014a41d124354dafc81",
    "width": 1459
  },
  "quadrant-37.png": {
    "height": 910,
    "sha256": "15d9b44efc980c0c7d2e41fb9e070d49299f04e9d85cbe24cded3bda9da7124a",
    "width": 1301
  },
  "recon-run.png": {
    "height": 909,
    "sha256": "66f717ae622c41f86293cfc0dfdf0a2062ec51a3a327f9f77a2dd08aa68eaad7",
    "width": 1303
  },
  "rescue.png": {
    "height": 956,
    "sha256": "c1cba443467e75775cdea9a3cbcfcb18c1d3e51bfbf1791d4ecc2d1551fa4dc7",
    "width": 1370
  },
  "second-battle-quadrant-14.png": {
    "height": 704,
    "sha256": "6d8f7523e278985bf7a2801e7f0f65c5309b4b3c9980b86dbf368df99d2d3a92",
    "width": 1004
  },
  "severed-dreams.png": {
    "height": 1876,
    "sha256": "5d5eb6fffe489e45c627c5878c0dfa9a23bfafd35df9ea0304e58d6572d7b2a5",
    "width": 1435
  },
  "shadow-dancing.png": {
    "height": 819,
    "sha256": "e1b49f32cdc25d965867fcf76327657aea463d2618c0a5f5b485f545709fe7ea",
    "width": 1173
  },
  "space-superiority.png": {
    "height": 956,
    "sha256": "de75b06c97b929dea135e572f6cabed253515cf51121e84ebf8392688a104f1b",
    "width": 1368
  },
  "supply-ships.png": {
    "height": 956,
    "sha256": "47610f228dfb475d098d28b17baae1d9e7f60aac1f310bf9f139e4aa6274b081",
    "width": 1370
  },
  "towering-inferno.png": {
    "height": 1040,
    "sha256": "d3d6bbbaa322ce14f65c20b3ff75e3cbe6849a3c3614e662cb68bd3c2adb2b48",
    "width": 1464
  }
}


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        signature = handle.read(8)
        if signature != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"Not a PNG file: {path}")
        length = struct.unpack(">I", handle.read(4))[0]
        chunk_type = handle.read(4)
        if chunk_type != b"IHDR" or length < 8:
            raise ValueError(f"Missing PNG IHDR: {path}")
        width, height = struct.unpack(">II", handle.read(8))
        return int(width), int(height)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    root = Path(__file__).resolve().parents[1] / "resources" / "scenario_maps"
    failures: list[str] = []

    actual_names = {path.name for path in root.glob("*.png")}
    expected_names = set(EXPECTED)
    missing = sorted(expected_names - actual_names)
    extra = sorted(actual_names - expected_names)
    if missing:
        failures.append("Missing maps: " + ", ".join(missing))
    if extra:
        failures.append("Unexpected maps: " + ", ".join(extra))

    for name, record in EXPECTED.items():
        path = root / name
        if not path.is_file():
            continue
        dimensions = png_dimensions(path)
        expected_dimensions = (int(record["width"]), int(record["height"]))
        if dimensions != expected_dimensions:
            failures.append(
                f"{name} dimensions changed: expected "
                f"{expected_dimensions[0]}x{expected_dimensions[1]}, "
                f"found {dimensions[0]}x{dimensions[1]}"
            )
        actual_hash = sha256(path)
        if actual_hash != record["sha256"]:
            failures.append(
                f"{name} content hash changed: expected {record['sha256']}, "
                f"found {actual_hash}"
            )

    print("=====================================")
    print("DFS SCENARIO MAP ASSET VERIFICATION")
    print("=====================================")
    print(f"Maps checked: {len(EXPECTED)}")
    print()

    if failures:
        for failure in failures:
            print("FAIL ", failure)
        print()
        print("Scenario map verification FAILED")
        return 1

    print("PASS  All scenario maps are full-frame authoritative extracts")
    print("PASS  Every map has the certified Sprint 005E dimensions and hash")
    print()
    print("Scenario map verification PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
