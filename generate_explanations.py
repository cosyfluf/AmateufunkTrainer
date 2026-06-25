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
    """Parse value with unit -> (value_in_SI, unit_str)"""
    s = s.strip().replace("\u03bc", "u").replace("\u00b5", "u")
    s = re.sub(r'\.(\d{3})(?!\d)', r'\1', s)  # remove thousand separators
    s = s.replace(",", ".")
    m = re.match(r"([\d.]+)\s*([pnumkMkK]?[VAW\u03a9\u2126FHzS]?)", s)
    if not m or not re.match(r"\d", m.group(1)): return None, s
    v = float(m.group(1))
    pref = m.group(2)[0] if m.group(2) else ""
    mul = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3, "": 1, "k": 1e3, "M": 1e6}
    return v * mul.get(pref, 1), m.group(2)

def fmt(v, unit="", sep=","):
    if v == 0: return f"0 {unit}"
    for mul, label in [(1e12, "p"), (1e9, "n"), (1e6, "u"), (1e3, "m"), (1, ""),
                       (1e-3, "k"), (1e-6, "M")]:
        if abs(v) >= mul * 0.995 or (mul == 1 and abs(v) < 1):
            val = v / mul
            s = f"{val:.3g}".replace(".", sep)
            return s + " " + label + unit
    return f"{v:.3g}".replace(".", sep) + " " + unit

# ---------- topic-specific generic helpers ----------

def topic(tag):
    """Return True if the question matches a topic keyword."""
    return re.search(tag, text, re.I) if isinstance(tag, str) else False

def nums_in_text(pattern):
    """Extract numeric values matching a regex pattern from question+answers."""
    vals = []
    for src in [text] + list(answers):
        for t in re.findall(pattern, src):
            v, _ = pv(t)
            if v: vals.append(v)
    return vals

# ---------- MAIN ----------

explanations = {}

def gen(q):
    global text, answers, correct
    text = q["question"]
    answers = [q.get(f"answer_{c}", "") for c in "abcd"]
    correct = q.get("answer_a", "")

    # ---------- PARALLEL RESISTORS ----------
    if topic(r"(parallel|Parallelschaltung)") and topic(r"(Widerstand|\u03a9|\u2126|Ohm)"):
        vals = [v for t in re.findall(r"([\d,.]+\s*[kK]?[\u03a9\u2126]?)", text) if (v := pv(t)[0])]
        if len(vals) >= 2:
            r = 1 / sum(1/v for v in vals)
            parts = " + ".join(f"1/{fmt(v)}" for v in vals)
            return (f"Formel Parallelschaltung von Widerst\u00e4nden:\n"
                    f"1/R_ges = 1/R1 + 1/R2 + ...\n= {parts}\n=> R_ges = {fmt(r, '\u2126')}")

    # ---------- PARALLEL CAPACITORS ----------
    if topic(r"(parallel|Parallelschaltung)") and topic(r"(Kapazit\u00e4t|Kondensator|nF|\u03bcF|pF)"):
        vals = [v for t in re.findall(r"([\d,.]+\s*[pnumkM]?F)", text) if (v := pv(t)[0])]
        if len(vals) >= 2:
            c = sum(vals)
            parts = " + ".join(fmt(v, "F") for v in vals)
            return (f"Bei Parallelschaltung addieren sich Kapazit\u00e4ten:\n"
                    f"C_ges = C1 + C2 + ...\n= {parts} = {fmt(c, 'F')}")

    # ---------- SERIES RESISTORS ----------
    if topic(r"(Reihenschaltung|in Reihe|Serien|hintereinander)") and topic(r"(Widerstand|\u03a9|\u2126|Ohm)"):
        vals = [v for t in re.findall(r"([\d,.]+\s*[kK]?[\u03a9\u2126]?)", text) if (v := pv(t)[0])]
        if len(vals) >= 2:
            r = sum(vals)
            parts = " + ".join(fmt(v, "\u2126") for v in vals)
            return (f"Bei Reihenschaltung addieren sich Widerst\u00e4nde:\n"
                    f"R_ges = R1 + R2 + ...\n= {parts} = {fmt(r, '\u2126')}")

    # ---------- SERIES CAPACITORS ----------
    if topic(r"(Reihenschaltung|in Reihe|Serien)") and topic(r"(Kapazit\u00e4t|Kondensator|nF|\u03bcF|pF)"):
        vals = [v for t in re.findall(r"([\d,.]+\s*[pnumkM]?F)", text) if (v := pv(t)[0])]
        if len(vals) >= 2:
            c = 1 / sum(1/v for v in vals)
            return (f"Formel Reihenschaltung von Kondensatoren:\n"
                    f"1/C_ges = 1/C1 + 1/C2 + ...\n=> C_ges = {fmt(c, 'F')}")

    # ---------- extract values for further patterns ----------
    volt = [v for v, _ in [(pv(t)[0], t) for t in re.findall(r"([\d,.]+\s*[kKmM]?V)", text)] if v]
    amp = [v for v, _ in [(pv(t)[0], t) for t in re.findall(r"([\d,.]+\s*[kKmMkK]?A)", text)] if v]
    ohm = [v for v, _ in [(pv(t)[0], t) for t in re.findall(r"([\d,.]+\s*[kK]?[\u03a9\u2126])", text)] if v]
    hz = [v for v, _ in [(pv(t)[0], t) for t in re.findall(r"([\d,.]+\s*[kKMm]?Hz)", text)] if v]
    meter = [v for v, _ in [(pv(t)[0], t) for t in re.findall(r"([\d,.]+\s*m)\b", text) if "mW" not in t and "mV" not in t] if v]
    watt = [v for v, _ in [(pv(t)[0], t) for t in re.findall(r"([\d,.]+\s*[kKmM]?W)", text) if "mW" not in t] if v]
    farad = [v for v, _ in [(pv(t)[0], t) for t in re.findall(r"([\d,.]+\s*[pnumkM]?F)", text)] if v]
    henry = [v for v, _ in [(pv(t)[0], t) for t in re.findall(r"([\d,.]+\s*[pnumkM]?H)", text)] if v]
    dbm_vals = [v for v, _ in [(pv(t)[0], t) for t in re.findall(r"([\d,.]+\s*dBm)", text)] if v]

    # Check if any numeric values present
    has_vals = bool(volt or amp or ohm or hz or meter or watt or farad or henry)

    # ---------- OHM'S LAW ----------
    ohms_law = topic(r"(Spannung|Strom(st\u00e4rke)?|Widerstand|Volt|Ampere|Ohm)")

    if ohms_law and ohm and amp:
        u = ohm[0] * amp[0]
        return (f"Ohm'sches Gesetz: U = R * I\n"
                f"= {fmt(ohm[0], '\u2126')} * {fmt(amp[0], 'A')} = {fmt(u, 'V')}")
    if ohms_law and volt and amp:
        r = volt[0] / amp[0]
        return (f"Ohm'sches Gesetz: R = U / I\n"
                f"= {fmt(volt[0], 'V')} / {fmt(amp[0], 'A')} = {fmt(r, '\u2126')}")
    if ohms_law and volt and ohm:
        a = volt[0] / ohm[0]
        return (f"Ohm'sches Gesetz: I = U / R\n"
                f"= {fmt(volt[0], 'V')} / {fmt(ohm[0], '\u2126')} = {fmt(a, 'A')}")

    # ---------- POWER ----------
    if topic("Leistung") and watt and amp:
        u = watt[0] / amp[0]
        return (f"Formel: P = U * I  => U = P / I\n"
                f"= {fmt(watt[0], 'W')} / {fmt(amp[0], 'A')} = {fmt(u, 'V')}")
    if topic("Leistung") and volt and amp:
        p = volt[0] * amp[0]
        return (f"Formel: P = U * I = {fmt(volt[0], 'V')} * {fmt(amp[0], 'A')} = {fmt(p, 'W')}")

    # ---------- FREQUENCY / WAVELENGTH ----------
    if topic(r"(Wellenl\u00e4nge|lambda|\u03bb)") and hz:
        lam = 300e6 / hz[0]
        return (f"lambda = c / f\nc = 300.000.000 m/s\n"
                f"lambda = {fmt(lam, 'm')}")
    if topic(r"Frequenz") and meter:
        f_hz = 300e6 / meter[0]
        return (f"f = c / lambda\nc = 300.000.000 m/s\n"
                f"f = {fmt(f_hz, 'Hz')}")

    # ---------- ANTENNA ----------
    if topic(r"(Antenne|Dipol|\u03bb/2|lambda/2|halbe Wellenl\u00e4nge)") and hz:
        lam = 300e6 / hz[0]
        dip = lam / 2
        return (f"lambda = c / f = {fmt(lam, 'm')}\n"
                f"lambda/2-Dipol: L = lambda / 2 = {fmt(dip, 'm')}")

    # ---------- BATTERY / CAPACITY ----------
    if topic(r"(Akk(u|umulator)?|Batterie|Kapazit\u00e4t.*Ah|mAh|Stromversorgung)"):
        # Look for Ah or mAh values
        ah = nums_in_text(r"([\d,.]+\s*m?Ah)")
        volt_bat = nums_in_text(r"([\d,.]+\s*V)")
        if len(ah) >= 1 and len(volt_bat) >= 1:
            wh = ah[0] * (volt_bat[0] if volt_bat else 12)
            hrs = nums_in_text(r"([\d,.]+\s*h)")
            if hrs:
                i = ah[0] / hrs[0]
                return (f"Kapazit\u00e4t: C = {fmt(ah[0], 'Ah')}\n"
                        f"Strom: I = C / t = {fmt(i, 'A')}\n"
                        f"Energie: W = U * C = {fmt(wh, 'Wh')}")
            return (f"Kapazit\u00e4t: {fmt(ah[0], 'Ah')} bei {fmt(volt_bat[0], 'V')}\n"
                    f"Energie: W = U * C = {fmt(wh, 'Wh')}")
        if topic(r"mAh"):
            return ("Die Kapazit\u00e4t eines Akkus wird in Ah oder mAh angegeben.\n"
                    "1 Ah = 1000 mAh. Energie = Spannung * Kapazit\u00e4t.")

    # ---------- dB ----------
    if topic("dB") and dbm_vals:
        # Convert dBm to mW
        mw = 10 ** (dbm_vals[0] / 10)
        return (f"dBm -> mW: P = 10^(dBm/10) mW\n"
                f"= 10^({fmt(dbm_vals[0], 'dBm')}/10) mW = {fmt(mw, 'mW')}\n"
                f"Faustregeln: 0 dBm = 1 mW, +3 dB = doppelt, +10 dB = Faktor 10")

    if topic("dB"):
        return ("dB ist ein Verh\u00e4ltnis: dB = 10 * log10(P2/P1)\n"
                "dBm bezieht sich auf 1 mW.\n"
                "Faustregeln: +3 dB = doppelt, -3 dB = halb, +10 dB = Faktor 10")

    # ---------- MODULATION ----------
    if topic(r"(Modulation|FM|AM|SSB| Seitenband)"):
        if topic("FM"):
            return ("FM (Frequenzmodulation):\n"
                    "Bandbreite = 2 * (Frequenzhub + Modulationsfrequenz)\n"
                    "Vorteile: unempfindlich gegen Amplitudenst\u00f6rungen")
        if topic("AM"):
            return ("AM (Amplitudenmodulation):\n"
                    "Bandbreite = 2 * Modulationsfrequenz\n"
                    "Tr\u00e4ger + 2 Seitenb\u00e4nder")
        if topic("SSB"):
            return ("SSB (Einseitenband):\n"
                    "Nur ein Seitenband wird \u00fcbertragen.\n"
                    "Bandbreite = Modulationsfrequenz\n"
                    "Vorteil: platzsparend, leistungseffizient")
        return ("Modulationsarten:\n"
                "AM: Tr\u00e4ger + 2 Seitenb\u00e4nder, Bandbreite = 2 * f_mod\n"
                "SSB: 1 Seitenband, Bandbreite = f_mod\n"
                "FM: Bandbreite = 2 * (Delta_f + f_mod)")

    # ---------- RESONANCE LC ----------
    if topic(r"(Resonanz|Schwingkreis|Eigenfrequenz)") and (henry or farad):
        if len(henry) >= 1 and len(farad) >= 1:
            fres = 1 / (2 * math.pi * math.sqrt(henry[0] * farad[0]))
            return (f"Resonanzfrequenz: f = 1 / (2*pi*sqrt(L*C))\n"
                    f"L = {fmt(henry[0], 'H')}, C = {fmt(farad[0], 'F')}\n"
                    f"f = {fmt(fres, 'Hz')}")
        return ("Resonanzfrequenz eines LC-Schwingkreises:\n"
                "f = 1 / (2*pi * sqrt(L * C))")

    # ---------- BANDPASS / FILTER ----------
    if topic(r"(Filter|Tiefpass|Hochpass|Bandpass|Bandsperre)"):
        return ("Tiefpass: l\u00e4sst tiefe Frequenzen passiert, sperrt hohe\n"
                "Hochpass: l\u00e4sst hohe Frequenzen passiert, sperrt tiefe\n"
                "Bandpass: l\u00e4sst einen Frequenzbereich passiert\n"
                "Grenzfrequenz: f_g = 1 / (2*pi*R*C)")

    # ---------- TRANSFORMER ----------
    if topic(r"(Transformator|\u00dcbertrager|Trafo|Windungszahl)"):
        windings = nums_in_text(r"([\d,.]+\s*[Ww]indungen|\d+)")
        volt_trafo = nums_in_text(r"([\d,.]+\s*V)")
        if len(windings) >= 2:
            ratio = windings[0] / windings[1]
            return (f"\u00dcbersetzungsverh\u00e4ltnis: u = N1/N2 = {fmt(ratio)}\n"
                    f"Spannungen: U1/U2 = N1/N2\n"
                    f"Str\u00f6me: I1/I2 = N2/N1")
        return ("Transformator: U1/U2 = N1/N2 = I2/I1\n"
                "Die Windungszahl bestimmt das Spannungs-/Stromverh\u00e4ltnis.")

    # ---------- TRANSMISSION LINE / COAX ----------
    if topic(r"(Koaxial|Impedanz|Wellenwiderstand|Leitung|Kabel)"):
        return ("Der Wellenwiderstand Z eines Koaxialkabels h\u00e4ngt ab von:\n"
                "- Durchmesser Innenleiter / Au\u00dfenleiter\n"
                "- Dielektrikum (Permittivit\u00e4t)\n"
                "Impedanzanpassung vermeidet Reflexionen.")

    # ---------- SEMICONDUCTOR ----------
    if topic(r"(Transistor|Diode|Halbleiter|Bipolar|FET|MOSFET|NPN|PNP|Thyristor|Triac)"):
        return ("Halbleiter: dotiertes Silizium (n- oder p-dotiert)\n"
                "Diode: l\u00e4sst Strom nur in einer Richtung\n"
                "Transistor: verst\u00e4rkt Signale (Bipolar: I_C = B * I_B)\n"
                "FET: spannungsgesteuert, hoher Eingangswiderstand")

    # ---------- REACTANCE ----------
    if topic(r"(Induktivit\u00e4t|Spule|Reaktanz|Blindwiderstand)"):
        if henry:
            if hz:
                xl = 2 * math.pi * hz[0] * henry[0]
                return (f"Induktiver Blindwiderstand: XL = 2*pi*f*L\n"
                        f"= 2*pi*{fmt(hz[0], 'Hz')}*{fmt(henry[0], 'H')} = {fmt(xl, '\u2126')}")
            return ("XL = 2 * pi * f * L\nXC = 1 / (2 * pi * f * C)")
        if farad and hz:
            xc = 1 / (2 * math.pi * hz[0] * farad[0])
            return (f"Kapazitiver Blindwiderstand: XC = 1 / (2*pi*f*C)\n"
                    f"= 1 / (2*pi*{fmt(hz[0], 'Hz')}*{fmt(farad[0], 'F')}) = {fmt(xc, '\u2126')}")
        return ("Blindwiderstand: XL = 2*pi*f*L (Spule), XC = 1/(2*pi*f*C) (Kondensator)")

    # ---------- SWR / REFLECTION ----------
    if topic(r"(SWR|VSWR|Reflexionsfaktor|stehende Welle|Anpassung)"):
        return ("SWR (Stehwellenverh\u00e4ltnis): SWR = (1+|r|)/(1-|r|)\n"
                "r = (Z_Last - Z_Leitung) / (Z_Last + Z_Leitung)\n"
                "SWR = 1 = ideale Anpassung, SWR > 1 = Fehlanpassung")

    # ---------- FREQUENCY BANDS ----------
    if topic(r"(Frequenzband|Kurzwell|Langwelle|Mittelwelle|UKW|KW|MW|LW|VHF|UHF|HF|160m|80m|40m|20m|15m|10m|2m|70cm)"):
        return ("Frequenzb\u00e4nder:\n"
                "LF (Langwelle): 30-300 kHz\n"
                "MF (Mittelwelle): 300-3000 kHz\n"
                "HF (Kurzwelle): 3-30 MHz\n"
                "VHF (UKW): 30-300 MHz\n"
                "UHF: 300-3000 MHz\n"
                "Amateurfunkb\u00e4nder: 160m (1,8 MHz), 80m (3,5 MHz), 40m (7 MHz),\n"
                "20m (14 MHz), 15m (21 MHz), 10m (28 MHz), 2m (144 MHz), 70cm (430 MHz)")

    # ---------- PROPAGATION ----------
    if topic(r"(Ausbreitung|Propagation|Fading|Skip|Raumwelle|Bodenwelle|Sporadic|Troposph)"):
        return ("Ausbreitungsarten:\n"
                "Bodenwelle: bis ca. 100 km\n"
                "Raumwelle: Reflexion an der Ionosph\u00e4re (Kurzwelle)\n"
                "Sichtverbindung: UKW und h\u00f6her (VHF/UHF)\n"
                "Troposph\u00e4rische \u00dcberreichweite: Temperaturinversion")

    # ---------- EMC / HARMONICS ----------
    if topic(r"(EMV|Harmonische|Oberwelle|St\u00f6rung|Entst\u00f6r|Filter)"):
        return ("EMV (elektromagnetische Vertr\u00e4glichkeit):\n"
                "Oberwellen sind Vielfache der Grundfrequenz\n"
                "Tiefpassfilter am Ausgang reduzieren Oberwellen\n"
                "Schirmung und Entst\u00f6rung sind wichtig f\u00fcr Zulassung")

    # ---------- SAFETY ----------
    if topic(r"(Sicherheit|Schutz|Ber\u00fchrung|Gefahr|Blitz|Erdung|FI|Schutzleiter)"):
        return ("Sicherheitsma\u00dfnahmen:\n"
                "Schutzleiter (PE) verhindert Ber\u00fchrungsspannungen\n"
                "FI-Schutzschalter erkennt Fehlerstr\u00f6me\n"
                "Blitzschutz: \u00dcberspannungsableiter, Erdung\n"
                "Trennstellen zur sicheren Trennung von Antenne und Ger\u00e4t")

    # ---------- OSCILLATOR ----------
    if topic(r"(Oszillator|Quarz|PLL|VFO|Schwingung|Frequenzerzeug)"):
        return ("Oszillatoren erzeugen Sinus-/Rechteckschwingungen:\n"
                "Quarzoszillator: sehr stabil, feste Frequenz\n"
                "VFO (Oszillator): durchstimmbar (PLL, DDS)\n"
                "PLL (Phase-Locked Loop): stabil und durchstimmbar")

    # ---------- MIXER ----------
    if topic(r"(Mischer|Mischstufe|Multiplizierer|Zwischenfrequenz|ZF)"):
        return ("Mischer erzeugen Summen- und Differenzfrequenzen:\n"
                "f_aus = |f1 +/- f2|\n"
                "Zwischenfrequenz (ZF): feste Frequenz nach dem Mischer\n"
                "f_ZF = f_Osz - f_Eingang oder f_Eingang - f_Osz")

    # ---------- RECEIVER ----------
    if topic(r"(Empf\u00e4nger|Superhet|Sensitivity\?t|Selektivit\?t|Rauschen|NF|ZF-Verst)"):
        return ("Superhet-Empf\u00e4nger: mischt Eingangsfrequenz auf feste ZF\n"
                "Selektivit\u00e4t: F\u00e4higkeit, benachbarte Sender zu trennen\n"
                "Sensitivity\u00e4t: minimale Empfangsfeldst\u00e4rke\n"
                "Rauschzahl: je kleiner, desto empfindlicher")

    # ---------- TRANSMITTER ----------
    if topic(r"(Sender|Sendeleistung|Endstufe|PA|Leistungsverst)"):
        if watt:
            if volt and amp:
                eff = watt[0] / (volt[0] * amp[0]) * 100
                return (f"Wirkungsgrad: eta = P_ab / P_zu * 100%\n"
                        f"= {fmt(watt[0], 'W')} / ({fmt(volt[0], 'V')} * {fmt(amp[0], 'A')}) * 100%\n"
                        f"= {eff:.1f}%")
            return ("Der Wirkungsgrad eines Senders:\n"
                    "eta = P_ab (HF) / P_zu (DC)\n"
                    "Klassen: A (25-50%), B (50-65%), C (65-80%)")
        return ("Sender-Endstufen:\n"
                "Klasse A: geringer Wirkungsgrad, lineare Verst\u00e4rkung\n"
                "Klasse C: hoher Wirkungsgrad, nichtlinear\n"
                "Oberwellen m\u00fcssen durch Tiefpass gefiltert werden")

    # ---------- ANTENNA GAIN ----------
    if topic(r"(Antennengewinn|dBi|dBd|Richtwirkung|Yagi|Halbraum)"):
        return ("Antennengewinn:\n"
                "dBi: Gewinn gegen\u00fcber Isotopstrahler (Kugel)\n"
                "dBd: Gewinn gegen\u00fcber lambda/2-Dipol (0 dBd = 2,15 dBi)\n"
                "Yagi-Antenne: h\u00f6herer Gewinn durch Direktor/Reflektor")

    # ---------- DIGITAL MODES ----------
    if topic(r"(digital|RTTY|PSK|FT8|CW|Morse|Packet|AX\\.25|DMR|DSTAR|C4FM)"):
        return ("Digitale Betriebsarten:\n"
                "CW (Morse): einfachste digitale Modulation (EIN/AUS)\n"
                "RTTY: Frequenzumtastung (FSK)\n"
                "PSK: Phasenumtastung\n"
                "FT8: extrem schwache Signale, 15s-Zeitraster\n"
                "DMR/D-STAR/C4FM: digitale Sprach\u00fcbertragung")

    # ---------- CALLSIGN / LICENSING ----------
    if topic(r"(Rufzeichen|Landeskenner|DM|DL|DK|DO|DB|Pr\u00e4fix|Suffix)"):
        return ("Deutsche Rufzeichen:\n"
                "DA-DR: Deutschland\n"
                "DL: Standardrufzeichenklasse A\n"
                "DO: Klasse E (Einsteiger)\n"
                "DN: Klasse N (Novice)\n"
                "Das Suffix ist individuell, das Pr\u00e4fix zeigt Klasse/Bezirk")

    # ---------- Q-Codes / Abbreviations ----------
    if topic(r"(QTH|QRM|QRN|QSO|QSL|QRP|QRO|QSY|QRZ)"):
        return ("Q-Codes:\n"
                "QTH: Standort\n"
                "QRM: k\u00fcnstliche St\u00f6rungen\n"
                "QRN: atmosph\u00e4rische St\u00f6rungen\n"
                "QSO: Verbindung\n"
                "QSL: Best\u00e4tigung\n"
                "QRP: geringe Sendeleistung\n"
                "QRO: hohe Sendeleistung\n"
                "QSY: Frequenzwechsel\n"
                "QRZ: wer ruft?")

    # ---------- FEEDLINE / CONNECTOR ----------
    if topic(r"(Stecker|PL\b|N-\u00ad|SMA|BNC|Crimp|L\u00f6ten|Antennenstecker)"):
        return ("H\u00e4ufige Steckertypen:\n"
                "PL-259 (UHF): bis 300 MHz, f\u00fcr \u00e4ltere Ger\u00e4te\n"
                "N-Stecker: bis 10 GHz, wasserdicht\n"
                "SMA: bis 18 GHz, f\u00fcr kleine Ger\u00e4te\n"
                "BNC: bis 4 GHz, Schnellverschluss\n"
                "Crimp: Quetschverbindung ohne L\u00f6ten")

    # ---------- TIME CONSTANT RC ----------
    if topic(r"(Zeitkonstante|tau|RC-Glied|Ladezeit|Entladezeit)") and ohm and farad:
        tau = ohm[0] * farad[0]
        return (f"Zeitkonstante: tau = R * C\n"
                f"= {fmt(ohm[0], '\u2126')} * {fmt(farad[0], 'F')} = {fmt(tau, 's')}\n"
                f"Nach 1*tau: 63% geladen/entladen\n"
                f"Nach 5*tau: nahezu vollst\u00e4ndig ({fmt(5*tau, 's')})")

    # ---------- Generic fallback ----------
    if has_vals:
        return ("Siehe richtige Antwort. Hinweise:\n"
                "Einheiten immer umrechnen (nF <-> pF, MHz <-> Hz etc.)\n"
                "Formeln aus den entsprechenden Themenbereichen anwenden.")

    return None

# --- Process all questions ---
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
