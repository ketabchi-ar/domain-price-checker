#!/usr/bin/env python3
"""
Sync TLD pricing from IranServer and update tlds.json and tlds.js
Accurately captures all 439 TLDs including both 2-column (standard rate)
and 3-column (first-year discount + renewal) structures.
Sorts popular and Iranian TLDs (.ir, .com, .net, etc.) at the top.
"""

import json
import os
import re
import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

PRIORITY_TLDS = [
    ".ir", ".com", ".net", ".org", ".co.ir", ".co", ".io", ".shop",
    ".online", ".store", ".site", ".me", ".xyz", ".biz", ".info",
    ".app", ".dev", ".ai", ".tech", ".website", ".top", ".cc", ".pro"
]

def fetch_iranserver_tlds():
    url = "https://www.iranserver.com/domains/tld/"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    })
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print("Error fetching IranServer TLD page:", e)
        return None

    # Pattern for 3-column rows (TLD, Register, Renew)
    p3 = re.findall(
        r'<div class="[^"]*ltr[^"]*">\s*(\.[a-zA-Z0-9\.\-]+)\s*</div>\s*'
        r'<div class="[^"]*price-color[^"]*">\s*([\d,]+)\s*</div>\s*'
        r'<div class="[^"]*price-color[^"]*">\s*([\d,]+)\s*</div>',
        html
    )
    
    # Pattern for 2-column rows (TLD, Register)
    p2 = re.findall(
        r'<div class="[^"]*ltr[^"]*">\s*(\.[a-zA-Z0-9\.\-]+)\s*</div>\s*'
        r'<div class="[^"]*price-color[^"]*">\s*([\d,]+)\s*</div>',
        html
    )

    tld_dict = {}

    # Populate 2-column first (standard rate)
    for tld, reg in p2:
        tld_clean = tld.strip().lower()
        tld_dict[tld_clean] = {
            "tld": tld_clean,
            "register_price": reg.strip(),
            "renew_price": reg.strip()
        }

    # Overlay with 3-column where renewal price is explicitly specified
    for tld, reg, ren in p3:
        tld_clean = tld.strip().lower()
        tld_dict[tld_clean] = {
            "tld": tld_clean,
            "register_price": reg.strip(),
            "renew_price": ren.strip()
        }

    tlds_list = list(tld_dict.values())
    print(f"Extracted {len(tlds_list)} unique TLDs from IranServer.")

    # Sort: Priority TLDs first, then alphabetical
    def sort_key(item):
        tld = item["tld"]
        if tld in PRIORITY_TLDS:
            return (0, PRIORITY_TLDS.index(tld))
        elif tld.endswith(".ir"):
            return (1, tld)
        else:
            return (2, tld)

    tlds_list.sort(key=sort_key)
    return tlds_list

def main():
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(repo_dir, "tlds.json")
    js_path = os.path.join(repo_dir, "tlds.js")

    latest_tlds = fetch_iranserver_tlds()
    if not latest_tlds or len(latest_tlds) < 200:
        print("Could not parse enough TLDs, keeping existing file.")
        return

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(latest_tlds, f, ensure_ascii=False, indent=2)

    with open(js_path, "w", encoding="utf-8") as f:
        f.write("window.IRANSERVER_TLDS = " + json.dumps(latest_tlds, ensure_ascii=False, indent=2) + ";\n")

    print(f"Updated tlds.json and tlds.js successfully ({len(latest_tlds)} TLDs with priority ordering).")

if __name__ == "__main__":
    main()
