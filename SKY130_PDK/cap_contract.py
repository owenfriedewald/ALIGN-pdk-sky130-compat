"""Static connectivity contract for generated Sky130 MIM capacitors."""


def _positive_area_overlap(left, right):
    return (
        min(left[2], right[2]) > max(left[0], right[0])
        and min(left[3], right[3]) > max(left[1], right[1])
    )


def _shapes(terminals, *, layer=None, net_name=...):
    result = []
    for terminal in terminals:
        if layer is not None and terminal.get("layer") != layer:
            continue
        if net_name is not ... and terminal.get("netName") != net_name:
            continue
        result.append(terminal)
    return result


def validate_cap_terminal_topology(terminals):
    """Reject MIM primitives whose streamed device topology is inconsistent.

    The compatibility PDK implements CAPM over the ALIGN M4 layer (official
    Sky130 met3).  M4 is the bottom electrode; CAPM is the top electrode and
    reaches the MINUS routing terminal through CapMIMContact and M5.  CAPM and
    its device contact are streamed device layers, not independent ALIGN
    routing nets.
    """

    plus_m4 = _shapes(terminals, layer="M4", net_name="PLUS")
    minus_m4 = _shapes(terminals, layer="M4", net_name="MINUS")
    minus_m5 = _shapes(terminals, layer="M5", net_name="MINUS")
    capm = _shapes(terminals, layer="CapMIMLayer")
    contacts = _shapes(terminals, layer="CapMIMContact")

    if not any("pin" in shape.get("netType", "") for shape in plus_m4):
        raise ValueError("MIM capacitor requires a routable PLUS pin on M4")
    if not any("pin" in shape.get("netType", "") for shape in minus_m4):
        raise ValueError("MIM capacitor requires a routable MINUS pin on M4")
    if not minus_m5:
        raise ValueError("MIM capacitor requires a MINUS M5 top-plate strap")
    if not capm or not contacts:
        raise ValueError("MIM capacitor requires CAPM and CapMIMContact geometry")

    if any(shape.get("netName") is not None for shape in capm + contacts):
        raise ValueError(
            "CAPM device geometry must not be represented as an independent routing net"
        )

    if any(
        _positive_area_overlap(plus["rect"], minus["rect"])
        for plus in plus_m4
        for minus in minus_m4
    ):
        raise ValueError("MIM capacitor PLUS and MINUS M4 conductors overlap")

    if not any(
        _positive_area_overlap(plate["rect"], device["rect"])
        for plate in plus_m4
        for device in capm
    ):
        raise ValueError("MIM capacitor CAPM does not overlap its M4 bottom plate")

    for contact in contacts:
        if not any(
            _positive_area_overlap(contact["rect"], device["rect"])
            for device in capm
        ):
            raise ValueError("MIM contact does not overlap CAPM")
        if not any(
            _positive_area_overlap(contact["rect"], strap["rect"])
            for strap in minus_m5
        ):
            raise ValueError("MIM contact does not overlap the MINUS M5 strap")

