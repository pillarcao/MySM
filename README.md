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

> **树形分组：** 设置 `TREE_LEVEL` 列（>=0）可将左侧面板记录按该字段分组显示。
> ```sql
> -- 例如：BCODE 表按 CODE_CAT 字段分组
> UPDATE SM_FIELD_DEF SET TREE_LEVEL = 0 WHERE TABLE_ID = 'TBLID_BXXXX' AND FIELD_NAME = 'XXXX_CAT';
> ```

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
| IS_KEY | 'Y'=主键，右侧面板 Item name 前加 `*` 标识 |
| IS_DUMMY | 'Y'=虚拟字段（数据库中不存在），右侧面板 Item name 用 `(括号)` 包裹 |
| IS_AUTO | 'Y'=系统自动管理字段（数据库中存在，用户不可编辑，显示在 Property 标签页） |
| SYSTEM_READONLY | 'Y'=系统只读（配合 IS_AUTO 使用，前端禁止编辑） |
| IS_SEARCH_ITEM | 'Y'=出现在中间表格列 |
| PROPERTY_NO | >0 时显示在右侧 Property 标签页，值为排序号 |
| FIELD_TYPE | SELECT(下拉)/NUMBER(数字)/STRING(文本) |
| RETRIEVAL_TABLE | 下拉数据源：`SYSDATA` / `BCODE` / `NONE`(无下拉) |
| FORMAT | 下拉格式键（SYSDATA 的 FLD_NAME 或 BCODE 的 CODE_CAT） |
| OPEN_BUTTON | >0 时右侧面板显示 OPEN 下钻按钮（跳转到 REF_TABLE_ID） |
| REF_TABLE_ID | 参照表 ID：有值时中间表头显示 Jump 按钮，右侧显示 J 选择按钮 |
| REF_FIELD_NAME | 参照字段名（Jump/选择时用于定位） |
| CALENDAR_BUTTON | 'Y'=日期选择器 |
| TREE_LEVEL | >=0 时左侧面板按此字段分组显示树形结构（-1=不分组） |

### 下拉框配置 (COMBO)

原系统 COMBO 类型与新系统配置映射：

| 原系统 | 新系统 SM_FIELD_DEF 配置 | 前端行为 |
|--------|------------------------|----------|
| COMBO_SYSDATA | `FIELD_TYPE='SELECT'`, `RETRIEVAL_TABLE='SYSDATA'`, `FORMAT='键名'` | 下拉框，选项来自 SYSDATA 表 |
| COMBO_CODE | `FIELD_TYPE='SELECT'`, `RETRIEVAL_TABLE='BCODE'`, `FORMAT='CODE_CAT值'` | 下拉框，选项来自 BCODE 表 |
| COMBO_TABLE | `FIELD_TYPE='STRING'`, `REF_TABLE_ID='TBLID_Bxxx'` | 文本框 + Jump(J) 弹出选择器 |
| COMBO_NONE | `FIELD_TYPE='STRING'`, `RETRIEVAL_TABLE='NONE'` | 普通文本输入框 |

**配置示例：**
```sql
-- COMBO_SYSDATA: EQP_CAT 下拉，选项来自 SYSDATA.FLD_NAME='EQP_CAT'
UPDATE SM_FIELD_DEF SET FIELD_TYPE = 'SELECT', RETRIEVAL_TABLE = 'SYSDATA',
  FORMAT = 'EQP_CAT' WHERE TABLE_ID = 'TBLID_BEQP' AND FIELD_NAME = 'EQP_CAT';

-- COMBO_CODE: FABID 下拉，选项来自 BCODE.CODE_CAT='FABID'
UPDATE SM_FIELD_DEF SET FIELD_TYPE = 'SELECT', RETRIEVAL_TABLE = 'BCODE',
  FORMAT = 'FABID' WHERE TABLE_ID = 'TBLID_BEQP' AND FIELD_NAME = 'FAB_ID';
```

> 使用 `tools/gen_combo_updates.py` 可从原系统头文件批量提取 COMBO 配置。

### OPEN 下钻按钮 (IS_DUMMY + OPEN_BUTTON)

原系统 `FLD_dummy` 字段在新系统中通过 `IS_DUMMY='Y'` + `OPEN_BUTTON>0` + `REF_TABLE_ID` 实现：

- 中间表格：不显示该字段列
- 右侧面板 Data 标签：Item name 显示 `(字段名)`，Value 列显示 `OPEN` 按钮
- 点击 OPEN 按钮跳转到 `REF_TABLE_ID` 对应的表

**配置示例：**
```sql
-- Eqp_Mtl: 虚拟字段，OPEN 按钮跳转到 BEQP_MTL 表
INSERT INTO SM_FIELD_DEF (...) VALUES (
  'TBLID_BEQP', 'Eqp_Mtl', '装置ﾏﾃﾘｱﾙ', 'Eqp Material',
  'STRING', 1, 'N', 'N', 'Y', 'N',  -- IS_DUMMY='Y'
  28, -1, -1, 0, 0,
  'N', 'N', 'N', 'STRING', 1,
  'N', 0, 'N', 'N', 'N', 'NONE', NULL, NULL, NULL, NULL,
  'N', 'N', 1,                       -- OPEN_BUTTON=1
  'TBLID_BEQP_MTL', 'EQP_ID', 0     -- REF_TABLE_ID + REF_FIELD
);
```

> 使用 `tools/regen_field_def.py` 可从原系统头文件完整重新生成所有字段定义（含 dummy 字段）。

### 表头 Jump 按钮

有 `REF_TABLE_ID` 的字段在中间表格的列头下方显示 `Jump` 按钮，点击跳转到参照表。
右侧面板中同样显示 `J` 按钮用于弹出参照选择器（RefPicker）。

### IS_DUMMY vs IS_AUTO 区别

| | IS_DUMMY='Y' | IS_AUTO='Y' |
|---|---|---|
| 数据库中存在 | 否（虚拟字段） | 是（真实列） |
| 用途 | OPEN 下钻跳转到关联表 | 系统自动维护的控制字段 |
| Save 时 | 跳过，不写 SQL | 跳过用户输入，后端自动填值 |
| 中间表格 | 不显示 | 显示为列 |
| 右侧面板 | Data 标签 - OPEN 按钮 | Property 标签 - 只读表格 |
| 典型字段 | Eqp_Mtl, RouteConnect, Q-Time | REL_FLG, COMP_FLG, CRE_DATE, OWNER, LAST_* |

### 25 个公共控制字段 (IS_AUTO='Y')

每张 B 表自动包含以下 25 个控制字段，通过 `tools/gen_control_fields.py` 批量生成配置：

| 字段 | 说明 | 中间表格显示 |
|------|------|:---:|
| REL_FLG | 发布状态 N=编辑 / Y=已发布 | Yes |
| COMP_FLG | 编辑完成 N=未完成 / Y=已完成 | Yes |
| CRE_DATE | 创建时间 | Yes |
| CRE_USER | 创建者 | - |
| OWNER | 记录所有者 | Yes |
| OWNERG | 所有者组 | - |
| PERMISSION | 权限 | - |
| LOCK_USER | 锁定者 | - |
| LOCK_TIME | 锁定时间 | - |
| COMMENT | 备注 | - |
| LAST_DATE1~5 | 操作时间（5 层 shift-register） | - |
| LAST_ACT1~5 | 操作类型（5 层） | - |
| LAST_USER1~5 | 操作者（5 层） | - |

### 工具脚本

| 脚本 | 用途 |
|------|------|
| `tools/regen_field_def.py` | 从 SmTableInformation*.h 完整重新生成 SM_FIELD_DEF（含 dummy 字段） |
| `tools/gen_control_fields.py` | 为所有表生成 25 个公共控制字段配置 |
| `tools/gen_combo_updates.py` | 从原系统提取 COMBO_SYSDATA/COMBO_CODE 配置并生成 UPDATE |
| `tools/parse_ddl.py` | 从 DB2 DDL 生成 H2 建表语句 |
| `tools/parse_checks.py` | 从 wdbtbl.h 提取校验规则 |

### 状态流转

每条记录通过 `REL_FLG` 和 `COMP_FLG` 两个标志位管理其生命周期状态。

**标志位含义：**
- `REL_FLG`: N=编辑中, Y=已发布
- `COMP_FLG`: N=未完成, Y=编辑完成

**状态转换规则：**

| 操作 | 说明 | REL_FLG | COMP_FLG |
|------|------|---------|----------|
| **UPDATE / NEW** | 进入编辑模式 / 新建记录 | N | N |
| **EDIT** | 字段级编辑（仅 UI 状态变更） | 不变 | 不变 |
| **SAVE** | 保存到数据库，UI 退出编辑态 | 不变 | 不变 |
| **EDITCOMP** | 编辑完成 | N | Y |
| **RELEASE** | 发布到运行表（B→D） | Y | Y |
| **ROLLBACK** | D 表数据覆盖 B 表，恢复到 Release 状态 | Y | Y |
| **UNDO** | 撤销当前编辑，回到上一步 | 上一步值 | 上一步值 |

**状态流转图：**

```
                    ┌─────────────┐
                    │  UPDATE/NEW │
                    │   (N, N)    │
                    └──────┬──────┘
                           │ SAVE
                           ▼
                    ┌─────────────┐
           ┌───────│   (N, N)    │
           │       └──────┬──────┘
           │ EDITCOMP     │ ROLLBACK (D→B)
           ▼              ▼
    ┌─────────────┐ ┌─────────────┐
    │   (N, Y)    │ │   (Y, Y)    │
    └──────┬──────┘ └─────────────┘
           │ RELEASE        ▲
           ▼                │
    ┌─────────────┐         │
    │   (Y, Y)    │─────────┘
    └─────────────┘   ROLLBACK
```

**ROLLBACK 说明：** 用 D 表数据覆盖 B 表对应记录，恢复为 Release 版本数据。B 表编辑态 (N) 记录被删除，D 表数据写入 B 表并设为 (Y, Y)。

### UNDO 撤销

UNDO 分两阶段执行，使用操作栈记录可撤销动作：

**阶段 1 — 本地撤销（未保存到 DB）：**

| 场景 | 行为 |
|------|------|
| 新增行未保存 | 从列表移除该行 |
| 编辑行未保存 | reload 服务端数据恢复原始值 |

**阶段 2 — DB 级撤销（已提交的操作）：**

| 原操作 | UNDO 行为 |
|--------|----------|
| **Add** (新增 + Save) | 调用 delete API 删除该记录 |
| **Delete** (删除) | 用删除前快照调用 save API 恢复记录 |
| **Update** (编辑 + Save) | 用更新前快照覆盖回 DB |

> 撤销失败时操作会推回栈中，可重试。

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
