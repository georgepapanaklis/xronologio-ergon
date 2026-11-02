"""Μετατρέπει τα ακατέργαστα δεδομένα ΕΣΠΑ (έξοδος του espa_fetch.py) σε data-espa.js.

Χρήση:
    python espa_convert.py espa_raw.json data-espa.js [ΗΜΕΡΟΜΗΝΙΑ_ΑΝΑΦΟΡΑΣ]

Δέχεται και την παλιά μορφή (λίστα από λίστες) του δείγματος Κρήτης.
"""
import datetime, json, re, sys, unicodedata

REGIONS = ["Ανατολικής Μακεδονίας και Θράκης", "Κεντρικής Μακεδονίας", "Δυτικής Μακεδονίας", "Ηπείρου", "Θεσσαλίας",
           "Ιονίων Νήσων", "Δυτικής Ελλάδας", "Στερεάς Ελλάδας", "Αττικής", "Πελοποννήσου", "Βορείου Αιγαίου",
           "Νοτίου Αιγαίου", "Κρήτης"]


def N(s):
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn").upper()


def region_name(r):
    """Το API γράφει π.χ. «Ανατολικής Μακεδονίας, Θράκης »· το αντιστοιχίζουμε στην επίσημη ονομασία."""
    key = N(r).replace(",", " ").replace(" ΚΑΙ ", " ").split()
    for name in REGIONS:
        if N(name).replace(" ΚΑΙ ", " ").split() == key:
            return name
    return r.strip()


def iso(d):
    if not d:
        return None
    dd, mm, yy = d.split(" ")[0].split("/")
    return f"{yy}-{int(mm):02d}-{int(dd):02d}"


def cat(t, th):
    T = N(t)
    if re.search(r"ΝΟΣΟΚΟΜ|ΚΕΝΤΡΟ ΥΓΕΙΑΣ", T): return "Νοσοκομεία"
    if re.search(r"ΜΕΤΡΟ|ΣΙΔΗΡΟΔΡΟΜ|\bΤΡΑΜ\b", T): return "Μετρό & σιδηρόδρομος"
    if re.search(r"ΣΧΟΛ|ΠΑΝΕΠΙΣΤΗΜ|ΝΗΠΙΑΓΩΓ|ΓΥΜΝΑΣΙ|ΛΥΚΕΙ", T): return "Παιδεία"
    if re.search(r"ΛΙΜΕΝ", T): return "Λιμάνια"
    if re.search(r"ΑΕΡΟΔΡ|ΑΕΡΟΛΙΜ", T): return "Αεροδρόμια"
    if re.search(r"ΑΠΟΧΕΤΕΥΣ|ΛΥΜΑΤ|ΒΙΟΛΟΓΙΚ|Ε\.Ε\.Λ|ΑΠΟΡΡΙΜ|ΑΠΟΒΛΗΤ|ΧΥΤΥ|ΧΥΤΑ|ΚΟΜΠΟΣΤ", T): return "Αποχέτευση & απόβλητα"
    if re.search(r"ΥΔΡΕΥΣ|ΦΡΑΓΜ|ΑΡΔΕΥΣ|ΑΝΤΙΠΛΗΜΜΥΡ|ΔΙΕΥΘΕΤΗΣ", T): return "Ύδρευση & φράγματα"
    if re.search(r"ΓΕΦΥΡ|ΣΗΡΑΓΓ", T): return "Γέφυρες & σήραγγες"
    if re.search(r"ΜΟΥΣΕΙ|ΘΕΑΤΡ|ΑΡΧΑΙΟΛΟΓ|ΜΝΗΜΕΙ|ΠΟΛΙΤΙΣ", T): return "Πολιτισμός"
    if re.search(r"ΑΘΛΗΤ|ΓΗΠΕΔ|ΚΟΛΥΜΒΗΤ", T): return "Αθλητισμός"
    if re.search(r"ΚΕΝΤΡΟ|ΚΤΙΡ|ΑΝΑΠΛΑΣ|ΠΑΡΚΟ", T): return "Δημόσια κτίρια & αναπλάσεις"
    if re.search(r"\bΟΔΙΚ|\bΟΔΟ[ΣΥΙ]?\b|ΔΡΟΜ|ΚΟΜΒ|ΒΟΑΚ|ΑΥΤΟΚΙΝΗΤΟΔΡΟΜ|ΠΑΡΑΚΑΜΨ", T): return "Οδικά έργα"
    if "Μεταφορ" in th: return "Οδικά έργα"
    return "Άλλα έργα"


def legacy(row):
    k, t, body, bud, pay, comp, th, mun, pref, lat, lon, en, au, co, cp, st = row
    no_place = not mun and not pref
    return {"k": k, "t": t, "body": body, "bud": bud, "pay": pay, "comp": comp, "th": th, "status": st,
            "regions": ["Κρήτης"], "prefs": [pref] if pref else [], "muns": [mun] if mun else [],
            "lat": None if no_place else lat, "lon": None if no_place else lon, "en": en, "au": au, "co": co, "cp": cp}


def convert(r, today):
    done = "ολοκληρωθεί" in (r.get("status") or "")
    ms = []
    if r.get("au"): ms.append({"t": "other", "d": iso(r["au"]), "l": "Δημοπράτηση κύριου υποέργου", "s": 0})
    if r.get("co"): ms.append({"t": "contract", "d": iso(r["co"]), "l": "Υπογραφή σύμβασης κύριου υποέργου", "s": 0})
    if r.get("en"): ms.append({"t": "other", "d": iso(r["en"]), "l": "Ένταξη στο ΕΣΠΑ 2014–2020", "s": 0})
    note = "Εισαγωγή από το ΕΣΠΑ 2014–2020. Οι ημερομηνίες δημοπράτησης και σύμβασης αφορούν το κύριο υποέργο (με τον μεγαλύτερο προϋπολογισμό)."
    if r.get("cp") and done:
        if iso(r["cp"]) <= today:
            ms.append({"t": "open", "d": iso(r["cp"]), "l": "Ολοκλήρωση (ημερομηνία ΕΣΠΑ)", "s": 0})
        else:
            note += f" Το ΕΣΠΑ αναφέρει το έργο ως ολοκληρωμένο, αλλά δίνει μελλοντική ημερομηνία ολοκλήρωσης ({r['cp']}), η οποία δεν καταγράφεται."
    ms = [m for m in ms if m["d"] and m["d"] >= "1960" and m["d"] <= today]
    if not ms:
        return None
    ms.sort(key=lambda m: m["d"])
    regions = [region_name(x) for x in r.get("regions") or []]
    prefs, muns = r.get("prefs") or [], r.get("muns") or []
    # χωρίς δήμο και νομό, η θέση του API είναι προεπιλεγμένο σημείο της περιφέρειας: δεν τη χρησιμοποιούμε
    geo = [r["lat"], r["lon"]] if r.get("lat") is not None and (prefs or muns) and len(regions) <= 1 else None
    if len(regions) == 1:
        place = "Περιφέρεια " + regions[0] + (f" – Π.Ε. {prefs[0]}" if len(prefs) == 1 else "") + (f", Δήμος {muns[0]}" if len(muns) == 1 else "")
    elif regions:
        place = "Περιφέρειες: " + ", ".join(regions)
    else:
        place = "Δεν έχει καταγραφεί περιοχή"
    bud, pay = r.get("bud") or 0, r.get("pay") or 0
    pct = f" ({round(pay / bud * 100)}%)" if bud else ""
    k = r["k"]
    return {"id": f"espa-{k}", "origin": "espa", "mis": k, "perif": regions, "pe": prefs, "name": r["t"].strip(),
            "cat": cat(r["t"], r.get("th") or ""), "region": place,
            "status": "Ολοκληρωμένο (κατά το ΕΣΠΑ)" if done else "Σε εξέλιξη (κατά το ΕΣΠΑ)", "geo": geo,
            "ministry": None, "mv": False,
            "cost": f"Προϋπολογισμός €{bud:,.0f} · Πληρωμές €{pay:,.0f}{pct}".replace(",", "."),
            "funding": "ΕΣΠΑ 2014–2020" + (f" · Θεματικός στόχος: {r['th']}" if r.get("th") else ""),
            "contractor": "Δικαιούχος: " + (r.get("body") or "").strip(), "note": note, "ms": ms,
            "src": [[f"anaptyxi.gov.gr: καρτέλα έργου MIS {k}",
                     f"https://anaptyxi.gov.gr/GetData.ashx?queryType=projectDetails&queryArgument={k}&outputFormat=html"]]}


def main():
    src, dst = sys.argv[1], sys.argv[2]
    today = sys.argv[3] if len(sys.argv) > 3 else datetime.date.today().isoformat()
    data = json.load(open(src, encoding="utf-8"))
    if isinstance(data, list):
        rows, fetched, desc = [legacy(x) for x in data], today, "δείγμα Περιφέρειας Κρήτης"
    else:
        rows, fetched = data["projects"], data.get("fetched", today)
        desc = f"τα έργα υποδομής ανάμεσα στα {data.get('top')} μεγαλύτερα σε προϋπολογισμό έργα όλης της χώρας"
    out, seen = [], set()
    for r in rows:
        if r["k"] in seen:
            continue
        seen.add(r["k"])
        c = convert(r, today)
        if c:
            out.append(c)
    hdr = ("/* Έργα από το ΕΣΠΑ 2014–2020 (anaptyxi.gov.gr), αυτόματη εισαγωγή.\n"
           f"   Περιεχόμενο: {desc}. Ημερομηνία λήψης: {fetched}.\n"
           "   Παράγεται από το espa_convert.py — μην το επεξεργάζεσαι με το χέρι. */\n")
    with open(dst, "w", encoding="utf-8") as f:
        f.write(hdr + "const P_ESPA=[\n" + ",\n".join(json.dumps(o, ensure_ascii=False, separators=(",", ":")) for o in out) + "\n];\n")
    cats = {}
    for o in out:
        cats[o["cat"]] = cats.get(o["cat"], 0) + 1
    print(f"{len(out)} έργα, {sum(1 for o in out if o['geo'])} με θέση. Κατηγορίες: {cats}")


if __name__ == "__main__":
    main()
