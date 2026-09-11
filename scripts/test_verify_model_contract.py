"""Source contract regression checks; no inference or parity claims."""

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_spec = importlib.util.spec_from_file_location(
    "verify_model_contract", Path(__file__).with_name("verify_model_contract.py")
)
assert _spec and _spec.loader
contract = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(contract)


class MobileSourceContractTest(unittest.TestCase):
    def test_current_production_defaults_are_accepted(self):
        contract.validate_source_defaults()

    def test_changed_breed_order_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mobile = Path("apps/mobile/app/src/main/java/id/sapikenal/app")
            paths = [
                "apps/backend/config.py",
                "apps/backend/model/loader.py",
                "apps/backend/docker-compose.yml",
                "apps/backend/.env.example",
                "apps/mobile/app/build.gradle.kts",
                "apps/mobile/local.properties.example",
                str(mobile / "ml/OfflineInferenceEngine.kt"),
                str(mobile / "ml/OnlineInferenceClient.kt"),
                str(mobile / "ml/preprocessing/ClientPreprocessor.kt"),
                str(mobile / "domain/model/BreedContract.kt"),
            ]
            for relative in paths:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(contract.ROOT / relative, target)
            definition = root / mobile / "domain/model/BreedContract.kt"
            definition.write_text(
                definition.read_text().replace(
                    'BreedDefinition("bali"', 'BreedDefinition("wrong"'
                )
            )
            with (
                patch.object(contract, "ROOT", root),
                self.assertRaises(contract.ContractError),
            ):
                contract.validate_source_defaults()


if __name__ == "__main__":
    unittest.main()
