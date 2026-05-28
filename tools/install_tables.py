#!/usr/bin/env python3
"""Quick install script: extract DDL for specific B tables, generate H2 schema + SM config."""
import re, os, sys

SM_DIR = "/Users/caolizhu/Documents/VibeCode/MySM"
DDL_FILE = os.path.join(SM_DIR, "WV-MMDBD_20241223_LS2.ddl")
CLIENT_HDRS = [
    os.path.join(SM_DIR, "Wafer_SMClient/SMClient/SmTableInformation1.h"),
    os.path.join(SM_DIR, "Wafer_SMClient/SMClient/SmTableInformation2.h"),
    os.path.join(SM_DIR, "Wafer_SMClient/SMClient/SmTableInformation3.h"),
    os.path.join(SM_DIR, "Wafer_SMClient/SMClient/SmTableInformation4.h"),
]
SERVER_HDR = os.path.join(SM_DIR, "Wafer_SMServer/SMServer/inc/wdbtbl.h")
SCHEMA_FILE = os.path.join(SM_DIR, "java-poc/src/main/resources/schema.sql")
DATA_FILE = os.path.join(SM_DIR, "java-poc/src/main/resources/data.sql")

TARGET_TABLES = ["BPROD", "BROUTE", "BOPE", "BEQP", "BAREA", "BEQPG"]
NL = '\n'

CONTROL_NAMES = {
    "REL_FLG", "COMP_FLG", "CRE_DATE", "CRE_USER",
    "LAST_DATE1", "LAST_ACT1", "LAST_USER1",
    "LAST_DATE2", "LAST_ACT2", "LAST_USER2",
    "LAST_DATE3", "LAST_ACT3", "LAST_USER3",
    "LAST_DATE4", "LAST_ACT4", "LAST_USER4",
    "LAST_DATE5", "LAST_ACT5", "LAST_USER5",
    "OWNER", "OWNERG", "PERMISSION", "LOCK_USER", "LOCK_TIME", "COMMENT",
}

TYPE_MAP = {
    "CHAR": "CHAR", "VARCHAR": "VARCHAR", "CHARACTER": "CHAR",
    "INTEGER": "INT", "INT": "INT", "BIGINT": "BIGINT", "SMALLINT": "INT",
    "DOUBLE": "DOUBLE", "FLOAT": "DOUBLE", "DECIMAL": "DECIMAL",
    "TIMESTAMP": "TIMESTAMP", "DATE": "DATE", "TIME": "TIME",
    "GRAPHIC": "CHAR", "VARGRAPHIC": "VARCHAR",
}

# ---------------------------------------------------------------------------
# Step 1: Parse DDL
# ---------------------------------------------------------------------------
def parse_ddl_tables(filepath, target_names):
    with open(filepath, 'r') as f:
        content = f.read()

    tables = {}
    for name in target_names:
        pattern = rf'CREATE TABLE "LS2WDEV"."{name}"\s*\((.*?)\)\s*;'
        m = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if m:
            tables[name] = parse_columns(m.group(1))
            print(f"  {name}: {len(tables[name])} columns")
        else:
            print(f"  {name}: NOT FOUND")
    return tables

def parse_columns(body):
    columns = []
    # Split by comma at top level
    entries = []
    current = ""
    depth = 0
    for c in body:
        if c == '(': depth += 1
        elif c == ')': depth -= 1
        if c == ',' and depth == 0:
            entries.append(current.strip())
            current = ""
        else:
            current += c
    if current.strip():
        entries.append(current.strip())

    for entry in entries:
        entry = entry.strip()
        if not entry or entry.startswith('--'):
            continue

        # Skip constraints
        if re.match(r'^\s*(PRIMARY\s+KEY|UNIQUE|FOREIGN\s+KEY|CHECK|CONSTRAINT|INDEX\s+IN|DISTRIBUTE|ORGANIZE|AUDIT|DATA\s+CAPTURE|PCTFREE|COMPRESS|PARTITIONING)', entry, re.IGNORECASE):
            continue

        m = re.match(r'\s*"([^"]+)"\s+(.+)$', entry, re.IGNORECASE)
        if not m:
            continue

        col_name = m.group(1)
        type_def = m.group(2).strip().upper()

        # Extract type and length
        type_m = re.match(r'(\w+)\s*(\([^)]*\))?\s*(.*)', type_def, re.IGNORECASE)
        if not type_m:
            continue

        db_type = TYPE_MAP.get(type_m.group(1).upper(), type_m.group(1).upper())
        len_str = type_m.group(2) or ""
        rest = type_m.group(3) or ""

        # Extract numeric length
        len_num = 0
        num_m = re.search(r'(\d+)', len_str)
        if num_m:
            len_num = int(num_m.group(1))

        not_null = "NOT NULL" in rest

        default = None
        def_m = re.search(r"DEFAULT\s+('[^']*'|\w+)", rest)
        if def_m:
            default = def_m.group(1)

        # H2 SQL type
        if db_type in ("CHAR", "VARCHAR", "GRAPHIC", "VARGRAPHIC"):
            h2_type = f"{db_type}({len_num})" if len_num > 0 else db_type
        elif db_type in ("DECIMAL",):
            h2_type = f"{db_type}{len_str.replace(' OCTETS','')}" if len_str else db_type
        else:
            h2_type = db_type

        columns.append({
            "name": col_name,
            "h2Type": h2_type,
            "notNull": not_null,
            "default": default,
            "isControl": col_name in CONTROL_NAMES,
        })
    return columns

# ---------------------------------------------------------------------------
# Step 2: Parse Client TABLEINFOEX for JP titles
# ---------------------------------------------------------------------------
def parse_client_fields():
    tables = {}
    for hdr in CLIENT_HDRS:
        if not os.path.exists(hdr):
            continue
        with open(hdr, 'r', encoding='latin-1') as f:
            content = f.read()

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
            fields = parse_client_field_entries(arr_m.group(1))
            if fields:
                tables[btbl] = fields
    return tables

def parse_client_field_entries(body):
    fields = []
    entries = []
    current = ""
    depth = 0
    for c in body:
        if c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                entries.append(current)
                current = ""
                continue
        if depth > 0:
            current += c

    for entry in entries:
        parts = split_csv(entry)
        if len(parts) < 25:
            continue

        def strip_l(s):
            s = s.strip().strip('"')
            for p in ['L"', 'l"']:
                if p in s: s = s.split(p, 1)[-1]
            return s.strip().strip('"')

        def yn(s): return 'Y' if s.strip().upper() in ('Y', '1') else 'N'
        def int_or(v, d):
            try: return int(v.strip())
            except: return d
        def db_type(v):
            v = v.strip().upper()
            if 'STRING' in v: return 'STRING'
            if 'NUMBER' in v or 'INT' in v: return 'NUMBER'
            if 'DOUBLE' in v: return 'DOUBLE'
            return 'STRING'
        def field_type(v):
            v = v.strip().upper()
            if 'SELECT' in v or 'COMBO' in v: return 'SELECT'
            if 'NUMBER' in v: return 'NUMBER'
            return 'STRING'
        def retrieval(v):
            v = v.strip().upper()
            if 'NONE' in v: return 'NONE'
            if 'TABLE' in v or 'SYSDATA' in v: return 'SYSDATA'
            return 'NONE'

        field_name = strip_l(parts[2]).replace('FLD_', '')
        ref_table = None
        ref_field = None
        if len(parts) >= 33 and 'TBLID_' in parts[32] and '-1' not in parts[32]:
            ref_table = parts[32].strip()
        if len(parts) >= 34 and 'FLD_' in parts[33]:
            ref_field = parts[33].strip().replace('FLD_', '')

        fields.append({
            "fieldName": field_name,
            "jpTitle": strip_l(parts[0]),
            "usTitle": strip_l(parts[1]),
            "dbType": db_type(parts[3]),
            "dbLength": int_or(parts[4], 0),
            "isKey": yn(parts[5]),
            "notBlank": yn(parts[6]),
            "isDummy": yn(parts[7]),
            "isSearchItem": yn(parts[8]),
            "sortNo": int_or(parts[9], -1),
            "treeLevel": int_or(parts[10], -1),
            "sheetNo": int_or(parts[11], 0),
            "pageNo": int_or(parts[12], 0),
            "propertyNo": int_or(parts[13], 0),
            "isAuto": yn(parts[14]),
            "isMandatory": yn(parts[15]),
            "systemReadonly": yn(parts[16]),
            "fieldType": field_type(parts[17]),
            "fieldLength": int_or(parts[18], 0),
            "inputAlphabet": yn(parts[19]) if len(parts) > 19 else 'Y',
            "inputMultibyte": int_or(parts[20], 0) if len(parts) > 20 else 0,
            "inputNumeric": yn(parts[21]) if len(parts) > 21 else 'Y',
            "inputSymbol": yn(parts[22]) if len(parts) > 22 else 'Y',
            "inputUppercase": yn(parts[23]) if len(parts) > 23 else 'Y',
            "retrievalTable": retrieval(parts[24]) if len(parts) > 24 else 'NONE',
            "format": None if len(parts) <= 25 or 'NULL' in parts[25].upper() else strip_l(parts[25]),
            "defaultValue": None if len(parts) <= 26 or 'NULL' in parts[26].upper() else strip_l(parts[26]),
            "minValue": None if len(parts) <= 27 or 'NULL' in parts[27].upper() else strip_l(parts[27]),
            "maxValue": None if len(parts) <= 28 or 'NULL' in parts[28].upper() else strip_l(parts[28]),
            "calendarButton": yn(parts[29]) if len(parts) > 29 else 'N',
            "jumpButton": yn(parts[30]) if len(parts) > 30 else 'N',
            "openButton": int_or(parts[31], 0) if len(parts) > 31 else 0,
            "refTableId": ref_table,
            "refFieldName": ref_field,
        })
    return fields

def split_csv(text):
    parts, cur = [], ""
    in_str, qc = False, None
    for c in text:
        if c in ('"', "'") and not in_str:
            in_str = True; qc = c
        elif c == qc and in_str:
            in_str = False; qc = None
        if c == ',' and not in_str:
            parts.append(cur.strip()); cur = ""
        else:
            cur += c
    if cur.strip(): parts.append(cur.strip())
    return parts

# ---------------------------------------------------------------------------
# Step 3: Parse Check Rules
# ---------------------------------------------------------------------------
def parse_server_checks(target_names):
    with open(SERVER_HDR, 'r', encoding='latin-1') as f:
        content = f.read()

    tables = {}
    for name in target_names:
        suffix = name[1:]  # remove B prefix
        tables[name] = {"SAVE": [], "RELEASE": [], "DELETE": []}

        for chk_type, chk_char in [("SAVE", "E"), ("RELEASE", "R"), ("DELETE", "D")]:
            # Find the start of the check array
            start_pat = r'extern\s+DBRECCHECKTBL\s+g_tChk' + chk_char + suffix + r'\[\]\s*=\s*\{'
            sm = re.search(start_pat, content, re.IGNORECASE)
            if not sm:
                continue
            # Extract from start to next '};'
            start_pos = sm.end() - 1  # include the first {
            depth = 0
            end_pos = start_pos
            for i in range(start_pos, len(content)):
                if content[i] == '{': depth += 1
                elif content[i] == '}':
                    depth -= 1
                    if depth == 0:
                        end_pos = i
                        break
            body = content[start_pos+1:end_pos]
            entries = []
            for line in body.split('\n'):
                    line = line.strip()
                    if not line or '{-1}' in line: continue
                    if line.startswith('//') or line.startswith('/*'): continue
                    for vm in re.finditer(r'\{([^}]*)\}', line):
                        vals = [x.strip().strip('"').strip("'") for x in vm.group(1).split(',')]
                        if len(vals) >= 7:
                            entries.append(vals)
                tables[name][chk_type] = entries
    return tables

def checks_to_sql(table_id, check_data):
    lines = []
    nl = '\n'
    CHECK_MAP = {
        "DB_CHECK_STAT_E": "STAT_E", "DB_CHECK_STAT_R": "STAT_R", "DB_CHECK_STAT_W": "STAT_E",
        "DB_CHECK_NOTNULL": "NOTNULL", "DB_CHECK_NULL": "NULLCHK",
        "DB_CHECK_STRING": "STRING", "DB_CHECK_KEY": "KEY",
        "DB_CHECK_ERRMSG": "ERRMSG",
        "DB_RELEASE_PARAM": "RELEASE_PARAM", "DB_RELEASE_WRITE": "RELEASE_WRITE",
    }

    for chk_type in ["SAVE", "RELEASE", "DELETE"]:
        entries = check_data.get(chk_type, [])
        if not entries: continue
        order = 1
        for entry in entries:
            if len(entry) < 7: continue
            group = int(entry[0]) if entry[0].lstrip('-').isdigit() else 0
            cond = entry[6].strip().upper() if len(entry) > 6 else ""

            if group == -2:  # Release metadata
                if "DB_RELEASE_PARAM" in cond: kind = "RELEASE_PARAM"
                elif "DB_RELEASE_WRITE" in cond: kind = "RELEASE_WRITE"
                else: continue
                fn = entry[5].strip()
                rt = entry[8].strip() if len(entry) > 8 else ""
                if rt: rt = "D" + rt.replace("D", "").lstrip("B")
                lines.append(f"('{table_id}','{chk_type}',{order},'{kind}','{fn}','{rt}',NULL,NULL,NULL),")
                order += 1
                continue

            mapped = CHECK_MAP.get(cond)
            if not mapped: continue
            kind = mapped
            if kind == "ERRMSG": continue

            fn = entry[5].strip() if len(entry) > 5 else ""
            fn_val = f"'{fn}'" if fn else "NULL"
            rt = entry[8].strip() if len(entry) > 8 else ""
            rf = entry[9].strip() if len(entry) > 9 else ""

            if kind == "KEY" and rt:
                lines.append(f"('{table_id}','{chk_type}',{order},'KEY','{fn}','{rt}','{rf}',NULL,NULL),")
            elif kind == "STRING":
                lines.append(f"('{table_id}','{chk_type}',{order},'STRING','{fn}',NULL,NULL,'{rf}',NULL),")
            else:
                lines.append(f"('{table_id}','{chk_type}',{order},'{kind}',{fn_val},NULL,NULL,NULL,NULL),")
            order += 1

    # Add EDITCOMP
    if lines:
        order = 1
        lines.append(f"('{table_id}','EDITCOMP',{order},'NOTNULL',NULL,NULL,NULL,NULL,'未指定主键'),"); order += 1
        lines.append(f"('{table_id}','EDITCOMP',{order},'STAT_E',NULL,NULL,NULL,NULL,'记录不是编辑态'),"); order += 1
        lines.append(f"('{table_id}','EDITCOMP',{order},'LOCK_FREE',NULL,NULL,NULL,NULL,'记录已被锁定'),"); order += 1
        lines.append(f"('{table_id}','EDITCOMP',{order},'COMP_N',NULL,NULL,NULL,NULL,'记录已编辑完成'),")

    return lines

# ---------------------------------------------------------------------------
# Step 4: Generate SQL
# ---------------------------------------------------------------------------
def q(v):
    """SQL quote"""
    if v is None: return "NULL"
    if isinstance(v, (int, float)): return str(v)
    return "'" + str(v).replace("'", "''") + "'"

def generate_sql(tables, ddl_data, client_data, check_data):
    schema_sql = ["\n-- ============================================"]
    schema_sql.append("-- Auto-installed tables: " + ", ".join(tables.keys()))
    schema_sql.append("-- ============================================\n")

    data_sql = ["\n-- ============================================"]
    data_sql.append("-- Auto-installed tables: " + ", ".join(tables.keys()))
    data_sql.append("-- ============================================\n")

    sort_no = 100  # Start after manually curated tables

    for btbl in tables.keys():
        ddl_cols = ddl_data.get(btbl, [])
        cli_fields = client_data.get(btbl, [])
        checks = check_data.get(btbl, {})

        if not ddl_cols:
            print(f"  SKIP {btbl}: no DDL data")
            continue

        table_id = f"TBLID_{btbl}"
        dtbl = "D" + btbl[1:] if btbl.startswith('B') else "D" + btbl

        # Build client field lookup
        cli_map = {}
        for f in cli_fields:
            cli_map[f["fieldName"].upper()] = f

        biz_cols = [c for c in ddl_cols if not c["isControl"]]
        key_fields = [f["fieldName"] for f in cli_fields if f["isKey"] == "Y"]

        if not key_fields:
            # Infer from DDL: first biz column is likely key
            key_fields = [biz_cols[0]["name"]] if biz_cols else ["ID"]

        # === B table schema ===
        schema_sql.append(f"CREATE TABLE {btbl} (")
        for c in biz_cols:
            nn = " NOT NULL" if c["notNull"] else ""
            df = f" DEFAULT {c['default']}" if c.get("default") else ""
            schema_sql.append(f'    {c["name"]:35s} {c["h2Type"]:15s}{nn}{df},')
        # Control columns (standardized)
        ctrl = [
            ('REL_FLG', 'CHAR(1)', "NOT NULL DEFAULT 'E'"),
            ('COMP_FLG', 'CHAR(1)', "NOT NULL DEFAULT 'N'"),
            ('CRE_DATE', 'TIMESTAMP', "DEFAULT CURRENT_TIMESTAMP"),
            ('CRE_USER', 'CHAR(20)', "NOT NULL DEFAULT 'SYSTEM'"),
            ('LAST_DATE1', 'TIMESTAMP', ''),
            ('LAST_ACT1', 'CHAR(12)', "NOT NULL DEFAULT ''"),
            ('LAST_USER1', 'CHAR(20)', "NOT NULL DEFAULT ''"),
            ('LAST_DATE2', 'TIMESTAMP', ''),
            ('LAST_ACT2', 'CHAR(12)', "NOT NULL DEFAULT ''"),
            ('LAST_USER2', 'CHAR(20)', "NOT NULL DEFAULT ''"),
            ('LAST_DATE3', 'TIMESTAMP', ''),
            ('LAST_ACT3', 'CHAR(12)', "NOT NULL DEFAULT ''"),
            ('LAST_USER3', 'CHAR(20)', "NOT NULL DEFAULT ''"),
            ('LAST_DATE4', 'TIMESTAMP', ''),
            ('LAST_ACT4', 'CHAR(12)', "NOT NULL DEFAULT ''"),
            ('LAST_USER4', 'CHAR(20)', "NOT NULL DEFAULT ''"),
            ('LAST_DATE5', 'TIMESTAMP', ''),
            ('LAST_ACT5', 'CHAR(12)', "NOT NULL DEFAULT ''"),
            ('LAST_USER5', 'CHAR(20)', "NOT NULL DEFAULT ''"),
            ('OWNER', 'CHAR(20)', "NOT NULL DEFAULT 'SYSTEM'"),
            ('OWNERG', 'CHAR(10)', "NOT NULL DEFAULT ''"),
            ('PERMISSION', 'CHAR(10)', "NOT NULL DEFAULT 'PUBLIC    '"),
            ('LOCK_USER', 'CHAR(20)', "NOT NULL DEFAULT ''"),
            ('LOCK_TIME', 'TIMESTAMP', ''),
            ('"COMMENT"', 'CHAR(128)', "NOT NULL DEFAULT ''"),
        ]
        for name, typ, extra in ctrl:
            schema_sql.append(f"    {name:35s} {typ:15s} {extra},".rstrip())

        pk = ', '.join(key_fields + ['REL_FLG'])
        schema_sql.append(f"    PRIMARY KEY ({pk})")
        schema_sql.append(");\n")

        # === D table schema ===
        schema_sql.append(f"CREATE TABLE {dtbl} (")
        for c in biz_cols:
            nn = " NOT NULL" if c["notNull"] else ""
            df = f" DEFAULT {c['default']}" if c.get("default") else ""
            schema_sql.append(f'    {c["name"]:35s} {c["h2Type"]:15s}{nn}{df},')
        dpk = ', '.join(key_fields)
        schema_sql.append(f"    PRIMARY KEY ({dpk})")
        schema_sql.append(");\n")

        # === SM_TABLE_DEF ===
        jp = btbl
        has_dummy = 'Y' if any(f.get('isDummy') == 'Y' for f in cli_fields) else 'N'
        data_sql.append(f"-- {btbl}")
        data_sql.append(f"INSERT INTO SM_TABLE_DEF (TABLE_ID,TABLE_NAME,JP_TITLE,US_TITLE,RELEASE_FLAG,DISTRIBUTE_FLAG,PERMISSION_TYPE,SCHEMA_TYPE,HAS_DUMMY,SORT_NO)")
        data_sql.append(f"VALUES ('{table_id}','{btbl}','{jp}','{jp}','Y','N','C','L','{has_dummy}',{sort_no});")
        sort_no += 10

        # === SM_FIELD_DEF ===
        FCOLS = "TABLE_ID,FIELD_NAME,JP_TITLE,US_TITLE,DB_TYPE,DB_LENGTH,IS_KEY,NOT_BLANK,IS_DUMMY,IS_SEARCH_ITEM,SORT_NO,TREE_LEVEL,SHEET_NO,PAGE_NO,PROPERTY_NO,IS_AUTO,IS_MANDATORY,SYSTEM_READONLY,FIELD_TYPE,FIELD_LENGTH,INPUT_ALPHABET,INPUT_MULTIBYTE,INPUT_NUMERIC,INPUT_SYMBOL,INPUT_UPPERCASE,RETRIEVAL_TABLE,FORMAT,DEFAULT_VALUE,MIN_VALUE,MAX_VALUE,CALENDAR_BUTTON,JUMP_BUTTON,OPEN_BUTTON,REF_TABLE_ID,REF_FIELD_NAME,SPECIAL_BUTTON"

        for c in biz_cols:
            cli = cli_map.get(c["name"].upper(), {})
            vals = (
                f"'{table_id}',"
                f"'{c['name']}',"
                f"{q(cli.get('jpTitle', c['name']))},"
                f"{q(cli.get('usTitle', c['name']))},"
                f"{q(cli.get('dbType', 'STRING'))},"
                f"{cli.get('dbLength', 0)},"
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
                f"{q(cli.get('format'))},"
                f"{q(cli.get('defaultValue'))},"
                f"{q(cli.get('minValue'))},"
                f"{q(cli.get('maxValue'))},"
                f"'{cli.get('calendarButton', 'N')}',"
                f"'{cli.get('jumpButton', 'N')}',"
                f"{cli.get('openButton', 0)},"
                f"{q(cli.get('refTableId'))},"
                f"{q(cli.get('refFieldName'))},"
                f"0"
            )
            data_sql.append(f"INSERT INTO SM_FIELD_DEF ({FCOLS}) VALUES ({vals});")

        # === SM_CHECK_DEF ===
        check_lines = checks_to_sql(table_id, checks)
        if check_lines:
            data_sql.append(f"\nINSERT INTO SM_CHECK_DEF (TABLE_ID,CHECK_TYPE,CHECK_ORDER,CHECK_KIND,FIELD_NAME,REF_TABLE,REF_FIELD,EXPECT_VALUE,ERR_MSG) VALUES")
            data_sql.extend(check_lines)
            data_sql.append("")  # blank line

    return '\n'.join(schema_sql), '\n'.join(data_sql)


def main():
    print("Loading DDL...")
    ddl_data = parse_ddl_tables(DDL_FILE, TARGET_TABLES)

    print("\nLoading client metadata...")
    client_data = parse_client_fields()
    for t in TARGET_TABLES:
        n = len(client_data.get(t, []))
        print(f"  {t}: {n} fields from client")

    print("\nLoading check rules...")
    check_data = parse_server_checks(TARGET_TABLES)
    for t in TARGET_TABLES:
        s = len(check_data.get(t, {}).get("SAVE", []))
        r = len(check_data.get(t, {}).get("RELEASE", []))
        d = len(check_data.get(t, {}).get("DELETE", []))
        print(f"  {t}: S={s} R={r} D={d}")

    print("\nGenerating SQL...")
    schema_sql, data_sql = generate_sql(ddl_data, ddl_data, client_data, check_data)

    schema_path = os.path.join(os.path.dirname(__file__), "auto_generated", "install_schema.sql")
    data_path = os.path.join(os.path.dirname(__file__), "auto_generated", "install_data.sql")
    with open(schema_path, 'w') as f: f.write(schema_sql)
    with open(data_path, 'w') as f: f.write(data_sql)
    print(f"Done! {schema_path}, {data_path}")

if __name__ == '__main__':
    main()
