#!/usr/bin/env python3
"""Parse check rules from wdbtbl.h for specific tables"""
import re, os, sys

SERVER_HDR = "/Users/caolizhu/Documents/VibeCode/MySM/Wafer_SMServer/SMServer/inc/wdbtbl.h"

def parse_checks_for(table_suffixes):
    """
    table_suffixes: list of B-table suffix names (e.g. ['PROD', 'ROUTE', 'OPE'])
    Returns: dict[btable_name] = {SAVE: [...], RELEASE: [...], DELETE: [...]}
    """
    with open(SERVER_HDR, 'r', encoding='latin-1') as f:
        content = f.read()

    tables = {}
    for suffix in table_suffixes:
        btbl = "B" + suffix.upper()
        tables[btbl] = {"SAVE": [], "RELEASE": [], "DELETE": []}

        for chk_type, chk_char in [("SAVE", "E"), ("RELEASE", "R"), ("DELETE", "D")]:
            # Find the check array
            start_pat = r'extern\s+DBRECCHECKTBL\s+g_tChk' + chk_char + suffix + r'\[\]\s*=\s*\{'
            sm = re.search(start_pat, content, re.IGNORECASE)
            if not sm:
                continue

            # Extract content between { and };
            start_pos = sm.end() - 1  # position of the opening {
            depth = 0
            end_pos = start_pos
            for i in range(start_pos, len(content)):
                if content[i] == '{':
                    depth += 1
                elif content[i] == '}':
                    depth -= 1
                    if depth == 0:
                        end_pos = i
                        break
            body = content[start_pos+1:end_pos]

            entries = []
            for line in body.split('\n'):
                line = line.strip()
                if not line or '{-1}' in line:
                    continue
                if line.startswith('//') or line.startswith('/*'):
                    continue
                for vm in re.finditer(r'\{([^}]*)\}', line):
                    vals = [x.strip().strip('"').strip("'") for x in vm.group(1).split(',')]
                    if len(vals) >= 7:
                        entries.append(vals)
            tables[btbl][chk_type] = entries

    return tables

def print_summary(tables):
    for btbl, checks in sorted(tables.items()):
        s = len(checks.get("SAVE", []))
        r = len(checks.get("RELEASE", []))
        d = len(checks.get("DELETE", []))
        print(f"{btbl:15s} SAVE={s:3d}  RELEASE={r:3d}  DELETE={d:3d}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        suffixes = sys.argv[1:]
    else:
        suffixes = ['Prod', 'Route', 'Ope', 'Eqp', 'Area', 'Eqpg']

    tables = parse_checks_for(suffixes)
    print_summary(tables)
