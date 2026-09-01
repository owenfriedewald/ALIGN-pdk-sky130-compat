from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sky130_gen_param", ROOT / "SKY130_PDK" / "gen_param.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_direct_sky130_models_dispatch_to_mos_generator() -> None:
    for model in MODULE.DIRECT_SKY130_MOS_GENERATORS:
        assert MODULE.canonical_generator_name(model) == "MOS"
        assert MODULE.canonical_generator_name(model.upper()) == "MOS"


def test_non_mos_generators_remain_distinct() -> None:
    assert MODULE.canonical_generator_name("CAP") == "CAP"
    assert MODULE.canonical_generator_name("RES") == "RES"
    assert MODULE.canonical_generator_name("black_box") == "black_box"
