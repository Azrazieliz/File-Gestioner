# NoWorld 3D asset bridge — Blender 5.2.2 / Koikatsu / File Gestioner

## Confirmed authorized PC dependencies (2026-10-23)

- Blender **5.2.2 LTS** executable (version probed live):
  `D:\Tools\Blender-5.2.2-LTS\blender-5.2.2-windows-x64\blender.exe`
- Koikatsu Party authoring ecosystem:
  `D:\Tools\GameAssetPipeline\KoikatsuParty`
- KKBP v9.5.0 staging with **Importer 9.5.0** and **Exporter 5.06** archives:
  `D:\Tools\GameAssetPipeline\KoikatsuParty\addons\KKBP_v9.5.0`
- NoWorld protected art and reviewed exports:
  `D:\NoWorld_Art_Production`, `D:\UnrealProjects\Gate09_Protected_Production_20261016`
- Unreal environment: `D:\Epic Games\UE_5.8`

The Koikatsu/KKBP archives exist, but archive presence is **not verification
that a plugin is enabled and working inside Blender or Koikatsu**.
No additional installs or original-game changes are made here.

## Concrete workflow

1. Keep NoWorld's `.blend`, original Koikatsu cards and Unity bundles intact.
2. If starting from a native Koikatsu PNG card or `.unity3d`, use
   the **existing NoWorld / KKBP** authorized extraction-export process
   to produce a **real** FBX/GLB first. **Do not claim a PNG card itself is
   renderable geometry.**
3. From the PC, run `noworld_asset_bridge.py probe` to verify local paths.
4. Generate an independent mobile preview GLB with the PC's Blender 5.2.2
   while keeping source rigs, original animations, morphs, metadata, materials
   and names unchanged in the SOURCE file. No automatic motion retarget.
5. Copy the generated GLB to your phone through your preferred file sync.
   File Gestioner loads it entirely offline and shows **NoWorld identity,
   Gate, provenance SHA-256, source lane and QA status**.
6. The accompanying `.nwasset.json` is an explicit immutable-ish
   inspection receipt, not an Unreal `.uasset`, not an approval and not a
   substitute for Gate09/Gate12 test records.

### Example: NoWorld Blender source

```powershell
& "D:\\Tools\\Python311\\python.exe" .\\noworld_asset_bridge.py probe

& "D:\\Tools\\Python311\\python.exe" .\\noworld_asset_bridge.py export `
  --input "D:\NoWorld_Art_Production\P03_Kingdom_River_Citadel_Environment\NW_Kingdom_RiverVale_P32_GROUNDED_URBAN_CORE.blend" `
  --output "D:\NoWorld_Art_Production\MobilePreviews\NW_RiverVale_P32.glb" `
  --asset-id "NW-RiverVale-P32" --gate "GATE03" --source-lane BLENDER `
  --ue-target "/Game/Experimental/FirstWorldR1"
```

### Example: real Koikatsu-derived FBX source

```powershell
& "D:\\Tools\\Python311\\python.exe" .\\noworld_asset_bridge.py export `
  --input "D:\UnrealProjects\Gate09_Protected_Production_20261016\UnrealInterchange_20261019\G09_LuminousV3_Idle_01_Thoughtful.fbx" `
  --output "D:\NoWorld_Art_Production\MobilePreviews\G09_Luminous_Thoughtful.glb" `
  --asset-id "G09-LuminousV3-Idle-01" --gate "GATE09" `
  --source-lane KOIKATSU_EXPORTED `
  --ue-target "/Game/Experimental/Gate12Koikatsu"
```

The exporter checks source identity via SHA-256 and records target paths, but
**does not infer approval** from filenames, output existence or successful
Blender export. `art_acceptance=NOT_APPROVED`,
`unreal_native_import=NOT_TESTED`, `device_validation=NOT_TESTED`.

**Animation-only FBXs may not contain renderable mesh.** They can show an
armature, or be empty in the mobile mesh viewer; renderable previews of
Koikatsu characters need their authorized **character mesh + skeleton +**
matching animation in the same source document. Gate09 notes 975-bone
skeletons, differing wardrobe bone paths and measured axis transforms.
File Gestioner must not automatically cross-link those variants.

## What is and is not supported

- Viewer already handles GLB/GLTF, OBJ, FBX, STL, PLY, DAE, 3MF, 3DS,
  AMF, USD variants (format and WebView caveats apply).
- `.blend`, `.blend1`, `.unity3d`, `.assetbundle` and `.zipmod` are
  classified as **native authoring sources**, shown with a conversion
  explanation without loading their full bytes. They are NOT parsed as 3D.
- The new NoWorld metadata panel is populated **only** when a valid tagged
  GLB actually embeds `noworld.asset.preview.v1` metadata. A filename
  beginning with `NW_` is not sufficient evidence.
- The viewer's self-contained single-file memory limit remains **80 MiB**.
  GLBs beyond that need a purposeful mobile LOD/texture/memory budget;
  this bridge does not silently degrade or resize fidelity.
- External textures / sidecar BINs are not automatically resolved. Use
  self-contained GLB for portable previews.
- Blender/Koikatsu Windows binaries are NEVER packaged inside Android;
  conversion must run on the authorized PC. This bridge does not run an
  unsecured network service or upload proprietary game assets to GitHub.
- Native Unreal `.uasset` is cooked/editor-managed binary and is not a
  portable GLB. To view, create a separate non-destructive preview export.

## Provenance / licensing / safety

Source names and SHA-256 hashes are labels for manual reconciliation against
NoWorld Registry v2 and Gate09 interchange manifests; they are not proof of
an actual import receipt. Gate09/12 **SOURCE_REVIEW, ART_QA,
UNREAL_NATIVE_IMPORT, DEVICE_QA** stay separate and remain unapproved
until evidence from the relevant gates is produced.

No Koikatsu game assemblies, mods, proprietary character files, private
user cards or source `.blend` files are committed here. The bridge scripts
contain only portable logic and known local dependency locations. All source
assets remain on the authorized PC.

References:
- NoWorld Gate09 rig contract:
  `Offline-Game@production/gate09-rig-motion-20261016/docs/production/gate09/GATE09_GATE12_RIG_ANIM_INTEGRATION_CONTRACT_V0_1.md`
- Gate09 motion interchange manifest:
  `Offline-Game@production/gate09-rig-motion-20261016/docs/production/gate09/GATE09_UNREAL_INTERCHANGE_MANIFEST_20261019.json`.
