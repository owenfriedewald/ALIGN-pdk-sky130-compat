from .align_compat import apply_align_runtime_patches

apply_align_runtime_patches()

from .cap import CapGenerator
from .res import ResGenerator
from .mos import MOSGenerator
from .guard_ring import RingGenerator
from .gen_param import canonical_generator_name
from align.primitive.default.via import ViaArrayGenerator


def generator_class(name):
    """Expose direct Sky130 MOS models to ALIGN's primitive dispatcher."""

    if canonical_generator_name(name) == "MOS" and str(name).upper() != "MOS":
        return MOSGenerator
    return False
