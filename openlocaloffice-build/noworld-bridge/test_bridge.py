import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("assetbridge", ROOT/"noworld_asset_bridge.py")
bridge=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=bridge
spec.loader.exec_module(bridge)

class NoWorldBridgeTests(unittest.TestCase):
    def test_dependency_paths_are_lazy_and_read_only(self):
        args=SimpleNamespace(
            blender=Path("X:/not-installed/blender.exe"),
            kkbp=Path("X:/not-installed/KKBP"),
            noworld=Path("X:/not-installed/NoWorld"),
        )
        observed=bridge.installed(args)
        self.assertFalse(observed["blender"]["present"])
        self.assertFalse(observed["koikatsu_exporter"]["present"])
        self.assertFalse(observed["noworld_art"]["present"])

    def test_source_hash_and_status_never_claim_acceptance(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/"protected-test.blend"
            source.write_bytes(b"private source fixture")
            args=SimpleNamespace(
                asset_id="G09-LuminousV3-Test",
                gate="GATE09",
                source_lane="KOIKATSU_EXPORTED",
                ue_target="/Game/Experimental/Gate12Koikatsu",
            )
            result=bridge.output_metadata(args,source)
            self.assertEqual(result["schema"], "noworld.asset.preview.v1")
            self.assertEqual(result["source_sha256"], bridge.sha256(source))
            self.assertEqual(result["unreal_native_import"],"NOT_TESTED")
            self.assertEqual(result["device_validation"],"NOT_TESTED")
            self.assertEqual(result["art_acceptance"],"NOT_APPROVED")
            self.assertTrue(result["source_approval_is_not_inferred"])

if __name__ == "__main__":
    unittest.main()
