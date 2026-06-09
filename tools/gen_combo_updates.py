#!/usr/bin/env python3
"""
Extract COMBO_SYSDATA field configs from old MFC SmTableInformation*.h
and generate UPDATE statements for SM_FIELD_DEF to set FIELD_TYPE='SELECT',
RETRIEVAL_TABLE='SYSDATA', FORMAT=<sysdata_key>.
"""
import re
import os
import glob

def extract_combos(h_files):
    """Extract (TABLE_ID, FIELD_NAME, SYSDATA_FORMAT) from COMBO_SYSDATA entries."""
    results = []
    current_table_id = None

    for h_file in sorted(h_files):
        with open(h_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Find table ID declarations: look for TBLID_B... patterns
        # The file has sections for each table, identified by comments or array names
        lines = content.split('\n')
        for line in lines:
            # Skip commented lines
            stripped = line.strip()
            if stripped.startswith('//') or stripped.startswith('/*'):
                continue

            # Detect table context from array variable names like g_tblInfoBEQP
            tbl_match = re.search(r'g_tblInfo(B\w+)', line)
            if tbl_match:
                current_table_id = 'TBLID_' + tbl_match.group(1).upper()

            # Also detect from TBLID_ constants
            tblid_match = re.search(r'(TBLID_B\w+)', line)
            if tblid_match and 'COMBO' not in line:
                current_table_id = tblid_match.group(1)

            # Extract COMBO_SYSDATA or COMBO_CODE entries only
            # COMBO_TABLE uses RefPicker (… button) via REF_TABLE_ID, not dropdown
            combo_type = None
            combo_keyword = None
            if 'COMBO_SYSDATA' in line and not stripped.startswith('//'):
                combo_type = 'SYSDATA'
                combo_keyword = 'COMBO_SYSDATA'
            elif 'COMBO_CODE' in line and 'COMBO_NONE' not in line and not stripped.startswith('//'):
                combo_type = 'BCODE'
                combo_keyword = 'COMBO_CODE'

            if combo_type:
                # The field name is always the second L"..." in the line
                all_strings = re.findall(r'L"([^"]+)"', line)
                if len(all_strings) < 2:
                    continue
                field_name = all_strings[1].upper()

                # Find the format key: it's the L"..." right after COMBO_SYSDATA/COMBO_CODE
                combo_idx = line.index(combo_keyword)
                after_combo = line[combo_idx:]
                format_strings = re.findall(r'L"([^"]+)"', after_combo)
                if format_strings:
                    format_key = format_strings[0]
                else:
                    continue

                if current_table_id:
                    results.append((current_table_id, field_name, format_key, combo_type))

    return results

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    h_pattern = os.path.join(script_dir, '..', 'Wafer_SMClient', 'SMClient', 'SmTableInformation*.h')
    h_files = glob.glob(h_pattern)

    if not h_files:
        print("No SmTableInformation*.h files found")
        return

    print(f"Scanning {len(h_files)} header files...")
    combos = extract_combos(h_files)
    print(f"Found {len(combos)} COMBO entries")

    # Deduplicate by (TABLE_ID, FIELD_NAME)
    seen = set()
    unique = []
    for item in combos:
        tid, fn, fmt, ctype = item
        key = (tid, fn)
        if key not in seen:
            seen.add(key)
            unique.append(item)

    print(f"Unique (table, field) pairs: {len(unique)}")
    sysdata_count = sum(1 for x in unique if x[3] == 'SYSDATA')
    bcode_count = sum(1 for x in unique if x[3] == 'BCODE')
    print(f"  COMBO_SYSDATA: {sysdata_count}")
    print(f"  COMBO_CODE: {bcode_count}")

    # Generate UPDATE SQL
    data_sql = os.path.join(script_dir, '..', 'java-poc', 'src', 'main', 'resources', 'data.sql')

    lines = []
    lines.append("")
    lines.append("-- ============================================================")
    lines.append("-- COMBO_SYSDATA + COMBO_CODE: Set FIELD_TYPE=SELECT")
    lines.append("-- (auto-generated from SmTableInformation*.h)")
    lines.append("-- ============================================================")

    for tid, fn, fmt, ctype in sorted(unique):
        retrieval = ctype  # 'SYSDATA' or 'BCODE'
        lines.append(
            f"UPDATE SM_FIELD_DEF SET FIELD_TYPE = 'SELECT', RETRIEVAL_TABLE = '{retrieval}', "
            f"FORMAT = '{fmt}' WHERE TABLE_ID = '{tid}' AND FIELD_NAME = '{fn}';"
        )

    with open(data_sql, 'a', encoding='utf-8') as f:
        f.write('\n'.join(lines))
        f.write('\n')

    print(f"Appended {len(unique)} UPDATE statements to data.sql")

if __name__ == '__main__':
    main()
