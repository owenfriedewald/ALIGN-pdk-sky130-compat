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


def _connected_component(start, shapes):
    reached = list(start)
    pending = list(start)
    while pending:
        current = pending.pop()
        for candidate in shapes:
            if candidate in reached:
                continue
            if _positive_area_overlap(current["rect"], candidate["rect"]):
                reached.append(candidate)
                pending.append(candidate)
    return reached


def _axis_gap(left, right, lower, upper):
    return max(left[lower] - right[upper], right[lower] - left[upper], 0)


def _contains(outer, inner):
    return (
        outer[0] <= inner[0]
        and outer[1] <= inner[1]
        and outer[2] >= inner[2]
        and outer[3] >= inner[3]
    )


def validate_cap_terminal_topology(
    terminals,
    *,
    m4_pitch=None,
    m4_offset=0,
    unrelated_m4_spacing=None,
    require_routing_halo=False,
):
    """Reject MIM primitives whose streamed device topology is inconsistent.

    The compatibility PDK implements CAPM over the ALIGN M4 layer (official
    Sky130 met3).  M4 is the bottom electrode; CAPM is the top electrode and
    reaches the MINUS routing terminal through CapMIMContact and M5.  CAPM and
    its device contact are streamed device layers, not independent ALIGN
    routing nets.
    """

    plus_m4 = _shapes(terminals, layer="M4", net_name="PLUS")
    minus_m4 = _shapes(terminals, layer="M4", net_name="MINUS")
    device_m4 = [
        shape
        for shape in _shapes(terminals, layer="M4", net_name=None)
        if shape.get("netType") != "blockage"
    ]
    minus_m5 = _shapes(terminals, layer="M5", net_name="MINUS")
    capm = _shapes(terminals, layer="CapMIMLayer")
    contacts = _shapes(terminals, layer="CapMIMContact")
    m4_blockages = [
        shape
        for shape in _shapes(terminals, layer="M4")
        if shape.get("netType") == "blockage"
    ]

    if not any("pin" in shape.get("netType", "") for shape in plus_m4):
        raise ValueError("MIM capacitor requires a routable PLUS pin on M4")
    if not any("pin" in shape.get("netType", "") for shape in minus_m4):
        raise ValueError("MIM capacitor requires a routable MINUS pin on M4")
    if not minus_m5:
        raise ValueError("MIM capacitor requires a MINUS M5 top-plate strap")
    if not capm or not contacts:
        raise ValueError("MIM capacitor requires CAPM and CapMIMContact geometry")

    if m4_pitch is not None:
        for pin in plus_m4 + minus_m4:
            center = (pin["rect"][1] + pin["rect"][3]) // 2
            if (center - m4_offset) % m4_pitch:
                raise ValueError("MIM capacitor M4 routing pin is off grid")

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

    if not device_m4:
        raise ValueError("MIM capacitor requires unnamed M4 bottom-plate geometry")
    if any(
        _positive_area_overlap(device["rect"], minus["rect"])
        for device in device_m4
        for minus in minus_m4
    ):
        raise ValueError("MIM capacitor bottom-plate geometry overlaps MINUS M4")

    if unrelated_m4_spacing is not None:
        for device in capm:
            for minus in minus_m4:
                x_gap = _axis_gap(device["rect"], minus["rect"], 0, 2)
                y_gap = _axis_gap(device["rect"], minus["rect"], 1, 3)
                if x_gap == 0 and y_gap < unrelated_m4_spacing:
                    raise ValueError(
                        "MIM capacitor CAPM clearance to unrelated MINUS M4 "
                        f"is {y_gap}, below required {unrelated_m4_spacing}"
                    )

    if require_routing_halo:
        if unrelated_m4_spacing is None:
            raise ValueError("MIM routing halo requires an unrelated-M4 spacing")
        plate_candidates = [
            shape
            for shape in device_m4
            if _contains(shape["rect"], capm[0]["rect"])
        ] if len(capm) == 1 else []
        if len(capm) != 1 or len(plate_candidates) != 1:
            raise ValueError(
                "MIM routing halo requires one CAPM and one overlapping bottom plate"
            )
        if not m4_blockages:
            raise ValueError("MIM capacitor requires routing-only M4 halo blockages")
        cap_rect = capm[0]["rect"]
        plate_rect = plate_candidates[0]["rect"]
        plus_top = max(shape["rect"][3] for shape in plus_m4)
        halo = [
            cap_rect[0] - unrelated_m4_spacing,
            cap_rect[1] - unrelated_m4_spacing,
            cap_rect[2] + unrelated_m4_spacing,
            cap_rect[3] + unrelated_m4_spacing,
        ]
        required_regions = [
            [halo[0], halo[1], plate_rect[0], halo[3]],
            [plate_rect[2], halo[1], halo[2], halo[3]],
            [plate_rect[0], halo[1], plate_rect[2], plate_rect[1]],
            [plate_rect[0], max(plate_rect[3], plus_top), plate_rect[2], halo[3]],
        ]
        for region in required_regions:
            if region[0] >= region[2] or region[1] >= region[3]:
                continue
            if not any(_contains(blockage["rect"], region) for blockage in m4_blockages):
                raise ValueError(
                    "MIM capacitor routing-only M4 halo does not cover "
                    f"required region {region}"
                )

        boundaries = _shapes(terminals, layer="Boundary")
        if len(boundaries) != 1 or not _contains(boundaries[0]["rect"], halo):
            raise ValueError("MIM capacitor boundary does not contain its routing halo")

    plus_component = _connected_component(plus_m4, plus_m4 + device_m4)
    if not any(shape in plus_component for shape in device_m4):
        raise ValueError("MIM capacitor PLUS pin does not reach bottom-plate geometry")
    if not any(
        shape in plus_component
        and _positive_area_overlap(shape["rect"], device["rect"])
        for shape in device_m4
        for device in capm
    ):
        raise ValueError("MIM capacitor PLUS access chain does not reach the CAPM overlap")

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
