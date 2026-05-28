#!/usr/bin/env python3
"""
Parse wdbtbl.h and Client TABLEINFOEX headers to generate:
1. B/D table schemas (CREATE TABLE)
2. SM_TABLE_DEF + SM_FIELD_DEF + SM_CHECK_DEF INSERT statements
"""
import re, sys, os

SM_DIR = "/Users/caolizhu/Documents/VibeCode/MySM"
WDBTBL = os.path.join(SM_DIR, "Wafer_SMServer/SMServer/inc/wdbtbl.h")

# Control fields shared by all B tables
CONTROL_FIELDS_B = [
    ("REL_FLG", "CHAR(1)", "NOT NULL DEFAULT 'E'"),
    ("COMP_FLG", "CHAR(1)", "NOT NULL DEFAULT 'N'"),
    ("CRE_DATE", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ("CRE_USER", "CHAR(20) NOT NULL DEFAULT 'SYSTEM'"),
    ("LAST_DATE1", "TIMESTAMP"),
    ("LAST_ACT1", "CHAR(12) NOT NULL DEFAULT ''"),
    ("LAST_USER1", "CHAR(20) NOT NULL DEFAULT ''"),
    ("LAST_DATE2", "TIMESTAMP"),
    ("LAST_ACT2", "CHAR(12) NOT NULL DEFAULT ''"),
    ("LAST_USER2", "CHAR(20) NOT NULL DEFAULT ''"),
    ("LAST_DATE3", "TIMESTAMP"),
    ("LAST_ACT3", "CHAR(12) NOT NULL DEFAULT ''"),
    ("LAST_USER3", "CHAR(20) NOT NULL DEFAULT ''"),
    ("LAST_DATE4", "TIMESTAMP"),
    ("LAST_ACT4", "CHAR(12) NOT NULL DEFAULT ''"),
    ("LAST_USER4", "CHAR(20) NOT NULL DEFAULT ''"),
    ("LAST_DATE5", "TIMESTAMP"),
    ("LAST_ACT5", "CHAR(12) NOT NULL DEFAULT ''"),
    ("LAST_USER5", "CHAR(20) NOT NULL DEFAULT ''"),
    ("OWNER", "CHAR(20) NOT NULL DEFAULT 'SYSTEM'"),
    ("OWNERG", "CHAR(10) NOT NULL DEFAULT ''"),
    ("PERMISSION", "CHAR(10) NOT NULL DEFAULT 'PUBLIC    '"),
    ("LOCK_USER", "CHAR(20) NOT NULL DEFAULT ''"),
    ("LOCK_TIME", "TIMESTAMP"),
    ('"COMMENT"', "CHAR(128) NOT NULL DEFAULT ''"),
]

# DB_CHECK types to CHECK_KIND mapping
CHECK_KIND_MAP = {
    "DB_CHECK_STAT_E": "STAT_E",
    "DB_CHECK_STAT_R": "STAT_R",
    "DB_CHECK_STAT_W": "STAT_W",
    "DB_CHECK_NOTNULL": "NOTNULL",
    "DB_CHECK_NULL": "NULLCHK",
    "DB_CHECK_STRING": "STRING",
    "DB_CHECK_KEY": "KEY",
    "DB_CHECK_PARAM": "PARAM",
    "DB_RELEASE_PARAM": "RELEASE_PARAM",
    "DB_RELEASE_WRITE": "RELEASE_WRITE",
    "DB_CHECK_ERRMSG": "ERRMSG",
}

# Known business fields for each table (extracted from schema.sql or inferred)
# Format: (field_name, db_type, db_length, is_key)
# These come from the C header TABLEINFOEX definitions

# ---- Critical missing tables ----

# BUSERG: User Group (4 business fields)
BUSERG_FIELDS = [
    ("USERG_ID", "STRING", 10, "Y"),
    ("USERG_NAME", "STRING", 40, "N"),
    ("USERG_DESC", "STRING", 80, "N"),
    ("MENU_FLG", "STRING", 128, "N"),
    ("ADMIN_FLG", "STRING", 1, "N"),
]

def parse_check_arrays():
    """Parse all g_tChkE/R/D arrays from wdbtbl.h"""
    with open(WDBTBL, 'r') as f:
        content = f.read()

    tables = {}

    # Find all g_tChkE arrays (SAVE checks)
    pattern = r'extern DBRECCHECKTBL g_tChk(E|R|D)(\w+)\[\] = \{([^;]+)\}'
    for m in re.finditer(pattern, content, re.DOTALL):
        check_type_char = m.group(1)
        table_name = m.group(2)
        body = m.group(3)

        check_type = {"E": "SAVE", "R": "RELEASE", "D": "DELETE"}[check_type_char]

        if table_name not in tables:
            tables[table_name] = {"SAVE": [], "RELEASE": [], "DELETE": []}

        # Parse individual check entries
        entries = parse_check_body(body)
        tables[table_name][check_type] = entries

    return tables

def parse_check_body(body):
    """Parse DBRECCHECKTBL entries from array body"""
    entries = []
    # Each entry looks like: {group,parent,result,errmsg,table,column,check_type,param_size,ref_table,ref_column,...}
    # Simplified parsing
    lines = body.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line or line == '{-1}' or line == '{-1,}':
            continue
        if line.startswith('//') or line.startswith('/*'):
            continue
        # Extract values between { }
        m = re.match(r'\{([^}]+)\}', line)
        if not m:
            continue
        values = [v.strip().strip('"').strip("'") for v in m.group(1).split(',')]
        if len(values) < 7:
            continue
        entries.append(values)
    return entries

def lookup_db_type(field_name, db_type_str):
    """Map DBVT_* to our types"""
    if "NUMBER" in db_type_str or "INT" in db_type_str or "DBVT_NUMBER" == db_type_str:
        return "NUMBER"
    if "DOUBLE" in db_type_str or "DBVT_DOUBLE" == db_type_str:
        return "DOUBLE"
    return "STRING"

def main():
    tables = parse_check_arrays()

    print(f"Found {len(tables)} tables with check rules\n")

    # List all tables sorted
    for i, (tname, checks) in enumerate(sorted(tables.items())):
        has_save = bool(checks["SAVE"])
        has_rel = bool(checks["RELEASE"])
        has_del = bool(checks["DELETE"])
        print(f"{i+1:3d}. {tname:30s} SAVE:{has_save} REL:{has_rel} DEL:{has_del}  "
              f"S={len(checks['SAVE'])} R={len(checks['RELEASE'])} D={len(checks['DELETE'])}")

if __name__ == '__main__':
    main()
