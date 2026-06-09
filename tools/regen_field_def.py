#!/usr/bin/env python3
"""
Regenerate SM_FIELD_DEF from SmTableInformation*.h header files.
Extracts ALL fields including dummy fields with OPEN buttons.
Replaces the existing SM_FIELD_DEF INSERT section in data.sql.
"""
import re
import os
import glob

COLUMNS = "TABLE_ID,FIELD_NAME,JP_TITLE,US_TITLE,DB_TYPE,DB_LENGTH,IS_KEY,NOT_BLANK,IS_DUMMY,IS_SEARCH_ITEM,SORT_NO,TREE_LEVEL,SHEET_NO,PAGE_NO,PROPERTY_NO,IS_AUTO,IS_MANDATORY,SYSTEM_READONLY,FIELD_TYPE,FIELD_LENGTH,INPUT_ALPHABET,INPUT_MULTIBYTE,INPUT_NUMERIC,INPUT_SYMBOL,INPUT_UPPERCASE,RETRIEVAL_TABLE,FORMAT,DEFAULT_VALUE,MIN_VALUE,MAX_VALUE,CALENDAR_BUTTON,JUMP_BUTTON,OPEN_BUTTON,REF_TABLE_ID,REF_FIELD_NAME,SPECIAL_BUTTON"

# Y/N mapping
def yn(val):
    return 'Y' if val.strip().upper() in ('Y', '1', 'TRUE') else 'N'

def parse_header_files(h_files):
    """Parse SmTableInformation*.h and extract field definitions per table."""
    all_fields = []  # list of (table_id, field_dict)

    for h_file in sorted(h_files):
        with open(h_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        current_table_id = None
        for line in content.split('\n'):
            stripped = line.strip()

            # Detect table section: #if (TABLEID==TBLID_Bxxx)
            tbl_match = re.search(r'TABLEID\s*==\s*(TBLID_\w+)', line)
            if tbl_match:
                current_table_id = tbl_match.group(1)
                continue

            # Skip comments
            if stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
                continue

            # Skip NULL terminator lines
            if '{NULL,NULL,NULL,' in line:
                continue

            # Match field definition lines: {L"title", L"FIELD_NAME", ...}
            if not ('{L"' in line or "L'" in line) or 'DBVT_' not in line:
                continue

            # Extract all tokens
            field = parse_field_line(line, current_table_id)
            if field:
                all_fields.append(field)

    return all_fields


def parse_field_line(line, table_id):
    """Parse a single field definition line."""
    if not table_id:
        return None

    # Extract L"..." strings
    strings = re.findall(r'L"([^"]*)"', line)
    if len(strings) < 2:
        return None

    jp_title = strings[0]
    field_name = strings[1]

    # Extract the core values between { and }
    inner = re.search(r'\{(.+)\}', line)
    if not inner:
        return None
    tokens_raw = inner.group(1)

    # Tokenize: split by comma but respect L"..." strings
    tokens = tokenize(tokens_raw)
    if len(tokens) < 35:
        return None

    # Map token positions to SM_FIELD_DEF fields
    # Position mapping from C struct:
    # 0: jp_title (L"...")
    # 1: field_name (L"...")
    # 2: FLD_xxx enum (skip)
    # 3: DBVT_xxx (db type)
    # 4: db_length
    # 5: IS_KEY
    # 6: NOT_BLANK
    # 7: IS_DUMMY
    # 8: IS_SEARCH_ITEM
    # 9: SORT_NO (or -1)
    # 10: TREE_LEVEL (or -1)
    # 11: SHEET_NO
    # 12: PAGE_NO
    # 13: PROPERTY_NO
    # 14: IS_AUTO
    # 15: IS_MANDATORY
    # 16: SYSTEM_READONLY
    # 17: FLDTYPE_xxx
    # 18: FIELD_LENGTH
    # 19: INPUT_ALPHABET
    # 20: INPUT_MULTIBYTE
    # 21: INPUT_NUMERIC
    # 22: INPUT_SYMBOL
    # 23: INPUT_UPPERCASE
    # 24: COMBO_xxx (retrieval type)
    # 25: FORMAT/default (L"..." or NULL)
    # 26: DEFAULT_VALUE (L"..." or NULL)
    # 27: MIN_VALUE (L"..." or NULL)
    # 28: MAX_VALUE (L"..." or NULL)
    # 29: CALENDAR_BUTTON
    # 30: JUMP_BUTTON
    # 31: OPEN_BUTTON (int)
    # 32: REF_TABLE_ID (TBLID_xxx or -1)
    # 33: REF_FIELD_NAME (FLD_xxx or NULL)
    # 34: SPECIAL_BUTTON

    try:
        db_type_raw = tokens[3].strip()
        if 'LONG' in db_type_raw or 'INT' in db_type_raw:
            db_type = 'NUMBER'
        elif 'DOUBLE' in db_type_raw or 'FLOAT' in db_type_raw:
            db_type = 'DOUBLE'
        else:
            db_type = 'STRING'

        db_length = int(re.search(r'-?\d+', tokens[4]).group())
        if db_length < 0:
            db_length = 1

        is_key = yn(tokens[5])
        not_blank = yn(tokens[6])
        is_dummy = yn(tokens[7])
        is_search = yn(tokens[8])

        sort_no = int(re.search(r'-?\d+', tokens[9]).group())
        tree_level = int(re.search(r'-?\d+', tokens[10]).group())
        sheet_no = int(re.search(r'-?\d+', tokens[11]).group())
        page_no = int(re.search(r'-?\d+', tokens[12]).group())
        property_no = int(re.search(r'-?\d+', tokens[13]).group())

        is_auto = yn(tokens[14])
        is_mandatory = yn(tokens[15])
        system_readonly = yn(tokens[16])

        field_type_raw = tokens[17].strip()
        if 'SELECT' in field_type_raw:
            field_type = 'SELECT'
        elif 'NUMBER' in field_type_raw:
            field_type = 'NUMBER'
        else:
            field_type = 'STRING'

        field_length = int(re.search(r'-?\d+', tokens[18]).group())
        if field_length < 0:
            field_length = 1

        input_alpha = yn(tokens[19])
        input_mb = int(re.search(r'-?\d+', tokens[20]).group())
        input_num = yn(tokens[21])
        input_sym = yn(tokens[22])
        input_upper = yn(tokens[23])

        # COMBO type → RETRIEVAL_TABLE
        combo_raw = tokens[24].strip()
        if 'COMBO_SYSDATA' in combo_raw:
            retrieval_table = 'SYSDATA'
        elif 'COMBO_CODE' in combo_raw:
            retrieval_table = 'BCODE'
        else:
            retrieval_table = 'NONE'

        # FORMAT (string after COMBO)
        format_val = extract_string(tokens[25])
        default_val = extract_string(tokens[26])
        min_val = extract_string(tokens[27])
        max_val = extract_string(tokens[28])

        cal_btn = yn(tokens[29])
        jump_btn = yn(tokens[30])
        open_btn = int(re.search(r'-?\d+', tokens[31]).group())

        # REF_TABLE_ID
        ref_tbl_raw = tokens[32].strip()
        ref_table_id = None
        if 'TBLID_' in ref_tbl_raw:
            m = re.search(r'(TBLID_\w+)', ref_tbl_raw)
            if m:
                ref_table_id = m.group(1)

        # REF_FIELD_NAME
        ref_fld_raw = tokens[33].strip()
        ref_field_name = None
        if 'FLD_' in ref_fld_raw and 'NULL' not in ref_fld_raw.upper():
            m = re.search(r'FLD_(\w+)', ref_fld_raw)
            if m:
                ref_field_name = m.group(1).upper()

        special_btn = 0
        if len(tokens) > 34:
            m = re.search(r'-?\d+', tokens[34])
            if m:
                special_btn = int(m.group())

        return {
            'table_id': table_id,
            'field_name': field_name,
            'jp_title': jp_title,
            'us_title': field_name,  # Default US title = field name
            'db_type': db_type,
            'db_length': db_length,
            'is_key': is_key,
            'not_blank': not_blank,
            'is_dummy': is_dummy,
            'is_search_item': is_search,
            'sort_no': sort_no,
            'tree_level': tree_level,
            'sheet_no': sheet_no,
            'page_no': page_no,
            'property_no': property_no,
            'is_auto': is_auto,
            'is_mandatory': is_mandatory,
            'system_readonly': system_readonly,
            'field_type': field_type,
            'field_length': field_length,
            'input_alphabet': input_alpha,
            'input_multibyte': input_mb,
            'input_numeric': input_num,
            'input_symbol': input_sym,
            'input_uppercase': input_upper,
            'retrieval_table': retrieval_table,
            'format': format_val,
            'default_value': default_val,
            'min_value': min_val,
            'max_value': max_val,
            'calendar_button': cal_btn,
            'jump_button': jump_btn,
            'open_button': open_btn,
            'ref_table_id': ref_table_id,
            'ref_field_name': ref_field_name,
            'special_button': special_btn,
        }
    except (ValueError, IndexError, AttributeError) as e:
        return None


def tokenize(s):
    """Split comma-separated tokens, respecting L"..." strings."""
    tokens = []
    current = ''
    in_string = False
    i = 0
    while i < len(s):
        c = s[i]
        if c == '"' and i > 0 and s[i-1] != '\\':
            in_string = not in_string
            current += c
        elif c == ',' and not in_string:
            tokens.append(current.strip())
            current = ''
        else:
            current += c
        i += 1
    if current.strip():
        tokens.append(current.strip())
    return tokens


def extract_string(token):
    """Extract string value from L"..." or NULL."""
    if not token or 'NULL' in token.upper():
        return None
    m = re.search(r'L"([^"]*)"', token)
    if m:
        return m.group(1)
    m = re.search(r'"([^"]*)"', token)
    if m:
        return m.group(1)
    return None


def sql_val(v):
    """Format value for SQL INSERT."""
    if v is None:
        return 'NULL'
    if isinstance(v, int):
        return str(v)
    # Escape single quotes
    return "'" + str(v).replace("'", "''") + "'"


def gen_insert(f):
    """Generate INSERT INTO SM_FIELD_DEF statement."""
    vals = [
        sql_val(f['table_id']),
        sql_val(f['field_name']),
        sql_val(f['jp_title']),
        sql_val(f['us_title']),
        sql_val(f['db_type']),
        str(f['db_length']),
        sql_val(f['is_key']),
        sql_val(f['not_blank']),
        sql_val(f['is_dummy']),
        sql_val(f['is_search_item']),
        str(f['sort_no']),
        str(f['tree_level']),
        str(f['sheet_no']),
        str(f['page_no']),
        str(f['property_no']),
        sql_val(f['is_auto']),
        sql_val(f['is_mandatory']),
        sql_val(f['system_readonly']),
        sql_val(f['field_type']),
        str(f['field_length']),
        sql_val(f['input_alphabet']),
        str(f['input_multibyte']),
        sql_val(f['input_numeric']),
        sql_val(f['input_symbol']),
        sql_val(f['input_uppercase']),
        sql_val(f['retrieval_table']),
        sql_val(f['format']),
        sql_val(f['default_value']),
        sql_val(f['min_value']),
        sql_val(f['max_value']),
        sql_val(f['calendar_button']),
        sql_val(f['jump_button']),
        str(f['open_button']),
        sql_val(f['ref_table_id']),
        sql_val(f['ref_field_name']),
        str(f['special_button']),
    ]
    return f"INSERT INTO SM_FIELD_DEF ({COLUMNS}) VALUES ({','.join(vals)});"


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    h_pattern = os.path.join(script_dir, '..', 'Wafer_SMClient', 'SMClient', 'SmTableInformation*.h')
    h_files = glob.glob(h_pattern)

    if not h_files:
        print("No SmTableInformation*.h files found")
        return

    print(f"Parsing {len(h_files)} header files...")
    all_fields = parse_header_files(h_files)
    print(f"Extracted {len(all_fields)} field definitions")

    # Count by type
    tables = set(f['table_id'] for f in all_fields)
    dummy_count = sum(1 for f in all_fields if f['is_dummy'] == 'Y')
    select_count = sum(1 for f in all_fields if f['field_type'] == 'SELECT')
    print(f"  Tables: {len(tables)}")
    print(f"  Dummy fields: {dummy_count}")
    print(f"  SELECT fields: {select_count}")

    # Deduplicate by (table_id, field_name) - keep last
    seen = {}
    for f in all_fields:
        key = (f['table_id'], f['field_name'])
        seen[key] = f
    unique_fields = list(seen.values())
    print(f"  Unique (table, field) pairs: {len(unique_fields)}")

    # Generate SQL
    lines = []
    lines.append("-- ============================================================")
    lines.append("-- SM_FIELD_DEF: Regenerated from SmTableInformation*.h")
    lines.append("-- ============================================================")

    current_table = None
    for f in sorted(unique_fields, key=lambda x: (x['table_id'], x['sort_no'])):
        if f['table_id'] != current_table:
            current_table = f['table_id']
            lines.append(f"-- {current_table}")
        lines.append(gen_insert(f))

    # Write to output file for review
    out_path = os.path.join(script_dir, 'generated_field_def.sql')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
        f.write('\n')

    print(f"\nGenerated {len(unique_fields)} INSERT statements → {out_path}")
    print("Review the output, then run with --apply to replace in data.sql")

    if '--apply' in __import__('sys').argv:
        apply_to_data_sql(script_dir, lines)


def apply_to_data_sql(script_dir, new_lines):
    """Replace SM_FIELD_DEF section in data.sql."""
    data_sql = os.path.join(script_dir, '..', 'java-poc', 'src', 'main', 'resources', 'data.sql')

    with open(data_sql, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the first SM_FIELD_DEF INSERT and the section boundary
    lines = content.split('\n')
    start_idx = None
    end_idx = None

    for i, line in enumerate(lines):
        if 'INSERT INTO SM_FIELD_DEF' in line and start_idx is None:
            start_idx = i
        if start_idx is not None and 'INSERT INTO SM_FIELD_DEF' not in line and 'UPDATE SM_FIELD_DEF' not in line:
            if line.strip() and not line.strip().startswith('--'):
                if 'SM_FIELD_DEF' not in line:
                    end_idx = i
                    break

    if start_idx is None:
        print("Could not find SM_FIELD_DEF section in data.sql")
        return

    # Keep everything before and after the SM_FIELD_DEF section
    before = lines[:start_idx]
    after = lines[end_idx:] if end_idx else []

    new_content = '\n'.join(before) + '\n' + '\n'.join(new_lines) + '\n' + '\n'.join(after)

    with open(data_sql, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"Applied to {data_sql}")


if __name__ == '__main__':
    main()
