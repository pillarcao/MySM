# SM System - Java POC

## 快速启动

```bash
# 后端 (Java Spring Boot)
cd java-poc
mvn spring-boot:run

# 前端 (Vue 3 + Element Plus)
cd vue-poc
npm run dev
```

- 前端: http://localhost:5173
- 后端: http://localhost:8080
- 登录: `ADMIN` / `admin123`

## 新增一张表

只需修改 `java-poc/src/main/resources/` 下的 `schema.sql` 和 `data.sql`，无需改 Java/Vue 代码。

### Step 1: 创建 B 表 + D 表 (schema.sql)

```sql
CREATE TABLE BXXXX (
    XXXX_ID     CHAR(20) NOT NULL,
    XXXX_NAME   CHAR(40) NOT NULL,
    XXXX_DESC   CHAR(80) NOT NULL,

    REL_FLG     CHAR(1)  NOT NULL DEFAULT 'N',
    COMP_FLG    CHAR(1)  NOT NULL DEFAULT 'N',
    CRE_DATE    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CRE_USER    CHAR(20) NOT NULL DEFAULT 'SYSTEM',
    LAST_DATE1  TIMESTAMP,
    LAST_ACT1   CHAR(12) NOT NULL DEFAULT '',
    LAST_USER1  CHAR(20) NOT NULL DEFAULT '',
    LAST_DATE2  TIMESTAMP,
    LAST_ACT2   CHAR(12) NOT NULL DEFAULT '',
    LAST_USER2  CHAR(20) NOT NULL DEFAULT '',
    LAST_DATE3  TIMESTAMP,
    LAST_ACT3   CHAR(12) NOT NULL DEFAULT '',
    LAST_USER3  CHAR(20) NOT NULL DEFAULT '',
    LAST_DATE4  TIMESTAMP,
    LAST_ACT4   CHAR(12) NOT NULL DEFAULT '',
    LAST_USER4  CHAR(20) NOT NULL DEFAULT '',
    LAST_DATE5  TIMESTAMP,
    LAST_ACT5   CHAR(12) NOT NULL DEFAULT '',
    LAST_USER5  CHAR(20) NOT NULL DEFAULT '',
    OWNER       CHAR(20) NOT NULL DEFAULT 'SYSTEM',
    OWNERG      CHAR(10) NOT NULL DEFAULT '',
    PERMISSION  CHAR(10) NOT NULL DEFAULT 'PUBLIC    ',
    LOCK_USER   CHAR(20) NOT NULL DEFAULT '',
    LOCK_TIME   TIMESTAMP,
    "COMMENT"   CHAR(128) NOT NULL DEFAULT '',

    PRIMARY KEY (XXXX_ID, REL_FLG)
);

CREATE TABLE DXXXX (
    XXXX_ID     CHAR(20) NOT NULL,
    XXXX_NAME   CHAR(40) NOT NULL,
    XXXX_DESC   CHAR(80) NOT NULL,

    PRIMARY KEY (XXXX_ID)
);
```

> B 表需包含 25 个控制字段 (REL_FLG ~ COMMENT)，D 表只需业务字段。

### Step 2: 配置表元数据 (data.sql)

```sql
-- 表定义
INSERT INTO SM_TABLE_DEF (TABLE_ID, TABLE_NAME, JP_TITLE, US_TITLE, SORT_NO, MENU_GROUP)
VALUES ('TBLID_BXXXX', 'BXXXX', '表中文名', 'Table Name', 500, 'Others');

-- 字段定义 (每个业务字段一条)
INSERT INTO SM_FIELD_DEF (TABLE_ID, FIELD_NAME, JP_TITLE, US_TITLE, DB_TYPE, DB_LENGTH, IS_KEY, NOT_BLANK, IS_DUMMY, IS_SEARCH_ITEM, SORT_NO, IS_AUTO, IS_MANDATORY, SYSTEM_READONLY, FIELD_TYPE, FIELD_LENGTH, INPUT_ALPHABET, INPUT_MULTIBYTE, INPUT_NUMERIC, INPUT_SYMBOL, INPUT_UPPERCASE, RETRIEVAL_TABLE, CALENDAR_BUTTON, JUMP_BUTTON, OPEN_BUTTON, REF_TABLE_ID, REF_FIELD_NAME, SPECIAL_BUTTON)
VALUES ('TBLID_BXXXX', 'XXXX_ID', 'ID', 'ID', 'STRING', 20, 'Y', 'Y', 'N', 'Y', 0, 'N', 'Y', 'N', 'STRING', 20, 'Y', 0, 'Y', 'Y', 'Y', 'NONE', 'N', 'N', 0, NULL, NULL, 0);

INSERT INTO SM_FIELD_DEF (...) VALUES ('TBLID_BXXXX', 'XXXX_NAME', '名称', 'Name', 'STRING', 40, 'N', 'N', 'N', 'Y', -1, 'N', 'N', 'N', 'STRING', 40, 'Y', 7, 'Y', 'Y', 'N', 'NONE', 'N', 'N', 0, NULL, NULL, 0);
```

### Step 3: 配置校验规则 (data.sql)

```sql
-- SAVE 校验
INSERT INTO SM_CHECK_DEF (TABLE_ID, CHECK_TYPE, CHECK_ORDER, CHECK_KIND, FIELD_NAME, ERR_MSG) VALUES
('TBLID_BXXXX', 'SAVE', 1, 'NOTNULL', 'XXXX_ID', 'ID不能为空'),
('TBLID_BXXXX', 'SAVE', 2, 'STAT_N', NULL, '记录不是编辑态'),
('TBLID_BXXXX', 'SAVE', 3, 'LOCK_FREE', NULL, '记录已被锁定');

-- RELEASE 校验 (含 D 表映射)
INSERT INTO SM_CHECK_DEF (TABLE_ID, CHECK_TYPE, CHECK_ORDER, CHECK_KIND, FIELD_NAME, REF_TABLE, ERR_MSG) VALUES
('TBLID_BXXXX', 'RELEASE', 1, 'NOTNULL', 'XXXX_ID', NULL, 'ID不能为空'),
('TBLID_BXXXX', 'RELEASE', 2, 'STAT_N', NULL, NULL, '记录不是编辑态'),
('TBLID_BXXXX', 'RELEASE', 3, 'LOCK_FREE', NULL, NULL, '记录已被锁定'),
('TBLID_BXXXX', 'RELEASE', 10, 'RELEASE_PARAM', 'XXXX_ID', 'DXXXX', NULL),
('TBLID_BXXXX', 'RELEASE', 11, 'RELEASE_WRITE', 'XXXX_NAME', 'DXXXX', NULL);

-- DELETE 校验
INSERT INTO SM_CHECK_DEF (TABLE_ID, CHECK_TYPE, CHECK_ORDER, CHECK_KIND, FIELD_NAME, ERR_MSG) VALUES
('TBLID_BXXXX', 'DELETE', 1, 'NOTNULL', 'XXXX_ID', 'ID不能为空'),
('TBLID_BXXXX', 'DELETE', 2, 'STAT_Y', NULL, '记录不是已发布态'),
('TBLID_BXXXX', 'DELETE', 3, 'LOCK_FREE', NULL, '记录已被锁定');

-- EDITCOMP 校验
INSERT INTO SM_CHECK_DEF (TABLE_ID, CHECK_TYPE, CHECK_ORDER, CHECK_KIND, FIELD_NAME, ERR_MSG) VALUES
('TBLID_BXXXX', 'EDITCOMP', 1, 'NOTNULL', 'XXXX_ID', 'ID不能为空'),
('TBLID_BXXXX', 'EDITCOMP', 2, 'STAT_N', NULL, '记录不是编辑态'),
('TBLID_BXXXX', 'EDITCOMP', 3, 'LOCK_FREE', NULL, '记录已被锁定'),
('TBLID_BXXXX', 'EDITCOMP', 4, 'COMP_N', NULL, '记录已编辑完成');
```

### Step 4: (可选) 配置下钻按钮 (data.sql)

```sql
-- 从其他表下钻到本表
INSERT INTO SM_DRILL_DEF (SOURCE_TABLE_ID, TARGET_TABLE_ID, LABEL, SORT_NO)
VALUES ('TBLID_BROUTE', 'TBLID_BXXXX', 'Related Table', 1);
```

### 校验规则类型 (CHECK_KIND)

| CHECK_KIND | 说明 |
|------------|------|
| `NOTNULL` | 字段非空 |
| `STAT_N` | 检查 REL_FLG='N' (编辑态) |
| `STAT_Y` | 检查 REL_FLG='Y' (已发布) |
| `LOCK_FREE` | 检查未被锁定 |
| `COMP_N` | 检查 COMP_FLG='N' (未完成) |
| `KEY` | 外键存在性检查 (需 REF_TABLE + REF_FIELD) |
| `STRING` | 字段值等于 EXPECT_VALUE |
| `RELEASE_PARAM` | Release 时 D 表定位主键 |
| `RELEASE_WRITE` | Release 时写入 D 表的字段 |

### 字段配置说明 (SM_FIELD_DEF 关键列)

| 列 | 说明 |
|----|------|
| IS_KEY | 'Y'=主键 |
| IS_DUMMY | 'Y'=虚拟字段(不存储) |
| IS_SEARCH_ITEM | 'Y'=出现在查询条件栏 |
| FIELD_TYPE | SELECT/NUMBER/STRING |
| RETRIEVAL_TABLE | SYSDATA(下拉选项) / NONE |
| CALENDAR_BUTTON | 'Y'=日期选择器 |
| REF_TABLE_ID | 参照表ID (外键) |
| REF_FIELD_NAME | 参照字段名 |

### 状态流转

```
新增/保存 → (N,N) → EditComp → (Y,N) → Release → (Y,Y)
             ↑                    │
             └── Update ──────────┘
```

- REL_FLG: N=编辑中, Y=已发布
- COMP_FLG: N=未完成, Y=编辑完成

## 批量迁移 (从旧系统 DDL)

```bash
# 从 DB2 DDL 生成 H2 建表语句
python3 tools/parse_ddl.py --h2

# 从 wdbtbl.h 提取校验规则
python3 tools/parse_checks.py

# 合并 DDL + TABLEINFOEX + 校验规则
python3 tools/merge_all.py

# 安装特定表
python3 tools/install_tables.py
```

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Java 8, Spring Boot 2.7, MyBatis, H2 |
| 前端 | Vue 3, Element Plus, Vite, Vue Router |
| 工具 | Python 3 (迁移脚本) |
