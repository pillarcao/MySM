# SM 系统迁移计划

> 目标：将现有 MFC 客户端 + C 服务端 + IBM MQ + DB2 架构，迁移为 Vue3 Web 客户端 + Spring Boot Java 服务端 + DB2 架构。
>
> 状态：第四阶段 POC 已完成（JWT 登录鉴权验证通过）
>
> 更新日期：2026-05-21

---

## 一、总体策略

**双轨并行，渐进替换**

- 旧系统（MFC + C + MQ）继续运行
- 新系统（Vue3 + Spring Boot + DB2）逐表上线
- 每张表独立验证，不对旧系统造成全局影响
- 开发期使用 H2 内存数据库快速迭代，功能验证通过后迁移到 DB2

---

## 二、当前系统架构分析

### 2.1 数据库分层

| 类型 | 数量 | 特征 | 示例 |
|------|------|------|------|
| **B 表（BuildTime/编辑态）** | ~85 张 | 含业务字段 + 21 个通用控制字段 | `BCODE`, `BUSER`, `BPROD` |
| **成对 D 表（Runtime/运行态）** | ~85 张 | 与 B 表字段相同，不含控制字段 | `DCODE`, `DUSER`, `DPROD` |
| **独立 D 表（业务运行时）** | ~150+ 张 | 无对应 B 表，纯业务数据 | `DLOT`, `DOPE`, `DEQP` |
| **SYSDATA** | 1 张 | 系统参数表，含控制字段 | `SYSDATA` |

### 2.2 B 表通用控制字段（21 个）

```
REL_FLG         CHAR(1)     -- Release 状态标志 (E=Edit, R=Released)
COMP_FLG        CHAR(1)     -- 完成标志
CRE_DATE        TIMESTAMP
CRE_USER        CHAR(20)
LAST_DATE1~5    TIMESTAMP   -- 5 层操作历史
LAST_ACT1~5     CHAR(12)
LAST_USER1~5    CHAR(20)
OWNER           CHAR(20)
OWNERG          CHAR(10)
PERMISSION      CHAR(10)    -- 默认 "PUBLIC    "
LOCK_USER       CHAR(20)    -- 记录锁
LOCK_TIME       TIMESTAMP
COMMENT         CHAR(128)
```

### 2.3 主键设计

- B 表主键 = `业务主键 + REL_FLG`
- D 表主键 = `业务主键`（不含 REL_FLG）

### 2.4 核心机制

1. **Release**：将 B 表中 `REL_FLG='R'` 的记录复制到对应 D 表
2. **记录锁**：通过 `LOCK_USER` + `LOCK_TIME` 实现
3. **权限**：`BUSER`（用户）+ `BUSERG`（用户组）+ `BUSERG_FUNC`（功能权限）
4. **配置驱动**：`TABLEINFOEX` 结构体数组定义 UI 和校验规则

---

## 三、技术选型

| 层级 | 旧技术 | 新技术 | 说明 |
|------|--------|--------|------|
| 前端 | MFC | Vue3 + ElementPlus | 动态表单引擎 |
| 后端 | C + MQ | Spring Boot 3.x | REST API |
| 持久层 | DB2 Embedded SQL | MyBatis + JdbcTemplate | MyBatis 用于配置查询，JdbcTemplate 用于动态 SQL |
| 数据库 | DB2 | H2(开发) → DB2(生产) | 兼容 DB2 语法 |
| 构建 | AIX 编译 | Maven + JDK 17 | 实际运行环境为 JDK 8 |
| 前端构建 | Visual Studio | Vite | |

---

## 四、六阶段迁移计划

### 第一阶段：基础骨架 + 单表 POC（已完成）

**目标**：证明"一张配置表从 DB2 到 Web 能完整跑通 CRUD"

| 步骤 | 内容 | 产出 | Checkpoint |
|------|------|------|------------|
| 1.1 | 创建 Spring Boot 项目，配置 H2 数据库 | 项目能启动 | `SELECT 1` 成功 |
| 1.2 | 设计 `BaseEntity`（21 控制字段）+ `BCode` 实体 | Java 类与 BCODE 表 1:1 映射 | 用 MyBatis 查出数据 |
| 1.3 | 手写 BCODE 的 TABLEINFOEX 配置 JSON | `table-config/bcode.json` | 字段与旧系统一致 |
| 1.4 | 写通用 CRUD Controller | Postman 能调通 | 返回数据与旧系统一致 |
| 1.5 | 写 Vue3 动态表单页面 | 浏览器能增删查改 | 界面字段与 MFC 一致 |

**为什么选 BCODE**：字段最少（4 个业务字段），无 Dummy Field，无复杂联动，失败成本低。

**当前状态**：✅ 已完成

---

### 第二阶段：通用框架固化（已完成）

**目标**：新增一张表只需配 JSON，前后端零代码

| 步骤 | 内容 | 产出 | 状态 |
|------|------|------|------|
| 2.1 | 设计 `SM_TABLE_DEF` / `SM_FIELD_DEF` 配置表 | 数据库配置表 | ✅ 已完成 |
| 2.2 | 将 C 头文件中的 `TABLEINFOEX` 批量迁移到配置表 | BCODE、BUSER 配置入库 | ✅ 已完成 |
| 2.3 | 写 `DynamicCrudService`：根据表名自动路由到对应 Mapper | 新增表时后端零代码 | ✅ 已完成 |
| 2.4 | 写 Vue3 `DynamicTableManager.vue` | 新增表时前端零代码 | ✅ 已完成 |
| 2.5 | 验证第二张表（`BUSER`，含登录逻辑） | 用户管理页面可用 | ✅ 已完成 |

**关键实现细节**：

- `DynamicCrudService` 使用 `JdbcTemplate` 拼接动态 SQL，根据 `SM_TABLE_DEF` 获取表名，`SM_FIELD_DEF` 获取字段列表和主键信息。
- save/delete 时，B 表自动将 `REL_FLG` 纳入 WHERE 条件（因为 B 表主键含 REL_FLG，但 SM_FIELD_DEF 中未配置 REL_FLG 字段）。
- 插入时自动补全 21 个控制字段的默认值（REL_FLG='E', COMP_FLG='0', CRE_USER='SYSTEM' 等）。
- 更新时自动更新 `LAST_DATE1/LAST_ACT1/LAST_USER1`。
- 前端 `DynamicTableManager.vue` 根据 `isSearchItem='Y'` 渲染列表列，根据 `isDummy='N'` 渲染表单字段，支持 `SELECT/NUMBER/STRING` 三种输入类型。

**已验证表**：
- `BCODE`：字段最少，无 Dummy Field，验证通过
- `BUSER`：含 10 个 USERG_ID 字段，含 Dummy Field（PROD_CODE_CAT, CODE_CAT），验证通过

**当前状态**：✅ 已完成

---

### 第三阶段：Release 机制 + B/D 双表同步（已完成）

**目标**：解决最核心的"编辑态 → 运行态"问题

| 步骤 | 内容 | 产出 | 状态 |
|------|------|------|------|
| 3.1 | 实现 `ReleaseService`：将 B* 表数据复制到 D* 表 | `ReleaseService.java` | ✅ 已完成 |
| 3.2 | 处理 B 表比 D 表多的 21 个控制字段（复制时去掉） | 控制字段白名单过滤 | ✅ 已完成 |
| 3.3 | 在 schema.sql 中增加 DCODE、DUSER | D 表结构与旧系统一致 | ✅ 已完成 |
| 3.4 | 写 `ReleaseController` + 前端 Release 按钮 | `POST /api/release/{tableId}` | ✅ 已完成 |
| 3.5 | 在 BCODE 上完整验证：编辑 → 保存 → Release → 查询 D 表确认 | 端到端验证通过 | ✅ 已完成 |

**关键实现细节**：

- `ReleaseService.release(tableId, keys)` 流程：
  1. 查询 B 表 REL_FLG='E' 的记录
  2. 过滤掉 25 个控制字段（硬编码白名单）
  3. D 表 UPSERT：先 UPDATE，影响行数为 0 则 INSERT
  4. 删除 B 表中旧的 REL_FLG='R' 记录（如果存在，避免主键冲突）
  5. 更新 B 表记录 REL_FLG='R'，同时更新 LAST_DATE1/ACT1/USER1
- D 表名推断：`B` 前缀替换为 `D`（如 BCODE → DCODE）
- 前端 Release 按钮仅在 `REL_FLG='E'` 时显示，调用 `/api/release/{tableId}` 后自动刷新列表

**已验证场景**：
- BCODE TEST/04：插入 E → Release → B 表变 R、DCODE 同步 → 修改 E → 再次 Release → DCODE 更新为修订版

**当前状态**：✅ 已完成

---

### 第四阶段：权限与登录（已完成）

**目标**：替代 MFC 的登录和权限控制

| 步骤 | 内容 | 产出 | 状态 |
|------|------|------|------|
| 4.1 | Spring Security + JWT，从 `BUSER` 表鉴权 | `JwtUtil`, `SecurityConfig`, `UserDetailsServiceImpl` | ✅ 已完成 |
| 4.2 | 写 `AuthController`：`/api/auth/login` 返回 JWT | `AuthController.java` | ✅ 已完成 |
| 4.3 | 前端登录页面 + Axios 拦截器自动附加 token | `LoginView.vue`, `App.vue` | ✅ 已完成 |
| 4.4 | 验证登录流程 | 端到端验证通过 | ✅ 已完成 |

**关键实现细节**：

- `UserDetailsServiceImpl.loadUserByUsername`：查询 BUSER 表 REL_FLG='E' 的用户，返回 `UserDetails`
- `PasswordEncoder`：使用 `NoOpPasswordEncoder`（旧系统密码是明文 CHAR(10)，不做 BCrypt 加密）
- `JwtUtil`：jjwt 0.9.1（JDK8 兼容），token 过期时间 24h
- `JwtAuthenticationFilter`：从 `Authorization: Bearer <token>` 提取 token，解析 userId，设置 `SecurityContextHolder`
- `SecurityConfig`：禁用 CSRF，放行 `/api/auth/**` 和 `/h2-console/**`，其他请求需认证；允许 iframe（H2 Console 需要）
- 前端 `LoginView.vue`：登录成功后将 token 存入 localStorage，设置 Axios 默认 `Authorization` 头；退出时清除

**已验证场景**：
- 不带 token 访问受保护接口返回 403
- 正确用户名密码登录返回 JWT token
- 错误密码返回 401
- 带 token 访问 `DynamicCrudController` 正常返回数据

**当前状态**：✅ 已完成

---

### 第五阶段：批量迁移剩余表（POC 验证已完成）

**目标**：验证"新增一张表只需配置 DDL + SM 配置数据，前后端零代码"

| 步骤 | 内容 | 产出 | 状态 |
|------|------|------|------|
| 5.1 | 选第三张表 BCALND 验证零代码新增 | `BCALND` / `DCALND` schema + 配置 | ✅ 已完成 |
| 5.2 | 修复 DynamicCrudService / ReleaseService 列名保留字问题 | SQL 列名统一加双引号 | ✅ 已完成 |
| 5.3 | 修复前端→后端字段名映射问题 | 移除 `toUnderscoreMap`，前端直接传数据库列名 | ✅ 已完成 |
| 5.4 | BCALND 端到端验证：CRUD + Release | 零代码全程通过 | ✅ 已完成 |

**关键实现细节**：

- 新增表只需三步：
  1. `schema.sql` 中增加 B 表（含 21 个控制字段）和 D 表（不含控制字段）
  2. `data.sql` 中插入 `SM_TABLE_DEF` 和 `SM_FIELD_DEF` 配置
  3. 重启后前后端自动识别并渲染
- SQL 列名统一加双引号（`"DATE"`、`"REL_FLG"` 等），兼容 H2/DB2 保留字
- 前端表单字段名直接使用数据库列名，后端不再做 camelCase → underscore 转换

**已验证场景**：
- BCALND：插入 E → Release → B 表变 R、DCALND 同步 → 修改 E → 再次 Release → DCALND 更新为修订版
- 全程未修改任何 Java/Vue 源码，仅通过配置生效

**当前状态**：✅ POC 验证已完成（~85 张表批量迁移可参照此模式执行）

---

### 第六阶段：切换与下线（预计 1 周）

| 步骤 | 内容 |
|------|------|
| 6.1 | 新旧系统并行运行 1~2 周，用户可同时访问 |
| 6.2 | 通过 Nginx/网关层按用户或按表灰度切流 |
| 6.3 | 旧系统 MFC Client 和 C Server 下线 |

**当前状态**：⏳ 待开始

---

## 五、POC 文件结构

```
MySM/
├── PLAN.md                    ← 本文件
│
├── java-poc/                  ← Spring Boot 后端
│   ├── pom.xml
│   └── src/main/
│       ├── java/com/sm/
│       │   ├── SmPocApplication.java
│       │   ├── entity/
│       │   │   ├── BaseEntity.java          ← 21 个通用控制字段
│       │   │   ├── BCode.java               ← BCODE 业务实体（第一阶段）
│       │   │   ├── SmTableDef.java          ← SM_TABLE_DEF 实体
│       │   │   └── SmFieldDef.java          ← SM_FIELD_DEF 实体
│       │   ├── mapper/
│       │   │   ├── BCodeMapper.java
│       │   │   ├── SmTableDefMapper.java
│       │   │   └── SmFieldDefMapper.java
│       │   ├── service/
│       │   │   ├── BCodeService.java
│       │   │   ├── MetaService.java         ← 获取表配置元数据
│       │   │   ├── DynamicCrudService.java  ← 通用 CRUD（第二/五阶段）
│       │   │   └── ReleaseService.java      ← B→D Release（第三阶段）
│       │   ├── security/
│       │   │   ├── SecurityConfig.java      ← Spring Security 配置（第四阶段）
│       │   │   ├── JwtAuthenticationFilter.java  ← JWT 过滤器（第四阶段）
│       │   │   └── UserDetailsServiceImpl.java   ← BUSER 鉴权（第四阶段）
│       │   ├── util/
│       │   │   └── JwtUtil.java             ← JWT 生成/解析（第四阶段）
│       │   └── controller/
│       │       ├── BCodeController.java
│       │       ├── MetaController.java
│       │       ├── DynamicCrudController.java
│       │       ├── ReleaseController.java
│       │       └── AuthController.java      ← 登录接口（第四阶段）
│       └── resources/
│           ├── application.yml              ← H2 内存库配置（开发用）
│           ├── schema.sql                   ← BCODE, BUSER, BCALND, DCODE, DUSER, DCALND + SM 配置表
│           ├── data.sql                     ← 初始数据 + SM 配置数据（含 BCALND 零代码配置）
│           └── mapper/
│               └── BCodeMapper.xml
│
├── vue-poc/                   ← Vue3 + ElementPlus 前端
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js
│       ├── App.vue
│       └── components/
│           ├── BCodeManager.vue             ← 第一阶段手写页面
│           ├── DynamicTableManager.vue      ← 第二/三/五阶段动态页面
│           └── LoginView.vue                ← 第四阶段登录页面
│
├── Wafer_SMClient/            ← 旧系统 MFC 客户端源码
├── Wafer_SMServer/            ← 旧系统 C 服务端源码
└── WV-MMDBD_20241223_LS2.ddl  ← DB2 完整 DDL 导出
```

---

## 六、运行方式

### 后端（需要 Maven + JDK）

```bash
cd java-poc
mvn spring-boot:run
```
- API 地址：`http://localhost:8080/api/...`
- H2 Console：`http://localhost:8080/h2-console`
  - JDBC URL: `jdbc:h2:mem:sm_db`
  - Username: `sa`
  - Password: (空)

### 前端（需要 Node.js）

```bash
cd vue-poc
npm install
npm run dev
```
- 页面地址：`http://localhost:5173`
- API 通过 Vite proxy 自动转发到 `localhost:8080`

---

## 七、Checkpoint 验证清单

### 第一阶段 POC 验证

- [x] `GET /api/bcode/list` 返回数据
- [x] H2 Console 能看到 BCODE 表结构和初始数据
- [x] 前端页面能显示列表，与旧系统 BCODE 字段对应
- [x] 前端能新增一条记录，保存后刷新列表可见
- [x] 前端能编辑记录，数据库中 `LAST_DATE1`/`LAST_ACT1` 自动更新
- [x] 前端能删除记录

### 第二阶段 通用框架验证

- [x] 新增一张表时，后端不需要新增 Java 类（DynamicCrudService 自动路由）
- [x] 新增一张表时，前端不需要新增 Vue 组件（DynamicTableManager 自动渲染）
- [x] BCODE 配置数据入库后，前后端自动识别并渲染
- [x] BUSER 配置数据入库后，前后端自动识别并渲染（含 Dummy Field）
- [x] B 表 save/delete 时 REL_FLG 正确参与主键逻辑

### 第三阶段 Release 机制验证

- [x] 向 BCODE 插入 REL_FLG='E' 记录，前端/Postman 能 Release
- [x] Release 后 B 表记录 REL_FLG 变为 'R'，LAST_ACT1='RELEASE'
- [x] Release 后 DCODE 出现对应记录，业务字段一致
- [x] 修改 B 表 E 记录后再次 Release，DCODE 记录被更新（幂等）
- [x] 前端 Release 按钮仅在 REL_FLG='E' 时显示

### 第四阶段 登录鉴权验证

- [x] 不带 token 访问受保护接口返回 403
- [x] `POST /api/auth/login` 正确密码返回 JWT
- [x] 错误密码返回 401
- [x] 带 token 访问 CRUD 接口正常

### 第五阶段 零代码新增表验证

- [x] 新增 BCALND 表仅通过 schema.sql + data.sql 配置，未修改 Java/Vue 代码
- [x] BCALND CRUD 正常（含保留字列名 DATE）
- [x] BCALND Release 正常，DCALND 同步正确
- [x] BCALND 幂等 Release 验证通过

### SELECT 下拉框数据源验证

- [x] 新增 SYSDATA 表存储下拉选项（TBL_NAME/FLD_NAME/FLD_VAL/FLD_STR）
- [x] 后端 `/api/meta/dropdown/{retrievalTable}/{format}` 接口正常返回选项
- [x] 前端 SELECT 字段自动调用接口加载选项（CODE_CAT、USERG_ID 等）
- [x] 新增/编辑表单中 SELECT 类型字段渲染为带选项的下拉框

---

## 八、待澄清问题

| 优先级 | 问题 | 状态 |
|--------|------|------|
| 高 | DB2 完整 DDL | 已提供 ✅ |
| 高 | MQ 报文体序列化格式 | 用户确认不需要 ❌ |
| 高 | 登录权限模型 | 已确认在 BUSER/BUSERG ✅ |
| 中 | 每张表的 `DBRECCHECKTBL` 验证规则 | 待补充 |
| 中 | BuildTime ↔ RunTime 同步详细逻辑 | 第三阶段已验证 ✅ |
| 低 | 数据量和并发用户数 | 待补充 |
| 低 | 是否有批量导入/导出、报表功能 | 待补充 |

---

## 九、下一步行动

1. **DBRECCHECKTBL 验证规则**：提供 `wdbrec.sqc` 中各表的检查数组，实现后端校验逻辑
2. **SELECT 下拉框数据源**：DynamicTableManager 支持从 SYSDATA / BCODE 等参照表加载选项
3. **BPROD 验证**：选一张字段多、含 Dummy Field 的表（如 BPROD）验证复杂场景
4. **DB2 迁移**：将 H2 schema 迁移到真实 DB2 环境验证语法兼容性
