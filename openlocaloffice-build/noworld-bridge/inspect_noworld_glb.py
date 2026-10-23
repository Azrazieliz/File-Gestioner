#!/usr/bin/env python3
"""Read glTF scene/node extras from a GLB without loading private geometry."""
import argparse
import json
from pathlib import Path
import struct
import sys

def embedded_manifest(path):
    with Path(path).open("rb") as f:
        header = f.read(12)
        if len(header) != 12:
            raise ValueError("Truncated GLB header")
        magic, version, total = struct.unpack("<4sII", header)
        if magic != b"glTF" or version != 2 or total != Path(path).stat().st_size:
            raise ValueError("Invalid GLB v2 header")
        size, kind = struct.unpack("<I4s", f.read(8))
        if kind != b"JSON" or size > 64 * 1024 * 1024:
            raise ValueError("GLB has no bounded JSON chunk")
        document = json.loads(f.read(size))
    sources = (document.get("scenes") or []) + (document.get("nodes") or [])
    for source in sources:
        candidate = source.get("extras", {}).get("noworld_asset")
        if not candidate:
            continue
        manifest = json.loads(candidate) if isinstance(candidate, str) else candidate
        if manifest.get("schema") == "noworld.asset.preview.v1":
            return manifest
    raise ValueError("No NoWorld scene/node provenance was embedded in this GLB")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("glb", type=Path)
    args = parser.parse_args()
    manifest = embedded_manifest(args.glb)
    print(json.dumps({
        "asset_id":manifest["asset_id"],
        "project":manifest["project"],
        "gate":manifest["gate"],
        "source_sha256":manifest["source_sha256"],
        "art_acceptance":manifest["art_acceptance"],
        "unreal_native_import":manifest["unreal_native_import"],
    }, indent=2))

if __name__ == "__main__":
    main()
