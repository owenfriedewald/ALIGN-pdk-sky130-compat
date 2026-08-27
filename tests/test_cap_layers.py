import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_mim_device_layer_streamout_and_clearance_contract() -> None:
    layers = json.loads((ROOT / "SKY130_PDK" / "layers.json").read_text())
    by_name = {entry["Layer"]: entry for entry in layers["Abstraction"]}

    assert by_name["CapMIMLayer"]["ViewerPassthrough"] is True
    assert by_name["CapMIMContact"]["ViewerPassthrough"] is True
    assert by_name["CapMIMLayer"]["UnrelatedMetalSpacing"] == 1340
    assert by_name["Cap"]["unrelatedMetalMargin"] == 20
