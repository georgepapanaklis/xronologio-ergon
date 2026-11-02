"""Μετατρέπει εγγραφές ΕΣΠΑ (anaptyxi.gov.gr, projects_v2 + projectDetails) σε εγγραφές για το data-espa.js."""
import json, re, sys, datetime, unicodedata
raw = json.load(open(sys.argv[1], encoding="utf-8"))
TODAY = sys.argv[3] if len(sys.argv) > 3 else datetime.date.today().isoformat()
PLACEHOLDER = (34.937, 23.988)  # σημείο χωρίς χωροθέτηση (έργα σε όλη την περιφέρεια)
def N(s): return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").upper()
def iso(d):
    if not d: return None
    dd, mm, yy = d.split("/"); return f"{yy}-{int(mm):02d}-{int(dd):02d}"
def cat(t, th):
    T = N(t)
    if re.search(r"ΝΟΣΟΚΟΜ", T): return "Νοσοκομεία"
    if re.search(r"ΛΙΜΕΝ", T): return "Λιμάνια"
    if re.search(r"ΑΠΟΧΕΤΕΥΣ|ΛΥΜΑΤ|ΒΙΟΛΟΓΙΚ|Ε\.Ε\.Λ|ΑΠΟΡΡΙΜ|ΑΠΟΒΛΗΤ|ΧΥΤΥ|ΚΟΜΠΟΣΤ", T): return "Αποχέτευση & απόβλητα"
    if re.search(r"ΥΔΡΕΥΣ|ΦΡΑΓΜ", T): return "Ύδρευση & φράγματα"
    if re.search(r"ΚΕΝΤΡΟ|ΚΤΙΡ", T): return "Δημόσια κτίρια"
    if "Μεταφορ" in th or re.search(r"ΟΔΙΚ|ΔΡΟΜ|ΚΟΜΒ|ΒΟΑΚ", T): return "Οδικά έργα"
    return "Άλλα έργα"
out = []
for (k, t, body, bud, pay, comp, th, mun, pref, lat, lon, en, au, co, cp, st) in raw:
    done = "ολοκληρωθεί" in st
    ms = []
    if au: ms.append({"t": "other", "d": iso(au), "l": "Δημοπράτηση κύριου υποέργου", "s": 0})
    if co: ms.append({"t": "contract", "d": iso(co), "l": "Υπογραφή σύμβασης κύριου υποέργου", "s": 0})
    if en: ms.append({"t": "other", "d": iso(en), "l": "Ένταξη στο ΕΣΠΑ 2014–2020", "s": 0})
    note = "Εισαγωγή από το ΕΣΠΑ 2014–2020. Οι ημερομηνίες δημοπράτησης και σύμβασης αφορούν το κύριο υποέργο (με τον μεγαλύτερο προϋπολογισμό)."
    if cp and done:
        if iso(cp) <= TODAY: ms.append({"t": "open", "d": iso(cp), "l": "Ολοκλήρωση (ημερομηνία ΕΣΠΑ)", "s": 0})
        else: note += f" Το ΕΣΠΑ αναφέρει το έργο ως ολοκληρωμένο, αλλά δίνει μελλοντική ημερομηνία ολοκλήρωσης ({cp}), η οποία δεν καταγράφεται."
    ms.sort(key=lambda m: m["d"])
    geo = None if (lat, lon) == PLACEHOLDER or lat is None else [lat, lon]
    region = "Κρήτη" + (f" – Π.Ε. {pref}" if pref else "") + (f", Δήμος {mun}" if mun else "")
    pct = round(pay / bud * 100) if bud else None
    out.append({"id": f"espa-{k}", "origin": "espa", "mis": k, "perif": ["Κρήτης"], "pe": [pref] if pref else [], "name": t.strip(), "cat": cat(t, th), "region": region,
        "status": "Ολοκληρωμένο (κατά το ΕΣΠΑ)" if done else "Σε εξέλιξη (κατά το ΕΣΠΑ)", "geo": geo, "ministry": None, "mv": False,
        "cost": f"Προϋπολογισμός €{bud:,.0f} · Πληρωμές €{pay:,.0f} ({pct}%)".replace(",", "."),
        "funding": f"ΕΣΠΑ 2014–2020 · Θεματικός στόχος: {th}", "contractor": f"Δικαιούχος: {body.strip()}",
        "note": note, "ms": ms,
        "src": [[f"anaptyxi.gov.gr: καρτέλα έργου MIS {k}", f"https://anaptyxi.gov.gr/GetData.ashx?queryType=projectDetails&queryArgument={k}&outputFormat=html"]]})
hdr = ("/* Έργα από το ΕΣΠΑ 2014–2020 (anaptyxi.gov.gr), αυτόματη εισαγωγή.\n"
       f"   Δείγμα: Περιφέρεια Κρήτης, 25 μεγαλύτερα έργα υποδομής (χωρίς κρατικές ενισχύσεις και χρηματοδοτικά εργαλεία). Ημερομηνία εισαγωγής: {TODAY}.\n"
       "   Παράγεται από το espa_convert.py — μην το επεξεργάζεσαι με το χέρι. */\n")
open(sys.argv[2], "w", encoding="utf-8").write(hdr + "const P_ESPA=" + json.dumps(out, ensure_ascii=False, indent=0) + ";\n")
print(len(out), "έργα;", sum(1 for o in out if o["geo"]), "με θέση;", {c: sum(1 for o in out if o["cat"] == c) for c in set(o["cat"] for o in out)})
