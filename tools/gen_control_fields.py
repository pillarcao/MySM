#!/usr/bin/env python3
"""
Generate SM_FIELD_DEF INSERT statements for 25 common control fields
across all configured tables.
"""
import re
import os

# Control fields template: (FIELD_NAME, JP_TITLE, US_TITLE, DB_TYPE, DB_LENGTH, IS_SEARCH_ITEM, SORT_NO, PROPERTY_NO)
CONTROL_FIELDS = [
    ("REL_FLG",    "状態",     "Status",    "STRING", 1,   "Y", 900, 1),
    ("COMP_FLG",   "編集完了", "Comp",      "STRING", 1,   "Y", 901, 2),
    ("CRE_DATE",   "作成日時", "Created",   "STRING", 26,  "Y", 902, 3),
    ("CRE_USER",   "作成者",   "Creator",   "STRING", 20,  "N", 903, 4),
    ("OWNER",      "所有者",   "Owner",     "STRING", 20,  "Y", 904, 5),
    ("OWNERG",     "所有G",    "OwnerG",    "STRING", 10,  "N", 905, 6),
    ("PERMISSION", "権限",     "Permission","STRING", 10,  "N", 906, 7),
    ("LOCK_USER",  "ロック者", "LockedBy",  "STRING", 20,  "N", 907, 8),
    ("LOCK_TIME",  "ロック時間","LockTime", "STRING", 26,  "N", 908, 9),
    ("COMMENT",    "コメント", "Comment",   "STRING", 128, "N", 909, 10),
    ("LAST_DATE1", "最終日時1","LastDate1", "STRING", 26,  "N", 910, 11),
    ("LAST_ACT1",  "最終操作1","LastAct1",  "STRING", 12,  "N", 911, 12),
    ("LAST_USER1", "最終者1",  "LastUser1", "STRING", 20,  "N", 912, 13),
    ("LAST_DATE2", "最終日時2","LastDate2", "STRING", 26,  "N", 913, 14),
    ("LAST_ACT2",  "最終操作2","LastAct2",  "STRING", 12,  "N", 914, 15),
    ("LAST_USER2", "最終者2",  "LastUser2", "STRING", 20,  "N", 915, 16),
    ("LAST_DATE3", "最終日時3","LastDate3", "STRING", 26,  "N", 916, 17),
    ("LAST_ACT3",  "最終操作3","LastAct3",  "STRING", 12,  "N", 917, 18),
    ("LAST_USER3", "最終者3",  "LastUser3", "STRING", 20,  "N", 918, 19),
    ("LAST_DATE4", "最終日時4","LastDate4", "STRING", 26,  "N", 919, 20),
    ("LAST_ACT4",  "最終操作4","LastAct4",  "STRING", 12,  "N", 920, 21),
    ("LAST_USER4", "最終者4",  "LastUser4", "STRING", 20,  "N", 921, 22),
    ("LAST_DATE5", "最終日時5","LastDate5", "STRING", 26,  "N", 922, 23),
    ("LAST_ACT5",  "最終操作5","LastAct5",  "STRING", 12,  "N", 923, 24),
    ("LAST_USER5", "最終者5",  "LastUser5", "STRING", 20,  "N", 924, 25),
]

def extract_table_ids(data_sql_path):
    """Extract all distinct TABLE_ID values from SM_FIELD_DEF inserts."""
    table_ids = set()
    with open(data_sql_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Match both formats: with and without column list
    for m in re.finditer(r"'(TBLID_\w+)'", content):
        tid = m.group(1)
        # Only include if it appears in SM_FIELD_DEF context (check surrounding text)
        start = max(0, m.start() - 200)
        context = content[start:m.start()]
        if 'SM_FIELD_DEF' in context or 'SM_TABLE_DEF' in context:
            table_ids.add(tid)
    # Also extract from SM_TABLE_DEF for completeness
    for m in re.finditer(r"INSERT INTO SM_TABLE_DEF.*?'(TBLID_\w+)'", content):
        table_ids.add(m.group(1))
    return sorted(table_ids)

COLUMNS = "TABLE_ID,FIELD_NAME,JP_TITLE,US_TITLE,DB_TYPE,DB_LENGTH,IS_KEY,NOT_BLANK,IS_DUMMY,IS_SEARCH_ITEM,SORT_NO,TREE_LEVEL,SHEET_NO,PAGE_NO,PROPERTY_NO,IS_AUTO,IS_MANDATORY,SYSTEM_READONLY,FIELD_TYPE,FIELD_LENGTH,INPUT_ALPHABET,INPUT_MULTIBYTE,INPUT_NUMERIC,INPUT_SYMBOL,INPUT_UPPERCASE,RETRIEVAL_TABLE,FORMAT,DEFAULT_VALUE,MIN_VALUE,MAX_VALUE,CALENDAR_BUTTON,JUMP_BUTTON,OPEN_BUTTON,REF_TABLE_ID,REF_FIELD_NAME,SPECIAL_BUTTON"

def gen_insert(table_id, field):
    """Generate one SM_FIELD_DEF INSERT statement."""
    fname, jp, us, db_type, db_len, is_search, sort_no, prop_no = field
    values = (
        f"'{table_id}','{fname}','{jp}','{us}',"
        f"'{db_type}',{db_len},"
        f"'N','N','N','{is_search}',"
        f"{sort_no},-1,0,0,{prop_no},"
        f"'Y','N','Y',"
        f"'STRING',{db_len},"
        f"'Y',0,'Y','Y','N',"
        f"'NONE',NULL,NULL,NULL,NULL,"
        f"'N','N',0,NULL,NULL,0"
    )
    return f"INSERT INTO SM_FIELD_DEF ({COLUMNS}) VALUES ({values});"

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_sql = os.path.join(script_dir, '..', 'java-poc', 'src', 'main', 'resources', 'data.sql')

    table_ids = extract_table_ids(data_sql)
    print(f"Found {len(table_ids)} tables")

    lines = []
    lines.append("")
    lines.append("-- ============================================================")
    lines.append("-- Common control fields for all tables (auto-generated)")
    lines.append("-- ============================================================")

    for tid in table_ids:
        lines.append(f"-- {tid}")
        for field in CONTROL_FIELDS:
            lines.append(gen_insert(tid, field))

    # Append to data.sql
    with open(data_sql, 'a', encoding='utf-8') as f:
        f.write('\n'.join(lines))
        f.write('\n')

    total = len(table_ids) * len(CONTROL_FIELDS)
    print(f"Appended {total} INSERT statements to data.sql")

if __name__ == '__main__':
    main()
