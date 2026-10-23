#!/usr/bin/env python3
"""NoWorld ↔ File Gestioner read-only 3D preview bridge.

Requires authorized access to the user's installed Blender; NO Koikatsu binary
is shipped or copied. Native Koikatsu cards/Unity asset bundles require the
existing KKBP/NoWorld extraction pipeline to produce a source FBX/GLB first.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone

DEFAULT_BLENDER = Path(r"D:\Tools\Blender-5.2.2-LTS\blender-5.2.2-windows-x64\blender.exe")
DEFAULT_KKBP = Path(r"D:\Tools\GameAssetPipeline\KoikatsuParty\addons\KKBP_v9.5.0")
DEFAULT_NOWORLD = Path(r"D:\NoWorld_Art_Production")
VALID_INPUTS = {".blend", ".fbx", ".obj", ".glb", ".gltf"}
MAX_ANDROID_PREVIEW = 80 * 1024 * 1024

def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def installed(args):
    return {
        "blender": {"path": str(args.blender), "present": args.blender.is_file()},
        "koikatsu_exporter": {"path": str(args.kkbp), "present": args.kkbp.is_dir()},
        "noworld_art": {"path": str(args.noworld), "present": args.noworld.is_dir()},
    }

def output_metadata(args, source):
    return {
        "schema": "noworld.asset.preview.v1",
        "project": "NoWorld: False Horizon",
        "asset_id": args.asset_id,
        "gate": args.gate,
        "source_lane": args.source_lane,
        "source_format": source.suffix.lower().lstrip("."),
        "source_sha256": sha256(source),
        "source_file": source.name,
        "source_size_bytes": source.stat().st_size,
        "ue_target": args.ue_target,
        "art_acceptance": "NOT_APPROVED",
        "unreal_native_import": "NOT_TESTED",
        "device_validation": "NOT_TESTED",
        "source_review": "PENDING",
        "rig_retention": "SOURCE_MUST_REMAIN_UNCHANGED",
        "source_approval_is_not_inferred": True,
        "fidelity": "MOBILE_PREVIEW_ONLY",
    }

def export(args):
    source = args.input.expanduser().resolve(strict=True)
    if source.suffix.lower() not in VALID_INPUTS:
        raise ValueError(
            "Requires .blend, .fbx, .obj, .glb or .gltf. Native Koikatsu PNG "
            "cards, .unity3d bundles and .zipmod packages must FIRST be exported "
            "with the already installed NoWorld/KKBP workflow."
        )
    if not re.fullmatch(r"[A-Za-z0-9_.:-]{2,100}", args.asset_id):
        raise ValueError("Provide a stable, nonblank NoWorld asset identity")
    if not args.blender.is_file():
        raise FileNotFoundError("Configured Blender 5.2 executable is missing: " + str(args.blender))
    path = args.output.expanduser().resolve()
    if path.suffix.lower() != ".glb":
        raise ValueError("Output must be a .glb preview file")
    if source == path:
        raise ValueError("Cannot overwrite source with generated preview")
    receipt = path.with_suffix(".nwasset.json")
    if path.exists() or receipt.exists():
        raise FileExistsError("Output already exists; supply a new path to preserve previous receipts")
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata = output_metadata(args, source)
    meta_path = path.with_suffix(".nwasset.metadata.tmp.json")
    try:
        meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        script = Path(__file__).with_name("blender_preview_export.py")
        result = subprocess.run(
            [str(args.blender), "--background", "--factory-startup",
             "--python", str(script), "--", "--input", str(source),
             "--output", str(path), "--metadata", str(meta_path)],
            capture_output=True, text=True, timeout=args.timeout,
        )
        if result.returncode != 0:
            raise RuntimeError(
                "Blender export failed (original source unchanged):\n" +
                (result.stderr + "\n" + result.stdout)[-3200:]
            )
        if not path.is_file() or path.stat().st_size < 20:
            raise RuntimeError("No valid preview was created")
        with path.open("rb") as f:
            if f.read(4) != b"glTF":
                raise RuntimeError("Invalid GLB magic")
        receipt_data = dict(metadata)
        receipt_data.update({
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "preview": {
                "name": path.name, "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "mobile_preview_within_80mib": path.stat().st_size <= MAX_ANDROID_PREVIEW,
            },
            "pc_dependencies": installed(args),
            "read_only": True,
            "unreal_import_performed": False,
            "koikatsu_installation_modified": False,
        })
        receipt.write_text(json.dumps(receipt_data, indent=2), encoding="utf-8")
        print(json.dumps({
            "preview": str(path), "receipt": str(receipt),
            "preview_supported_on_phone": path.stat().st_size <= MAX_ANDROID_PREVIEW,
            "unreal_import_status": "NOT_TESTED",
            "art_approval": "NOT_APPROVED",
        }, indent=2))
    finally:
        meta_path.unlink(missing_ok=True)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--blender", type=Path, default=DEFAULT_BLENDER)
    p.add_argument("--kkbp", type=Path, default=DEFAULT_KKBP)
    p.add_argument("--noworld", type=Path, default=DEFAULT_NOWORLD)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("probe", help="Inspect existing PC dependency paths, no mutations")
    e = sub.add_parser("export", help="Export a NoWorld-tagged GLB preview + receipt")
    e.add_argument("--input", type=Path, required=True)
    e.add_argument("--output", type=Path, required=True)
    e.add_argument("--asset-id", required=True)
    e.add_argument("--gate", default="GATE09")
    e.add_argument("--source-lane", choices=["BLENDER", "KOIKATSU_EXPORTED", "OTHER"], default="BLENDER")
    e.add_argument("--ue-target", default="/Game/Experimental/NoWorldPreview")
    e.add_argument("--timeout", type=int, default=1800)
    args = p.parse_args()
    if args.command == "probe":
        print(json.dumps(installed(args), indent=2))
        return 0
    export(args)
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("NoWorld preview export rejected: " + str(exc), file=sys.stderr)
        sys.exit(1)
