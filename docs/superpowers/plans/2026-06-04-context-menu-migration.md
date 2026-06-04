# 右键菜单迁移 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 MFC 原系统右键菜单的 6 项功能迁移到 Vue3 + Spring Boot，同时将菜单 UI 抽离为独立 ContextMenu 组件。

**Architecture:** 新建 ContextMenu.vue 负责菜单 UI 渲染和事件 emit；DynamicTableManager.vue 处理所有 action 业务逻辑；Java 后端新增 Rollback 和 ForceUnlock 两个 REST API。

**Tech Stack:** Vue3 + ElementPlus + Axios (前端), Spring Boot + JdbcTemplate + MyBatis (后端)

---

### Task 1: Create ContextMenu.vue component

**Files:**
- Create: `vue-poc/src/components/ContextMenu.vue`

- [ ] **Step 1: Write the component file**

```vue
<template>
  <div v-if="visible" class="ctx-menu" :style="{ left: x + 'px', top: y + 'px' }" @click.stop @mouseleave="emit('close')">
    <div class="ctx-item" @click="emit('action', 'add')"><el-icon><Plus /></el-icon> New</div>
    <div class="ctx-item" :class="{ disabled: disabled.hasSelection === false }" @click="emit('action', 'update')"><el-icon><Edit /></el-icon> Edit</div>
    <div class="ctx-item" :class="{ disabled: disabled.isEditMode === false }" @click="emit('action', 'save')"><el-icon><Check /></el-icon> Save</div>
    <div class="ctx-divider"></div>
    <div class="ctx-item" :class="{ disabled: disabled.canEditComp === false }" @click="emit('action', 'editcomp')"><el-icon><Finished /></el-icon> Edit Comp</div>
    <div class="ctx-item" :class="{ disabled: disabled.canRelease === false }" @click="emit('action', 'release')"><el-icon><Promotion /></el-icon> Release</div>
    <div class="ctx-divider"></div>
    <div class="ctx-item" @click="emit('action', 'undo')"><el-icon><RefreshLeft /></el-icon> Undo</div>
    <div class="ctx-divider"></div>
    <div class="ctx-item" :class="{ disabled: disabled.cannotClear }" @click="emit('action', 'clear')">Clear</div>
    <div class="ctx-item" :class="{ disabled: disabled.cannotCopy }" @click="emit('action', 'copy')">Copy</div>
    <div class="ctx-item" :class="{ disabled: disabled.cannotPaste }" @click="emit('action', 'paste')">Paste</div>
    <div class="ctx-item" :class="{ disabled: disabled.cannotFind }" @click="emit('action', 'find')">Find</div>
    <div class="ctx-divider"></div>
    <div class="ctx-item" :class="{ disabled: disabled.hasSelection === false }" @click="emit('action', 'delete')"><el-icon><Delete /></el-icon> Delete</div>
    <div class="ctx-divider"></div>
    <div class="ctx-item" :class="{ disabled: disabled.cannotRollback }" @click="emit('action', 'rollback')">Rollback</div>
    <div class="ctx-item" :class="{ disabled: disabled.cannotForceUnlock }" @click="emit('action', 'forceUnlock')">Force Unlock</div>
    <div class="ctx-divider"></div>
    <div class="ctx-item" :class="{ disabled: !col }" @click="emit('action', 'sort-asc')"><el-icon><SortUp /></el-icon> Sort Asc</div>
    <div class="ctx-item" :class="{ disabled: !col }" @click="emit('action', 'sort-desc')"><el-icon><SortDown /></el-icon> Sort Desc</div>
    <div class="ctx-divider"></div>
    <div class="ctx-item" :class="{ disabled: !col }" @click="emit('action', 'hide-col')"><el-icon><Hide /></el-icon> Hide Column</div>
    <div class="ctx-item" @click="emit('action', 'show-all')"><el-icon><View /></el-icon> Show All Columns</div>
  </div>
</template>

<script setup>
import { Plus, Edit, Check, Finished, Promotion, Delete, RefreshLeft, SortUp, SortDown, Hide, View } from '@element-plus/icons-vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  x: { type: Number, default: 0 },
  y: { type: Number, default: 0 },
  col: { type: Object, default: null },
  disabled: {
    type: Object,
    default: () => ({
      hasSelection: false,
      isEditMode: false,
      canEditComp: false,
      canRelease: false,
      cannotClear: true,
      cannotCopy: true,
      cannotPaste: true,
      cannotFind: true,
      cannotRollback: true,
      cannotForceUnlock: true
    })
  }
})

const emit = defineEmits(['action', 'close'])
</script>

<style scoped>
.ctx-menu { position: fixed; z-index: 9999; background: #fff; border: 1px solid #e0e0e0; border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,.12); padding: 4px 0; min-width: 180px; font-size: 13px; }
.ctx-item { display: flex; align-items: center; gap: 8px; padding: 6px 14px; cursor: pointer; color: #333; }
.ctx-item:hover { background: #e6f7ff; color: #1890ff; }
.ctx-item.disabled { color: #ccc; cursor: default; pointer-events: none; }
.ctx-item .el-icon { font-size: 14px; }
.ctx-divider { height: 1px; background: #f0f0f0; margin: 4px 0; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add vue-poc/src/components/ContextMenu.vue
git commit -m "feat: add ContextMenu component, extract context menu UI from DynamicTableManager"
```

---

### Task 2: Create Rollback backend API

**Files:**
- Create: `java-poc/src/main/java/com/sm/controller/RollbackController.java`
- Create: `java-poc/src/main/java/com/sm/service/RollbackService.java`

- [ ] **Step 1: Write RollbackService**

File: `java-poc/src/main/java/com/sm/service/RollbackService.java`

```java
package com.sm.service;

import com.sm.entity.SmFieldDef;
import com.sm.mapper.SmFieldDefMapper;
import com.sm.mapper.SmTableDefMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class RollbackService {

    private final SmTableDefMapper tableDefMapper;
    private final SmFieldDefMapper fieldDefMapper;
    private final JdbcTemplate jdbcTemplate;

    @Transactional
    public void rollback(String tableId, Map<String, Object> keys) {
        String tableName = getTableName(tableId);
        List<SmFieldDef> keyFields = fieldDefMapper.findByTableId(tableId).stream()
                .filter(f -> "Y".equals(f.getIsKey()) && !"REL_FLG".equals(f.getFieldName()))
                .collect(Collectors.toList());

        // 1. Check editable record exists (REL_FLG='N')
        StringBuilder whereN = new StringBuilder("\"REL_FLG\" = 'N'");
        List<Object> keyValues = new ArrayList<>();
        for (SmFieldDef kf : keyFields) {
            whereN.append(" AND \"").append(kf.getFieldName()).append("\" = ?");
            keyValues.add(keys.get(kf.getFieldName()));
        }
        List<Map<String, Object>> editRows = jdbcTemplate.queryForList(
                "SELECT * FROM " + tableName + " WHERE " + whereN, keyValues.toArray());
        if (editRows.isEmpty()) {
            throw new IllegalArgumentException("未找到可回滚的记录（需存在编辑态记录）");
        }

        // 2. Check released record exists (REL_FLG='Y')
        StringBuilder whereY = new StringBuilder("\"REL_FLG\" = 'Y'");
        List<Object> whereYValues = new ArrayList<>();
        for (SmFieldDef kf : keyFields) {
            whereY.append(" AND \"").append(kf.getFieldName()).append("\" = ?");
            whereYValues.add(keys.get(kf.getFieldName()));
        }
        List<Map<String, Object>> relRows = jdbcTemplate.queryForList(
                "SELECT * FROM " + tableName + " WHERE " + whereY, whereYValues.toArray());
        if (relRows.isEmpty()) {
            throw new IllegalArgumentException("未找到已 Release 版本记录，无法回滚");
        }

        // 3. Delete the editable record
        jdbcTemplate.update("DELETE FROM " + tableName + " WHERE " + whereN, keyValues.toArray());
    }

    private String getTableName(String tableId) {
        var table = tableDefMapper.findByTableId(tableId);
        if (table == null) {
            throw new IllegalArgumentException("Table config not found: " + tableId);
        }
        return table.getTableName();
    }
}
```

- [ ] **Step 2: Write RollbackController**

File: `java-poc/src/main/java/com/sm/controller/RollbackController.java`

```java
package com.sm.controller;

import com.sm.service.RollbackService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/rollback")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class RollbackController {

    private final RollbackService rollbackService;

    @PostMapping("/{tableId}")
    public ResponseEntity<?> rollback(@PathVariable String tableId, @RequestBody Map<String, Object> keys) {
        try {
            rollbackService.rollback(tableId, keys);
            return ResponseEntity.ok(Map.of("message", "回滚成功"));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }
}
```

- [ ] **Step 3: Verify backend compiles**

```bash
cd java-poc && mvn compile -q 2>&1 | tail -5
```

Expected: BUILD SUCCESS

- [ ] **Step 4: Commit**

```bash
git add java-poc/src/main/java/com/sm/service/RollbackService.java java-poc/src/main/java/com/sm/controller/RollbackController.java
git commit -m "feat: add Rollback API - delete editable record, keep released version"
```

---

### Task 3: Create ForceUnlock backend API

**Files:**
- Create: `java-poc/src/main/java/com/sm/controller/ForceUnlockController.java`
- Create: `java-poc/src/main/java/com/sm/service/ForceUnlockService.java`

- [ ] **Step 1: Write ForceUnlockService**

File: `java-poc/src/main/java/com/sm/service/ForceUnlockService.java`

```java
package com.sm.service;

import com.sm.entity.SmFieldDef;
import com.sm.mapper.SmFieldDefMapper;
import com.sm.mapper.SmTableDefMapper;
import com.sm.util.JwtUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ForceUnlockService {

    private final SmTableDefMapper tableDefMapper;
    private final SmFieldDefMapper fieldDefMapper;
    private final JdbcTemplate jdbcTemplate;

    @Transactional
    public void forceUnlock(String tableId, Map<String, Object> keys) {
        String tableName = getTableName(tableId);
        List<SmFieldDef> keyFields = fieldDefMapper.findByTableId(tableId).stream()
                .filter(f -> "Y".equals(f.getIsKey()) && !"REL_FLG".equals(f.getFieldName()))
                .collect(Collectors.toList());

        // Build WHERE clause
        StringBuilder where = new StringBuilder("\"REL_FLG\" = 'N'");
        List<Object> values = new ArrayList<>();
        for (SmFieldDef kf : keyFields) {
            where.append(" AND \"").append(kf.getFieldName()).append("\" = ?");
            values.add(keys.get(kf.getFieldName()));
        }

        // Check record exists and is locked
        List<Map<String, Object>> rows = jdbcTemplate.queryForList(
                "SELECT * FROM " + tableName + " WHERE " + where, values.toArray());
        if (rows.isEmpty()) {
            throw new IllegalArgumentException("未找到该记录");
        }

        Map<String, Object> record = rows.get(0);
        String lockUser = (String) record.get("LOCK_USER");
        if (lockUser == null || lockUser.trim().isEmpty()) {
            throw new IllegalArgumentException("该记录未被锁定");
        }

        // Clear lock fields
        String sql = "UPDATE " + tableName + " SET \"LOCK_USER\" = '', \"LOCK_TIME\" = null WHERE " + where;
        jdbcTemplate.update(sql, values.toArray());
    }

    private String getTableName(String tableId) {
        var table = tableDefMapper.findByTableId(tableId);
        if (table == null) {
            throw new IllegalArgumentException("Table config not found: " + tableId);
        }
        return table.getTableName();
    }
}
```

- [ ] **Step 2: Write ForceUnlockController**

File: `java-poc/src/main/java/com/sm/controller/ForceUnlockController.java`

```java
package com.sm.controller;

import com.sm.service.ForceUnlockService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/force-unlock")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class ForceUnlockController {

    private final ForceUnlockService forceUnlockService;

    @PostMapping("/{tableId}")
    public ResponseEntity<?> forceUnlock(@PathVariable String tableId, @RequestBody Map<String, Object> keys) {
        try {
            forceUnlockService.forceUnlock(tableId, keys);
            return ResponseEntity.ok(Map.of("message", "解锁成功"));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }
}
```

- [ ] **Step 3: Verify backend compiles**

```bash
cd java-poc && mvn compile -q 2>&1 | tail -5
```

Expected: BUILD SUCCESS

- [ ] **Step 4: Commit**

```bash
git add java-poc/src/main/java/com/sm/service/ForceUnlockService.java java-poc/src/main/java/com/sm/controller/ForceUnlockController.java
git commit -m "feat: add ForceUnlock API - clear lock_user and lock_time fields"
```

---

### Task 4: Modify DynamicTableManager.vue - wire ContextMenu + 6 new actions

**Files:**
- Modify: `vue-poc/src/components/DynamicTableManager.vue`

This task has 4 sub-steps: (A) replace inline template with ContextMenu component, (B) update script imports and ctx state, (C) add 6 new action handlers and disabled computed, (D) update ctxAction switch, (E) cleanup old styles.

- [ ] **Step 4A: Replace inline context menu template with ContextMenu component**

In `vue-poc/src/components/DynamicTableManager.vue`, find lines 121-138 (the `<div v-if="ctxMenu.visible" class="ctx-menu"...>` block) and replace with:

```html
    <ContextMenu
      :visible="ctxMenu.visible"
      :x="ctxMenu.x"
      :y="ctxMenu.y"
      :col="ctxMenu.col"
      :disabled="ctxDisabled"
      @action="ctxAction"
      @close="ctxMenu.visible = false"
    />
```

- [ ] **Step 4B: Update script imports and ctxMenu state**

In the `<script setup>` section:

a) Add ContextMenu import (after line 150, before RefPicker import):

```javascript
import ContextMenu from './ContextMenu.vue'
```

b) Replace the `ctxMenu` reactive declaration (line 167):

```javascript
const ctxMenu = reactive({ visible: false, x: 0, y: 0, col: null })
```

(Remove unused imports if they were only used by the old inline ctx-menu template. The icons `Plus, Edit, Check, Finished, Promotion, Delete, RefreshLeft, SortUp, SortDown, Hide, View` that were imported at line 148 are now only used by ContextMenu.vue — BUT keep them since they might be used elsewhere. Actually check: they're not used in DynamicTableManager's template anymore. Remove them from this file's imports.)

c) Replace the icon import line (line 148):

```javascript
import { Plus, Edit, Check, Finished, Promotion, Delete, RefreshLeft, SortUp, SortDown, Hide, View } from '@element-plus/icons-vue'
```

With (remove unused icons, keep only what DynamicTableManager template uses):

Look at the template: no icons used directly in DynamicTableManager's template anymore. So remove the entire icon import line. Actually wait — let me check the template again... The template only uses ElementPlus components (el-table, el-card, etc.) — no icon components are used directly. So we can remove the import.

```javascript
// Remove line 148 entirely (the @element-plus/icons-vue import)
```

- [ ] **Step 4C: Add ctxDisabled computed and 6 new action handlers**

Add after the `canRelease` computed (after line 181):

```javascript
const ctxDisabled = computed(() => ({
  hasSelection: !!currentRow.value,
  isEditMode: !!editingRow.value,
  canEditComp: canEditComp.value,
  canRelease: canRelease.value,
  cannotClear: !currentRow.value,
  cannotCopy: !currentRow.value,
  cannotPaste: !editingRow.value,
  cannotFind: list.value.length === 0,
  cannotRollback: !currentRow.value || (currentRow.value.REL_FLG || '').trim() !== 'N' || isNewRow.value,
  cannotForceUnlock: !currentRow.value || !(currentRow.value.LOCK_USER && currentRow.value.LOCK_USER.trim())
}))
```

Add new handlers after `handleDelete` function (after line 367):

```javascript
// --- New context menu actions ---

const handleClear = () => {
  if (editingRow.value) {
    formFields.value.forEach(f => {
      if (f.isKey !== 'Y' || isNewRow.value) {
        editingRow.value[f.fieldName] = f.fieldType === 'NUMBER' ? 0 : ''
      }
    })
    ElMessage.info('已清除')
  } else if (currentRow.value) {
    // Enter edit mode then clear
    editingRow.value = currentRow.value
    isNewRow.value = false
    editingRow.value.COMP_FLG = 'N'
    editingRow.value.REL_FLG = 'N'
    formFields.value.forEach(f => {
      if (f.isKey !== 'Y') {
        editingRow.value[f.fieldName] = f.fieldType === 'NUMBER' ? 0 : ''
      }
    })
    updateToolbarState()
    ElMessage.info('已清除')
  }
}

const handleCopy = async () => {
  if (!currentRow.value) return
  const parts = formFields.value
    .filter(f => f.isDummy !== 'Y')
    .map(f => {
      const val = currentRow.value[f.fieldName]
      return (val != null ? String(val).trim() : '')
    })
  const text = parts.join('\t')
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch (e) {
    // Fallback for non-HTTPS contexts
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    ElMessage.success('已复制到剪贴板')
  }
}

const handlePaste = async () => {
  if (!editingRow.value) {
    ElMessage.warning('请先进入编辑模式')
    return
  }
  try {
    const text = await navigator.clipboard.readText()
    const values = text.split('\t')
    const visibleFields = formFields.value.filter(f => f.isDummy !== 'Y')
    for (let i = 0; i < Math.min(values.length, visibleFields.length); i++) {
      const f = visibleFields[i]
      if (f.isKey === 'Y' && !isNewRow.value) continue
      const val = values[i].trim()
      if (f.fieldType === 'NUMBER') {
        const num = parseFloat(val)
        if (!isNaN(num)) editingRow.value[f.fieldName] = num
      } else {
        editingRow.value[f.fieldName] = val
      }
    }
    ElMessage.success('已粘贴')
  } catch (e) {
    ElMessage.warning('无法读取剪贴板')
  }
}

const handleFind = async () => {
  if (list.value.length === 0) return
  try {
    const { value: searchText } = await ElMessageBox.prompt('请输入搜索文本', '查找', {
      confirmButtonText: '查找下一个',
      cancelButtonText: '取消',
      inputPlaceholder: '输入要搜索的文本...'
    })
    if (!searchText || !searchText.trim()) return
    const text = searchText.trim().toLowerCase()
    // Start from current row or first row
    const startIdx = currentRow.value
      ? Math.max(0, list.value.indexOf(currentRow.value))
      : 0
    // Search forward from current position, wrap around
    for (let offset = 0; offset < list.value.length; offset++) {
      const idx = (startIdx + offset + 1) % list.value.length
      const row = list.value[idx]
      const match = formFields.value.some(f => {
        const val = row[f.fieldName]
        return val != null && String(val).toLowerCase().includes(text)
      })
      if (match) {
        currentRow.value = row
        updateToolbarState()
        tableRef.value.setCurrentRow(row)
        emit('row-select', row, config.value.fields, props.tableId)
        // Scroll to row
        setTimeout(() => {
          const body = tableRef.value.$el.querySelector('.el-table__body-wrapper')
          if (body) {
            const rowEl = body.querySelectorAll('.el-table__row')[idx]
            if (rowEl) rowEl.scrollIntoView({ behavior: 'smooth', block: 'center' })
          }
        }, 50)
        return
      }
    }
    ElMessage.info('未找到匹配项')
  } catch (e) {
    // User cancelled
  }
}

const handleRollback = async () => {
  if (!currentRow.value) return
  try {
    await ElMessageBox.confirm('确认回滚？这将删除当前编辑记录并恢复 Release 版本。', '提示', { type: 'warning' })
    const keys = {}
    keyFields.value.forEach(f => { keys[f.fieldName] = currentRow.value[f.fieldName] })
    await axios.post(`/api/rollback/${props.tableId}`, keys)
    ElMessage.success('回滚成功')
    editingRow.value = null
    isNewRow.value = false
    currentRow.value = null
    updateToolbarState()
    doSearch()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('回滚失败: ' + (err.response?.data?.error || err.message))
  }
}

const handleForceUnlock = async () => {
  if (!currentRow.value) return
  try {
    await ElMessageBox.confirm('确认强制解锁该记录？', '提示', { type: 'warning' })
    const keys = {}
    keyFields.value.forEach(f => {
      if (f.fieldName !== 'REL_FLG') {
        keys[f.fieldName] = currentRow.value[f.fieldName]
      }
    })
    await axios.post(`/api/force-unlock/${props.tableId}`, keys)
    ElMessage.success('解锁成功')
    doSearch()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('解锁失败: ' + (err.response?.data?.error || err.message))
  }
}
```

- [ ] **Step 4D: Update ctxAction switch to handle new actions**

Replace the `ctxAction` function (lines 258-273) with:

```javascript
const ctxAction = (action) => {
  ctxMenu.visible = false
  switch (action) {
    case 'add': toolbar.add(); break
    case 'update': if (toolbar.hasSelection) toolbar.update(); break
    case 'save': if (toolbar.isEditMode) toolbar.save(); break
    case 'editcomp': if (toolbar.canEditComp) toolbar.editComp(); break
    case 'release': if (toolbar.canRelease) toolbar.release(); break
    case 'delete': if (toolbar.hasSelection) toolbar.delete(); break
    case 'undo': toolbar.undo(); break
    case 'clear': handleClear(); break
    case 'copy': handleCopy(); break
    case 'paste': handlePaste(); break
    case 'find': handleFind(); break
    case 'rollback': handleRollback(); break
    case 'forceUnlock': handleForceUnlock(); break
    case 'sort-asc': list.value.sort((a,b) => String(a[ctxMenu.col?.property]||'').localeCompare(String(b[ctxMenu.col?.property]||''))); break
    case 'sort-desc': list.value.sort((a,b) => String(b[ctxMenu.col?.property]||'').localeCompare(String(a[ctxMenu.col?.property]||''))); break
    case 'hide-col': if (ctxMenu.col?.property) hiddenCols.value.add(ctxMenu.col.property); break
    case 'show-all': hiddenCols.value.clear(); break
  }
}
```

- [ ] **Step 4E: Remove old ctx-menu CSS**

Remove lines 467-473 from the `<style scoped>` section (the `/* Context Menu */` block):

```css
/* Context Menu */
.ctx-menu { position: fixed; z-index: 9999; background: #fff; border: 1px solid #e0e0e0; border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,.12); padding: 4px 0; min-width: 180px; font-size: 13px; }
.ctx-item { display: flex; align-items: center; gap: 8px; padding: 6px 14px; cursor: pointer; color: #333; }
.ctx-item:hover { background: #e6f7ff; color: #1890ff; }
.ctx-item.disabled { color: #ccc; cursor: default; pointer-events: none; }
.ctx-item .el-icon { font-size: 14px; }
.ctx-divider { height: 1px; background: #f0f0f0; margin: 4px 0; }
```

- [ ] **Step 5: Verify frontend builds**

```bash
cd vue-poc && npx vite build 2>&1 | tail -10
```

Expected: Build succeeds with no errors.

If there are build errors related to missing imports, check: the `ElMessageBox` is already imported at line 147. It is used in handleDelete, so it's already imported.

- [ ] **Step 6: Commit**

```bash
git add vue-poc/src/components/ContextMenu.vue vue-poc/src/components/DynamicTableManager.vue
git commit -m "feat: add Clear/Copy/Paste/Find/Rollback/ForceUnlock context menu actions"
```

---

## Verification Checklist

After all tasks complete:

- [ ] `cd java-poc && mvn compile` — builds without errors
- [ ] `cd vue-poc && npx vite build` — builds without errors
- [ ] Right-click on a table row → context menu shows all 23 items
- [ ] Clear — clears non-key fields on editing row
- [ ] Copy — copies row data to clipboard as TSV
- [ ] Paste — pastes TSV data into editing row
- [ ] Find — opens prompt, searches and navigates to matching row
- [ ] Rollback — confirms, calls API, refreshes list
- [ ] Force Unlock — confirms, calls API, refreshes list
- [ ] Disabled states work correctly for all menu items
