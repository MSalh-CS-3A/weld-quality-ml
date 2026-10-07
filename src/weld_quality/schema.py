"""Documented raw schema and analysis blocks; no target is adopted here."""

WT_PERCENT = """carbon silicon manganese sulphur phosphorus nickel chromium
molybdenum vanadium copper cobalt tungsten""".split()
PPM = "oxygen titanium nitrogen aluminium boron niobium tin arsenic antimony".split()
MICROSTRUCTURE = """primary_ferrite ferrite_second_phase acicular_ferrite
martensite ferrite_carbide_aggregate""".split()
CATEGORICAL = ["current_type", "electrode_polarity", "weld_type"]
TENSILE = ["yield_strength", "ultimate_tensile_strength", "elongation", "reduction_area"]
PROPERTIES = TENSILE + ["charpy_temperature", "charpy_toughness", "hardness", "fatt_50"]
CORE_INPUTS = [
    "carbon", "silicon", "manganese", "sulphur", "phosphorus", "current",
    "voltage", "heat_input", "interpass_temperature", "pwht_temperature", "pwht_time",
]
EXTENDED_INPUTS = CORE_INPUTS + [
    "oxygen", "nitrogen", "nickel", "chromium", "molybdenum", "vanadium",
    "copper", "titanium", "aluminium", "boron", "niobium",
]
INPUT_COLUMNS = WT_PERCENT + PPM + CORE_INPUTS[5:]
COLUMNS = WT_PERCENT + PPM + [
    "current", "voltage", "current_type", "electrode_polarity", "heat_input",
    "interpass_temperature", "weld_type", "pwht_temperature", "pwht_time",
] + PROPERTIES + MICROSTRUCTURE + ["weld_id"]
UNITS = {
    **dict.fromkeys(WT_PERCENT, "wt%"),
    **dict.fromkeys(PPM, "ppm by weight"),
    **dict.fromkeys(MICROSTRUCTURE, "%"),
    "current": "A", "voltage": "V", "heat_input": "kJ/mm",
    "interpass_temperature": "°C", "pwht_temperature": "°C", "pwht_time": "h",
    "yield_strength": "MPa", "ultimate_tensile_strength": "MPa",
    "elongation": "%", "reduction_area": "%", "charpy_temperature": "°C",
    "charpy_toughness": "J", "hardness": "kg/mm² (documented; protocol unresolved)",
    "fatt_50": "not specified",
}
NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
MISSING_TOKENS = ["N", "NA", "na", "NaN", "nan", "?", ""]


def physical_bounds(column):
    """Broad admissibility bounds, not inferred ranges or domain validation."""
    if column in WT_PERCENT + MICROSTRUCTURE + ["elongation", "reduction_area"]:
        return 0.0, 100.0
    if column in PPM:
        return 0.0, 1_000_000.0
    if column in ["interpass_temperature", "pwht_temperature", "charpy_temperature"]:
        return -273.15, float("inf")
    if column == "fatt_50":
        return -float("inf"), float("inf")
    return 0.0, float("inf")
