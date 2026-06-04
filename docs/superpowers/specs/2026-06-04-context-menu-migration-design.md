# 右键菜单迁移设计

> 从 MFC 原系统右键菜单迁移 6 项核心功能到 Vue3 前端 + Spring Boot 后端

## 范围

迁移 4 项纯前端 + 2 项需后端支持的功能：

| 类别 | 菜单项 | 快捷键 | 说明 |
|------|--------|--------|------|
| 纯前端 | **Clear** | Ctrl+Del | 清空选中单元格/行数据 |
| 纯前端 | **Copy** | Ctrl+C | 复制选中行数据到系统剪贴板 |
| 纯前端 | **Paste** | Ctrl+V | 从剪贴板粘贴数据到当前编辑行 |
| 纯前端 | **Find** | Ctrl+F | 在当前已加载行中搜索文本 |
| 需后端 | **Rollback** | — | 删除编辑态记录，恢复 Release 版本 |
| 需后端 | **Force Unlock** | — | 强制清除记录锁（需 Supervisor 权限） |

## 架构

```
DynamicTableManager.vue (父组件)
  ├─ SearchDialog.vue
  ├─ RefPicker.vue
  ├─ ContextMenu.vue       ★ 新增组件
  │   渲染右键菜单 UI
  │   所有 action emit 给父组件处理
  └─ 业务逻辑处理所有 action
```

## 组件设计

### ContextMenu.vue

**职责**：渲染右键菜单 UI，不包含业务逻辑。

**Props：**
- `visible: Boolean` — 是否显示
- `x: Number` — 屏幕 X 坐标
- `y: Number` — 屏幕 Y 坐标
- `col: Object` — 右键所在的列配置
- `disabled: Object` — 各菜单项的禁用状态 `{ clear, copy, paste, find, rollback, forceUnlock }`

**Emits：**
- `action(type)` — 所有菜单操作
- `close` — 关闭菜单

**菜单项布局（从上到下）：**
```
New          — 始终可用
Edit         — hasSelection
Save         — isEditMode
─────────────
Edit Comp    — canEditComp
Release      — canRelease
─────────────
Undo         — 始终可用
─────────────
Clear        — hasSelection ★新增
Copy         — hasSelection ★新增
Paste        — isEditMode ★新增
Find         — 始终可用 ★新增
─────────────
Delete       — hasSelection
─────────────
Rollback     — hasSelection ★新增
Force Unlock — hasSelection (Supervisor only) ★新增
─────────────
Sort Asc     — 需要 col
Sort Desc    — 需要 col
Hide Column  — 需要 col
Show All     — 始终可用
```

## 数据流

### Clear
```
右键点击 → ContextMenu emit('action','clear')
→ DynamicTableManager 清空 editingRow/clipboardRow 中的非 key 字段值
→ 如 editingRow 存在则直接置空；否则操作 currentRow
```

### Copy
```
右键点击 → ContextMenu emit('action','copy')
→ DynamicTableManager 将 currentRow 序列化为 TSV 文本写入 navigator.clipboard
→ 显示提示信息
```

### Paste
```
右键点击 → ContextMenu emit('action','paste')
→ DynamicTableManager 从 navigator.clipboard 读文本，解析为 key-value
→ 将值写入 editingRow 对应字段（仅允许修改非 key 字段）
→ 需要进入编辑模式（如果不在编辑中）
```

### Find
```
右键点击 → ContextMenu emit('action','find')
→ DynamicTableManager 显示内联查找输入框
→ 在当前 list 中逐行搜索文本
→ 匹配时定位到对应行
```

### Rollback
```
右键点击 → ContextMenu emit('action','rollback')
→ 弹出确认对话框
→ POST /api/rollback/{tableId} 提交 key 字段
→ 后端：删除编辑态记录(REL_FLG='N'), 重新加载 Release 版本
→ 前端刷新列表
```

### Force Unlock
```
右键点击 → ContextMenu emit('action','forceUnlock')
→ POST /api/force-unlock/{tableId} 提交 key 字段
→ 后端：验证 Supervisor 权限, 清除 LOCK_USER + LOCK_TIME
→ 前端刷新列表
```

## 后端 API

### POST /api/rollback/{tableId}

请求体：key 字段 JSON
```json
{ "PROD_ID": "ABC001", "REL_FLG": "N" }
```

处理逻辑：
1. 查找当前编辑态记录（key + REL_FLG='N'）
2. 查找对应 Release 版记录（key + REL_FLG='Y'）
3. 删除编辑态记录
4. 重新查询返回当前数据

### POST /api/force-unlock/{tableId}

请求体：key 字段 JSON
```json
{ "PROD_ID": "ABC001" }
```

处理逻辑：
1. 验证当前用户是否为 Supervisor
2. 查找记录，清除 LOCK_USER 和 LOCK_TIME 字段
3. 更新记录状态为 BROWSE

## 禁用状态逻辑

| 菜单项 | 启用条件 |
|--------|---------|
| Clear | currentRow 存在 |
| Copy | currentRow 存在 |
| Paste | editingRow 存在（编辑模式中） |
| Find | list 有数据 |
| Rollback | currentRow 存在，非新增记录，REL_FLG='N'，且存在对应的 Release 版记录 |
| Force Unlock | currentRow 存在，记录被锁定，当前用户是 Supervisor |

## 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `vue-poc/src/components/ContextMenu.vue` | 新建 | 右键菜单组件 |
| `vue-poc/src/components/DynamicTableManager.vue` | 修改 | 接入 ContextMenu，新增 6 个 action 处理逻辑 |
| `java-poc/src/main/java/com/sm/controller/RollbackController.java` | 新建 | Rollback API |
| `java-poc/src/main/java/com/sm/service/RollbackService.java` | 新建 | Rollback 业务逻辑 |
| `java-poc/src/main/java/com/sm/controller/ForceUnlockController.java` | 新建 | Force Unlock API |
| `java-poc/src/main/java/com/sm/service/ForceUnlockService.java` | 新建 | Force Unlock 业务逻辑 |
