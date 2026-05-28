#!/usr/bin/env python3
"""
Parse wdbtbl.h + SmTableInformation*.h to generate:
  - schema.sql  (B/D table CREATE TABLE)
  - data.sql    (SM_TABLE_DEF, SM_FIELD_DEF, SM_CHECK_DEF, seed data)

Usage: python3 generate_sql.py [--dry-run]
  --dry-run: print tables found without writing files
"""
import re, os, sys, json
from collections import OrderedDict

SM_DIR = "/Users/caolizhu/Documents/VibeCode/MySM"
SERVER_DIR = os.path.join(SM_DIR, "Wafer_SMServer/SMServer/inc")
CLIENT_DIR = os.path.join(SM_DIR, "Wafer_SMClient/SMClient")

WDBTBL = os.path.join(SERVER_DIR, "wdbtbl.h")
CLIENT_HEADERS = [
    os.path.join(CLIENT_DIR, "SmTableInformation1.h"),
    os.path.join(CLIENT_DIR, "SmTableInformation2.h"),
    os.path.join(CLIENT_DIR, "SmTableInformation3.h"),
    os.path.join(CLIENT_DIR, "SmTableInformation4.h"),
]

OUTPUT_DIR = os.path.join(SM_DIR, "java-poc/src/main/resources")

# CHECK_KIND mapping from DB_CHECK_* constants
CHECK_MAP = {
    "DB_CHECK_STAT_E":     ("STAT_E",       None),
    "DB_CHECK_STAT_R":     ("STAT_R",       None),
    "DB_CHECK_STAT_W":     ("STAT_E",       None),  # Map STAT_W -> STAT_E (our system uses E)
    "DB_CHECK_NOTNULL":    ("NOTNULL",      None),
    "DB_CHECK_NULL":       ("NULLCHK",      None),
    "DB_CHECK_STRING":     ("STRING",       "expectValue"),
    "DB_CHECK_KEY":        ("KEY",          "refTable,refField"),
    "DB_CHECK_PARAM":      ("PARAM",        None),  # parameter pass-through
    "DB_CHECK_ERRMSG":    ("ERRMSG",        None),
    "DB_RELEASE_PARAM":    ("RELEASE_PARAM", "refTable"),
    "DB_RELEASE_WRITE":    ("RELEASE_WRITE", "refTable"),
    "DB_MOD_PARAM":        ("PARAM",         None),
}

# DBVT_* to our DB_TYPE mapping
DBVT_MAP = {
    "DBVT_STRING": "STRING",
    "DBVT_NUMBER": "NUMBER",
    "DBVT_DOUBLE": "DOUBLE",
    "DBVT_INT":    "NUMBER",
}

CHAR_TO_DB = {"CHAR": "STRING", "INT": "NUMBER", "DOUBLE": "DOUBLE", "TIMESTAMP": "TIMESTAMP"}

def parse_check_arrays():
    """Parse g_tChkE/R/D arrays from wdbtbl.h"""
    with open(WDBTBL, 'r', encoding='latin-1') as f:
        content = f.read()

    tables = OrderedDict()
    pattern = r'extern\s+DBRECCHECKTBL\s+g_tChk([ERD])(\w+)\[\]\s*=\s*\{([^;]+?)\n\};'
    for m in re.finditer(pattern, content, re.DOTALL):
        chk_char = m.group(1)
        tbl_suffix = m.group(2)
        body = m.group(3)

        chk_type = {"E": "SAVE", "R": "RELEASE", "D": "DELETE"}[chk_char]

        # Normalize table name
        btbl = "B" + tbl_suffix.upper()
        if btbl not in tables:
            tables[btbl] = {"SAVE": [], "RELEASE": [], "DELETE": [], "has_editcomp": False}

        entries = parse_check_body(body)
        # Also check if there's a separate EditComp check
        # EditComp uses the SAVE (E) check type but has different structure
        tables[btbl][chk_type] = entries

        # Detect if this is actually EditComp (has STAT_E + COMP_N pattern, or explicitly noted)
        # The first g_tChkE is EditComp if there are two g_tChkE arrays for the same table
        # We'll handle this later

    return tables

def parse_check_body(body):
    """Parse DBRECCHECKTBL entries from array body"""
    entries = []
    for line in body.split('\n'):
        line = line.strip()
        if not line or line in ('{-1}', '{-1,}'):
            continue
        if line.startswith('//') or line.startswith('/*'):
            # Check if it's a comment with WRN_ identifier
            cmt = line.lstrip('/').lstrip('*').lstrip('/').strip()
            if 'WRN_' in cmt:
                # Extract warning message identifier
                pass
            continue

        # Find all { ... } blocks in the line
        for m in re.finditer(r'\{([^}]*)\}', line):
            vals = [v.strip().strip('"').strip("'") for v in m.group(1).split(',')]
            if len(vals) >= 7:
                entries.append(vals)
    return entries

def parse_client_fields():
    """Parse TABLEINFOEX from SmTableInformation*.h"""
    table_fields = OrderedDict()
    current_table = None

    for hdr in CLIENT_HEADERS:
        if not os.path.exists(hdr):
            continue
        with open(hdr, 'r', encoding='latin-1') as f:
            content = f.read()

        # Find #if (TABLEID==TBLID_XXXX) ... #endif
        pattern = r'#if\s*\(TABLEID\s*==\s*(TBLID_\w+)\)(.*?)(?=#if\s*\(TABLEID|#endif\s*$|\Z)'
        for m in re.finditer(pattern, content, re.DOTALL):
            table_id = m.group(1)
            block = m.group(2)

            # Extract the TABLEINFORMATION array
            arr_pat = r'static\s+const\s+TABLEINFOEX\s+TABLEINFORMATION\s*\[\]\s*=\s*\{(.*?)\}\s*;'
            arr_m = re.search(arr_pat, block, re.DOTALL)
            if not arr_m:
                continue
            arr_body = arr_m.group(1)

            btbl_name = table_id.replace("TBLID_", "")
            if btbl_name not in table_fields:
                table_fields[btbl_name] = []

            fields = parse_field_entries(arr_body)
            table_fields[btbl_name].extend(fields)

    return table_fields

def parse_field_entries(body):
    """Parse individual field entries from TABLEINFOEX"""
    fields = []
    # Each field is {L"...", L"...", FLD_xxx, DBVT_xxx, ...}
    # Use a multi-line approach
    lines = body.split('\n')
    current = ""
    for line in lines:
        line = line.strip()
        if not line or line.startswith('//') or line.startswith('/*'):
            continue
        current += line
        if current.count('{') > current.count('}'):
            continue  # incomplete entry

        # We have a complete entry
        m = re.search(r'\{([^}]*)\}', current)
        if m:
            content_inner = m.group(1)
            field = parse_single_field(content_inner)
            if field:
                fields.append(field)
        current = ""

    return fields

def parse_single_field(content):
    """Parse a single field entry"""
    # Split by commas, but handle L"..." strings
    parts = []
    current = ""
    in_string = False
    for c in content:
        if c == '"':
            in_string = not in_string
            current += c
        elif c == ',' and not in_string:
            parts.append(current.strip())
            current = ""
        else:
            current += c
    if current.strip():
        parts.append(current.strip())

    if len(parts) < 25:
        return None

    def strip_l(s):
        s = s.strip().strip('"')
        if s.startswith('L"'):
            s = s[2:]
        return s.strip().strip('"')

    def yn(s):
        return 'Y' if s.strip().upper() in ('Y', '1') else 'N'

    def map_dbtype(dbt):
        for prefix, mapped in DBVT_MAP.items():
            if dbt.strip().startswith(prefix):
                return mapped
        return 'STRING'

    def map_fieldtype(ft):
        if 'STRING' in ft.upper():
            return 'STRING'
        if 'NUMBER' in ft.upper() or 'INT' in ft.upper():
            return 'NUMBER'
        if 'DOUBLE' in ft.upper():
            return 'NUMBER'
        if 'SELECT' in ft.upper() or 'COMBO' in ft.upper():
            return 'SELECT'
        return 'STRING'

    def map_retrieval(rt):
        rt = rt.strip()
        if 'COMBO_NONE' in rt:
            return 'NONE'
        if 'COMBO_TABLE' in rt:
            return 'SYSDATA'
        return 'NONE'

    def int_or(val, default):
        try:
            return int(val.strip())
        except:
            return default

    field = {
        'fieldName': strip_l(parts[2]).replace('FLD_', ''),
        'jpTitle': strip_l(parts[0]),
        'usTitle': strip_l(parts[1]),
        'dbType': map_dbtype(parts[3]),
        'dbLength': int_or(parts[4], 0),
        'isKey': yn(parts[5]),
        'notBlank': yn(parts[6]),
        'isDummy': yn(parts[7]),
        'isSearchItem': yn(parts[8]),
        'sortNo': int_or(parts[9], -1),
        'treeLevel': int_or(parts[10], -1),
        'sheetNo': int_or(parts[11], -1),
        'pageNo': int_or(parts[12], -1),
        'propertyNo': int_or(parts[13], -1),
        'isAuto': yn(parts[14]),
        'isMandatory': yn(parts[15]),
        'systemReadonly': yn(parts[16]),
        'fieldType': map_fieldtype(parts[17]),
        'fieldLength': int_or(parts[18], 0),
        'inputAlphabet': yn(parts[19]),
        'inputMultibyte': int_or(parts[20], 0),
        'inputNumeric': yn(parts[21]),
        'inputSymbol': yn(parts[22]),
        'inputUppercase': yn(parts[23]),
        'retrievalTable': map_retrieval(parts[24]),
        'format': None if 'NULL' in parts[25].upper() else strip_l(parts[25]),
        'defaultValue': None if 'NULL' in parts[26].upper() else strip_l(parts[26]),
        'minValue': None if 'NULL' in parts[27].upper() else strip_l(parts[27]),
        'maxValue': None if 'NULL' in parts[28].upper() else strip_l(parts[28]),
        'calendarButton': yn(parts[29]),
        'jumpButton': yn(parts[30]),
        'openButton': int_or(parts[31], 0),
        'refTableId': None,
        'refFieldName': None,
        'specialButton': int_or(parts[34], 0) if len(parts) >= 35 else 0,
    }

    # Handle ref_table_id and ref_field_name (parts 32, 33)
    if len(parts) >= 34:
        ref = parts[32].strip()
        if ref and '-1' not in ref and 'NULL' not in ref.upper() and 'TBLID_' in ref:
            field['refTableId'] = ref.strip()
    if len(parts) >= 35:
        ref_fld = parts[33].strip()
        if ref_fld and ref_fld != 'NULL' and 'FLD_' in ref_fld:
            field['refFieldName'] = ref_fld.strip().replace('FLD_', '')

    return field

def convert_checks_to_config(btbl_name, checks):
    """Convert DBRECCHECKTBL entries to SM_CHECK_DEF records"""
    config = {"SAVE": [], "RELEASE": [], "DELETE": [], "EDITCOMP": []}
    key_fields = set()

    for chk_type in ["SAVE", "RELEASE", "DELETE"]:
        entries = checks.get(chk_type, [])
        order = 1
        seen_kinds = set()

        for entry in entries:
            if len(entry) < 7:
                continue

            group_no = int(entry[0]) if entry[0].isdigit() or (entry[0].startswith('-') and entry[0][1:].isdigit()) else 0
            check_condition = entry[6].strip().upper() if len(entry) > 6 else ""

            # Skip release metadata (group -2)
            if group_no == -2:
                chk_type_for_entry = "RELEASE"
                if check_condition.startswith("DB_RELEASE_PARAM"):
                    kind = "RELEASE_PARAM"
                    ref_tbl = entry[8] if len(entry) > 8 else ""
                    if ref_tbl:
                        ref_tbl = "D" + ref_tbl.replace("D", "").lstrip("B")
                elif check_condition.startswith("DB_RELEASE_WRITE"):
                    kind = "RELEASE_WRITE"
                    ref_tbl = entry[8] if len(entry) > 8 else ""
                    if ref_tbl:
                        ref_tbl = "D" + ref_tbl.replace("D", "").lstrip("B")
                else:
                    continue

                field_name = entry[5].strip()
                if field_name and field_name != '""' and field_name != '""':
                    field_name = field_name.strip('"').strip()
                else:
                    continue

                rec = {"checkType": chk_type_for_entry, "checkOrder": order,
                       "checkKind": kind, "fieldName": field_name,
                       "refTable": ref_tbl}
                order += 1
                config[chk_type_for_entry].append(rec)
                continue

            # Map check condition
            mapped = CHECK_MAP.get(check_condition)
            if not mapped:
                continue

            kind, extra = mapped
            if kind == "PARAM":
                # PARAM = primary key parameter, used in SAVE to identify key fields
                field_name = entry[5].strip()
                if field_name:
                    key_fields.add(field_name)
                continue

            if kind == "ERRMSG":
                continue  # Error messages are informational, not actionable

            field_name = entry[5].strip() if len(entry) > 5 else ""
            err_msg = entry[3] if len(entry) > 3 and entry[3] and not entry[3].isdigit() and 'WRN_' not in entry[3] else ""
            err_msg = err_msg.strip() if err_msg else ""
            if 'WRN_' in entry[3]:
                err_msg = "检查失败"

            ref_table = entry[8] if len(entry) > 8 else ""
            ref_field = entry[9] if len(entry) > 9 else ""

            rec = {
                "checkType": chk_type,
                "checkOrder": order,
                "checkKind": kind,
                "fieldName": field_name if field_name else None,
                "refTable": None,
                "refField": None,
                "expectValue": None,
                "errMsg": err_msg if err_msg else None,
            }

            if kind == "KEY" and extra:
                rec["refTable"] = ref_table
                rec["refField"] = ref_field
            elif kind == "STRING":
                rec["expectValue"] = entry[9] if len(entry) > 9 else ""
            elif kind in ("RELEASE_PARAM", "RELEASE_WRITE"):
                rec["refTable"] = ref_table

            if kind == "RELEASE_PARAM" or kind == "RELEASE_WRITE":
                pass
            elif rec["checkOrder"] < 100 and kind not in seen_kinds:
                pass

            config[chk_type].append(rec)
            order += 1

    return config, key_fields

def field_sql_type(db_type, db_length):
    """Map our DB types to SQL types"""
    if db_type == "NUMBER":
        return "INT"
    if db_type == "DOUBLE":
        return "DOUBLE"
    if db_type == "TIMESTAMP":
        return "TIMESTAMP"
    return f"CHAR({db_length})"

def generate_schema(tables_data):
    """Generate CREATE TABLE SQL"""
    lines = []
    lines.append("-- Auto-generated from wdbtbl.h + SmTableInformation*.h")
    lines.append("-- Generated by tools/generate_sql.py\n")

    for btbl_name, data in tables_data.items():
        fields = data.get("fields", [])
        if not fields:
            continue

        # B table
        btbl = btbl_name
        primary_keys = [f for f in fields if f['isKey'] == 'Y']

        lines.append(f"CREATE TABLE {btbl} (")
        for f in fields:
            sql_type = field_sql_type(f['dbType'], f['dbLength'])
            not_null = "NOT NULL" if f['notBlank'] == 'Y' else ""
            default_val = ""
            if f['defaultValue'] and f['defaultValue'] != '':
                default_val = f"DEFAULT '{f['defaultValue']}'"
            lines.append(f"    {f['fieldName']:30s} {sql_type:12s} {not_null} {default_val},".rstrip(',') + ",")
        # Control fields
        lines.append("    -- Control fields")
        lines.append("    REL_FLG     CHAR(1)  NOT NULL DEFAULT 'E',")
        lines.append("    COMP_FLG    CHAR(1)  NOT NULL DEFAULT 'N',")
        lines.append("    CRE_DATE    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,")
        lines.append("    CRE_USER    CHAR(20) NOT NULL DEFAULT 'SYSTEM',")
        lines.append("    LAST_DATE1  TIMESTAMP,")
        lines.append("    LAST_ACT1   CHAR(12) NOT NULL DEFAULT '',")
        lines.append("    LAST_USER1  CHAR(20) NOT NULL DEFAULT '',")
        lines.append("    LAST_DATE2  TIMESTAMP,")
        lines.append("    LAST_ACT2   CHAR(12) NOT NULL DEFAULT '',")
        lines.append("    LAST_USER2  CHAR(20) NOT NULL DEFAULT '',")
        lines.append("    LAST_DATE3  TIMESTAMP,")
        lines.append("    LAST_ACT3   CHAR(12) NOT NULL DEFAULT '',")
        lines.append("    LAST_USER3  CHAR(20) NOT NULL DEFAULT '',")
        lines.append("    LAST_DATE4  TIMESTAMP,")
        lines.append("    LAST_ACT4   CHAR(12) NOT NULL DEFAULT '',")
        lines.append("    LAST_USER4  CHAR(20) NOT NULL DEFAULT '',")
        lines.append("    LAST_DATE5  TIMESTAMP,")
        lines.append("    LAST_ACT5   CHAR(12) NOT NULL DEFAULT '',")
        lines.append("    LAST_USER5  CHAR(20) NOT NULL DEFAULT '',")
        lines.append("    OWNER       CHAR(20) NOT NULL DEFAULT 'SYSTEM',")
        lines.append("    OWNERG      CHAR(10) NOT NULL DEFAULT '',")
        lines.append("    PERMISSION  CHAR(10) NOT NULL DEFAULT 'PUBLIC    ',")
        lines.append("    LOCK_USER   CHAR(20) NOT NULL DEFAULT '',")
        lines.append("    LOCK_TIME   TIMESTAMP,")
        lines.append('    "COMMENT"   CHAR(128) NOT NULL DEFAULT \'\',')

        pk_names = [f['fieldName'] for f in primary_keys] + ['REL_FLG']
        lines.append(f"    PRIMARY KEY ({', '.join(pk_names)})")
        lines.append(");\n")

        # D table (no control fields, no REL_FLG in PK)
        dtbl = "D" + btbl_name[1:] if btbl_name.startswith('B') else "D" + btbl_name
        lines.append(f"CREATE TABLE {dtbl} (")
        for f in fields:
            sql_type = field_sql_type(f['dbType'], f['dbLength'])
            not_null = "NOT NULL" if f['notBlank'] == 'Y' else ""
            lines.append(f"    {f['fieldName']:30s} {sql_type:12s} {not_null},")
        d_pk_names = [f['fieldName'] for f in primary_keys]
        lines.append(f"    PRIMARY KEY ({', '.join(d_pk_names)})")
        lines.append(");\n")

    return '\n'.join(lines)

def generate_data(tables_data):
    """Generate data.sql (SM_TABLE_DEF, SM_FIELD_DEF, SM_CHECK_DEF)"""
    lines = []
    lines.append("-- Auto-generated from wdbtbl.h + SmTableInformation*.h")
    lines.append("-- Generated by tools/generate_sql.py\n")

    sort_counter = 10

    for btbl_name, data in tables_data.items():
        fields = data.get("fields", [])
        if not fields:
            continue

        table_id = "TBLID_" + btbl_name
        jp_title = btbl_name  # Will be overridden if client data has it

        # SM_TABLE_DEF
        has_dummy = 'Y' if any(f['isDummy'] == 'Y' for f in fields) else 'N'
        lines.append(f"-- {btbl_name}")
        lines.append(f"INSERT INTO SM_TABLE_DEF (TABLE_ID, TABLE_NAME, JP_TITLE, US_TITLE, RELEASE_FLAG, DISTRIBUTE_FLAG, PERMISSION_TYPE, SCHEMA_TYPE, HAS_DUMMY, SORT_NO)")
        lines.append(f"VALUES ('{table_id}', '{btbl_name}', '{jp_title}', '{jp_title}', 'Y', 'N', 'C', 'L', '{has_dummy}', {sort_counter});")
        sort_counter += 10

        # SM_FIELD_DEF
        for f in fields:
            cols = "TABLE_ID,FIELD_NAME,JP_TITLE,US_TITLE,DB_TYPE,DB_LENGTH,IS_KEY,NOT_BLANK,IS_DUMMY,IS_SEARCH_ITEM,SORT_NO,TREE_LEVEL,SHEET_NO,PAGE_NO,PROPERTY_NO,IS_AUTO,IS_MANDATORY,SYSTEM_READONLY,FIELD_TYPE,FIELD_LENGTH,INPUT_ALPHABET,INPUT_MULTIBYTE,INPUT_NUMERIC,INPUT_SYMBOL,INPUT_UPPERCASE,RETRIEVAL_TABLE,FORMAT,DEFAULT_VALUE,MIN_VALUE,MAX_VALUE,CALENDAR_BUTTON,JUMP_BUTTON,OPEN_BUTTON,REF_TABLE_ID,REF_FIELD_NAME,SPECIAL_BUTTON"
            vals = f"'{table_id}','{f['fieldName']}','{f['jpTitle']}','{f['usTitle']}','{f['dbType']}',{f['dbLength']},'{f['isKey']}','{f['notBlank']}','{f['isDummy']}','{f['isSearchItem']}',{f['sortNo']},{f['treeLevel']},{f['sheetNo']},{f['pageNo']},{f['propertyNo']},'{f['isAuto']}','{f['isMandatory']}','{f['systemReadonly']}','{f['fieldType']}',{f['fieldLength']},'{f['inputAlphabet']}',{f['inputMultibyte']},'{f['inputNumeric']}','{f['inputSymbol']}','{f['inputUppercase']}','{f['retrievalTable']}',{f['format'] and repr(f['format']) or 'NULL'},{f['defaultValue'] and repr(f['defaultValue']) or 'NULL'},{f['minValue'] and repr(f['minValue']) or 'NULL'},{f['maxValue'] and repr(f['maxValue']) or 'NULL'},'{f['calendarButton']}','{f['jumpButton']}',{f['openButton']},{f['refTableId'] and repr(f['refTableId']) or 'NULL'},{f['refFieldName'] and repr(f['refFieldName']) or 'NULL'},{f['specialButton']}"
            lines.append(f"INSERT INTO SM_FIELD_DEF ({cols}) VALUES ({vals});")

        # SM_CHECK_DEF
        chk_cfg = data.get("check_config", {})
        for chk_type in ["SAVE", "RELEASE", "DELETE", "EDITCOMP"]:
            checks = chk_cfg.get(chk_type, [])
            if not checks:
                continue
            for c in checks:
                cols = "TABLE_ID,CHECK_TYPE,CHECK_ORDER,CHECK_KIND,FIELD_NAME,REF_TABLE,REF_FIELD,EXPECT_VALUE,ERR_MSG"
                vals = f"'{table_id}','{chk_type}',{c.get('checkOrder',0)},'{c.get('checkKind','')}',{c.get('fieldName') and repr(c.get('fieldName')) or 'NULL'},{c.get('refTable') and repr(c.get('refTable')) or 'NULL'},{c.get('refField') and repr(c.get('refField')) or 'NULL'},{c.get('expectValue') and repr(c.get('expectValue')) or 'NULL'},{c.get('errMsg') and repr(c.get('errMsg')) or 'NULL'}"
                lines.append(f"INSERT INTO SM_CHECK_DEF ({cols}) VALUES ({vals});")

        lines.append("")  # blank line separator

    return '\n'.join(lines)

def main():
    dry_run = '--dry-run' in sys.argv

    print("Parsing check arrays from wdbtbl.h...")
    check_tables = parse_check_arrays()
    print(f"  Found {len(check_tables)} tables with check rules")

    print("\nParsing field definitions from SmTableInformation*.h...")
    field_tables = parse_client_fields()
    print(f"  Found {len(field_tables)} tables with field definitions")

    # Merge data
    all_tables = OrderedDict()
    all_names = set(check_tables.keys()) | set(field_tables.keys())

    # Priority: show tables that are in both sources first
    both = [n for n in all_names if n in check_tables and n in field_tables]
    check_only = [n for n in all_names if n in check_tables and n not in field_tables]
    field_only = [n for n in all_names if n not in check_tables and n in field_tables]

    print(f"\n  Both: {len(both)} tables")
    print(f"  Check-only: {len(check_only)} tables")
    print(f"  Field-only: {len(field_only)} tables")

    if dry_run:
        print("\n=== Tables with BOTH check + field data ===")
        for name in sorted(both):
            print(f"  {name:30s} fields={len(field_tables.get(name,[]))} checks={sum(len(v) for v in check_tables.get(name,{}).values())}")
        print(f"\n=== Field-only tables ===")
        for name in sorted(field_only):
            print(f"  {name:30s} fields={len(field_tables.get(name,[]))}")
        return

    # Build merged data for SQL generation
    merged = OrderedDict()
    for name in both:
        merged[name] = {
            "fields": field_tables[name],
            "checks": check_tables.get(name, {}),
        }

        # Generate check config
        chk_cfg, key_fields = convert_checks_to_config(name, check_tables.get(name, {}))
        merged[name]["check_config"] = chk_cfg

    print(f"\nGenerating SQL for {len(merged)} tables...")
    schema_sql = generate_schema(merged)
    data_sql = generate_data(merged)

    schema_path = os.path.join(OUTPUT_DIR, "schema_auto.sql")
    data_path = os.path.join(OUTPUT_DIR, "data_auto.sql")

    with open(schema_path, 'w') as f:
        f.write(schema_sql)
    with open(data_path, 'w') as f:
        f.write(data_sql)

    print(f"\nGenerated:")
    print(f"  {schema_path}  ({len(schema_sql)} bytes)")
    print(f"  {data_path}    ({len(data_sql)} bytes)")

    # Print summary of issues
    print("\n=== Quality Report ===")
    for name, data in merged.items():
        fields = data.get("fields", [])
        chk_cfg = data.get("check_config", {})
        issues = []

        # Check for fields with garbled names
        for f in fields:
            if len(f['fieldName']) > 40:
                issues.append(f"long_field_name: {f['fieldName'][:50]}")
            if any(ord(c) > 0x3000 for c in f['jpTitle']):
                pass  # Japanese chars are fine

        # Count checks
        total_checks = sum(len(v) for v in chk_cfg.values())

        if issues:
            print(f"  {name}: {len(fields)} fields, {total_checks} checks - ISSUES: {issues[:3]}")
        elif len(fields) == 0:
            print(f"  {name}: NO FIELDS - {total_checks} checks")
        elif total_checks == 0:
            print(f"  {name}: {len(fields)} fields, NO CHECKS")

if __name__ == '__main__':
    main()
