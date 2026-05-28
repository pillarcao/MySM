# SM 系统运维开发配置手册

## 目录
1. [系统架构](#系统架构)
2. [配置表结构](#配置表结构)
3. [字段配置详解 (SM_FIELD_DEF)](#字段配置详解-sm_field_def)
4. [校验规则配置 (SM_CHECK_DEF)](#校验规则配置-sm_check_def)
5. [菜单配置 (MENU_GROUP)](#菜单配置-menu_group)
6. [下钻配置 (SM_DRILL_DEF)](#下钻配置-sm_drill_def)
7. [新增一张表 (完整流程)](#新增一张表)
8. [状态流转](#状态流转)
9. [按钮功能对照表](#按钮功能对照表)

---

## 系统架构

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Vue 3 前端   │───→│  Spring Boot │───→│   H2 数据库   │
│  Element Plus │    │  后端 API    │    │  (可切MySQL)  │
└──────────────┘    └──────────────┘    └──────────────┘
    配置驱动：新增表只需写 SQL，无需改 Java/Vue 代码
```

**B表 (BuildTime)**：编辑态表，含 25 个控制字段 (REL_FLG~COMMENT)  
**D表 (Runtime)**：运行时表，仅含业务字段，Release 后从 B 表同步

---

## 配置表结构

### SM_TABLE_DEF（表定义）

| 列名 | 类型 | 必填 | 说明 |
|------|------|------|------|
| TABLE_ID | VARCHAR(32) | Y | 表唯一ID，格式 `TBLID_BXXXX` |
| TABLE_NAME | VARCHAR(40) | Y | B表名，如 `BCODE` |
| JP_TITLE | VARCHAR(80) | Y | 日文标题（菜单/表头显示） |
| US_TITLE | VARCHAR(80) | Y | 英文标题（默认显示，无US时用JP） |
| SORT_NO | INT | Y | 菜单排序号 |
| MENU_GROUP | VARCHAR(80) | - | 菜单分组（Route/Product/Equipment/User/Others等） |
| RELEASE_FLAG | VARCHAR(1) | Y | 是否支持Release，默认 'Y' |
| HAS_DUMMY | VARCHAR(1) | Y | 是否有虚拟字段，默认 'N' |

### SM_FIELD_DEF（字段定义）

| 列名 | 类型 | 必填 | 说明 |
|------|------|------|------|
| TABLE_ID | VARCHAR(32) | Y | 所属表ID |
| FIELD_NAME | VARCHAR(40) | Y | 字段名（必须与 DDL 列名一致） |
| JP_TITLE | VARCHAR(80) | - | 日文标题 |
| US_TITLE | VARCHAR(80) | - | 英文标题（默认显示） |
| DB_TYPE | VARCHAR(20) | Y | 数据库类型：`STRING`/`NUMBER`/`DOUBLE`/`TIMESTAMP` |
| DB_LENGTH | INT | Y | 字段长度 |
| IS_KEY | VARCHAR(1) | Y | 是否主键：`Y`/`N` |
| NOT_BLANK | VARCHAR(1) | Y | 是否非空：`Y`/`N` |
| IS_DUMMY | VARCHAR(1) | Y | 是否虚拟字段：`Y`/`N`（虚拟字段不存储不显示） |
| IS_SEARCH_ITEM | VARCHAR(1) | Y | 是否检索项：`Y`/`N`（出现在搜索对话框） |
| FIELD_TYPE | VARCHAR(20) | Y | 前端控件类型 |
| RETRIEVAL_TABLE | VARCHAR(20) | - | 下拉数据源 |
| CALENDAR_BUTTON | VARCHAR(1) | - | 日历按钮：`Y`/`N` |
| JUMP_BUTTON | VARCHAR(1) | - | Jump跳转按钮：`Y`/`N`（已废弃，用REF_TABLE_ID） |
| OPEN_BUTTON | INT | - | 0=无 1=Open按钮 2=Jump按钮 |
| REF_TABLE_ID | VARCHAR(32) | - | 参照表ID（外键） |
| REF_FIELD_NAME | VARCHAR(40) | - | 参照字段名 |
| SPECIAL_BUTTON | INT | - | 特殊按钮（保留） |

### SM_CHECK_DEF（校验规则）

| 列名 | 类型 | 必填 | 说明 |
|------|------|------|------|
| TABLE_ID | VARCHAR(32) | Y | 所属表ID |
| CHECK_TYPE | VARCHAR(10) | Y | 操作类型：`SAVE`/`RELEASE`/`DELETE`/`EDITCOMP` |
| CHECK_ORDER | INT | Y | 校验执行顺序 |
| CHECK_KIND | VARCHAR(20) | Y | 校验类型（见下方详细说明） |
| FIELD_NAME | VARCHAR(40) | - | 校验字段 |
| REF_TABLE | VARCHAR(40) | - | 参照表（KEY/RELEASE_PARAM/RELEASE_WRITE 时使用） |
| REF_FIELD | VARCHAR(40) | - | 参照字段（KEY 时使用） |
| EXPECT_VALUE | VARCHAR(50) | - | 期望值（STRING 校验时使用） |
| ERR_MSG | VARCHAR(100) | - | 错误消息 |

### SM_DRILL_DEF（下钻配置）

| 列名 | 类型 | 必填 | 说明 |
|------|------|------|------|
| SOURCE_TABLE_ID | VARCHAR(32) | Y | 源表ID |
| TARGET_TABLE_ID | VARCHAR(32) | Y | 目标表ID |
| LABEL | VARCHAR(80) | Y | 下钻按钮标签 |
| SORT_NO | INT | Y | 排序号 |

---

## 字段配置详解 (SM_FIELD_DEF)

### 核心必填列

#### TABLE_ID
- **类型**: VARCHAR(32)
- **格式**: `TBLID_BXXXX` (B表) 或 `TBLID_DXXXX` (D表)
- **示例**: `TBLID_BCODE`, `TBLID_BPROD`
- **说明**: 表唯一标识，与 schema.sql 中的表名对应

#### FIELD_NAME
- **类型**: VARCHAR(40)
- **格式**: 大写英文字母+下划线
- **示例**: `CODE_CAT`, `ROUTE_ID`, `EQP_NAME`
- **说明**: 必须与 DDL CREATE TABLE 中定义的列名完全一致（大小写敏感）

#### IS_KEY (`Y`/`N`)
- **Y**: 主键字段
  - 新增行时可编辑
  - 编辑已有行时只读
  - 用于 WHERE 条件定位记录
  - Release 时作为 D 表主键
- **N**: 非主键字段
  - 正常可编辑

#### IS_DUMMY (`Y`/`N`)
- **Y**: 虚拟字段
  - 不存储在数据库表中
  - 不显示在列表和表单中
  - 用于特殊计算或过渡用途
- **N**: 真实字段（默认）

#### IS_SEARCH_ITEM (`Y`/`N`)
- **Y**: 出现在搜索对话框中
- **N**: 不出现在搜索对话框中
- **建议**: 主键和常用查询字段设为 Y

### 类型与输入控制

#### FIELD_TYPE（前端控件类型）

| 值 | 控件 | 适用场景 |
|----|------|---------|
| `STRING` | `el-input` 文本输入 | 普通文本字段 |
| `NUMBER` | `el-input-number` 数字输入 | 数值字段 |
| `SELECT` | `el-select` 下拉选择 | 固定选项字段 |
| - | `el-date-picker` 日期选择 | CALENDAR_BUTTON='Y' 时自动使用 |

#### RETRIEVAL_TABLE（下拉数据源）

| 值 | 说明 | 示例 |
|----|------|------|
| `NONE` | 无下拉 | 普通文本输入 |
| `SYSDATA` | 从 SYSDATA 表取选项 | 下拉选择框 |
| `COMBO_TABLE` | 从参照表取选项（前端处理） | - |
| `COMBO_CODE` | 代码表选项 | 如 BATCH_CAT |

**SYSDATA 下拉配置示例：**
```sql
-- SYSDATA 存储下拉选项
-- TBL_NAME: 用于哪个"表"的下拉
-- FLD_NAME: 字段类别名
-- FLD_VAL: 选项值
-- FLD_STR: 选项显示文本
INSERT INTO SYSDATA VALUES ('*', 'CODE_CAT', 'BATCH_CAT', 'Batch Category');
```

当 `RETRIEVAL_TABLE='SYSDATA'` 且 `FORMAT='CODE_CAT'` 时，前端调用 `/api/meta/dropdown/SYSDATA/CODE_CAT` 获取选项列表。

### 按钮配置

#### CALENDAR_BUTTON (`Y`/`N`)
- **Y**: 显示日历选择器
  - 编辑时自动使用 `el-date-picker` 替代文本输入
  - 值格式：`YYYYMMDD`（8位数字字符串）
  - 适用字段：日期类型字段（如 BCALND.DATE）
- **N**: 普通文本输入

#### JUMP_BUTTON (`Y`/`N`) — 已废弃
- 旧系统用于控制是否显示 Jump 跳转按钮
- 新系统改用 `REF_TABLE_ID` + `REF_FIELD_NAME` 自动判断

#### OPEN_BUTTON (`0`/`1`/`2`)
| 值 | 含义 | 按钮 | 功能 |
|----|------|------|------|
| 0 | 无 | - | 无特殊按钮 |
| 1 | Open | O | 打开文件路径（将字段值作为路径/URL在新标签页打开） |
| 2 | Jump | J | 跳转到参照表（同 REF_TABLE_ID 机制） |

#### REF_TABLE_ID + REF_FIELD_NAME（外键参照）
- 当 `REF_TABLE_ID` 非空时：
  - 右侧 KV 面板显示 `→` 跳转按钮（字段有值时）
  - 右侧 KV 面板显示 `…` 选择按钮（始终显示）
  - `→` 点击：打开参照表，按 `REF_FIELD_NAME`=当前值过滤
  - `…` 点击：打开 RefPicker 选择参照表的值回填
- 示例：BUSER.USERG_ID1 设置 REF_TABLE_ID='TBLID_BUSERG', REF_FIELD_NAME='USERG_ID'

---

## 校验规则配置 (SM_CHECK_DEF)

### CHECK_TYPE（操作类型）

| 值 | 触发时机 |
|----|---------|
| `SAVE` | 新增/编辑保存时 |
| `RELEASE` | Release 发布时 |
| `DELETE` | 删除记录时 |
| `EDITCOMP` | EditComp 编辑完成时 |

### CHECK_KIND（校验类型详解）

#### NOTNULL — 非空校验
```sql
-- SAVE 时检查 CODE_CAT 不能为空
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_BCODE','SAVE',1,'NOTNULL','CODE_CAT',NULL,NULL,NULL,'代码分类不能为空');
```
- **FIELD_NAME**: 要检查的字段
- **ERR_MSG**: 校验失败时的错误消息

#### STAT_N / STAT_Y — 状态校验
```sql
-- SAVE 时只允许编辑态 (REL_FLG='N') 的记录
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_BCODE','SAVE',2,'STAT_N',NULL,NULL,NULL,NULL,'记录不是编辑态');

-- DELETE 时只允许已发布态 (REL_FLG='Y') 的记录
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_BCODE','DELETE',2,'STAT_Y',NULL,NULL,NULL,NULL,'记录不是已发布态');
```
- **N** = 编辑中（对应 REL_FLG='N'）
- **Y** = 已发布（对应 REL_FLG='Y'）
- **FIELD_NAME**: 留空，系统自动检查 REL_FLG 字段

#### COMP_N — 编辑完成状态校验
```sql
-- EDITCOMP 时检查 COMP_FLG='N'（未编辑完成才能执行）
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_BCODE','EDITCOMP',4,'COMP_N',NULL,NULL,NULL,NULL,'记录已编辑完成');
```
- 只在 EDITCOMP 操作中使用
- 防止重复编辑完成

#### LOCK_FREE — 锁校验
```sql
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_BCODE','SAVE',3,'LOCK_FREE',NULL,NULL,NULL,NULL,'记录已被锁定');
```
- 检查 LOCK_USER 为空且 LOCK_TIME 为 NULL
- 被锁定的记录不能编辑/删除/Release

#### KEY — 外键存在性校验
```sql
-- SAVE 时检查 USERG_ID1 在 BUSERG 表中存在
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_BUSER','SAVE',5,'KEY','USERG_ID1','BUSERG','USERG_ID',NULL,'业务组不存在');
```
- **FIELD_NAME**: 外键字段
- **REF_TABLE**: 参照表名
- **REF_FIELD**: 参照表的主键字段名

#### STRING — 固定值校验
```sql
-- 检查字段值等于固定值
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_BUSERG','SAVE',4,'STRING','lock_user',NULL,NULL,'     ','锁定用户须为空');
```
- **FIELD_NAME**: 要检查的字段
- **EXPECT_VALUE**: 期望的固定值

#### REF_STAT_R — 参照表状态校验
```sql
-- EDITCOMP 时检查参照表记录必须是已发布状态
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_BPROD','EDITCOMP',5,'REF_STAT_R','ROUTE_ID','BROUTE','ROUTE_ID',NULL,'工艺路线未发布');
```
- 检查 REF_TABLE 中 REF_FIELD=当前值 的记录 REL_FLG='Y'

#### RELEASE_PARAM / RELEASE_WRITE — D表映射
```sql
-- Release 时 D 表的 WHERE 条件字段 = 主键
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_BCODE','RELEASE',10,'RELEASE_PARAM','CODE_CAT','DCODE',NULL,NULL,NULL);

-- Release 时写入 D 表的字段
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_BCODE','RELEASE',12,'RELEASE_WRITE','CODE_NAME','DCODE',NULL,NULL,NULL);
```
- **RELEASE_PARAM**: D 表 UPSERT 的 WHERE 条件（通常是主键字段）
- **RELEASE_WRITE**: D 表 SET 的字段（业务数据）
- **REF_TABLE**: D 表名

### 标准校验模板

每张表至少需要以下 4 组校验：

```sql
-- SAVE 校验
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_XXX','SAVE',1,'NOTNULL','XXX_ID',NULL,NULL,NULL,'ID不能为空');
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_XXX','SAVE',2,'STAT_N',NULL,NULL,NULL,NULL,'记录不是编辑态');
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_XXX','SAVE',3,'LOCK_FREE',NULL,NULL,NULL,NULL,'记录已被锁定');

-- RELEASE 校验（含 D 表映射）
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_XXX','RELEASE',1,'NOTNULL','XXX_ID',NULL,NULL,NULL,'ID不能为空');
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_XXX','RELEASE',2,'STAT_N',NULL,NULL,NULL,NULL,'记录不是编辑态');
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_XXX','RELEASE',3,'LOCK_FREE',NULL,NULL,NULL,NULL,'记录已被锁定');
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_XXX','RELEASE',10,'RELEASE_PARAM','XXX_ID','DXXX',NULL,NULL,NULL);
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_XXX','RELEASE',11,'RELEASE_WRITE','XXX_NAME','DXXX',NULL,NULL,NULL);

-- DELETE 校验
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_XXX','DELETE',1,'NOTNULL','XXX_ID',NULL,NULL,NULL,'ID不能为空');
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_XXX','DELETE',2,'STAT_Y',NULL,NULL,NULL,NULL,'记录不是已发布态');
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_XXX','DELETE',3,'LOCK_FREE',NULL,NULL,NULL,NULL,'记录已被锁定');

-- EDITCOMP 校验
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_XXX','EDITCOMP',1,'NOTNULL','XXX_ID',NULL,NULL,NULL,'ID不能为空');
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_XXX','EDITCOMP',2,'STAT_N',NULL,NULL,NULL,NULL,'记录不是编辑态');
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_XXX','EDITCOMP',3,'LOCK_FREE',NULL,NULL,NULL,NULL,'记录已被锁定');
INSERT INTO SM_CHECK_DEF VALUES ('TBLID_XXX','EDITCOMP',4,'COMP_N',NULL,NULL,NULL,NULL,'记录已编辑完成');
```

---

## 菜单配置 (MENU_GROUP)

### 原理

前端 `App.vue` 从 `/api/meta/tables` 读取所有表，按 `menuGroup` 字段分组，渲染为 `File` 菜单下的二级子菜单：

```
File
├── Route       → 所有 MENU_GROUP='Route' 的表
├── Product     → 所有 MENU_GROUP='Product' 的表
├── Equipment   → ...
├── User        → ...
├── Others      → 默认分组（未配置或空字符串归入）
└── ...
```

### 配置方式

修改 `SM_TABLE_DEF` 的 `MENU_GROUP` 列即可。无需重启前端，下次打开菜单自动生效。

```sql
-- 将表归入指定分组
UPDATE SM_TABLE_DEF SET MENU_GROUP = 'Route' WHERE TABLE_ID = 'TBLID_BROUTE';

-- 从菜单中隐藏（设为空或 NULL，同时不在任何分组中）
UPDATE SM_TABLE_DEF SET MENU_GROUP = '' WHERE TABLE_ID = 'TBLID_BXXX';
```

### 当前分组列表

| MENU_GROUP | 显示名称 | 包含的表（示例） | 说明 |
|------------|---------|-----------------|------|
| Route | Route | BROUTE, BMROUTE, BOPE, BROUTECNCT | 工艺路线相关 |
| Product | Product | BPROD, BPRODCODE, BRECIP_LOOKUP | 产品相关 |
| Equipment | Equipment | BEQPG, BEQP, BAREA, BEQP_RECIP | 设备相关 |
| Measurement | Measurement | BMEAS_LOOKUP, BMEAS_ID, BMEAS_ITEM | 测量相关 |
| ProcessData | ProcessData | BPROCDATA_LOOKUP, BPROCDATA_ID | 过程数据 |
| Stocker | Stocker | BSTK, BSTKOUTLET, BEMPCAR_SC | 库存相关 |
| Cassette | Cassette | BCARG, BCARTYPE | 卡匣相关 |
| User | User | BUSER, BUSERG, BUSERG_FUNC | 用户相关 |
| Stage | Stage | BSTG, BSTGG | 阶段相关 |
| Compile | Compile | BCMPL_MODE, BCMPL_DEST_TYPE | 编译相关 |
| Others | Others | BCODE, BCALND, BHOLDCODE 等 | 其他（默认） |

### 新增表时配置菜单

```sql
-- Step 1: 插入表定义时直接指定 MENU_GROUP
INSERT INTO SM_TABLE_DEF (TABLE_ID, TABLE_NAME, JP_TITLE, US_TITLE, SORT_NO, MENU_GROUP)
VALUES ('TBLID_BXXXX', 'BXXXX', '新表', 'NewTable', 500, 'Others');

-- Step 2: 如果忘记设置，后续可 UPDATE
UPDATE SM_TABLE_DEF SET MENU_GROUP = 'Others' WHERE TABLE_ID = 'TBLID_BXXXX';
```

### 新增/修改分组

分组名称在前端 `App.vue` 的 `menuGroups` 数组中定义。要新增分组需同时修改前后端：

**1. 后端（data.sql）：**
```sql
UPDATE SM_TABLE_DEF SET MENU_GROUP = 'NewGroup' WHERE TABLE_ID IN ('TBLID_BXXX', 'TBLID_BYYY');
```

**2. 前端（App.vue `menuGroups` 数组）：**
```javascript
const menuGroups = ['Route','Product','Equipment','Measurement','ProcessData',
  'Stocker','Cassette','User','Stage','Compile','Others', 'NewGroup']  // 追加
```

> 注意：分组显示顺序由 `menuGroups` 数组决定，不在数组中的 `MENU_GROUP` 值不会出现在菜单中。

### 菜单不显示排查

| 现象 | 可能原因 | 解决 |
|------|---------|------|
| 整个 File 菜单为空 | Token 过期，fetchTables 失败 | 重新登录 |
| 某个分组为空 | 该分组下无任何表的 MENU_GROUP 匹配 | 检查是否有表配置了该 MENU_GROUP |
| 某张表不在菜单中 | MENU_GROUP 为空或 NULL | 设置为有效分组名 |
| 表出现在 Others | MENU_GROUP 值不在 menuGroups 数组中 | 更正 MENU_GROUP 值为已注册的分组名 |

---

## 下钻配置 (SM_DRILL_DEF)

定义表之间的层级钻取关系：

```sql
-- BROUTE → BROUTE_MROUTE 下钻
INSERT INTO SM_DRILL_DEF (SOURCE_TABLE_ID, TARGET_TABLE_ID, LABEL, SORT_NO)
VALUES ('TBLID_BROUTE', 'TBLID_BROUTE_MROUTE', 'Module Route', 1);

-- BROUTE → BROUTECNCT 下钻
INSERT INTO SM_DRILL_DEF (SOURCE_TABLE_ID, TARGET_TABLE_ID, LABEL, SORT_NO)
VALUES ('TBLID_BROUTE', 'TBLID_BROUTECNCT', 'Route Connect', 2);
```

下钻时自动传递源表的所有主键字段（除 REL_FLG）作为查询条件。

---

## 新增一张表

### 完整流程（5步）

**Step 1: 创建 B/D 表 (schema.sql)**

```sql
CREATE TABLE BXXXX (
    XXXX_ID     CHAR(20) NOT NULL,
    XXXX_NAME   CHAR(40) NOT NULL,
    -- ... 业务字段 ...

    -- 以下 25 个控制字段（复制即可，不需要修改）
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
    -- ... 同 B 表业务字段 ...
    PRIMARY KEY (XXXX_ID)
);
```

**Step 2: 配置 SM_TABLE_DEF (data.sql)**

```sql
INSERT INTO SM_TABLE_DEF (TABLE_ID, TABLE_NAME, JP_TITLE, US_TITLE, SORT_NO, MENU_GROUP)
VALUES ('TBLID_BXXXX', 'BXXXX', '日本語名', 'English Name', 500, 'Others');
```

**Step 3: 配置 SM_FIELD_DEF (data.sql)**

每个业务字段一条 INSERT，关键列：
- `IS_KEY`: 主键='Y'，其他='N'
- `IS_SEARCH_ITEM`: 需要出现在搜索框='Y'
- `NOT_BLANK`: 不允许空值='Y'
- `FIELD_TYPE`: STRING/NUMBER/SELECT

**Step 4: 配置 SM_CHECK_DEF (data.sql)**

复制标准校验模板（见上文），替换 `XXX_ID`、`XXX_NAME`、`DXXX`。

**Step 5: (可选) 配置下钻/菜单**

```sql
-- 设置菜单分组
UPDATE SM_TABLE_DEF SET MENU_GROUP = 'Others' WHERE TABLE_ID = 'TBLID_BXXXX';

-- 配置下钻关系
INSERT INTO SM_DRILL_DEF VALUES ('TBLID_BROUTE', 'TBLID_BXXXX', 'Related', 1);
```

---

## 状态流转

```
                    Save / 新增
                        ↓
                 ┌─────────────┐
            ┌───→│ (N, N)      │ ←── REL_FLG='N', COMP_FLG='N'
            │    │  编辑中      │       可编辑、可EditComp
            │    └──────┬──────┘
            │           │ EditComp
            │           ↓
            │    ┌─────────────┐
            │    │ (Y, N)      │ ←── REL_FLG='N', COMP_FLG='Y'
            │    │  编辑完成    │       可Release、不可EditComp
            │    └──────┬──────┘
            │           │ Release
            │           ↓
            │    ┌─────────────┐
            │    │ (Y, Y)      │ ←── REL_FLG='Y', COMP_FLG='Y'
            │    │  已发布      │       可Delete、同步到D表
            │    └─────────────┘
            │
            └── Update（将已发布记录重新变为编辑中）
```

---

## 按钮功能对照表

### 工具栏按钮

| 按钮 | 前置条件 | 功能 |
|------|---------|------|
| 新增 | 无 | 表格顶部插入空白行，进入编辑模式 |
| Update | 需选中一行 | 切换编辑模式（已发布→编辑中，COMP_FLG='N', REL_FLG='N'） |
| 保存 | 编辑模式 | 保存当前编辑行到数据库 |
| 编辑完成 | 选中 REL_FLG='N' 的行 | COMP_FLG → 'Y' |
| Release | 选中 REL_FLG='N' 的行 | 发布到 D 表，REL_FLG='Y', COMP_FLG='Y' |
| 删除 | 选中 REL_FLG='Y' 的行 | 删除记录 |
| Undo | 新增行未保存 | 撤销新增，移除空白行 |

### 字段级按钮（表格单元格 + 右侧面板）

#### → Jump（跳转按钮）

| 配置组合 | 显示位置 | 显示条件 | 点击行为 |
|---------|---------|---------|---------|
| `REF_TABLE_ID` 非空 + `JUMP_BUTTON='Y'` | **表格单元格** | 字段值非空 | 打开参照表，按 `REF_FIELD_NAME`=当前值过滤 |
| `REF_TABLE_ID` 非空（字段有值） | **右侧面板** | 字段值非空 | 同上 |

**实现逻辑：**
```
1. 取当前字段的值作为查询条件
2. 查询字段名 = REF_FIELD_NAME（如果为空则用当前字段名）
3. 打开 TARGET = REF_TABLE_ID 对应的表
4. 自动执行查询: TARGET WHERE REF_FIELD_NAME = 当前值
```

**配置示例（BUSER.USERG_ID1 → BUSERG）：**
```sql
-- USERG_ID1 字段配置了参照到 BUSERG
-- REF_TABLE_ID = 'TBLID_BUSERG', REF_FIELD_NAME = 'USERG_ID'
-- 当 USERG_ID1 = 'ADMIN' 时点击 →
-- → 打开 BUSERG 表，自动查询 WHERE USERG_ID = 'ADMIN'
```

#### … Select（选择按钮）

| 配置组合 | 显示位置 | 显示条件 | 点击行为 |
|---------|---------|---------|---------|
| `REF_TABLE_ID` 非空 | **右侧面板** | 始终显示 | 打开 RefPicker 弹窗，浏览参照表，选中一行回填值 |
| `REF_TABLE_ID` 非空 + 第一列或编辑行 | **表格单元格** | 编辑模式 | 同上 |

#### C Calendar（日历按钮）

| 配置组合 | 显示位置 | 显示条件 | 点击行为 |
|---------|---------|---------|---------|
| `CALENDAR_BUTTON='Y'` | **表格单元格 + 右侧面板** | 编辑状态 | 显示日期选择器，值格式 `YYYYMMDD` |

### 表级按钮（右侧面板 Related 区域）

| 配置组合 | 显示位置 | 点击行为 |
|---------|---------|---------|
| `SM_DRILL_DEF` 中 SOURCE_TABLE_ID = 当前表 | **右侧面板 Data Tab 底部** | 打开 TARGET_TABLE_ID，传递当前记录所有主键字段（除 REL_FLG）作为查询条件 |

**实现逻辑：**
```
1. 取当前记录的所有 IS_KEY='Y' 且 FIELD_NAME != 'REL_FLG' 的字段
2. 将每个主键字段的值作为查询参数
3. 打开 TARGET_TABLE_ID 表
4. 自动执行查询
```

**配置示例（BROUTE → BROUTECNCT）：**
```sql
INSERT INTO SM_DRILL_DEF (SOURCE_TABLE_ID, TARGET_TABLE_ID, LABEL, SORT_NO)
VALUES ('TBLID_BROUTE', 'TBLID_BROUTECNCT', 'Route Connect', 2);
```

### 旧系统按钮对照总表

| 旧系统 TABLEINFOEX 列 | 旧系统值 | 旧系统按钮 | 新系统实现 | 状态 |
|----------------------|---------|-----------|-----------|------|
| `JUMP_BUTTON='Y'` + `REF_TABLE_ID ≠ VIEW` | Jump | J | `→` 按钮（表格+右侧面板） | ✅ |
| `JUMP_BUTTON='Y'` + `REF_TABLE_ID = VIEW` | View | V | 未实现（Web无对应） | ❌ |
| `OPEN_BUTTON=1` | Open | O | 未实现（文件路径不适用Web） | ❌ |
| `OPEN_BUTTON=2` | Jump(Prop) | J | `→` 按钮（同 Jump） | ✅ |
| `SPECIAL_BUTTON=1` | Jump(Sheet) | J | `→` 按钮（同 Jump） | ✅ |
| `SPECIAL_BUTTON=2` | More | M | 未实现（Web textarea 替代） | ❌ |
| `SPECIAL_BUTTON=3` | RouteID | R | 未实现（特定业务逻辑） | ❌ |
| `CALENDAR_BUTTON='Y'` | Calendar | C | `el-date-picker` | ✅ |
| 字段长度 ≥ 100 | More | M | 未实现 | ❌ |
| `RETRIEVAL_TABLE ≠ NONE` | Dropdown | - | `el-select` | ✅ |
| `REF_TABLE_ID` 非空 | Select | - | `…` RefPicker | ✅ |
| `SM_DRILL_DEF` 配置 | - | - | Related 下钻 | ✅ |

### 按钮配置决策树

```
新增表时，按以下流程判断需要配置哪些按钮：

字段需要参照/下拉？
├── 固定选项 → RETRIEVAL_TABLE='SYSDATA', FORMAT='选项类别'
├── 参照其他表 → REF_TABLE_ID='TBLID_XXX', REF_FIELD_NAME='xxx_id'
│   └── 需要表格单元格跳转？ → JUMP_BUTTON='Y'
├── 日期字段 → CALENDAR_BUTTON='Y'
└── 表级下钻 → SM_DRILL_DEF INSERT
```

---

> **版本**: v2.0 | **最后更新**: 2026-05-28
