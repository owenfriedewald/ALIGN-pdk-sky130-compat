import json
import logging
from math import sqrt, floor, ceil, log10
from copy import deepcopy
from decimal import Decimal
logger = logging.getLogger(__name__)


def uniform_int_parameter(mvalues, parameter, default, primitive_name):
    """Return a generator-wide integer parameter or reject mixed values.

    ``MOSGenerator`` has one geometry value for parameters such as ``stack``.
    A grouped primitive therefore cannot safely contain devices with different
    stack depths.  Reject that representation before layout generation instead
    of silently taking the first member's value.
    """

    values = {
        key: int(params.get(parameter, default))
        for key, params in mvalues.items()
    }
    distinct = set(values.values())
    if len(distinct) != 1:
        rendered = ", ".join(f"{key}={value}" for key, value in sorted(values.items()))
        raise ValueError(
            f"Unsupported heterogeneous {parameter} in grouped MOS primitive "
            f"{primitive_name}: {rendered}. The generator has one shared "
            f"{parameter.lower()} geometry; prevent this grouping upstream."
        )
    return next(iter(distinct))


def limit_pairs(pairs):
    # Hack to limit aspect ratios when there are a lot of choices
    if len(pairs) > 12:
        new_pairs = []
        log10_aspect_ratios = [-0.3, 0, 0.3]
        for l in log10_aspect_ratios:
            best_pair = min((abs(log10(newy) - log10(newx) - l), (newx, newy))
                            for newx, newy in pairs)[1]
            new_pairs.append(best_pair)
        return new_pairs
    else:
        return pairs

def maximum_one_sided_body_tap_rows(
        max_distance_nm, unit_height_fins, fin_pitch_nm):
    """Return the largest safe MOS row count for a one-sided body tap.

    The current bulk-MOS generator places its body contact along one outer
    edge of the generated array.  Concrete aspect-ratio variants must
    therefore keep the opposite edge within the official latch-up distance.
    """

    unit_height_nm = int(unit_height_fins) * int(fin_pitch_nm)
    if unit_height_nm <= 0 or int(max_distance_nm) <= 0:
        raise ValueError("body-tap distance and MOS unit height must be positive")
    return max(1, int(max_distance_nm) // unit_height_nm)


def mos_width_to_nfin(width, fin_pitch_nm, device_name, primitive_name):
    """Convert a SPICE MOS width to an exact integral PDK fin count.

    Binary-float truncation turns legal decimal widths such as 4.2 um into
    4199 nm on some Python builds.  SPICE tokens are decimal authority, so use
    exact decimal arithmetic and reject genuinely off-grid widths.
    """

    width_nm = Decimal(str(width)) * Decimal("1e9")
    integral_nm = width_nm.to_integral_value()
    if width_nm != integral_nm:
        raise ValueError(
            f"Width of device {device_name} in {primitive_name} must be an "
            f"integral number of nanometers: {width}"
        )
    width_nm_int = int(integral_nm)
    pitch = int(fin_pitch_nm)
    if width_nm_int % pitch:
        raise ValueError(
            f"Width of device {device_name} in {primitive_name} should be "
            f"multiple of fin pitch:{pitch}"
        )
    return width_nm_int // pitch


def add_primitive(primitives, block_name, block_args, max_y_cells=None):
    if block_name in primitives:
        if not primitives[block_name] == block_args:
            logger.warning(f"Distinct devices mapped to the same primitive {block_name}: \
                             existing: {primitives[block_name]}\
                             new: {block_args}")
    else:
        logger.debug(f"Found primitive {block_name} with {block_args}")
        if 'x_cells' in block_args and 'y_cells' in block_args:
                x, y = block_args['x_cells'], block_args['y_cells']
                pairs = set()
                m = x*y
                y_sqrt = floor(sqrt(x*y))
                for y in range(y_sqrt, 0, -1):
                    if m % y == 0:
                        pairs.add((y, m//y))
                        pairs.add((m//y, y))
                    if y == 1:
                        break
                pairs = limit_pairs((pairs))
                if max_y_cells is not None:
                    pairs = {
                        (newx, newy)
                        for newx, newy in pairs
                        if newy <= max_y_cells
                    }
                    if not pairs:
                        raise ValueError(
                            f"No legal aspect ratio for {block_name}: all "
                            f"variants exceed max_y_cells={max_y_cells}"
                        )
                for newx, newy in sorted(pairs):
                    concrete_name = f'{block_name}_X{newx}_Y{newy}'
                    if concrete_name not in primitives:
                        primitives[concrete_name] = deepcopy(block_args)
                        primitives[concrete_name]['x_cells'] = newx
                        primitives[concrete_name]['y_cells'] = newy
                        primitives[concrete_name]['abstract_template_name'] = block_name
                        primitives[concrete_name]['concrete_template_name'] = concrete_name
        else:
            primitives[block_name] = block_args
            primitives[block_name]['abstract_template_name'] = block_name
            primitives[block_name]['concrete_template_name'] = block_name

def gen_param(subckt, primitives, pdk_dir):
    block_name = subckt.name
    vt = subckt.elements[0].model
    values = subckt.elements[0].parameters
    generator_name = subckt.generator["name"]
    block_name = subckt.name
    generator_name = subckt.generator["name"]
    layers_json = pdk_dir / "layers.json"
    with open(layers_json, "rt") as fp:
        pdk_data = json.load(fp)
    design_config = pdk_data["design_info"]

    if len(subckt.elements) == 1:
        values = subckt.elements[0].parameters
    else:
        mvalues = {}
        for ele in subckt.elements:
            mvalues[ele.name] = ele.parameters

    if generator_name == 'CAP':

        size = round(float(values["VALUE"]) * 1E15, 4)

        assert size <= design_config["max_size_cap"], f"caps larger than {design_config['max_size_cap']}fF are not supported"

        if "L" in values and "W" in values:
            length = round(float(values["L"]) * 1E9, 4)
            width = round(float(values["W"]) * 1E9, 4)
        else:
            # HACK for unit cap used in common centroid and support older SPICE
            length = int((sqrt(size/2))*1000)
            if length % 2 > 0 : length += 1
            width = int((sqrt(size/2))*1000)
            if width % 2 > 0 : width += 1

        # TODO: use float in name
        logger.debug(f"Generating capacitor for:{block_name}, {size}")
        block_args = {
            'primitive': generator_name,
            'value':  [int(length), int(width)]
        }
        add_primitive(primitives, block_name, block_args)

    elif generator_name == 'RES':
        assert float(values["VALUE"]) or float(values["R"]), f"unidentified size {values['VALUE']} for {name}"
        if "R" in values:
            size = round(float(values["R"]), 2)
        elif 'VALUE' in values:
            size = round(float(values["VALUE"]), 2)
        # TODO: use float in name
        if size.is_integer():
            size = int(size)
        height = ceil(sqrt(float(size) / design_config["unit_height_res"]))
        logger.debug(f'Generating resistor for: {block_name} {size}')
        block_args = {
            'primitive': generator_name,
            'value': (height, float(size))
        }
        add_primitive(primitives, block_name, block_args)

    else:
        assert 'MOS' == generator_name, f'{generator_name} is not recognized'
        if "vt_type" in design_config:
            vt = [vt.upper() for vt in design_config["vt_type"] if vt.upper() in subckt.elements[0].model]
        mvalues = {}
        for ele in subckt.elements:
            mvalues[ele.name] = ele.parameters
        device_name_all = [*mvalues.keys()]
        device_name = next(iter(mvalues))
        stack = uniform_int_parameter(mvalues, "STACK", 1, block_name)

        for key in mvalues:
            assert mvalues[key]["W"] != str, f"unrecognized size of device {key}:{mvalues[key]['W']} in {block_name}"
            size = mos_width_to_nfin(
                mvalues[key]["W"],
                design_config["Fin_pitch"],
                key,
                block_name,
            )
            mvalues[key]["NFIN"] = size
        name_arg = 'NFIN'+str(size)

        if 'NF' in mvalues[device_name].keys():
            for key in mvalues:
                assert int(mvalues[key]["NF"]), f"unrecognized NF of device {key}:{mvalues[key]['NF']} in {name}"
                assert int(mvalues[key]["NF"]) % 2 == 0, f"NF must be even for device {key}:{mvalues[key]['NF']} in {name}"
            name_arg = name_arg+'_NF'+str(int(mvalues[device_name]["NF"]))

        if 'M' in mvalues[device_name].keys():
            for key in mvalues:
                assert int(mvalues[key]["M"]), f"unrecognized M of device {key}:{mvalues[key]['M']} in {name}"
                if "PARALLEL" in mvalues[key].keys() and int(mvalues[key]['PARALLEL']) > 1:
                    mvalues[key]["PARALLEL"] = int(mvalues[key]['PARALLEL'])
                    mvalues[key]['M'] = int(mvalues[key]['M'])*int(mvalues[key]['PARALLEL'])
            name_arg = name_arg+'_M'+str(int(mvalues[device_name]["M"]))
            size = 0

        logger.debug(f"Generating lef for {block_name}")
        if isinstance(size, int):
            for key in mvalues:
                assert int(mvalues[device_name]["NFIN"]) == int(mvalues[key]["NFIN"]), f"W should be same for all devices in {name} {mvalues}"
                size_device = int(mvalues[key]["NF"])*int(mvalues[key]["M"])
                size = size + size_device
            no_units = ceil(size / (2*len(mvalues)))  # Factor 2 is due to NF=2 in each unit cell; needs to be generalized
            if any(x in block_name for x in ['DP', '_S']) and floor(sqrt(no_units/3)) >= 1:
                square_y = floor(sqrt(no_units/3))
            else:
                square_y = floor(sqrt(no_units))
            while no_units % square_y != 0:
                square_y -= 1
            yval = square_y
            xval = int(no_units / square_y)

        unit_counts = None
        if 'SCM' in block_name:
            if int(mvalues[device_name_all[0]]["NFIN"])*int(mvalues[device_name_all[0]]["NF"])*int(mvalues[device_name_all[0]]["M"]) != \
                    int(mvalues[device_name_all[1]]["NFIN"])*int(mvalues[device_name_all[1]]["NF"])*int(mvalues[device_name_all[1]]["M"]):
                square_y = 1
                yval = square_y
                xval = int(no_units / square_y)
                unit_counts = {}
                for key in device_name_all:
                    nf = int(mvalues[key]["NF"])
                    mult = int(mvalues[key]["M"])
                    assert (nf * mult) % 2 == 0, f"NF*M must be even for grouped MOS device {key}:{mvalues[key]} in {name}"
                    unit_counts[key] = (nf * mult) // 2

        block_args = {
            'primitive': generator_name,
            'value': mvalues[device_name]["NFIN"],
            'x_cells': xval,
            'y_cells': yval,
            'parameters': mvalues
        }
        if unit_counts:
            block_args['parameters']['unit_counts'] = unit_counts
        if stack > 1:
            block_args['stack'] = stack
        if vt:
            block_args['vt_type'] = vt[0]
        max_y_cells = maximum_one_sided_body_tap_rows(
            design_config["max_diffusion_to_body_tap_nm"],
            design_config["mos_unit_height_fins"],
            design_config["Fin_pitch"],
        )
        add_primitive(
            primitives,
            block_name,
            block_args,
            max_y_cells=max_y_cells,
        )
    return True
