"""Κατεβάζει έργα υποδομής από το ΕΣΠΑ 2014–2020 (API του anaptyxi.gov.gr).

Χρήση:
    python espa_fetch.py --top 5000 --out espa_raw.json

Βήματα:
1. Παίρνει τα --top μεγαλύτερα σε προϋπολογισμό έργα όλης της χώρας (projects_v2).
2. Κρατά μόνο έργα υποδομής. Εξαιρεί κρατικές ενισχύσεις, χρηματοδοτικά εργαλεία και δράσεις
   όπως προσωπικό, κατάρτιση ή επιδοτήσεις.
3. Για κάθε έργο κατεβάζει τα στοιχεία του (projectDetails): ημερομηνίες κύριου υποέργου,
   περιοχές και θέση.

Χρησιμοποιεί μόνο την τυπική βιβλιοθήκη της Python. Το API είναι αργό (20–60 δευτερόλεπτα
ανά αίτημα), γι' αυτό τα αιτήματα γίνονται παράλληλα και επαναλαμβάνονται αν αποτύχουν.
"""
import argparse, json, re, sys, time, unicodedata, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

API = "https://anaptyxi.gov.gr/GetData.ashx"
INC = re.compile(r"\bΟΔΙΚ|\bΟΔΟ[ΣΥΙ]?\b|ΔΡΟΜ|ΥΔΡΕΥΣ|ΑΠΟΧΕΤΕΥΣ|ΦΡΑΓΜ|ΜΟΝΑΔΑ|ΧΥΤ|ΛΙΜΕΝ|ΣΧΟΛΙΚΟΥ ΣΥΓΚΡΟΤΗΜ|ΣΧΟΛΙΚΟ ΣΥΓΚΡΟΤΗΜ|ΝΟΣΟΚΟΜ|ΚΤΙΡ|ΓΕΦΥΡ|ΑΝΤΙΠΛΗΜΜΥΡ|ΚΑΤΑΣΚΕΥ|ΑΝΑΒΑΘΜ|ΒΕΛΤΙΩΣ|ΕΓΚΑΤΑΣΤΑΣ|ΑΕΡΟΔΡ|ΑΕΡΟΛΙΜ|ΑΘΛΗΤ|ΕΠΕΜΒΑΣ|ΔΙΕΥΘΕΤΗΣ|ΜΟΥΣΕΙ|ΑΝΑΠΛΑΣ|ΑΓΩΓΟ|Ε\.Ε\.Λ|\bΜΕΤΡΟ\b|ΣΙΔΗΡΟΔΡΟΜ|\bΤΡΑΜ\b|ΣΗΡΑΓΓ|ΚΟΜΒ|ΠΑΡΚΟ|ΒΙΟΛΟΓΙΚ|ΑΡΔΕΥΣ|ΛΥΜΑΤ|ΑΥΤΟΚΙΝΗΤΟΔΡΟΜ")
EXC = re.compile(r"^ΕΝΙΣΧΥΣΗ|ΛΕΙΤΟΥΡΓΙΑ|ΔΡΑΣΗ|ΔΡΑΣΕΙΣ|ΚΑΤΟΙΚΙ|ΠΡΟΣΩΠΙΚ|ΚΑΤΑΡΤΙΣ|ΠΡΟΓΡΑΜΜΑ|ΥΠΗΡΕΣΙ|ΕΝΑΡΜΟΝΙΣΗ|ΕΠΙΔΟΤΗΣ|ΕΠΙΧΟΡΗΓΗΣ|ΕΠΙΤΑΓΗ|ΥΠΟΣΤΗΡΙΞ|ΣΥΜΒΟΥΛΕΥΤΙΚ|ΕΠΙΜΟΡΦΩΣ|ΥΠΟΤΡΟΦΙ|ΕΡΕΥΝΗΤΙΚ|ΠΑΡΑΤΗΡΗΤΗΡΙ|ΨΗΦΙΑΚ|ΕΜΒΟΛΙΑΣ|ΝΟΣΗΛΕΥΤ|ΟΛΟΗΜΕΡ|ΕΝΙΑΙΟΣ ΤΥΠΟΣ|ΕΝΙΑΙΟΥ ΤΥΠΟΥ|ΦΥΣΙΚΩΝ ΠΡΟΣΩΠΩΝ|ΑΝΕΡΓ|ΝΕΟΥΣ|ΕΡΓΑΖΟΜΕΝ|ΕΚΠΑΙΔΕΥΤΙΚ|ΕΥΑΛΩΤ|ΚΟΙΝΩΝΙΚΗΣ ΕΝΤΑΞΗΣ|ΚΟΙΝΩΝΙΚΟ ΕΙΣΟΔΗΜΑ|VOUCHER")
MULTI_OK = re.compile(r"ΣΙΔΗΡΟΔΡΟΜ|ΑΥΤΟΚΙΝΗΤΟΔΡΟΜ|\bΜΕΤΡΟ\b|ΑΓΩΓΟ|ΣΗΡΑΓΓ|ΓΕΦΥΡ")
THEMES = re.compile(r"Μεταφορ|Περιβάλλ|Κλιματ")


def N(s):
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn").upper()


def get(params, tries=4, timeout=180):
    url = API + "?" + urllib.parse.urlencode(params, doseq=True)
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "xronologio-ergon/1.0"}), timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # δίκτυο ή αργή απόκριση: ξαναδοκίμασε με αναμονή
            print(f"  προσπάθεια {i + 1} απέτυχε: {e}", file=sys.stderr, flush=True)
            time.sleep(10 * (i + 1))
    raise RuntimeError("Το API δεν απάντησε: " + url)


def is_infrastructure(r):
    t = N(r.get("title"))
    if r.get("kratikiEnisxisi") != "ΟΧΙ" or r.get("isFunding") != "ΟΧΙ":
        return False
    # ΕΠ 2 = «Υποδομές Μεταφορών, Περιβάλλον και Αειφόρος Ανάπτυξη»: δεκτό και χωρίς λέξη-κλειδί στον τίτλο
    return not EXC.search(t) and (bool(INC.search(t)) or str(r.get("epKodikos")) == "2")


def details(kodikos):
    d = get({"queryType": "projectDetails", "queryArgument": kodikos, "outputFormat": "json"})
    subs = sorted(d.get("subprojects") or [], key=lambda s: s.get("budget") or 0, reverse=True)
    a = (subs[0].get("actualStatus") or {}) if subs else {}
    m = re.search(r"<coordinates>\s*([-\d.]+),([-\d.]+)", d.get("map") or "")
    geo = d.get("geoamounts") or []
    uniq = lambda xs: list(dict.fromkeys(x.strip() for x in xs if x and x.strip()))
    return {
        "k": kodikos, "t": (d.get("title") or "").strip(), "body": (d.get("body") or "").strip(),
        "bud": round(d.get("totalBudget") or 0), "pay": round(d.get("payments") or 0), "comp": d.get("completion"),
        "th": d.get("thematics") or "", "status": d.get("statusReport") or "", "statusCode": d.get("statusCode"),
        "regions": uniq(g.get("region") for g in geo), "prefs": uniq(g.get("prefecture") for g in geo),
        "muns": uniq(g.get("municipality") for g in geo),
        "lat": round(float(m.group(2)), 3) if m else None, "lon": round(float(m.group(1)), 3) if m else None,
        "en": a.get("entranceDate") or "", "au": a.get("auctionDate") or "", "co": a.get("contractDate") or "",
        "cp": a.get("completionDate") or "", "isMajor": d.get("isMajor"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=5000, help="πόσα έργα (κατά προϋπολογισμό) να εξεταστούν")
    ap.add_argument("--pagesize", type=int, default=1000)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default="espa_raw.json")
    args = ap.parse_args()

    records, page = [], 0
    while len(records) < args.top:
        print(f"Λίστα: σελίδα {page + 1}", flush=True)
        j = get({"queryType": "projects_v2", "outputFormat": "json", "pagesize": args.pagesize, "pagenum": page,
                 "sortdatafield": "budget", "sortorder": "desc"})
        recs = j.get("Records") or []
        if not recs:
            break
        records += recs
        page += 1
    records = records[: args.top]
    cands = [r for r in records if is_infrastructure(r)]
    print(f"{len(records)} έργα εξετάστηκαν, {len(cands)} έργα υποδομής", flush=True)

    out, failed = [], []
    with ThreadPoolExecutor(args.workers) as ex:
        futs = {ex.submit(details, r["kodikos"]): r["kodikos"] for r in cands}
        for i, f in enumerate(as_completed(futs), 1):
            try:
                out.append(f.result())
            except Exception as e:
                failed.append(futs[f])
                print(f"  MIS {futs[f]}: {e}", file=sys.stderr, flush=True)
            if i % 50 == 0:
                print(f"Στοιχεία: {i}/{len(cands)}", flush=True)
    # δεύτερο φίλτρο: χωρίς λέξη-κλειδί στον τίτλο, μένουν μόνο έργα με θεματικό στόχο μεταφορών/περιβάλλοντος
    out = [r for r in out if INC.search(N(r["t"])) or THEMES.search(r["th"])]
    # έργα σε 5+ περιφέρειες είναι συνήθως πανελλαδικές δράσεις· μένουν μόνο τα γραμμικά έργα (σιδηρόδρομος, αυτοκινητόδρομοι κ.λπ.)
    out = [r for r in out if len(r["regions"]) < 5 or MULTI_OK.search(N(r["t"]))]
    out.sort(key=lambda r: -r["bud"])
    json.dump({"source": "anaptyxi.gov.gr (ΕΣΠΑ 2014–2020)", "fetched": time.strftime("%Y-%m-%d"),
               "top": args.top, "failed": failed, "projects": out}, open(args.out, "w", encoding="utf-8"),
              ensure_ascii=False, indent=0)
    print(f"Αποθηκεύτηκαν {len(out)} έργα στο {args.out} ({len(failed)} αποτυχίες)", flush=True)


if __name__ == "__main__":
    main()
