#!/usr/bin/env python3
"""
Parse DB2 DDL file to extract CREATE TABLE statements and convert to H2 format.
Usage: python3 parse_ddl.py [--h2] [--summary] [--table BCODE]
"""

import re, sys, os

DDL_FILE = "/Users/caolizhu/Documents/VibeCode/MySM/WV-MMDBD_20241223_LS2.ddl"

def parse_tables(filepath):
    """Parse DB2 DDL file and extract all CREATE TABLE statements"""
    with open(filepath, 'r') as f:
        content = f.read()

    tables = {}
    # Match CREATE TABLE ... ( ... );
    pattern = r'CREATE\s+TABLE\s+"[^"]+"\."([^"]+)"\s*\((.*?)\)\s*;'
    for m in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
        table_name = m.group(1)
        body = m.group(2)
        tables[table_name] = parse_columns(body)

    return tables

def parse_columns(body):
    """Parse column definitions from CREATE TABLE body"""
    columns = []
    constraints = []  # PRIMARY KEY, UNIQUE, etc.
    lines = body.split('\n')

    current_line = ""
    for line in lines:
        line = line.strip()
        if not line or line.startswith('--'):
            continue

        current_line += " " + line
        if ',' in line or 'PRIMARY KEY' in line.upper() or 'UNIQUE' in line.upper():
            parts = current_line.split(',')
            for part in parts[:-1]:
                process_line(part.strip(), columns, constraints)
            current_line = parts[-1] if len(parts) > 1 else ""
            if line.endswith(','):
                continue
            else:
                process_line(current_line.strip(), columns, constraints)
                current_line = ""

    if current_line.strip():
        process_line(current_line.strip(), columns, constraints)

    return {"columns": columns, "constraints": constraints}

def process_line(line, columns, constraints):
    """Process a single column or constraint line"""
    line = line.strip()
    if not line:
        return

    # Check if it's a constraint (PRIMARY KEY, UNIQUE, FOREIGN KEY, CHECK)
    if re.match(r'^\s*(PRIMARY\s+KEY|UNIQUE|FOREIGN\s+KEY|CHECK|CONSTRAINT|IN\s+)', line, re.IGNORECASE):
        constraints.append(line)
        return

    # Parse column: "COLUMN_NAME" TYPE [NOT NULL] [DEFAULT ...] [WITH DEFAULT ...]
    # DB2-specific: "COLUMN_NAME" TYPE NOT NULL WITH DEFAULT '' COMPRESS SYSTEM DEFAULT
    # Strip quotes and extra DB2 cruft
    m = re.match(r'^\s*"([^"]+)"\s+(.+)$', line, re.IGNORECASE)
    if not m:
        return

    col_name = m.group(1)
    type_def = m.group(2).strip()

    # Parse type (e.g., "CHAR(20 OCTETS) NOT NULL DEFAULT 'SYSTEM'")
    type_match = re.match(r'(\w+)\s*(\([^)]*\))?\s*(.*)', type_def, re.IGNORECASE)
    if not type_match:
        return

    col_type = type_match.group(1).upper()
    col_len = type_match.group(2)  # e.g., "(20)" or "(20, 2)"
    rest = type_match.group(3).upper()

    # Map DB2 types to H2 types
    type_map = {
        "CHAR": "CHAR",
        "CHARACTER": "CHAR",
        "VARCHAR": "VARCHAR",
        "VARG": "VARCHAR",
        "INTEGER": "INT",
        "INT": "INT",
        "BIGINT": "BIGINT",
        "SMALLINT": "INT",
        "DOUBLE": "DOUBLE",
        "FLOAT": "DOUBLE",
        "DECIMAL": "DECIMAL",
        "DATE": "DATE",
        "TIMESTAMP": "TIMESTAMP",
        "TIME": "TIME",
        "CLOB": "CLOB",
        "BLOB": "BLOB",
        "GRAPHIC": "CHAR",
        "VARGRAPHIC": "VARCHAR",
        "DBCLOB": "CLOB",
    }

    h2_type = type_map.get(col_type, col_type)
    if col_len:
        # DB2 can have: CHAR(20 OCTETS), CHAR(20), VARCHAR(200 OCTETS)
        # Extract just the number
        num_match = re.search(r'\((\d+)', col_len)
        if num_match:
            h2_type += f"({num_match.group(1)})"

    # Parse modifiers
    not_null = "NOT NULL" in rest
    default_val = None

    # Extract DEFAULT value
    def_match = re.search(r"DEFAULT\s+('[^']*'|[\w.]+|NULL)", rest)
    if def_match:
        default_val = def_match.group(1)

    columns.append({
        "name": col_name,
        "type": h2_type,
        "notNull": not_null,
        "default": default_val,
    })

def generate_h2_ddl(tables, btbl_only=True):
    """Generate H2 CREATE TABLE statements"""
    lines = []
    for tbl_name in sorted(tables.keys()):
        if btbl_only and not tbl_name.startswith('B'):
            continue

        data = tables[tbl_name]
        columns = data.get("columns", [])
        constraints = data.get("constraints", [])

        if not columns:
            continue

        lines.append(f"CREATE TABLE {tbl_name} (")

        for col in columns:
            parts = [f'    "{col["name"]}"', col["type"]]
            if col["notNull"]:
                parts.append("NOT NULL")
            if col["default"] and col["default"] != "NULL":
                parts.append(f"DEFAULT {col['default']}")
            lines.append(" ".join(parts) + ",")

        # Add constraints (PRIMARY KEY etc.)
        for c in constraints:
            # Convert DB2 constraint format to H2
            c = c.strip().rstrip(',')
            # Convert IN "TX_BUFF" ... etc. to nothing
            if c.upper().startswith('IN '):
                continue
            if c.upper().startswith('COMPRESS'):
                continue
            if c.upper().startswith('INDEX '):
                continue
            if c.upper().startswith('ORGANIZE'):
                continue
            if c.upper().startswith('AUDIT'):
                continue
            if c.upper().startswith('DATA CAPTURE'):
                continue
            if c.upper().startswith('PCTFREE'):
                continue
            if c.upper().startswith('PARTITIONING'):
                continue
            if c.upper().startswith('DISTRIBUTE'):
                continue

            # Fix quoted names
            c = re.sub(r'"([^"]+)"', r'\1', c)
            # Remove DB2-specific WITH DEFAULT
            c = re.sub(r'WITH\s+DEFAULT\s+\'[^\']*\'', '', c, flags=re.IGNORECASE)
            c = re.sub(r'WITH\s+DEFAULT\s+\d+', '', c, flags=re.IGNORECASE)
            c = re.sub(r'COMPRESS\s+SYSTEM\s+DEFAULT', '', c, flags=re.IGNORECASE)
            c = c.strip().rstrip(',')

            if c:
                lines.append(f"    {c},")

        # Remove trailing comma from last line
        lines[-1] = lines[-1].rstrip(',')

        lines.append(");\n")

    return '\n'.join(lines)

def main():
    print("Parsing DDL file...")
    tables = parse_tables(DDL_FILE)
    print(f"  Found {len(tables)} tables")

    btables = [n for n in tables if n.startswith('B')]
    dtables = [n for n in tables if n.startswith('D')]
    other = [n for n in tables if not n.startswith('B') and not n.startswith('D')]
    print(f"  B tables: {len(btables)}, D tables: {len(dtables)}, Other: {len(other)}")

    if '--summary' in sys.argv:
        for t in sorted(btables):
            cols = tables[t].get("columns", [])
            print(f"  {t:30s} {len(cols)} columns")
        return

    if '--h2' in sys.argv:
        ddl = generate_h2_ddl(tables, btbl_only=True)
        out = os.path.join(os.path.dirname(__file__), "auto_generated", "tables_h2.sql")
        with open(out, 'w') as f:
            f.write("-- Auto-generated from DDL file: " + DDL_FILE + "\n")
            f.write("-- B tables only (H2 compatible)\n\n")
            f.write(ddl)
        count = len(ddl.split('CREATE TABLE')) - 1
        print(f"\nGenerated {out} ({count} B tables, {len(ddl)} bytes)")
        return

    if '--table' in sys.argv:
        idx = sys.argv.index('--table')
        name = sys.argv[idx + 1].upper()
        if name in tables:
            print(f"\n=== {name} ===")
            for col in tables[name].get("columns", []):
                print(f"  {col['name']:30s} {col['type']:15s} {'NOT NULL' if col['notNull'] else '':10s} {col['default'] or ''}")
        else:
            print(f"Table {name} not found")

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Usage: python3 parse_ddl.py [--h2] [--summary] [--table NAME]")
        main()
    else:
        main()
