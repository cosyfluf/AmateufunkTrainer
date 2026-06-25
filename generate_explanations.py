"""Generate explanations.json for Amateurfunk Trainer.
Uses section-path mapping so explanations match the actual question topic."""
import json, re, math

with open("PruefungsfragenZIP/fragenkatalog3b.json", "r", encoding="utf-8") as f:
    data = json.load(f)

def asciify(s):
    rep = {"\u00e4": "ae", "\u00f6": "oe", "\u00fc": "ue", "\u00df": "ss",
           "\u00c4": "Ae", "\u00d6": "Oe", "\u00dc": "Ue",
           "\u03a9": "Ohm", "\u2126": "Ohm", "\u03bc": "u", "\u00b5": "u",
           "\u03bb": "lambda", "\u03c0": "pi", "\u03b7": "eta", "\u03c4": "tau",
           "\u03b3": "gamma", "\u03b5": "epsilon", "\u03b4": "delta",
           "\u03c6": "phi", "\u03d5": "phi", "\u03b8": "theta",
           "\u03b1": "alpha", "\u03b2": "beta", "\u00b0": " Grad",
           "\u2192": "->"}
    for old, new in rep.items():
        s = s.replace(old, new)
    return s

# ---- Build section-path map ----
def build_path_map(items, path=None):
    if path is None: path = []
    result = {}
    for item in items:
        new_path = path + ([asciify(item["title"])] if "title" in item else [])
        if "number" in item: result[item["number"]] = new_path
        if "questions" in item: result.update(build_path_map(item["questions"], new_path))
        if "sections" in item: result.update(build_path_map(item["sections"], new_path))
    return result

def flatten(items):
    r = []
    for item in items:
        if "number" in item: r.append(item)
        if "questions" in item: r.extend(flatten(item["questions"]))
        if "sections" in item: r.extend(flatten(item["sections"]))
    return r

sections = data.get("sections", [])
path_map = build_path_map(sections)
questions = flatten(sections)
question_map = {q["number"]: q for q in questions}

# ---- Helper ----
def pv(s):
    """Parse value with unit -> (value_in_SI, unit_str)"""
    s = s.strip().replace("\u03bc", "u").replace("\u00b5", "u")
    s = re.sub(r'\.(\d{3})(?!\d)', r'\1', s)
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
            return f"{val:.3g}".replace(".", sep) + " " + label + unit
    return f"{v:.3g}".replace(".", sep) + " " + unit

# ---- Extract values from a question ----
def get_vals(q):
    text = q["question"]
    answers = [q.get(f"answer_{c}", "") for c in "abcd"]
    all_text = text + " " + " ".join(answers)
    def nums(pattern):
        vals = []
        for t in re.findall(pattern, all_text):
            v, _ = pv(t)
            if v: vals.append(v)
        return vals
    ohm_vals = nums(r"([\d,.]+\s*[kK]?[\u03a9\u2126])")
    volt_vals = nums(r"([\d,.]+\s*[kKmM]?V)")
    amp_vals = nums(r"([\d,.]+\s*[kKmMkK]?A)")
    watt_vals = nums(r"([\d,.]+\s*[kKmM]?W)")
    hz_vals = nums(r"([\d,.]+\s*[kKMm]?Hz)")
    farad_vals = nums(r"([\d,.]+\s*[pnumkM]?F)")
    henry_vals = nums(r"([\d,.]+\s*[pnumkM]?H)")
    meter_vals = nums(r"([\d,.]+\s*m)\b")
    return ohm_vals, volt_vals, amp_vals, watt_vals, hz_vals, farad_vals, henry_vals, meter_vals

# ---- Section path -> explanation mapping ----
# Keys are tuples of path substrings that ALL must appear in the section path.
# The first matching key wins.

EXPLANATIONS = {}

# ===== TECHNISCHE KENNTNISSE =====

# -- Groessen und Einheiten --
EXPLANATIONS[("Groessen und Einheiten",)] = (
    "Wichtige Einheiten-Vorsaetze (Vorsatz = Faktor):\n"
    "p (pico) = 10^-12, n (nano) = 10^-9, u (micro) = 10^-6\n"
    "m (milli) = 10^-3, k (kilo) = 10^3, M (Mega) = 10^6, G (Giga) = 10^9\n"
    "Umrechnung: 1 MHz = 1000 kHz, 1 A = 1000 mA, 1 V = 1000 mV\n"
    "1 pF = 10^-12 F, 1 nF = 10^-9 F, 1 uF = 10^-6 F\n"
    "Grundgroessen: Spannung U in V, Strom I in A, Widerstand R in Ohm\n"
    "Leistung P in W, Frequenz f in Hz, Kapazitaet C in F, Induktivitaet L in H"
)

# -- Allgemeine mathematische Grundkenntnisse --
EXPLANATIONS[("Allgemeine mathematische Grundkenntnisse",)] = (
    "Grundlegende mathematische Operationen fuer den Amateurfunk:\n"
    "Dreisatz, Prozentrechnung, Bruchrechnung, Potenzen\n"
    "Wissenschaftliche Schreibweise: 1,5 * 10^6 = 1.500.000\n"
    "Umrechnen von Einheiten: Vorsaetze wie kilo, Mega, milli, micro\n"
    "Formeln umstellen: U = R*I -> R = U/I, I = U/R\n"
    "Logarithmen: dB = 10 * log10(P2/P1), Neper fuer Spaennungsverhaeltnisse"
)

# -- Binäres Zahlensystem --
EXPLANATIONS[("Binaeres Zahlensystem",)] = (
    "Binaer (Dualsystem): Basis 2, Ziffern 0 und 1.\n"
    "Umrechnung binaer -> dezimal: Stellen mit 2^Position multiplizieren\n"
    "Beispiel: 1101 = 1*8 + 1*4 + 0*2 + 1*1 = 13\n"
    "Byte = 8 Bit, Wertebereich 0-255 (00-FF hex)\n"
    "Hexadezimal: Basis 16, Ziffern 0-9 und A-F"
)

# -- Leiter, Halbleiter und Isolator --
EXPLANATIONS[("Leiter, Halbleiter und Isolator",)] = (
    "Leiter: Metalle (Cu, Ag, Au), viele freie Elektronen, geringer Widerstand\n"
    "Halbleiter: Si, Ge, GaAs – Leitfaehigkeit durch Dotierung steuerbar\n"
    "Isolator: Kunststoff, Glas, Keramik – sehr hoher Widerstand\n"
    "Dotierung: n-dotiert (ueberschuesselektronen) oder p-dotiert (Loecher)\n"
    "Temperatur: bei Metallen steigt R mit T, bei Halbleitern sinkt R mit T"
)

# -- Strom- und Spannungsquellen --
EXPLANATIONS[("Strom- und Spannungsquellen",)] = (
    "Spannungsquelle: liefert konstante Spannung (Batterie, Netzgeraet)\n"
    "Stromquelle: liefert konstanten Strom unabhaengig von der Last\n"
    "Innenwiderstand: ideale Spannungsquelle Ri=0 Ohm, reale haben Ri>0\n"
    "Kurzschlussstrom: Ik = Uq / Ri bei Belastung mit Ra=0\n"
    "Leerlaufspannung: U0 = Uq an den Klemmen ohne Last"
)

# -- Elektrisches Feld --
EXPLANATIONS[("Elektrisches Feld",)] = (
    "Elektrisches Feld E = U / d (Spannung / Abstand)\n"
    "Feldstaerke in V/m. Kondensator: C = epsilon * A / d\n"
    "Dielektrikum: erhoeht die Kapazitaet (epsilon_r > 1)\n"
    "Durchschlag: bei zu hoher Feldstaerke (Ueberschlag, Funke)"
)

# -- Magnetisches Feld --
EXPLANATIONS[("Magnetisches Feld",)] = (
    "Magnetfeld einer Spule: H = N * I / l (Durchflutung / Laenge)\n"
    "Flussdichte B = my * H (Permeabilitaet * Feldstaerke)\n"
    "Induktivitaet L = N^2 * my * A / l\n"
    "Induktion: U_ind = -N * dPhi/dt (Lenzsche Regel)\n"
    "Permeabilitaetszahl my_r: Eisen my_r >> 1, Luft my_r = 1"
)

# -- Elektromagnetisches Feld --
EXPLANATIONS[("Elektromagnetisches Feld",)] = (
    "Elektromagnetische Welle: E- und H-Feld schwingen senkrecht zueinander\n"
    "Ausbreitungsgeschwindigkeit c = 300.000.000 m/s (Lichtgeschwindigkeit)\n"
    "Zusammenhang: c = lambda * f (Wellenlaenge * Frequenz)\n"
    "Wellenwiderstand des Freiraums: Z0 = 120 * pi Ohm = 377 Ohm\n"
    "Polarisation: Ausrichtung des E-Feldes (horizontal, vertikal, zirkular)"
)

# -- Sinusförmige Signale --
EXPLANATIONS[("Sinusfoermige Signale",)] = (
    "Wechselspannung: u(t) = U_peak * sin(2*pi*f*t + phi)\n"
    "Effektivwert (RMS): U_eff = U_peak / sqrt(2) bei Sinus\n"
    "Spitze-Spitze: U_ss = 2 * U_peak\n"
    "Periodendauer: T = 1 / f\n"
    "Kreisfrequenz: omega = 2 * pi * f"
)

# -- Nichtsinusfoermige Signale --
EXPLANATIONS[("Nichtsinusfoermige Signale",)] = (
    "Nichtsinusfoermige Signale: Rechteck, Dreieck, Saegezahn, Impulse\n"
    "Bestehen aus Grundwelle + Oberschwingungen (Fourier-Analyse)\n"
    "Tastverhaeltnis: duty cycle = Impulsdauer / Periodendauer\n"
    "Mittelwert: Gleichanteil des Signals\n"
    "Effektivwert: abhaengig von der Signalform (nicht U_peak/sqrt(2)!)"
)

# -- Ohmsches Gesetz --
EXPLANATIONS[("Ohmsches Gesetz",)] = (
    "Ohmsches Gesetz: U = R * I\n"
    "Formeln: U = R * I, I = U / R, R = U / I\n"
    "Leistung: P = U * I = I^2 * R = U^2 / R\n"
    "Kirchhoff: Knotenregel (Summe I = 0) und Maschenregel (Summe U = 0)"
)

# -- Leistung --
EXPLANATIONS[("Leistung",)] = (
    "Elektrische Leistung: P = U * I (Gleichstrom)\n"
    "Wechselstrom: P = U * I * cos(phi) (Wirkleistung)\n"
    "Scheinleistung: S = U * I (VA), Blindleistung: Q = U * I * sin(phi) (var)\n"
    "Wirkungsgrad: eta = P_ab / P_zu, oft in Prozent\n"
    "PEP (Peak Envelope Power): Spitzenleistung bei Modulation"
)

# -- Ladung und Energie --
EXPLANATIONS[("Ladung und Energie",)] = (
    "Ladung: Q = I * t (Coulomb = Amperesekunde)\n"
    "Energie im Kondensator: W = 0,5 * C * U^2\n"
    "Energie in der Spule: W = 0,5 * L * I^2\n"
    "1 kWh = 3,6 MJ, 1 Ah = 3600 C"
)

# -- Der Stromkreis --
EXPLANATIONS[("Der Stromkreis",)] = (
    "Stromkreis: Spannungsquelle, Verbraucher (Widerstand), Leitung\n"
    "Reihenschaltung: Strom ueberall gleich, Spannung teilt sich auf\n"
    "Parallelschaltung: Spannung ueberall gleich, Strom teilt sich auf\n"
    "Kurzschluss: niederohmige Verbindung, hoher Strom\n"
    "Unterbrechung: Stromkreis offen, kein Stromfluss"
)

# -- Widerstand --
EXPLANATIONS[("Widerstand",)] = (
    "Widerstand R = U / I, Einheit Ohm.\n"
    "Farbcode: 4- oder 5-Ringe fuer Wert + Toleranz\n"
    "Reihe: R_ges = R1 + R2 + ...\n"
    "Parallel: 1/R_ges = 1/R1 + 1/R2 + ...\n"
    "NTC (heisser = kleiner), PTC (heisser = groesser)\n"
    "Belastbarkeit: P_max = I^2 * R, sonst Ueberhitzung"
)

# -- Kondensator --
EXPLANATIONS[("Kondensator",)] = (
    "Kondensator: speichert Ladung, sperrt Gleichstrom\n"
    "Kapazitaet: C = epsilon_r * epsilon_0 * A / d\n"
    "Reihe: 1/C_ges = 1/C1 + 1/C2 + ...\n"
    "Parallel: C_ges = C1 + C2 + ...\n"
    "Blindwiderstand: XC = 1 / (2 * pi * f * C)\n"
    "Je hoeher f, desto kleiner XC (Grund: Kondensator laesst HF passieren)"
)

# -- Spule --
EXPLANATIONS[("Spule",)] = (
    "Spule: speichert Energie im Magnetfeld, laesst Gleichstrom passieren\n"
    "Induktivitaet: L abhaengig von Windungszahl, Kernmaterial, Geometrie\n"
    "Blindwiderstand: XL = 2 * pi * f * L\n"
    "Je hoeher f, desto groesser XL (Sperrwirkung fuer HF)\n"
    "Kern: Luftkern (geringes L), Eisenkern (hohes L, Saettigung)"
)

# -- Uebertrager und Transformatoren --
EXPLANATIONS[("Uebertrager und Transformatoren",)] = (
    "Transformator: U1/U2 = N1/N2 (Spannungsuebersetzung)\n"
    "Stromuebersetzung: I1/I2 = N2/N1 (umgekehrt)\n"
    "Widerstandstransformation: R_prim = (N1/N2)^2 * R_sek\n"
    "Idealer Trafo: P_prim = P_sek (keine Verluste)\n"
    "Kern: Eisen fuer NF, Ferrit fuer HF, Luft fuer sehr hohe Frequenzen"
)

# -- Diode --
EXPLANATIONS[("Diode",)] = (
    "Diode: laesst Strom nur in Durchlassrichtung (p->n)\n"
    "Schwellspannung: Si ca. 0,7 V, Ge ca. 0,3 V, Schottky ca. 0,2 V\n"
    "Z-Diode: in Sperrrichtung betrieben, Konstantspannung (Referenz)\n"
    "LED: Lichtemission, Durchlassspannung farbabhaengig (1,6-3,5 V)\n"
    "Kapazitaetsdiode (Varicap): C aendert sich mit Sperrspannung\n"
    "Gleichrichter: Einweg (1 Diode), Zweiweg-Bruecke (4 Dioden)"
)

# -- Transistor --
EXPLANATIONS[("Transistor",)] = (
    "Bipolartransistor: NPN oder PNP, Stromverstaerkung B = Ic/Ib\n"
    "FET: spannungsgesteuert, hoher Eingangswiderstand\n"
    "MOSFET: isolierte Gate-Elektrode, sehr hoher Eingangswiderstand\n"
    "Arbeitspunkt: Einstellung durch Basis-Vorwiderstand / Spannungsteiler\n"
    "Kennlinien: Ausgangskennlinienfeld (Ic/Uce), Steuerkennlinie (Ic/Ib)\n"
    "Schaltungen: Emitterschaltung (hohe Verstaerkung), Kollektorschaltung"
)

# -- Integrierte Schaltkreise --
EXPLANATIONS[("Integrierte Schaltkreise",)] = (
    "Operationsverstaerker (OPV): Differenzverstaerker mit hoher Verstaerkung\n"
    "Logikgatter: AND, OR, NOT, NAND, NOR, XOR, XNOR\n"
    "Flipflop: 1 Bit Speicher (RS, D, JK, T)\n"
    "Timer NE555: mono- und astabile Kippstufe\n"
    "Spannungsregler: 78xx (positive), 79xx (negative Spannung)"
)

# -- Reihen- und Parallelschaltung --
EXPLANATIONS[("Reihen- und Parallelschaltung von Widerstaenden, Spulen und Kondensatoren",)] = (
    "Widerstaende Reihe: R_ges = R1 + R2 + ...\n"
    "Widerstaende Parallel: 1/R_ges = 1/R1 + 1/R2 + ...\n"
    "Kondensatoren Reihe: 1/C_ges = 1/C1 + 1/C2 + ...\n"
    "Kondensatoren Parallel: C_ges = C1 + C2 + ...\n"
    "Spulen Reihe: L_ges = L1 + L2 + ...\n"
    "Spulen Parallel: 1/L_ges = 1/L1 + 1/L2 + ..."
)

# -- Schwingkreise und Filter --
EXPLANATIONS[("Schwingkreise und Filter",)] = (
    "LC-Schwingkreis: Resonanz bei f = 1 / (2*pi*sqrt(L*C))\n"
    "Parallelschwingkreis: hohe Impedanz bei Resonanz (Sperrkreis)\n"
    "Reihenschwingkreis: niedrige Impedanz bei Resonanz (Saugkreis)\n"
    "Guete Q: je hoeher, desto schmalbandiger\n"
    "Tiefpass: laesst tiefe Frequenzen passiert, sperrt hohe\n"
    "Hochpass: laesst hohe Frequenzen passiert, sperrt tiefe\n"
    "Bandpass: laesst nur einen Frequenzbereich passiert"
)

# -- Strom- und Spannungsversorgung --
EXPLANATIONS[("Strom- und Spannungsversorgung",)] = (
    "Netzteil: Gleichrichter + Siebkondensator + Spannungsregler\n"
    "Brummspannung: Restwelligkeit nach Gleichrichtung + Siebung\n"
    "Siebung: C, RC-Glied oder LC-Glied glattet die Spannung\n"
    "Schaltnetzteil: hoher Wirkungsgrad, aber moegliche HF-Stoerungen\n"
    "Akku: Kapazitaet in Ah, Energie in Wh = U * Ah\n"
    "LiPo, NiMH, NiCd, Blei: unterschiedliche Zellspannungen und Eigenschaften"
)

# -- Verstaerker --
EXPLANATIONS[("Verstaerker",)] = (
    "Verstaerkung: V = U_aus / U_ein (Spannungsverstaerkung)\n"
    "dB: G = 20 * log10(V) (Spannung) bzw. 10 * log10(P_aus/P_ein) (Leistung)\n"
    "Kennlinie: lineare Verstaerkung bis zur Aussteuerungsgrenze\n"
    "Uebersteuerung: Signal wird verzerrt (Oberwellen, Clipping)\n"
    "Gegenkopplung: reduziert Verstaerkung, verbessert Linearitaet/Bandbreite\n"
    "Rauschzahl: je kleiner, desto rauschaermer"
)

# -- Modulator / Demodulator --
EXPLANATIONS[("Modulator / Demodulator",)] = (
    "Modulator: wandelt NF-Signal in HF-Signal um\n"
    "AM: Traeger + 2 Seitenbaender, Bandbreite = 2 * f_mod\n"
    "SSB: nur ein Seitenband, Bandbreite = f_mod\n"
    "FM: Frequenzhub proportional zur Modulationsspannung\n"
    "Mischer: erzeugt Summen- und Differenzfrequenzen |f1 +/- f2|\n"
    "Produktdetektor: fuer SSB/CW, multipliziert mit lokalem Oscillator"
)

# -- Oszillator --
EXPLANATIONS[("Oszillator",)] = (
    "Oszillator erzeugt Sinus- oder Rechteckschwingung\n"
    "Quarzoszillator: sehr frequenzstabil (piezoelektrischer Effekt)\n"
    "VFO (Variable Frequency Oscillator): durchstimmbar (LC, PLL)\n"
    "PLL (Phase-Locked Loop): Oszillator wird auf Referenz synchronisiert\n"
    "DDS (Direct Digital Synthesis): digitale Frequenzerzeugung, sehr fein"
)

# -- Phasenregelkreise --
EXPLANATIONS[("Phasenregelkreise",)] = (
    "PLL (Phase-Locked Loop): Phasenregelkreis\n"
    "Bestandteile: Phasendetektor, Schleifenfilter, VCO\n"
    "Anwendung: Frequenzsynthese, FM-Demodulation, digitale Taktgenerierung\n"
    "Vorteil: stabile, durchstimmbare Frequenz mit Quarzgenauigkeit"
)

# -- Daempfungsglieder --
EXPLANATIONS[("Daempfungsglieder",)] = (
    "Daempfungsglied (Attenuator): reduziert Signalleistung\n"
    "T-Glied, Pi-Glied: Widerstandsnetzwerke zur definierten Daempfung\n"
    "dB = 10 * log10(P_ein/P_aus)\n"
    "Kaskade: Daempfungen addieren sich in dB\n"
    "Anwendung: Schutz von Messgeraeten, Anpassung von Pegeln"
)

# -- Modulation allgemein --
EXPLANATIONS[("Modulation allgemein",)] = (
    "Modulation: Aufmodulieren des Nutzsignals (NF) auf einen Traeger (HF)\n"
    "Demodulation: Rueckgewinnung des Nutzsignals\n"
    "Analogmodulation: AM, FM, PM\n"
    "Digitalmodulation: ASK, FSK, PSK, QAM\n"
    "Bandbreite abhaengig von Modulationsart und Signalbandbreite"
)

# -- AM, SSB, CW --
EXPLANATIONS[("Amplitudenmodulation AM, SSB, CW",)] = (
    "AM (Amplitudenmodulation): Traeger + 2 Seitenbaender\n"
    "Bandbreite B = 2 * f_mod (z.B. 2 * 3 kHz = 6 kHz)\n"
    "SSB (Einseitenband): nur ein Seitenband, B = f_mod\n"
    "CW (Morse): Traeger ein/aus, Bandbreite sehr schmal (ca. 100 Hz)\n"
    "Vorteil SSB: platzsparend, leistungseffizient gegenueber AM\n"
    "Seitenbandlage: USB oberhalb, LSB unterhalb der Traegerfrequenz"
)

# -- FM/PM --
EXPLANATIONS[("Frequenz- und Phasenmodulation",)] = (
    "FM (Frequenzmodulation): Frequenzhub proportional zur Signalamplitude\n"
    "Bandbreite (Carson): B = 2 * (Delta_f + f_mod)\n"
    "FM-Vorteile: unempfindlich gegen Amplitudenstoerungen\n"
    "NFM (Schmalband-FM): Hub +/- 2,5 kHz, fuer Amateurfunk typisch\n"
    "WFM (Breitband-FM): Hub +/- 75 kHz, fuer Rundfunk\n"
    "PM (Phasenmodulation): Phasenhub proportional zur Signalamplitude"
)

# -- Digitale Uebertragungsverfahren --
EXPLANATIONS[("Digitale Uebertragungsverfahren",)] = (
    "Digitale Betriebsarten:\n"
    "RTTY: FSK (Frequency Shift Keying), 45-300 Baud\n"
    "PSK31: Phasenumtastung, 31,25 Baud, sehr schmalbandig\n"
    "FT8/FT4: 15s/7,5s-Zeitraster, extrem schwache Signale dekodierbar\n"
    "CW (Morse): EIN/AUS-Tastung des Traegers\n"
    "DMR: TDMA-Zeitmultiplex (2 Slots auf einer Frequenz)\n"
    "C4FM: 4-stufige Frequenzmodulation, 9600 Bit/s"
)

# -- Transceiver --
EXPLANATIONS[("Transceiver",)] = (
    "Transceiver (TRX): Kombination aus Sender und Empfaenger\n"
    "Gemeinsame Nutzung von Oszillator, Netzteil, Gehaeuse\n"
    "Simplex: Senden und Empfangen auf gleicher Frequenz\n"
    "Duplex: getrennte Frequenzen fuer Senden/Empfangen (z.B. Relais)\n"
    "Crossband: Senden auf einem Band, Empfang auf anderem Band"
)

# -- Empfaenger --
EXPLANATIONS[("Empfaenger",)] = (
    "Superhet-Empfaenger: mischt HF auf feste Zwischenfrequenz (ZF)\n"
    "Vorteil: hohe Selektivitaet durch feste ZF-Filter\n"
    "Empfindlichkeit: minimale Eingangsspannung fuer verstaendliches Signal\n"
    "Selektivitaet: Trennung benachbarter Sender\n"
    "Rauschzahl: je kleiner, desto geringer das Eigenrauschen\n"
    "Spiegelfrequenz: unerwuenschte zweite Mischung (f_Eingang + 2*f_ZF)"
)

# -- Empfaengerstufen --
EXPLANATIONS[("Empfaengerstufen",)] = (
    "Empfaengerstufen:\n"
    "HF-Verstaerker (Vorstufe): rauscharm, Verstaerkung des Eingangssignals\n"
    "Mischer: HF -> ZF durch Mischung mit lokalem Oszillator\n"
    "ZF-Verstaerker: Hauptverstaerkung und Selektion (Bandpass, Quarzfilter)\n"
    "Demodulator: ZF -> NF (AM/FM/SSB-Demodulation)\n"
    "NF-Verstaerker: Verstaerkung auf Lautsprecherpegel\n"
    "S-Meter: Anzeige der Empfangsfeldstaerke"
)

# -- Sender und Senderstufen --
EXPLANATIONS[("Sender und Senderstufen",)] = (
    "Senderstufen:\n"
    "Oszillator: Erzeugung der Traegerfrequenz\n"
    "Treiberstufe: Verstaerkung auf Zwischenpegel\n"
    "Endstufe (PA): Leistungsverstaerkung auf Sendeleistung\n"
    "Modulator: Aufmodulation des NF-Signals\n"
    "Antennenfilter (LPF): Unterdrueckung von Oberwellen\n"
    "SWR-Schutz: Abschaltung bei Fehlanpassung"
)

# -- Leistungsverstaerker --
EXPLANATIONS[("Leistungsverstaerker",)] = (
    "Leistungsverstaerker (PA): erhoeht die HF-Ausgangsleistung\n"
    "Wirkungsgrad eta = P_ab / P_zu\n"
    "Klasse A: linear, geringer Wirkungsgrad (25-50%)\n"
    "Klasse B: linearer Bereich (50-65%), aber Crossover-Verzerrungen\n"
    "Klasse C: nichtlinear, hoher Wirkungsgrad (65-80%), nur FM/CW\n"
    "Kuehlung: Kuehlkoerper, Luefter notwendig bei hoher Leistung"
)

# -- Konverter und Transverter --
EXPLANATIONS[("Konverter und Transverter",)] = (
    "Konverter: setzt Frequenzbereich um (z.B. 144 -> 28 MHz)\n"
    "Transverter: Konverter + Sende-/Empfangsumschaltung\n"
    "Ermoeglicht Betrieb auf hohen Baendern mit vorhandenem TRX\n"
    "Mischer + Oszillator erzeugen die Frequenzumsetzung"
)

# -- DSP / Digitale Signalverarbeitung --
EXPLANATIONS[("Digitale Signalverarbeitung",)] = (
    "DSP (Digital Signal Processing): Signalverarbeitung im Digitalen\n"
    "ADC/DAC: Analog-Digital- bzw. Digital-Analog-Umsetzer\n"
    "Sampling: Abtastung mit mindestens 2*f_max (Nyquist-Kriterium)\n"
    "Anwendungen: Filter, Demodulation, Rauschunterdrueckung (NR), VOX\n"
    "SDR (Software Defined Radio): Signalverarbeitung weitgehend in Software\n"
    "FFT: schnelle Fourier-Transformation fuer Spektrumanalyse"
)

# -- Remote-Station (Technisch) --
EXPLANATIONS[("Remote-Station",)] = (
    "Remote-Station: Amateurfunkstelle wird per Internet fernbedient\n"
    "Voraussetzung: zuverlaessige Steuerung und Sicherheitsmassnahmen\n"
    "Trenneinrichtung zur sicheren Abschaltung bei Fehlern\n"
    "Der Betreiber muss jederzeit eingreifen koennen"
)

# -- Antennen --
EXPLANATIONS[("Antennen",)] = (
    "Antenne: wandelt HF-Leitungswelle in Raumwelle um (und umgekehrt)\n"
    "lambda/2-Dipol: einfachste Antenne, Laenge = lambda/2\n"
    "lambda/4-Vertikal: Viertelwellenantenne, benoetigt Erdnetz (Gegengewicht)\n"
    "Yagi-Antenne: Dipol + Reflektor + Direktor, Richtwirkung\n"
    "Lange Leitung: Amateurband, Laenge Bruchteile von lambda\n"
    "Magnetische Antenne (Loop): klein, aber schmalbandig"
)

# -- Antennenmerkmale --
EXPLANATIONS[("Antennenmerkmale",)] = (
    "Antennengewinn: dBi (gegen Isotopstrahler), dBd (gegen Dipol)\n"
    "0 dBd = 2,15 dBi\n"
    "Richtdiagramm: Darstellung der Abstrahlung ueber Horizontal-/Vertikalwinkel\n"
    "Vor-Rueck-Verhaeltnis (F/B): Daempfung in Rueckrichtung\n"
    "Impedanz: Dipol ca. 73 Ohm, Vertikal ca. 36 Ohm\n"
    "Polarisation: horizontal (Dipol), vertikal (Vertikal), zirkular"
)

# -- Uebertragungsleitungen --
EXPLANATIONS[("Uebertragungsleitungen",)] = (
    "Koaxialkabel: Innenleiter + Abschirmung (Schirm)\n"
    "Wellenwiderstand: typisch 50 Ohm oder 75 Ohm\n"
    "Daempfung: steigt mit Frequenz (Skin-Effekt, Dielektrikumsverluste)\n"
    "RG58, RG213, RG174: verschiedene Daempfungen und Durchmesser\n"
    "Hohlleiter: fuer UKW/SHF, geringe Verluste aber grosser Querschnitt\n"
    "Stehwellenverhaeltnis (SWR): Mass fuer Fehlanpassung"
)

# -- Anpassung, Transformation, Symmetrierung --
EXPLANATIONS[("Anpassung, Transformation, Symmetrierung und Mantelwellen",)] = (
    "Impedanzanpassung: maximale Leistungsuebertragung bei Z_aus = Z_ein\n"
    "SWR = 1: ideale Anpassung, SWR > 1: Fehlanpassung\n"
    "Balun: symmetrisch <-> asymmetrisch (Dipol an Koax)\n"
    "Mantelwellen: unerwuenschte Aussenleiterstroeme, werden durch Drosseln unterdrueckt\n"
    "Transformationsleitung: lambda/4-Transformator (Quartwellentransformator)\n"
    "r = (Z_Last - Z_Leitung) / (Z_Last + Z_Leitung)"
)

# -- Strahlungsleistung --
EXPLANATIONS[("Strahlungsleistung (EIRP und ERP)",)] = (
    "EIRP (Equivalent Isotropic Radiated Power): Leistung gegenueber Isotopstrahler\n"
    "ERP (Effective Radiated Power): Leistung gegenueber lambda/2-Dipol\n"
    "ERP = EIRP - 2,15 dB (EIRP = ERP + 2,15 dB)\n"
    "Berechnung: EIRP = P_Sender + G_Antenne (dBi) - Leitungsdaempfung (dB)\n"
    "Wichtig fuer EMVU-Grenzwerte und Lizenzauflagen"
)

# -- Ionosphaere --
EXPLANATIONS[("Ionosphaere",)] = (
    "Ionosphaere: ionisierte Schichten in 60-400 km Hoehe\n"
    "D-Schicht (60-90 km): tagsueber, dmpft KW-Signale\n"
    "E-Schicht (100-130 km): reflektiert MW, hilft bei KW\n"
    "F-Schicht (200-400 km): wichtigste Schicht fuer KW, tags F1+F2, nachts F2\n"
    "MUF (Maximum Usable Frequency): hoechste nutzbare Frequenz\n"
    "LUF (Lowest Usable Frequency): niedrigste nutzbare Frequenz"
)

# -- Kurzwellenausbreitung --
EXPLANATIONS[("Kurzwellenausbreitung",)] = (
    "KW-Ausbreitung: Raumwelle wird an der Ionosphaere reflektiert\n"
    "Springe: mehrere 100-3000 km pro Sprung\n"
    "Tote Zone: Bereich zwischen Bodenwelle und erstem Reflexionspunkt\n"
    "Sonnenfleckenzyklus (11 Jahre): mehr Sonnenflecken = bessere KW-Ausbreitung\n"
    "Fading: Signalschwankungen durch Phasenueberlagerung mehrerer Wege\n"
    "Sporadic-E: unregelmaessige starke E-Schicht-Ionisation (Sommer)"
)

# -- Wellenausbreitung oberhalb 30 MHz --
EXPLANATIONS[("Wellenausbreitung oberhalb 30 MHz",)] = (
    "VHF/UHF: quasioptische Ausbreitung (Sichtverbindung)\n"
    "Funkhorizont: ca. 4,1 * (sqrt(h1) + sqrt(h2)) (h in m, Reichweite in km)\n"
    "Tropo: Ueberreichweiten durch Temperaturinversionen\n"
    "Aurora: Reflexion an polaren Leuchterscheinungen\n"
    "Sporadic-E auf VHF: bis 144 MHz (selten auch 432 MHz)\n"
    "Meteorscatter: Reflexion an Meteoriten-Ionisationsspuren (kurze Signale)"
)

# -- Messgeraete: Strom/Spannung --
EXPLANATIONS[("Strom- und Spannungsmessgeraete",)] = (
    "Strommessung: Amperemeter in Reihe zum Verbraucher\n"
    "Spannungsmessung: Voltmeter parallel zum Verbraucher\n"
    "Multimeter: kombiniert Strom-, Spannungs- und Widerstandsmessung\n"
    "Innenwiderstand: Voltmeter hochohmig (belastet wenig), Amperemeter niederohmig\n"
    "True RMS: misst Effektivwert nichtsinusfoermiger Signale"
)

# -- VNA --
EXPLANATIONS[("Vektorieller Netzwerk Analysator (VNA)",)] = (
    "VNA: misst komplexe Impedanzen und S-Parameter\n"
    "Reflexionsmessung: SWR, Rueckflussdaempfung\n"
    "Transmissionsmessung: Daempfung, Phasenverschiebung\n"
    "Smith-Diagramm: grafische Darstellung von Impedanzen\n"
    "Kalibrierung: Open/Short/Load vor Messung erforderlich"
)

# -- Oszilloskop --
EXPLANATIONS[("Oszilloskop",)] = (
    "Oszilloskop: zeitraumkurven von Signalen (U(t))\n"
    "Zeitbasis: s/cm oder s/div, bestimmt horizontale Aufloesung\n"
    "Vertikalverstaerkung: V/cm oder V/div\n"
    "Triggerung: stabilisiert das Bild durch Synchronisation\n"
    "Tastkopf (Probe): 1:1 oder 10:1, beeinflusst Eingangsimpedanz\n"
    "FFT-Funktion: Spektrumanalyse des Eingangssignals"
)

# -- SWR-Messgeraet --
EXPLANATIONS[("Stehwellenmessgeraet",)] = (
    "SWR-Meter: misst vorwaerts- und ruecklaufende Leistung\n"
    "SWR = (sqrt(P_vor) + sqrt(P_rueck)) / (sqrt(P_vor) - sqrt(P_rueck))\n"
    "SWR = 1: ideale Anpassung (P_rueck = 0)\n"
    "SWR > 1: Fehlanpassung (Leistung wird reflektiert)\n"
    "Messung: SWR-Meter zwischen Sender und Antenne (oder Dummy Load)"
)

# -- Frequenzmessung --
EXPLANATIONS[("Frequenzmessung",)] = (
    "Frequenzzaehler: digital, misst die Anzahl der Schwingungen pro Torzeit\n"
    "Genauigkeit: abhaengig von Torzeit und Quarzgenauigkeit\n"
    "ppm (parts per million): 1 ppm = 0,0001 % Abweichung\n"
    "OCXO (Oven Controlled Xtal Oscillator): hochstabil durch Temperierung\n"
    "Frequenzteiler: erweitert den Messbereich nach oben"
)

# -- Sonstige Messgeraete --
EXPLANATIONS[("Sonstige Messgeraete und Messmittel",)] = (
    "Dummy Load (kuenstliche Antenne): 50 Ohm Abschlusswiderstand\n"
    "Spektrumanalysator: Darstellung der Signalamplitude ueber Frequenz\n"
    "Leistungsmesser: misst HF-Leistung (thermisch oder diode)\n"
    "Reflektometer: misst vorwaerts-/ruecklaufende Leistung\n"
    "Durchgangspruefung: Pruefung der Leiterbahn-/Kabelverbindung\n"
    "Dipping: Resonanzmessung mit Grid-Dip-Meter"
)

# -- Stoerungen --
EXPLANATIONS[("Stoerungen elektronischer Geraete",)] = (
    "EMV-Stoerungen: koennen ueber Kabel (Leitung) oder Luft (Strahlung) wirken\n"
    "Einstrahlung: HF dringt direkt in ein Geraet ein (fehlende Schirmung)\n"
    "Einstroemung: HF gelangt ueber Leitungen (Netz, Antenne) ins Geraet\n"
    "Massnahmen gegen Stoerungen:\n"
    "  - Ferritkerne auf Kabel\n"
    "  - Schirmung empfindlicher Geraete\n"
    "  - Mantelwellendrosseln\n"
    "  - Tiefpassfilter vor Geraeteingang\n"
    "  - Netzfilter (gegen Leitungsgebundene Stoerungen)"
)

# -- Unerwuenschte Aussendungen --
EXPLANATIONS[("Unerwuenschte Aussendungen",)] = (
    "Harmonische (Oberwellen): ganzzahlige Vielfache der Grundfrequenz\n"
    "Parasitaere Schwingungen: unerwuenschte Eigenschwingungen (HF-Schwingen)\n"
    "Nachbarkanalaussendungen: durch Uebersteuerung oder Intermodulation\n"
    "Unterdrueckung: Tiefpassfilter am Senderausgang, saubere Verstaerkerklasse\n"
    "Zulaessige Grenzwerte fuer unerwuenschte Aussendungen:\n"
    "  nach Frequenzbereich und Kanalbandbreite gestaffelt\n"
    "FT8/JT65: auf saubere Taktung und Bandbegrenzung achten"
)

# -- Stoerfestigkeit --
EXPLANATIONS[("Stoerfestigkeit",)] = (
    "Stoerfestigkeit: Widerstandsfaehigkeit eines Geraets gegen HF-Stoerungen\n"
    "EMV-optimierter Aufbau: Kurze Leitungen, gute Entkopplung\n"
    "Gehaeuseschirmung: geschlossene Metallgehaeuse, Federn an Tueren/Fugen\n"
    "Ferrite: unterdruecken Gleichtaktstoerungen auf Leitungen"
)

# -- Schutz von Personen --
EXPLANATIONS[("Schutz von Personen",)] = (
    "Personenschutz: Grenzwerte fuer elektrische und magnetische Feldstaerken\n"
    "BEMFV: Verordnung ueber das Nachweisverfahren zum Schutz von Personen\n"
    "Sicherheitsabstand: abhaengig von Sendeleistung, Antennengewinn, Frequenz\n"
    "Nahfeld / Fernfeld: unterschiedliche Berechnung von E- und H-Feld\n"
    "Ortsfeste Anlagen: Anzeige bei der BNetzA erforderlich (ab bestimmter Leistung)"
)

# -- Sicherheit --
EXPLANATIONS[("Sicherheit",)] = (
    "Wichtige Sicherheitsmassnahmen bei der Amateurfunkstation:\n"
    "- Schutzleiter (PE) zur Erdung aller Gehaeuse\n"
    "- Erdung von Antennenanlagen (Blitzschutz)\n"
    "- Trennstellen fueur Antennen (galvanische Trennung)\n"
    "- Sicherungen in den Versorgungsleitungen\n"
    "- Netzgeraete erst nach Entladen der Elkos beruehren\n"
    "- FI-Schutzschalter fuer den Gesamtstromkreis empfohlen\n"
    "- VDE-Vorschriften fuer Antennenanlagen beachten\n"
    "Gefahren durch Strom: Kammerflimmern > 30 mA, Verbrennungen, Lichtbogen"
)

# ===== BETRIEBLICHE KENNTNISSE =====

# -- Internationales Buchstabieralphabet --
EXPLANATIONS[("Internationales Buchstabieralphabet",)] = (
    "Internationales Buchstabieralphabet (ICAO/ITU):\n"
    "A=Alpha, B=Bravo, C=Charlie, D=Delta, E=Echo, F=Foxtrot,\n"
    "G=Golf, H=Hotel, I=India, J=Juliett, K=Kilo, L=Lima,\n"
    "M=Mike, N=November, O=Oscar, P=Papa, Q=Quebec, R=Romeo,\n"
    "S=Sierra, T=Tango, U=Uniform, V=Victor, W=Whiskey,\n"
    "X=X-Ray, Y=Yankee, Z=Zulu\n"
    "Zahlen: 0=Zero, 1=One, 2=Two, 3=Three, 4=Four, 5=Five,\n"
    "6=Six, 7=Seven, 8=Eight, 9=Niner"
)

# -- Betriebliche Abkuerzungen --
EXPLANATIONS[("Betriebliche Abkuerzungen",)] = (
    "Wichtige betriebliche Abkuerzungen:\n"
    "CQ: allgemeiner Anruf (seeking any station)\n"
    "DX: entfernte Station (Distant station)\n"
    "TX/RX/TRX: Sender/Empfaenger/Transceiver\n"
    "CW: Morse-Telegrafie\n"
    "BK: Break (Unterbrechung eines Durchgangs)\n"
    "K: Aufforderung zu senden (over)\n"
    "R: Received (verstanden)\n"
    "73: freundliche Gruesse\n"
    "88: Liebe und Kuesse"
)

# -- Q-Gruppen --
EXPLANATIONS[("Q-Gruppen",)] = (
    "Wichtige Q-Codes:\n"
    "QRM: kuenstliche Stoerungen\n"
    "QRN: atmosphaerische Stoerungen\n"
    "QSB: Signalschwankungen (Fading)\n"
    "QSL: Empfangsbestaetigung\n"
    "QSO: Funkverbindung\n"
    "QRP: geringe Sendeleistung\n"
    "QRO: hohe Sendeleistung\n"
    "QRZ: Wer ruft mich?\n"
    "QRT: Sendeschluss\n"
    "QRV: bereit (auf Empfang)\n"
    "QSY: Frequenzwechsel\n"
    "QRX: warten"
)

# -- Frequenzbereiche (BG) --
EXPLANATIONS[("Frequenzbereiche",)] = (
    "Frequenzbereichsbezeichnungen:\n"
    "LF (Langwelle): 30-300 kHz\n"
    "MF (Mittelwelle): 300-3000 kHz\n"
    "HF (Kurzwelle): 3-30 MHz\n"
    "VHF (UKW): 30-300 MHz\n"
    "UHF: 300-3000 MHz\n"
    "SHF: 3-30 GHz\n"
    "Wichtige Amateurfunkbaender:\n"
    "160m (1,8 MHz), 80m (3,5 MHz), 40m (7 MHz), 30m (10 MHz),\n"
    "20m (14 MHz), 15m (21 MHz), 10m (28 MHz),\n"
    "2m (144 MHz), 70cm (430 MHz), 23cm (1,3 GHz)"
)

# -- IARU-Bandplaene --
EXPLANATIONS[("IARU-Bandplaene",)] = (
    "IARU-Bandplan: nationale und regionale Frequenzaufteilung\n"
    "In Deutschland regelt die AFuV die Frequenzbereiche\n"
    "Bandplan-Empfehlungen: welche Betriebsart in welchem Bereich\n"
    "Allgemeine Aufteilung pro Band (Beispiel 2m):\n"
    "144,000-144,150 MHz: CW, schmale Betriebsarten\n"
    "144,150-144,390 MHz: SSB, digitale Betriebsarten\n"
    "144,600-145,800 MHz: FM, Relais (Ablage 600 kHz)\n"
    "145,800-146,000 MHz: Amateurfunksatelliten\n"
    "Bandplan ist nicht rechtsverbindlich, aber internationaler Standard"
)

# -- Rufzeichen --
EXPLANATIONS[("Rufzeichen",)] = (
    "Deutsches Rufzeichensystem:\n"
    "DA-DR Praefix: Deutschland\n"
    "DL: Standard-A-Lizenz\n"
    "DO: Klasse E (Einsteiger)\n"
    "DN: Klasse N (Novice)\n"
    "Klubstationen: DL0xxx, DO0xxx, etc.\n"
    "Sonderrufzeichen: DLxxx (zum Anlass von Veranstaltungen)\n"
    "Das Suffix (Buchstaben nach Zahl) ist individuell"
)

# -- Rufzeichenzusaetze --
EXPLANATIONS[("Rufzeichenzusaetze",)] = (
    "Rufzeichenzusätze:\n"
    "/m: mobile Station (Fahrzeug)\n"
    "/p: portable (tragbare) Station\n"
    "/mm: maritime mobile (Schiff)\n"
    "/am: Luftfahrzeug (Aircraft)\n"
    "/QRP: mit geringer Leistung\n"
    "/P: portable (in Deutschland nicht mehr ueblich, stattdessen /p)\n"
    "Remote: kein eigener Zusatz, aber spezielle Kennzeichnung"
)

# -- Landeskenner --
EXPLANATIONS[("Landeskenner",)] = (
    "Internationale Landeskenner (Praefixe):\n"
    "D: Deutschland (DA-DR), OE: Oesterreich, HB: Schweiz\n"
    "ON: Belgien, PA: Niederlande, OK: Tschechien, SP: Polen\n"
    "DL: Deutschland (Standard), DK: Deutschland (A-Lizenz)\n"
    "F: Frankreich, G: England, I: Italien, SM: Schweden\n"
    "LA: Norwegen, OH: Finnland, OZ: Daenemark, EA: Spanien\n"
    "W/K/N/AA-AL: USA, VE: Kanada, VK: Australien\n"
    "JA: Japan, ZL: Neuseeland, ZS: Suedafrika, PY: Brasilien\n"
    "U: Russland, 4X: Israel, 5B: Zypern, YU: Serbien\n"
    "Prefix-Verzeichnis: in den Radio Regulations (App. S42)"
)

# -- Betriebsabwicklung --
EXPLANATIONS[("Betriebsabwicklung",)] = (
    "Allgemeine Betriebsabwicklung:\n"
    "Standard-Anruf: CQ CQ CQ DE [eigenes Rufzeichen] PSE K\n"
    "Antwort: [Rufzeichen der Gegenstation] DE [eigenes Rufzeichen]\n"
    "Betriebskurzbefehle: QSY (Frequenzwechsel), QRZ? (Wer ruft?)\n"
    "Maidenhead-Locator (QTH-Locator): 6-8-stelliges Raster\n"
    "Geschwindigkeit: dem Gegenueber anpassen (insb. bei Telegrafie)"
)

# -- Signalbeurteilung --
EXPLANATIONS[("Signalbeurteilung",)] = (
    "RST-System (Readability, Strength, Tone):\n"
    "R (Readability): 1-5 (Lesbarkeit: unverstaendlich bis perfekt)\n"
    "S (Strength): 1-9 (Feldstaerke: sehr schwach bis sehr stark)\n"
    "T (Tone): 1-9 (Modulationsqualitaet, nur bei CW)\n"
    "Beispiel: RST 599 = perfekt lesbar, sehr stark, reiner Ton\n"
    "Bei SSB/Teldfonie wird nur RS verwendet (Tone entfaellt)\n"
    "SSTV: Bilduebertragung, eigene Beurteilungskriterien"
)

# -- Contest, Pile-Up, DX-Pedition --
EXPLANATIONS[("Contest, Pile-Up, DX-Pedition und Fuchsjagd",)] = (
    "Contest (Funkwettbewerb): moeglichst viele Verbindungen in bestimmter Zeit\n"
    "Pile-Up: viele Stationen rufen gleichzeitig eine Station\n"
    "DX-Pedition: Expedition in ein seltenes Land\n"
    "Split: Senden und Empfangen auf verschiedenen Frequenzen\n"
    "Log: Austausch von Rapport + laufender Nummer + evtl. Name\n"
    "Fuchsjagd (ARDF): Peilen und Finden versteckter Sender im Gelände"
)

# -- Relais, Baken, Satelliten --
EXPLANATIONS[("Relaisfunkstellen, Baken, Satelliten und Transponder",)] = (
    "Relais (Repeater): automatische Station, empfaengt und sendet gleichzeitig\n"
    "Uplink: Frequenz, auf der zur Relaisstation gesendet wird\n"
    "Downlink: Frequenz, auf der die Relaisstation sendet\n"
    "Ablage (Shift): Abstand zwischen Uplink und Downlink (z.B. 600 kHz bei 2m)\n"
    "CTCSS (Subton): Ton-codierte Schaltung des Relais\n"
    "Bake (Beacon): sendet automatisch Kennung, dient der Ausbreitungsbeobachtung\n"
    "Satelliten (OSCAR): Orbiting Satellite Carrying Amateur Radio\n"
    "Transponder: setzt Uplink-Frequenzbereich in Downlink-Bereich um"
)

# -- Notfunk --
EXPLANATIONS[("Notfunkverkehr und Nachrichtenverkehr bei Naturkatastrophen",)] = (
    "Notfunk: Amateurfunk kann bei Notlagen Leben retten\n"
    "Internationale Notrufe: SOS (-.-.---) in Morse, Mayday in Telefonie\n"
    "Notfunk im Amateurfunk: kein Privileg, aber erlaubt und sinnvoll\n"
    "IMPORTANT: Notrufe haben absoluten Vorrang im Amateurfunk\n"
    "Nachrichtenverkehr bei Naturkatastrophen: koordiniert durch IARU-Regionen"
)

# -- Stationstagebuch / Logbuch --
EXPLANATIONS[("Stationstagebuch und QSL-Karten",)] = (
    "Logbuch: Aufzeichnung aller Funkverbindungen\n"
    "Inhalt mindestens: Datum, Zeit (UTC!), Frequenz, Betriebsart, Rufzeichen, Rapport\n"
    "QSL-Karte: schriftliche Bestaetigung einer Funkverbindung\n"
    "Buro-Wege: QSL via Buro oder direkt mit Adresse\n"
    "LOTW (Logbook of the World): elektronisches QSL-System der ARRL\n"
    "Uhrzeit: immer UTC (Coordinated Universal Time) im Logbuch und auf QSL"
)

# ===== KENNTNISSE VON VORSCHRIFTEN =====

# -- ITU-RR --
EXPLANATIONS[("Radio Regulations (ITU RR)",)] = (
    "Radio Regulations (RR): internationales Vertragswerk der ITU\n"
    "Regelt Frequenznutzung weltweit, einschliesslich Amateurfunk\n"
    "Welt in 3 Regionen eingeteilt: Region 1 (Europa/Afrika), 2 (Amerika), 3 (Asien/Oz)\n"
    "Definition: Amateurfunk = Funkdienst, der von Funkamateuren betrieben wird\n"
    "Artikel 25 (RR): spezielle Regelungen fuer den Amateurfunkdienst\n"
    "Deutschland gehoert zu Region 1"
)

# -- ITU-RR Definitionen --
EXPLANATIONS[("Definition des Amateurfunkdienstes und des Amateurfunkdienstes ueber Satelliten",)] = (
    "Amateurfunkdienst: Funkdienst, der von Funkamateuren fuer persoenliche Zwecke\n"
    "ohne gewerbliche Interessen betrieben wird.\n"
    "Amateurfunkstelle: Funkstelle des Amateurfunkdienstes.\n"
    "Funkamateur: Person mit Zulassung und Kenntnis der Vorschriften\n"
    "Ziele: Selbstaendiges Lernen, technische Untersuchungen, VOeLkerverstaendigung"
)

# -- ITU-RR Definition der Amateurfunkstelle --
EXPLANATIONS[("Definition der Amateurfunkstelle",)] = (
    "Amateurfunkstelle: Eine Funkstelle des Amateurfunkdienstes.\n"
    "Funkstelle: ein oder mehrere Sender/Empfaenger fuer den Funkdienst.\n"
    "Jede Amateurfunkstelle benoetigt ein zugeteiltes Rufzeichen.\n"
    "Ortsfeste und mobile/betriebliche Amateurfunkstellen sind zu unterscheiden."
)

# -- ITU-RR Artikel 25 --
EXPLANATIONS[("Artikel 25",)] = (
    "Artikel 25 der RR regelt den Amateurfunkdienst:\n"
    "Funkamateure duerfen international nur offene Sprache verwenden\n"
    "Keine verschluesselten Nachrichten oder verdeckte Inhalte\n"
    "Keine gewerblichen oder wirtschaftlichen Zwecke\n"
    "Morsepflicht: keine internationale Vorgabe mehr, jeder Staat regelt selbst\n"
    "Aussendungen duerfen nur zur technischen Untersuchung und zu Lernzwecken"
)

# -- Weitere Regelungen (ITU-RR) --
EXPLANATIONS[("Weitere Regelungen",)] = (
    "Die ITU-RR enthalten auch:\n"
    "Landeskenner-Praefixe (Appendix 42)\n"
    "Frequenzbereichszuteilungen fuer die 3 Regionen\n"
    "Q-Codes und Abkuerzungen (Appendix 41)\n"
    "Frequenzklassen und Kanalabstaende\n"
    "Regionale Abkommen (z.B. CEPT- und Genfer Abkommen)"
)

# -- CEPT --
EXPLANATIONS[("Regelungen der CEPT (Europaeische Konferenz der Verwaltungen fuer Post und Telekommunikation)",)] = (
    "CEPT: Europaeische Konferenz der Verwaltungen fuer Post und Telekommunikation\n"
    "T/R 61-01 (HAREC): Harmonized Amateur Radio Examination Certificate\n"
    "T/R 61-02: CEPT-Amateurfunkgenehmigung fuer Besuchende\n"
    "Mit HAREC darf man in allen CEPT-Laendern funk\n"
    "CEPT-Novice-Lizenz: fuer Laender mit Novice-Klasse (seit 2013)\n"
    "Deutschland hat HAREC sowie Novice-Genehmigung umgesetzt"
)

# -- AFuG --
EXPLANATIONS[("Amateurfunkgesetz (AFuG)",)] = (
    "Amateurfunkgesetz (AFuG): nationales deutsches Gesetz\n"
    "Regelt: Voraussetzungen fuer Amateurfunk, Pruefungen, Rufzeichen\n"
    "Amateurfunk = oeffentlicher Funkdienst, kein gewerblicher Zweck\n"
    "Zustaendige Behoerde: Bundesnetzagentur (BNetzA)\n"
    "Feste Station: Standort muss mitgeteilt werden\n"
    "Zulassung: pruefung + persoenliche Zuverlaessigkeit + Mindestalter\n"
    "Auflagen: Stoerungsfreiheit, Einhaltung der Frequenzbereiche"
)

# -- AFuV Allgemeines --
EXPLANATIONS[("Allgemeines",)] = (
    "AFuV (Amateurfunkverordnung): Detailregelungen zum AFuG\n"
    "Enthaelt: Frequenzbereiche, Leistungsgrenzen, Rufzeichenbildung\n"
    "Betrieb: nur offene Sprache, kein Missbrauch, Rufzeichenpflicht\n"
    "Abgleicharbeiten: duerfen nur mit geringer Leistung und koaxialer Dummy-Load\n"
    "Nachtrags-/Aenderungsanzeige: bei Aenderung der Standortdaten oder Aufgabe\n"
    "Buchstabenalphabet: nach Verfuegung 13/2005 (internationales Alphabet)"
)

# -- AFuV Rufzeichen --
EXPLANATIONS[("Rufzeichen und Rufzeichenanwendung",)] = (
    "Bildung von Rufzeichen nach AFuV:\n"
    "Aufbau: 1-2 Buchstaben (Praefix) + Ziffer + 1-3 Buchstaben (Suffix)\n"
    "Personengebunden: DO, DL, DK, DG, DN, DC, etc.\n"
    "Klubstation: DO0, DL0, DK0, DN0, etc.\n"
    "Rufzeichenzusaetze: /m, /p, /mm, /am\n"
    "Rufzeichen bei Ausbildungsfunk: des Ausbilders mit dem Zusatz der Auszubildenden\n"
    "Anspruch: kein Rechtsanspruch auf bestimmtes Rufzeichen"
)

# -- AFuV Ausbildungsfunk --
EXPLANATIONS[("Ausbildungsfunkbetrieb",)] = (
    "Ausbildungsfunk: Nicht-Funkamateure duerfen unter Aufsicht funk\n"
    "Voraussetzung: verantwortlicher Funkamateur mit gueltiger Zulassung\n"
    "Der Ausbilder (Inhaber des Rufzeichens) ist jederzeit verantwortlich\n"
    "Rufzeichen: Rufzeichen des Ausbilders, evtl. mit Zusatz\n"
    "Zweck: praktische Ausbildung vor der Pruefung"
)

# -- AFuV Klubstationen --
EXPLANATIONS[("Klubstationen",)] = (
    "Klubstation: Amateurfunkstelle eines Amateurfunkvereins oder einer Gruppe\n"
    "Voraussetzungen: eingetragener Verein, verantwortlicher Funkamateur\n"
    "Rufzeichen: DO0, DL0, DK0, etc. + Ortskennung\n"
    "Betrieb: nur unter Aufsicht eines verantwortlichen Funkamateurs\n"
    "Standort: beim Verein oder Clubhaus, Aenderung meldepflichtig"
)

# -- AFuV Relais --
EXPLANATIONS[("Relaisfunkstellen und Funkbaken",)] = (
    "Relaisfunkstelle: automatische Station mit Sender und Empfaenger\n"
    "Zulassung: Antrag bei der BNetzA erforderlich\n"
    "Maximale Leistung fuer Relais und Baken: durch AFuV geregelt\n"
    "Bake (Funkbake): sendet automatisch Kennung und ggf. Messton\n"
    "Der verantwortliche Funkamateur muss den zuverlaessigen Betrieb sicherstellen"
)

# -- AFuV Remote --
EXPLANATIONS[("Remote-Stationen",)] = (
    "Remote-Station: Amateurfunkstelle, die per Fernzugriff gesteuert wird\n"
    "Betriebsmeldung bei der BNetzA erforderlich\n"
    "Betriebssicherheit: Abschaltmoeglichkeit bei Fehlfunktion\n"
    "Zugriff nur durch berechtigte Funkamateure\n"
    "Der Betreiber muss seine Kontaktdaten hinterlegen\n"
    "Trenneinrichtung: ermoeglicht sichere Trennung der Antenne"
)

# -- AFuV Frequenzbereiche --
EXPLANATIONS[("Frequenzbereiche und Frequenznutzungsparameter",)] = (
    "AFuV legt die Frequenzbereiche fuer den Amateurfunk in Deutschland fest\n"
    "Primaer-/Sekundaernutzung: Amateurfunk ist primaer oder sekundaer\n"
    "Leistungsgrenzen: verschiedene Maximalleistungen pro Band und Lizenzklasse\n"
    "Klasse A: volle Leistung (max. 750 W auf den meisten Baendern)\n"
    "Klasse E: geringere Leistung (max. 100 W auf den meisten Baendern)\n"
    "Klasse N: noch geringer (max. 25 oder 10 W)\n"
    "Nicht alle Baender stehen allen Klassen zur Verfuegung"
)

# -- TKG --
EXPLANATIONS[("Telekommunikationsgesetz (TKG)",)] = (
    "TKG: regelt Telekommunikationsdienste und Frequenzordnung in Deutschland\n"
    "Frequenzzuteilung: jede Frequenznutzung bedarf der Zuteilung\n"
    "Amateurfunk ist von bestimmten TKG-Bestimmungen ausgenommen\n"
    "Ordnungswidrigkeit: Verstoesse koennen mit Geldbussen geahndet werden"
)

# -- TTDSG --
EXPLANATIONS[("Telekommunikation-Telemedien-Datenschutz-Gesetz (TTDSG)",)] = (
    "TTDSG (Telekommunikation-Telemedien-Datenschutz-Gesetz):\n"
    "Regelt Fernmeldegeheimnis und Datenschutz in der Telekommunikation\n"
    "Funkamateure duerfen den Funkverkehr nicht abhoeren oder weitersagen\n"
    "Ausnahme: fuer den Empfang bestimmte Sendungen (Amateurfunk)\n"
    "Verletzung des Fernmeldegeheimnisses ist strafbar"
)

# -- EMVG --
EXPLANATIONS[("Gesetz ueber die elektromagnetische Vertraeglichkeit von Geraeten (EMVG), Stoerfaelle",)] = (
    "EMVG (Gesetz ueber die elektromagnetische Vertraeglichkeit):\n"
    "Geraete muessen bestimmte EMV-Anforderungen erfuellen\n"
    "Stoerungsfall: zustaendige Behoerde ist die BNetzA\n"
    "Zusammenarbeit: Funkamateure sollen bei Stoerungen kooperieren\n"
    "Entstoerungsmassnahmen koennen angeordnet werden"
)

# -- FuAG --
EXPLANATIONS[("Gesetz ueber die Bereitstellung von Funkanlagen auf dem Markt (FuAG)",)] = (
    "FuAG (Gesetz ueber die Bereitstellung von Funkanlagen auf dem Markt):\n"
    "Regelt Inverkehrbringen von Funkgeraeten\n"
    "CE-Kennzeichnung: Funkgeraete benoetigen Kennzeichnung\n"
    "Selbstbau: von Funkamateuren selstgebaute Geraete sind ausgenommen\n"
    "Grundlegende Anforderungen: Schutz von Gesundheit, EMV, Frequenznutzung"
)

# -- EMVU / BEMFV --
EXPLANATIONS[("EMVU (elektromagnetische Umweltvertraeglichkeit) / BEMFV",)] = (
    "EMVU (Elektromagnetische Umweltvertraeglichkeit):\n"
    "BEMFV: Verordnung ueber das Nachweisverfahren zum Schutz von Personen\n"
    "Ortsfeste Amateurfunkanlagen mit bestimmter Leistung muessen angezeigt werden\n"
    "Standortbescheinigung: Nachweis der Einhaltung der Grenzwerte\n"
    "Grenzwerte schuetzen vor gesundheitlichen Wirkungen\n"
    "Anzeigepflicht: unabhaengig von Spitzenleistung, ab bestimmten Werten\n"
    "Verfahren: Standortbescheinigung oder vereinfachtes Verfahren"
)

# -- Sicherheitsvorschriften --
EXPLANATIONS[("Sicherheitsvorschriften",)] = (
    "Sicherheitsvorschriften fuer Amateurfunkstellen:\n"
    "VDE 0855-300: Norm fuer Antennenanlagen (Errichtung und Betrieb)\n"
    "DIN VDE-Vorschriften: anerkannte Regeln der Technik\n"
    "Stromversorgung von Eigenbaugeraeten: Netzteil muss VDE entsprechen\n"
    "Schutzleiter, Sicherungen, ausreichende Isolation sind Pflicht"
)

# -- Sonstiges --
EXPLANATIONS[("Sonstiges",)] = (
    "Weitere Gesetze, Vorschriften und Bestimmungen fuer den Amateurfunk:\n"
    "Haftung: Der Funkamateur haftet fuer Schaeden durch die Station\n"
    "Gebuehren: jaerliche Beitraege nach BNetzA-Gebuaehrenverordnung\n"
    "Beitraege: abhaengig von Lizenzklasse und Standort\n"
    "Betrieb an Bord: zusaetzliche Genehmigungen des Schiffsluftfahrzeugbetreibers"
)

# ===== GENERATION LOGIC =====

explanations = {}
for q in questions:
    num = q["number"]
    path = path_map.get(num)
    if num in explanations:
        continue
    text = q["question"]

    # Check path-based explanations (first matching wins)
    # Exact match against the last (most specific) section name
    found = False
    last_section = path[-1] if path else ""
    for path_fragment, exp in EXPLANATIONS.items():
        if all(p == last_section for p in path_fragment):
            explanations[num] = asciify(exp)
            found = True
            break
    if found:
        continue

    # For calculation-heavy sections, try value extraction within the right context
    section_name = path[-1] if path else ""

    if "Ohmsches Gesetz" in section_name or "Widerstand" in section_name:
        ohm_vals, volt_vals, amp_vals, watt_vals, hz_vals, farad_vals, henry_vals, meter_vals = get_vals(q)
        if ohm_vals and amp_vals:
            u = ohm_vals[0] * amp_vals[0]
            explanations[num] = asciify(
                f"Ohm'sches Gesetz: U = R * I = {fmt(ohm_vals[0], 'Ohm')} * {fmt(amp_vals[0], 'A')} = {fmt(u, 'V')}")
        elif volt_vals and amp_vals:
            r = volt_vals[0] / amp_vals[0]
            explanations[num] = asciify(
                f"Ohm'sches Gesetz: R = U / I = {fmt(volt_vals[0], 'V')} / {fmt(amp_vals[0], 'A')} = {fmt(r, 'Ohm')}")
        elif volt_vals and ohm_vals:
            a = volt_vals[0] / ohm_vals[0]
            explanations[num] = asciify(
                f"Ohm'sches Gesetz: I = U / R = {fmt(volt_vals[0], 'V')} / {fmt(ohm_vals[0], 'Ohm')} = {fmt(a, 'A')}")

    if "Reihen- und Parallelschaltung" in section_name:
        ohm_vals, volt_vals, amp_vals, watt_vals, hz_vals, farad_vals, henry_vals, meter_vals = get_vals(q)
        if ohm_vals and len(ohm_vals) >= 2 and "parallel" in text.lower():
            r = 1 / sum(1 / v for v in ohm_vals)
            explanations[num] = asciify(
                f"Parallelschaltung: 1/R_ges = 1/R1 + 1/R2 + ...\n=> R_ges = {fmt(r, 'Ohm')}")
        elif ohm_vals and len(ohm_vals) >= 2:
            r = sum(ohm_vals)
            explanations[num] = asciify(
                f"Reihenschaltung: R_ges = R1 + R2 + ... = {fmt(r, 'Ohm')}")
        elif farad_vals and len(farad_vals) >= 2 and "parallel" in text.lower():
            c = sum(farad_vals)
            explanations[num] = asciify(
                f"Parallelschaltung Kondensatoren: C_ges = C1 + C2 + ... = {fmt(c, 'F')}")
        elif farad_vals and len(farad_vals) >= 2:
            c = 1 / sum(1 / v for v in farad_vals)
            explanations[num] = asciify(
                f"Reihenschaltung Kondensatoren: 1/C_ges = 1/C1 + 1/C2 + ...\n=> C_ges = {fmt(c, 'F')}")

    if "Leistung" in section_name:
        ohm_vals, volt_vals, amp_vals, watt_vals, hz_vals, farad_vals, henry_vals, meter_vals = get_vals(q)
        if watt_vals and amp_vals:
            u = watt_vals[0] / amp_vals[0]
            explanations[num] = asciify(f"Leistung: P = U * I => U = P / I = {fmt(watt_vals[0], 'W')} / {fmt(amp_vals[0], 'A')} = {fmt(u, 'V')}")
        elif volt_vals and amp_vals:
            p = volt_vals[0] * amp_vals[0]
            explanations[num] = asciify(f"Leistung: P = U * I = {fmt(volt_vals[0], 'V')} * {fmt(amp_vals[0], 'A')} = {fmt(p, 'W')}")

    if "Schwingkreise" in section_name:
        ohm_vals, volt_vals, amp_vals, watt_vals, hz_vals, farad_vals, henry_vals, meter_vals = get_vals(q)
        if henry_vals and farad_vals:
            fres = 1 / (2 * math.pi * math.sqrt(henry_vals[0] * farad_vals[0]))
            explanations[num] = asciify(
                f"Resonanzfrequenz: f = 1 / (2*pi*sqrt(L*C))\nL = {fmt(henry_vals[0], 'H')}, C = {fmt(farad_vals[0], 'F')}\nf = {fmt(fres, 'Hz')}")

# Save
safe = {k: explanations[k] for k in explanations}
with open("explanations.json", "w", encoding="ascii") as f:
    json.dump(safe, f, indent=2, ensure_ascii=True)

# Stats
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
