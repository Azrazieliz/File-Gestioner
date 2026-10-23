"""Execute with Blender 5.2.2 headless, never by system Python.

Preserves source .blend / FBX / OBJ / GLB files; exports a read-only mobile
GLB preview with NoWorld provenance in glTF node extras. No automatic UE import
or production approval, no automatic Koikatsu game/mod file extraction.
"""
import argparse
import json
import sys
from pathlib import Path

import bpy

def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--metadata", required=True)
    options = parser.parse_args(args)

    original = Path(options.input).resolve(strict=True)
    preview = Path(options.output).resolve()
    preview.parent.mkdir(parents=True, exist_ok=True)
    metadata = json.loads(Path(options.metadata).read_text(encoding="utf-8"))
    suffix = original.suffix.lower()

    # Native .blend projects must be opened by Blender, never parsed as text
    # or submitted to any third-party service.
    if suffix == ".blend":
        bpy.ops.wm.open_mainfile(filepath=str(original))
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        if suffix == ".fbx":
            bpy.ops.import_scene.fbx(filepath=str(original))
        elif suffix == ".obj":
            bpy.ops.wm.obj_import(filepath=str(original))
        elif suffix in {".glb", ".gltf"}:
            bpy.ops.import_scene.gltf(filepath=str(original))
        else:
            raise ValueError("Supported inputs: .blend, .fbx, .obj, .glb, .gltf. Koikatsu cards require KKBP export first.")

    # The viewer reads glTF scene/node extras; set BOTH for predictable access.
    # Keep the original scene/meshes/bones/shapekeys/actions unchanged.
    compact = json.dumps(metadata, ensure_ascii=True, separators=(",", ":"))
    for scene in bpy.data.scenes:
        scene["noworld_asset"] = compact
    for obj in bpy.data.objects:
        if obj.parent is None:
            obj["noworld_asset"] = compact
    if not bpy.data.objects:
        raise ValueError("The source contains no objects")

    # The source is never overwritten; GLB is a separate preview product.
    bpy.ops.export_scene.gltf(
        filepath=str(preview),
        export_format="GLB",
        use_selection=False,
        export_extras=True,
        export_animations=True,
        export_skins=True,
        export_morph=True
    )
    if not preview.is_file() or preview.stat().st_size < 20:
        raise RuntimeError("Blender produced no valid GLB preview")
    with preview.open("rb") as f:
        if f.read(4) != b"glTF":
            raise RuntimeError("Export is not a GLB file")
    print("NOWORLD_PREVIEW_EXPORT_OK", preview, preview.stat().st_size)

if __name__ == "__main__":
    main()
