"""Generate explanations.json for Amateurfunk Trainer."""
import json, re, math

with open("PruefungsfragenZIP/fragenkatalog3b.json", "r", encoding="utf-8") as f:
    data = json.load(f)

def flatten(items):
    result = []
    for item in items:
        if "number" in item:
            result.append(item)
        if "questions" in item:
            result.extend(flatten(item["questions"]))
        if "sections" in item:
            result.extend(flatten(item["sections"]))
    return result

questions = flatten(data.get("sections", []))

def pv(s):
    """Parse value with unit like '50 Ohm',  '22 nF' -> (value, unit_str)"""
    s = s.strip()
    # German format: dots are thousand separators, comma is decimal
    s = s.replace("\u03bc", "u").replace("\u00b5", "u")
    # Remove thousand separators (dot followed by 3 digits, not at end)
    s = re.sub(r'\.(\d{3})(?!\d)', r'\1', s)
    s = s.replace(",", ".")
    m = re.match(r"([\d.]+)\s*([pnumkM]?[AVW\u03a9\u2126FHz]?)", s)
    if not m or not re.match(r"\d", m.group(1)): return None, s
    v = float(m.group(1))
    pref = m.group(2)[0] if m.group(2) else ""
    mul = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3, "": 1, "k": 1e3, "M": 1e6}
    return v * mul.get(pref, 1), m.group(2)

def fmt(v, unit="", sep=","):
    """Format value with  prefix."""
    if v == 0: return f"0{unit}"
    for mul, label in [(1e12, "p"), (1e9, "n"), (1e6, "u"), (1e3, "m"), (1, ""),
                       (1e-3, "k"), (1e-6, "M")]:
        if abs(v) >= mul * 0.995 or (mul == 1 and abs(v) < 1):
            val = v / mul
            s = f"{val:.3g}"
            s = s.replace(".", sep)
            return s + " " + label + unit
    return f"{v:.3g}".replace(".", sep) + " " + unit

explanations = {}

# --- Manual explanations for specific questions ---
explanations.update({
    "ED118": (
        "Alle Werte in dieselbe Einheit umrechnen:\n"
        "- 22 nF = 22000 pF\n"
        "- 0,033 \u03bcF = 33000 pF\n"
        "- 15000 pF = 15000 pF\n\n"
        "Bei Parallelschaltung addieren sich die Kapazit\u00e4ten:\n"
        "C_ges = C1 + C2 + C3\n"
        "= 22 nF + 33 nF + 15 nF = 70 nF = 0,070 \u03bcF"
    ),
    "NB303": (
        "Formel: Wellenl\u00e4nge lambda = c / f\n"
        "c = 300 000 000 m/s (Lichtgeschwindigkeit)\n"
        "f = 433,500 MHz = 433.500.000 Hz\n\n"
        "lambda = 300.000.000 / 433.500.000 = 0,692 m = 69,2 cm"
    ),
})

def gen(q):
    """Auto-generate explanation."""
    text = q["question"]
    answers = [q.get(f"answer_{c}", "") for c in "abcd"]
    correct = q.get("answer_a", "")

    # --- Parallel resistors ---
    if re.search(r"(parallel|Parallelschaltung)", text) and re.search(r"(Widerstand|\u03a9|\u2126|Ohm)", text):
        vals = [v for t in re.findall(r"([\d,.]+\s*[kK]?[\u03a9\u2126]?)", text) if (v := pv(t)[0])]
        if len(vals) >= 2:
            r = 1 / sum(1/v for v in vals)
            parts = " + ".join(f"1/{fmt(v)}" for v in vals)
            return (f"Formel Parallelschaltung von Widerst\u00e4nden:\n"
                    f"1/R_ges = 1/R1 + 1/R2 + ...\n"
                    f"= {parts}\n"
                    f"=> R_ges = {fmt(r, '\u2126')}")

    # --- Parallel capacitors ---
    if re.search(r"(parallel|Parallelschaltung)", text) and re.search(r"(Kapazit\u00e4t|Kondensator|nF|\u03bcF|pF)", text):
        vals = [v for t in re.findall(r"([\d,.]+\s*[pnumkM]?F)", text) if (v := pv(t)[0])]
        if len(vals) >= 2:
            c = sum(vals)
            parts = " + ".join(fmt(v, "F") for v in vals)
            return (f"Bei Parallelschaltung addieren sich Kapazit\u00e4ten:\n"
                    f"C_ges = C1 + C2 + ...\n"
                    f"= {parts} = {fmt(c, 'F')}")

    # --- Wrong answer detection helper ---
    vals = []
    for t in re.findall(r"([\d,.]+\s*[pnumkMkK]?[AV\u03a9\u2126W\u03bcF]?)", text):
        v, _ = pv(t)
        if v: vals.append(v)

    # --- Ohm's law (U, I, R) ---
    has_ohm = re.search(r"(Spannung|Stromst\u00e4rke|Widerstand|Volt|Ampere|Ohm|U\s*=|I\s*=|R\s*=)", text)
    volt = [v for v, t in [(pv(t)[0], t) for t in re.findall(r"([\d,.]+\s*[kKmM]?V)", text)] if v]
    amp = [v for v, t in [(pv(t)[0], t) for t in re.findall(r"([\d,.]+\s*[kKmM]?A)", text)] if v]
    ohm = [v for v, t in [(pv(t)[0], t) for t in re.findall(r"([\d,.]+\s*[kK]?[\u03a9\u2126])", text)] if v]

    # --- Frequency / wavelength ---
    hz_vals = [v for v, t in [(pv(t)[0], t) for t in re.findall(r"([\d,.]+\s*[kKMm]?Hz)", text)] if v]
    meter_vals = [v for v, t in [(pv(t)[0], t) for t in re.findall(r"([\d,.]+\s*m)", text) if "mW" not in t and "mV" not in t and t.strip().endswith("m")] if v]

    if re.search(r"(Wellenl\u00e4nge|lambda|\u03bb)", text) and hz_vals:
        f = hz_vals[0]
        lam = 300e6 / f
        return (f"Formel: lambda = c / f\n"
                f"c = 300.000.000 m/s, f = {fmt(f, 'Hz')}\n"
                f"lambda = {fmt(lam, 'm')}")

    if re.search(r"(Frequenz|frequenz)", text) and meter_vals:
        lam = meter_vals[0]
        f = 300e6 / lam
        return (f"Formel: f = c / lambda\n"
                f"c = 300.000.000 m/s, lambda = {fmt(lam, 'm')}\n"
                f"f = {fmt(f, 'Hz')}")

    # --- Antenna half-wave dipole ---
    if re.search(r"(Antenne|Dipol|lambda/2|\u03bb/2|halbe Wellenl\u00e4nge)", text) and hz_vals:
        f = hz_vals[0]
        lam = 300e6 / f
        dip = lam / 2
        return (f"Formel: lambda = c / f = {fmt(lam, 'm')}\n"
                f"lambda/2-Dipol: L = lambda / 2 = {fmt(dip, 'm')}")

    # --- dB calculations ---
    if "dB" in text:
        return (r"dBm bezieht sich auf 1 mW: P(dBm) = 10 * log10(P / 1 mW)" + "\n"
                r"Faustregeln: +3 dB = Verdopplung, +10 dB = Faktor 10, +20 dB = Faktor 100")

    # --- Power P = U * I ---
    if re.search(r"Leistung", text) and volt and amp:
        p = volt[0] * amp[0]
        return (f"Formel: P = U * I = {fmt(volt[0], 'V')} * {fmt(amp[0], 'A')} = {fmt(p, 'W')}")

    # --- Ohm: U = R * I (given R and I, find U) ---
    if has_ohm and ohm and amp:
        u = ohm[0] * amp[0]
        return (f"Ohm'sches Gesetz: U = R * I\n"
                f"= {fmt(ohm[0], '\u2126')} * {fmt(amp[0], 'A')} = {fmt(u, 'V')}")

    # --- Ohm: R = U / I ---
    if has_ohm and volt and amp:
        r = volt[0] / amp[0]
        return (f"Ohm'sches Gesetz: R = U / I\n"
                f"= {fmt(volt[0], 'V')} / {fmt(amp[0], 'A')} = {fmt(r, '\u2126')}")

    # --- Ohm: I = U / R ---
    if has_ohm and volt and ohm:
        a = volt[0] / ohm[0]
        return (f"Ohm'sches Gesetz: I = U / R\n"
                f"= {fmt(volt[0], 'V')} / {fmt(ohm[0], '\u2126')} = {fmt(a, 'A')}")

    # --- Modulation ---
    if re.search(r"(Modulation|Bandbreite|Seitenband|FM|AM|SSB)", text):
        return ("AM: Bandbreite = 2 * Audio-Frequenz\n"
                "SSB: Bandbreite = Audio-Frequenz\n"
                "FM: Bandbreite = 2 * (Hub + Audio-Frequenz)")

    if re.search(r"(Koaxial|Impedanz|Wellenwiderstand)", text):
        return ("Koaxialkabel haben einen charakteristischen Wellenwiderstand Z.\n"
                "Dieser h\u00e4ngt vom Durchmesserverh\u00e4ltnis und Dielektrikum ab.\n"
                "Zur Vermeidung von Reflexionen muss die Impedanz angepasst sein.")

    if re.search(r"(Transistor|Diode|Halbleiter|Bipolarl|FET|MOSFET|NPN|PNP)", text):
        return ("Halbleiterbauelemente bestehen aus dotiertem Silizium.\n"
                "Transistoren verst\u00e4rken Signale, Dioden lassen Strom nur in einer Richtung.")

    if re.search(r"(Induktivit\u00e4t|Spule|Reaktanz|Blindwiderstand)", text):
        return ("Eine Spule hat einen induktiven Blindwiderstand XL = 2 * pi * f * L.\n"
                "Ein Kondensator hat einen kapazitiven Blindwiderstand XC = 1 / (2 * pi * f * C).")

    return None

for q in questions:
    num = q["number"]
    if num not in explanations:
        exp = gen(q)
        if exp:
            explanations[num] = exp

with open("explanations.json", "w", encoding="utf-8") as f:
    json.dump(explanations, f, indent=2, ensure_ascii=False)

stats = {}
for q in questions:
    c = q["class"]
    stats[c] = stats.get(c, 0) + 1
gt = {}
for q in questions:
    if q["number"] in explanations:
        c = q["class"]
        gt[c] = gt.get(c, 0) + 1
print(f"Explanations: {len(explanations)} / {len(questions)} questions")
for c in ("1", "2", "3"):
    print(f"  Klasse {c}: {gt.get(c, 0)} / {stats.get(c, 0)}")
