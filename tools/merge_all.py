#!/usr/bin/env python3
"""
Combined migration tool: reads DDL + client TABLEINFOEX + server check rules,
generates complete schema.sql and data.sql for target B tables.

Usage:
  python3 merge_all.py                    # generate all tables
  python3 merge_all.py --tables BCODE,BUSER,BUSERG  # specific tables only
  python3 merge_all.py --verbose          # show field-level detail
"""
import re, os, sys

SM_DIR = "/Users/caolizhu/Documents/VibeCode/MySM"
DDL_FILE = os.path.join(SM_DIR, "WV-MMDBD_20241223_LS2.ddl")
SERVER_HDR = os.path.join(SM_DIR, "Wafer_SMServer/SMServer/inc/wdbtbl.h")
CLIENT_HDRS = [
    os.path.join(SM_DIR, "Wafer_SMClient/SMClient/SmTableInformation1.h"),
    os.path.join(SM_DIR, "Wafer_SMClient/SMClient/SmTableInformation2.h"),
    os.path.join(SM_DIR, "Wafer_SMClient/SMClient/SmTableInformation3.h"),
    os.path.join(SM_DIR, "Wafer_SMClient/SMClient/SmTableInformation4.h"),
]
OUT_DIR = os.path.join(SM_DIR, "java-poc/src/main/resources")

# ---------------------------------------------------------------------------
# Part 1: Parse DDL (column names, types, lengths)
# ---------------------------------------------------------------------------
def parse_ddl(filepath):
    tables = {}
    with open(filepath, 'r') as f:
        content = f.read()

    pattern = r'CREATE\s+TABLE\s+"[^"]+"\."([^"]+)"\s*\((.*?)\)\s*;'
    for m in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
        tbl_name = m.group(1)
        body = m.group(2)
        cols = parse_ddl_columns(body)
        if cols:
            tables[tbl_name] = cols
    return tables

def parse_ddl_columns(body):
    """Parse column definitions, handling multi-line entries"""
    columns = []
    # Split by top-level commas that aren't inside parens
    entries = split_ddl_entries(body)
    for entry in entries:
        m = re.match(r'\s*"([^"]+)"\s+(.+)$', entry, re.IGNORECASE)
        if not m:
            continue
        name = m.group(1)
        type_def = m.group(2).strip()

        # Extract type and length
        type_m = re.match(r'(\w+)\s*(\([^)]*\))?\s*(.*)', type_def, re.IGNORECASE)
        if not type_m:
            continue
        db_type = type_m.group(1).upper()
        len_str = type_m.group(2) or ""
        rest = type_m.group(3).upper()

        # Extract numeric length
        len_num = 0
        num_m = re.search(r'(\d+)', len_str)
        if num_m:
            len_num = int(num_m.group(1))

        not_null = "NOT NULL" in rest

        # Extract default
        default = None
        def_m = re.search(r"DEFAULT\s+('[^']*'|\w+)", rest)
        if def_m:
            default = def_m.group(1)

        columns.append({
            "name": name,
            "dbType": db_type,
            "length": len_num,
            "notNull": not_null,
            "default": default,
        })
    return columns

def split_ddl_entries(body):
    """Split CREATE TABLE body into individual entries"""
    entries = []
    current = ""
    depth = 0
    for c in body:
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
        if c == ',' and depth == 0:
            entries.append(current.strip())
            current = ""
        else:
            current += c
    if current.strip():
        entries.append(current.strip())
    return entries

# ---------------------------------------------------------------------------
# Part 2: Parse Client TABLEINFOEX (JP/US titles, KEY flags, etc.)
# ---------------------------------------------------------------------------
def parse_client_headers():
    tables = {}
    for hdr in CLIENT_HDRS:
        if not os.path.exists(hdr):
            continue
        with open(hdr, 'r', encoding='latin-1') as f:
            content = f.read()

        # Find each table block
        blocks = re.split(r'#if\s*\(TABLEID\s*==\s*TBLID_\w+\)', content)
        ids = re.findall(r'#if\s*\(TABLEID\s*==\s*(TBLID_\w+)\)', content)

        for i, tbl_id in enumerate(ids):
            if i >= len(blocks) - 1:
                break
            block = blocks[i + 1]

            arr_m = re.search(r'TABLEINFORMATION\s*\[\]\s*=\s*\{(.*?)\}\s*;', block, re.DOTALL)
            if not arr_m:
                continue

            btbl = "B" + tbl_id.replace("TBLID_B", "").replace("TBLID_", "")
            fields = parse_client_fields(arr_m.group(1))
            if fields:
                tables[btbl] = fields
    return tables

def parse_client_fields(body):
    """Parse TABLEINFOEX field entries"""
    fields = []
    entries = split_c_entries(body)
    DBVT_MAP = {"DBVT_STRING": "STRING", "DBVT_NUMBER": "NUMBER", "DBVT_DOUBLE": "DOUBLE", "DBVT_INT": "NUMBER"}

    for entry in entries:
        parts = split_c_values(entry)
        if len(parts) < 25:
            continue

        def strip_l(s):
            s = s.strip().strip('"')
            for prefix in ['L"', 'l"']:
                if prefix in s:
                    s = s.split(prefix, 1)[-1]
            return s.strip().strip('"')

        def yn(s):
            return 'Y' if s.strip().upper() in ('Y', '1') else 'N'

        def map_dbtype(dbt):
            for prefix, mapped in DBVT_MAP.items():
                if prefix in dbt.strip():
                    return mapped
            return 'STRING'

        def map_ftype(ft):
            fu = ft.strip().upper()
            if 'SELECT' in fu or 'COMBO' in fu: return 'SELECT'
            if 'NUMBER' in fu: return 'NUMBER'
            if 'DOUBLE' in fu: return 'NUMBER'
            return 'STRING'

        def map_retrieval(rt):
            ru = rt.strip().upper()
            if 'NONE' in ru: return 'NONE'
            if 'TABLE' in ru or 'SYSDATA' in ru: return 'SYSDATA'
            return ru

        def int_or(val, default):
            try: return int(val.strip())
            except: return default

        field_name = strip_l(parts[2]).replace('FLD_', '')

        # Extract ref table and ref field
        ref_table_id = None
        ref_field_name = None
        if len(parts) >= 33:
            r = parts[32].strip()
            if r and 'TBLID_' in r and '-1' not in r:
                ref_table_id = r.strip()
        if len(parts) >= 34:
            r = parts[33].strip()
            if r and 'FLD_' in r:
                ref_field_name = r.strip().replace('FLD_', '')

        def safe_part(idx, default=None):
            return parts[idx] if len(parts) > idx else default

        fields.append({
            "fieldName": field_name,
            "jpTitle": strip_l(parts[0]),
            "usTitle": strip_l(parts[1]),
            "dbType": map_dbtype(parts[3]),
            "dbLength": int_or(parts[4], 0),
            "isKey": yn(parts[5]),
            "notBlank": yn(parts[6]),
            "isDummy": yn(parts[7]),
            "isSearchItem": yn(parts[8]),
            "sortNo": int_or(parts[9], -1),
            "treeLevel": int_or(parts[10], -1),
            "sheetNo": int_or(parts[11], -1),
            "pageNo": int_or(parts[12], -1),
            "propertyNo": int_or(parts[13], -1),
            "isAuto": yn(parts[14]),
            "isMandatory": yn(parts[15]),
            "systemReadonly": yn(parts[16]),
            "fieldType": map_ftype(parts[17]),
            "fieldLength": int_or(parts[18], 0),
            "inputAlphabet": yn(safe_part(19, 'Y')),
            "inputMultibyte": int_or(safe_part(20, 0), 0),
            "inputNumeric": yn(safe_part(21, 'Y')),
            "inputSymbol": yn(safe_part(22, 'Y')),
            "inputUppercase": yn(safe_part(23, 'Y')),
            "retrievalTable": map_retrieval(safe_part(24, 'COMBO_NONE')),
            "format": None if is_null(safe_part(25)) else strip_l(safe_part(25, '')),
            "defaultValue": None if is_null(safe_part(26)) else strip_l(safe_part(26, '')),
            "minValue": None if is_null(safe_part(27)) else strip_l(safe_part(27, '')),
            "maxValue": None if is_null(safe_part(28)) else strip_l(safe_part(28, '')),
            "calendarButton": yn(safe_part(29, 'N')),
            "jumpButton": yn(safe_part(30, 'N')),
            "openButton": int_or(safe_part(31, 0), 0),
            "refTableId": ref_table_id,
            "refFieldName": ref_field_name,
            "specialButton": int_or(safe_part(34, 0), 0),
        })
    return fields

def split_c_entries(body):
    """Split TABLEINFOEX entries, handling { ... } blocks with nested braces"""
    entries = []
    current = ""
    depth = 0
    for c in body:
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                entries.append(current)
                current = ""
                continue
        if depth > 0:
            current += c
    return entries

def split_c_values(entry):
    """Split comma-separated values, handling quoted strings"""
    parts = []
    current = ""
    in_quote = False
    quote_char = None
    for c in entry:
        if c in ('"', "'") and not in_quote:
            in_quote = True
            quote_char = c
        elif c == quote_char and in_quote:
            in_quote = False
            quote_char = None
        if c == ',' and not in_quote:
            parts.append(current.strip())
            current = ""
        else:
            current += c
    if current.strip():
        parts.append(current.strip())
    return parts

# ---------------------------------------------------------------------------
# Part 3: Parse Server Check Rules (g_tChkE/R/D)
# ---------------------------------------------------------------------------
def parse_check_rules():
    tables = {}
    with open(SERVER_HDR, 'r', encoding='latin-1') as f:
        content = f.read()

    pattern = r'extern\s+DBRECCHECKTBL\s+g_tChk([ERD])(\w+)\[\]\s*=\s*\{([^;]+?)\n\};'
    for m in re.finditer(pattern, content, re.DOTALL):
        chk_type = {"E": "SAVE", "R": "RELEASE", "D": "DELETE"}[m.group(1)]
        tbl_suffix = m.group(2).upper()
        btbl = "B" + tbl_suffix
        body = m.group(3)

        if btbl not in tables:
            tables[btbl] = {"SAVE": [], "RELEASE": [], "DELETE": []}

        entries = []
        for line in body.split('\n'):
            line = line.strip()
            if not line or '{-1}' in line:
                continue
            if line.startswith('//') or line.startswith('/*'):
                continue
            vals_m = re.findall(r'\{([^}]*)\}', line)
            for v in vals_m:
                vals = [x.strip().strip('"').strip("'") for x in v.split(',')]
                if len(vals) >= 7:
                    entries.append(vals)

        tables[btbl][chk_type] = entries
    return tables

def convert_check_entries(entries, check_type):
    """Convert DBRECCHECKTBL entries to SM_CHECK_DEF records"""
    configs = []
    CHECK_MAP = {
        "DB_CHECK_STAT_E": ("STAT_E", None),
        "DB_CHECK_STAT_R": ("STAT_R", None),
        "DB_CHECK_STAT_W": ("STAT_E", None),
        "DB_CHECK_NOTNULL": ("NOTNULL", None),
        "DB_CHECK_NULL": ("NULLCHK", None),
        "DB_CHECK_STRING": ("STRING", "expectValue"),
        "DB_CHECK_KEY": ("KEY", "refTable,refField"),
        "DB_CHECK_ERRMSG": ("ERRMSG", None),
        "DB_RELEASE_PARAM": ("RELEASE_PARAM", "refTable"),
        "DB_RELEASE_WRITE": ("RELEASE_WRITE", "refTable"),
    }

    order = 1
    for entry in entries:
        if len(entry) < 7:
            continue

        group_no = int(entry[0]) if entry[0].lstrip('-').isdigit() else 0
        check_cond = entry[6].strip().upper() if len(entry) > 6 else ""

        # Release metadata (group -2)
        if group_no == -2:
            if check_cond.startswith("DB_RELEASE_PARAM"):
                kind = "RELEASE_PARAM"
            elif check_cond.startswith("DB_RELEASE_WRITE"):
                kind = "RELEASE_WRITE"
            else:
                continue
            field_name = entry[5].strip()
            ref_tbl = entry[8].strip() if len(entry) > 8 else ""
            if ref_tbl:
                ref_tbl = "D" + ref_tbl.replace("D", "").lstrip("B")
            configs.append({
                "checkType": "RELEASE", "checkOrder": order,
                "checkKind": kind, "fieldName": field_name, "refTable": ref_tbl
            })
            order += 1
            continue

        mapped = CHECK_MAP.get(check_cond)
        if not mapped:
            continue

        kind, extra = mapped
        if kind == "ERRMSG":
            continue

        field_name = entry[5].strip() if len(entry) > 5 else ""
        err_msg = entry[3] if len(entry) > 3 else ""
        ref_table = entry[8].strip() if len(entry) > 8 else ""
        ref_field = entry[9].strip() if len(entry) > 9 else ""

        rec = {
            "checkType": check_type, "checkOrder": order,
            "checkKind": kind, "fieldName": field_name if field_name else None,
            "refTable": None, "refField": None, "expectValue": None, "errMsg": None,
        }

        if kind == "KEY" and ref_table:
            rec["refTable"] = ref_table
            rec["refField"] = ref_field
        elif kind == "STRING":
            rec["expectValue"] = ref_field
        elif kind in ("RELEASE_PARAM", "RELEASE_WRITE"):
            rec["refTable"] = ref_table

        if err_msg and 'WRN_' in err_msg:
            rec["errMsg"] = "检查失败"
        elif err_msg and err_msg not in ('0', 'DB_RESULT_0', 'DB_RESULT_1', 'DB_RESULT_N') and not err_msg.isdigit():
            rec["errMsg"] = err_msg.strip()

        configs.append(rec)
        order += 1

    return configs

# ---------------------------------------------------------------------------
# Part 4: Merge and Generate SQL
# ---------------------------------------------------------------------------
def map_char_to_db(col):
    """Map DDL column type to our DB_TYPE"""
    t = col["dbType"]
    if t in ("CHAR", "VARCHAR", "GRAPHIC", "VARGRAPHIC"):
        return "STRING", col["length"]
    if t in ("INT", "INTEGER", "BIGINT", "SMALLINT"):
        return "NUMBER", col["length"]
    if t in ("DOUBLE", "FLOAT", "DECIMAL"):
        return "DOUBLE", col["length"]
    if t in ("TIMESTAMP", "DATE", "TIME"):
        return "TIMESTAMP", col["length"]
    return "STRING", col["length"]

CONTROL_NAMES = {
    "REL_FLG", "COMP_FLG", "CRE_DATE", "CRE_USER",
    "LAST_DATE1", "LAST_ACT1", "LAST_USER1",
    "LAST_DATE2", "LAST_ACT2", "LAST_USER2",
    "LAST_DATE3", "LAST_ACT3", "LAST_USER3",
    "LAST_DATE4", "LAST_ACT4", "LAST_USER4",
    "LAST_DATE5", "LAST_ACT5", "LAST_USER5",
    "OWNER", "OWNERG", "PERMISSION", "LOCK_USER", "LOCK_TIME", "COMMENT",
}

def generate_final_sql(all_b_tables, ddl_tables, client_fields, check_rules):
    """Generate schema.sql and data.sql"""
    schema_lines = []
    data_lines = []

    sort_counter = 10

    for btbl in sorted(all_b_tables):
        ddl_cols = ddl_tables.get(btbl, [])
        cli_fields = client_fields.get(btbl, [])
        checks = check_rules.get(btbl, {"SAVE": [], "RELEASE": [], "DELETE": []})

        if not ddl_cols:
            continue

        table_id = "TBLID_" + btbl

        # Separate business vs control columns
        biz_cols = [c for c in ddl_cols if c["name"] not in CONTROL_NAMES]
        control_cols = [c for c in ddl_cols if c["name"] in CONTROL_NAMES]

        # Build client field lookup
        cli_map = {}
        for f in cli_fields:
            cli_map[f["fieldName"]] = f

        # === schema.sql: B table ===
        schema_lines.append(f"CREATE TABLE {btbl} (")
        for c in biz_cols:
            db_type, db_len = map_char_to_db(c)
            sql_type = "CHAR({})".format(db_len) if db_type == "STRING" else c["dbType"]
            if db_type == "STRING" and sql_type == "CHAR({})".format(db_len):
                pass
            elif db_type == "NUMBER" and c["dbType"] in ("INT", "INTEGER"):
                sql_type = "INT"
            elif db_type == "DOUBLE":
                sql_type = "DOUBLE"

            nn = "NOT NULL" if c["notNull"] else ""
            df = f"DEFAULT {c['default']}" if c.get("default") else ""
            schema_lines.append(f"    {c['name']:30s} {sql_type:12s} {nn:8s} {df}".rstrip() + ",")

        # Control columns
        for c in control_cols:
            sql_type = c["dbType"]
            nn = "NOT NULL" if c["notNull"] else ""
            df = f"DEFAULT {c['default']}" if c.get("default") else ""
            schema_lines.append(f"    {c['name']:30s} {sql_type:12s} {nn:8s} {df}".rstrip() + ",")

        # Primary key from DDL constraints or client fields
        key_fields = [f["fieldName"] for f in cli_fields if f["isKey"] == "Y"]
        if not key_fields:
            # Try to infer from DDL (no easy way, skip)
            key_fields = [biz_cols[0]["name"]] if biz_cols else ["ID"]
        if "REL_FLG" in [c["name"] for c in ddl_cols]:
            pk = key_fields + ["REL_FLG"]
        else:
            pk = key_fields

        schema_lines.append(f"    PRIMARY KEY ({', '.join(pk)})")
        schema_lines.append(");\n")

        # === schema.sql: D table (same business cols, no control cols, no REL_FLG in PK) ===
        dtbl = "D" + btbl[1:] if btbl.startswith('B') else "D" + btbl
        schema_lines.append(f"CREATE TABLE {dtbl} (")
        for c in biz_cols:
            db_type, db_len = map_char_to_db(c)
            sql_type = "CHAR({})".format(db_len) if db_type == "STRING" else c["dbType"]
            if db_type == "STRING":
                sql_type = "CHAR({})".format(db_len)
            elif db_type == "NUMBER" and c["dbType"] in ("INT", "INTEGER"):
                sql_type = "INT"
            nn = "NOT NULL" if c["notNull"] else ""
            schema_lines.append(f"    {c['name']:30s} {sql_type:12s} {nn:8s}".rstrip() + ",")
        schema_lines.append(f"    PRIMARY KEY ({', '.join(key_fields)})")
        schema_lines.append(");\n")

        # === data.sql: SM_TABLE_DEF ===
        has_dummy = 'Y' if any(f['isDummy'] == 'Y' for f in cli_fields) else 'N'
        jp_title = btbl
        if cli_fields:
            pass  # Could use first field's table name

        data_lines.append(f"-- {btbl}")
        data_lines.append(f"INSERT INTO SM_TABLE_DEF (TABLE_ID, TABLE_NAME, JP_TITLE, US_TITLE, RELEASE_FLAG, DISTRIBUTE_FLAG, PERMISSION_TYPE, SCHEMA_TYPE, HAS_DUMMY, SORT_NO)")
        data_lines.append(f"VALUES ('{table_id}', '{btbl}', '{jp_title}', '{jp_title}', 'Y', 'N', 'C', 'L', '{has_dummy}', {sort_counter});")
        sort_counter += 10

        # === data.sql: SM_FIELD_DEF ===
        for c in biz_cols:
            fname = c["name"]
            cli = cli_map.get(fname, {})

            vals = (
                f"'{table_id}',"
                f"'{fname}',"
                f"'{cli.get('jpTitle', fname)}',"
                f"'{cli.get('usTitle', fname)}',"
                f"'{cli.get('dbType', 'STRING')}',"
                f"{cli.get('dbLength', c.get('length', 0))},"
                f"'{cli.get('isKey', 'N')}',"
                f"'{cli.get('notBlank', 'Y' if c['notNull'] else 'N')}',"
                f"'{cli.get('isDummy', 'N')}',"
                f"'{cli.get('isSearchItem', 'Y')}',"
                f"{cli.get('sortNo', -1)},"
                f"{cli.get('treeLevel', -1)},"
                f"{cli.get('sheetNo', 0)},"
                f"{cli.get('pageNo', 0)},"
                f"{cli.get('propertyNo', 0)},"
                f"'{cli.get('isAuto', 'N')}',"
                f"'{cli.get('isMandatory', 'N')}',"
                f"'{cli.get('systemReadonly', 'N')}',"
                f"'{cli.get('fieldType', 'STRING')}',"
                f"{cli.get('fieldLength', 0)},"
                f"'{cli.get('inputAlphabet', 'Y')}',"
                f"{cli.get('inputMultibyte', 0)},"
                f"'{cli.get('inputNumeric', 'Y')}',"
                f"'{cli.get('inputSymbol', 'Y')}',"
                f"'{cli.get('inputUppercase', 'Y')}',"
                f"'{cli.get('retrievalTable', 'NONE')}',"
                f"{sql_val(cli.get('format'))},"
                f"{sql_val(cli.get('defaultValue'))},"
                f"{sql_val(cli.get('minValue'))},"
                f"{sql_val(cli.get('maxValue'))},"
                f"'{cli.get('calendarButton', 'N')}',"
                f"'{cli.get('jumpButton', 'N')}',"
                f"{cli.get('openButton', 0)},"
                f"{sql_val(cli.get('refTableId'))},"
                f"{sql_val(cli.get('refFieldName'))},"
                f"{cli.get('specialButton', 0)}"
            )
            cols = "TABLE_ID,FIELD_NAME,JP_TITLE,US_TITLE,DB_TYPE,DB_LENGTH,IS_KEY,NOT_BLANK,IS_DUMMY,IS_SEARCH_ITEM,SORT_NO,TREE_LEVEL,SHEET_NO,PAGE_NO,PROPERTY_NO,IS_AUTO,IS_MANDATORY,SYSTEM_READONLY,FIELD_TYPE,FIELD_LENGTH,INPUT_ALPHABET,INPUT_MULTIBYTE,INPUT_NUMERIC,INPUT_SYMBOL,INPUT_UPPERCASE,RETRIEVAL_TABLE,FORMAT,DEFAULT_VALUE,MIN_VALUE,MAX_VALUE,CALENDAR_BUTTON,JUMP_BUTTON,OPEN_BUTTON,REF_TABLE_ID,REF_FIELD_NAME,SPECIAL_BUTTON"
            data_lines.append(f"INSERT INTO SM_FIELD_DEF ({cols}) VALUES ({vals});")

        # === data.sql: SM_CHECK_DEF ===
        all_check_configs = {}
        for chk_type_key in ["SAVE", "RELEASE", "DELETE"]:
            raw_entries = checks.get(chk_type_key, [])
            configs = convert_check_entries(raw_entries, chk_type_key)
            if configs:
                if chk_type_key not in all_check_configs:
                    all_check_configs[chk_type_key] = []
                all_check_configs[chk_type_key].extend(configs)

        # Add EDITCOMP (same as SAVE but with COMP_N check)
        if "SAVE" in all_check_configs:
            save_configs = all_check_configs["SAVE"]
            has_stat_e = any(c["checkKind"] == "STAT_E" for c in save_configs)
            if has_stat_e:
                editcomp = [c for c in save_configs if c["checkKind"] in ("NOTNULL", "STAT_E", "LOCK_FREE")]
                editcomp.append({
                    "checkType": "EDITCOMP", "checkOrder": len(editcomp) + 1,
                    "checkKind": "COMP_N", "fieldName": None,
                    "refTable": None, "refField": None, "expectValue": None,
                    "errMsg": "记录已编辑完成"
                })
                all_check_configs["EDITCOMP"] = editcomp

        for chk_type_key in ["SAVE", "RELEASE", "DELETE", "EDITCOMP"]:
            for c in all_check_configs.get(chk_type_key, []):
                vals = (
                    f"'{table_id}',"
                    f"'{chk_type_key}',"
                    f"{c.get('checkOrder', 0)},"
                    f"'{c.get('checkKind', '')}',"
                    f"{sql_val(c.get('fieldName'))},"
                    f"{sql_val(c.get('refTable'))},"
                    f"{sql_val(c.get('refField'))},"
                    f"{sql_val(c.get('expectValue'))},"
                    f"{sql_val(c.get('errMsg'))}"
                )
                cols = "TABLE_ID,CHECK_TYPE,CHECK_ORDER,CHECK_KIND,FIELD_NAME,REF_TABLE,REF_FIELD,EXPECT_VALUE,ERR_MSG"
                data_lines.append(f"INSERT INTO SM_CHECK_DEF ({cols}) VALUES ({vals});")

        data_lines.append("")

    return '\n'.join(schema_lines), '\n'.join(data_lines)

def is_null(s):
    """Check if a value represents SQL NULL"""
    if s is None:
        return True
    return 'NULL' in str(s).upper()

def sql_val(v):
    if v is None:
        return "NULL"
    if isinstance(v, str):
        # Escape single quotes
        escaped = v.replace("'", "''")
        return f"'{escaped}'"
    return str(v)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    verbose = '--verbose' in sys.argv
    target_tables = None
    if '--tables' in sys.argv:
        idx = sys.argv.index('--tables')
        target_tables = set(sys.argv[idx + 1].upper().split(','))

    print("Loading DDL...")
    ddl = parse_ddl(DDL_FILE)
    b_ddl = {k: v for k, v in ddl.items() if k.startswith('B')}
    print(f"  {len(b_ddl)} B tables from DDL")

    print("Loading client field metadata...")
    client = parse_client_headers()
    print(f"  {len(client)} tables from client headers")

    print("Loading check rules...")
    checks = parse_check_rules()
    print(f"  {len(checks)} tables with check rules")

    # Determine which tables to generate
    all_b = set(b_ddl.keys()) & set(client.keys())
    check_only = set(b_ddl.keys()) - set(client.keys())
    field_only = set(client.keys()) - set(b_ddl.keys())

    print(f"  {len(all_b)} tables in BOTH DDL + client")
    print(f"  {len(check_only)} tables DDL-only")
    print(f"  {len(field_only)} tables client-only")

    if target_tables:
        all_b = target_tables & all_b
        print(f"  Filtered to {len(all_b)} target tables: {sorted(all_b)}")

    if verbose:
        for btbl in sorted(all_b):
            fc = len(client.get(btbl, []))
            cc = sum(len(v) for v in checks.get(btbl, {}).values())
            print(f"  {btbl:30s} {len(ddl[btbl])} cols  {fc} fields  {cc} checks")

    print("\nGenerating SQL...")
    schema_sql, data_sql = generate_final_sql(sorted(all_b), ddl, client, checks)

    schema_path = os.path.join(OUT_DIR, "schema_migrated.sql")
    data_path = os.path.join(OUT_DIR, "data_migrated.sql")

    with open(schema_path, 'w') as f:
        f.write(f"-- Auto-generated from DDL + TABLEINFOEX + check rules\n")
        f.write(f"-- {len(all_b)} B tables + {len(all_b)} D tables\n\n")
        f.write(schema_sql)
    with open(data_path, 'w') as f:
        f.write(f"-- Auto-generated from DDL + TABLEINFOEX + check rules\n")
        f.write(f"-- {len(all_b)} tables\n\n")
        f.write(data_sql)

    print(f"Done!")
    print(f"  schema: {schema_path} ({len(schema_sql):,} bytes)")
    print(f"  data:   {data_path} ({len(data_sql):,} bytes)")

if __name__ == '__main__':
    main()
