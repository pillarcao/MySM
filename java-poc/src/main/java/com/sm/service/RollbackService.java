package com.sm.service;

import com.sm.entity.SmFieldDef;
import com.sm.mapper.SmFieldDefMapper;
import com.sm.mapper.SmTableDefMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.sql.Timestamp;
import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class RollbackService {

    private final SmTableDefMapper tableDefMapper;
    private final SmFieldDefMapper fieldDefMapper;
    private final JdbcTemplate jdbcTemplate;
    private final HistoryService historyService;
    private final com.sm.util.UserContext userContext;
    private final EventLogService eventLogService;

    @Transactional
    public void rollback(String tableId, Map<String, Object> keys) {
        String bTableName = getTableName(tableId);
        String dTableName = bTableName.replaceFirst("^B", "D");

        List<SmFieldDef> keyFields = fieldDefMapper.findByTableId(tableId).stream()
                .filter(f -> "Y".equals(f.getIsKey()) && !"REL_FLG".equals(f.getFieldName()))
                .collect(Collectors.toList());

        if (keyFields.isEmpty()) {
            throw new IllegalArgumentException("表 " + tableId + " 未配置业务主键");
        }

        // 1. Find D-table released record
        StringBuilder whereD = new StringBuilder();
        List<Object> dValues = new ArrayList<>();
        for (SmFieldDef kf : keyFields) {
            if (whereD.length() > 0) whereD.append(" AND ");
            whereD.append("\"").append(kf.getFieldName()).append("\" = ?");
            dValues.add(keys.get(kf.getFieldName()));
        }
        List<Map<String, Object>> dRows;
        try {
            dRows = jdbcTemplate.queryForList(
                    "SELECT * FROM " + dTableName + " WHERE " + whereD, dValues.toArray());
        } catch (Exception e) {
            throw new IllegalArgumentException("D 表 " + dTableName + " 不存在或查询失败: " + e.getMessage());
        }
        if (dRows.isEmpty()) {
            throw new IllegalArgumentException("未找到 D 表 Release 版本记录，无法回滚");
        }
        Map<String, Object> dRecord = dRows.get(0);

        // 2. Delete B-table editable record (REL_FLG='N')
        StringBuilder whereB = new StringBuilder("\"REL_FLG\" = 'N'");
        List<Object> bValues = new ArrayList<>();
        for (SmFieldDef kf : keyFields) {
            whereB.append(" AND \"").append(kf.getFieldName()).append("\" = ?");
            bValues.add(keys.get(kf.getFieldName()));
        }
        int deleted = jdbcTemplate.update("DELETE FROM " + bTableName + " WHERE " + whereB, bValues.toArray());

        // 3. Delete old B-table released record (REL_FLG='Y') if exists, to avoid duplicate key
        StringBuilder whereOldY = new StringBuilder("\"REL_FLG\" = 'Y'");
        List<Object> yValues = new ArrayList<>();
        for (SmFieldDef kf : keyFields) {
            whereOldY.append(" AND \"").append(kf.getFieldName()).append("\" = ?");
            yValues.add(keys.get(kf.getFieldName()));
        }
        jdbcTemplate.update("DELETE FROM " + bTableName + " WHERE " + whereOldY, yValues.toArray());

        // 4. Insert D-table data into B-table with REL_FLG='Y', COMP_FLG='Y'
        List<String> columns = new ArrayList<>();
        List<Object> values = new ArrayList<>();
        List<String> placeholders = new ArrayList<>();

        List<SmFieldDef> allFields = fieldDefMapper.findByTableId(tableId);
        Set<String> fieldNames = allFields.stream()
                .filter(f -> !"Y".equals(f.getIsDummy()) && !"Y".equals(f.getIsAuto()))
                .map(SmFieldDef::getFieldName)
                .collect(Collectors.toSet());

        for (Map.Entry<String, Object> entry : dRecord.entrySet()) {
            String colName = entry.getKey();
            if (!fieldNames.contains(colName)) continue;
            columns.add("\"" + colName + "\"");
            values.add(entry.getValue());
            placeholders.add("?");
        }

        // Add B-table control fields
        addField(columns, values, placeholders, "REL_FLG", "Y");
        addField(columns, values, placeholders, "COMP_FLG", "Y");
        String user = userContext.getCurrentUser();
        addField(columns, values, placeholders, "CRE_USER", dRecord.getOrDefault("CRE_USER", user));
        addField(columns, values, placeholders, "CRE_DATE", dRecord.getOrDefault("CRE_DATE", new Timestamp(System.currentTimeMillis())));
        addField(columns, values, placeholders, "OWNER", dRecord.getOrDefault("OWNER", user));
        addField(columns, values, placeholders, "OWNERG", dRecord.getOrDefault("OWNERG", ""));
        addField(columns, values, placeholders, "PERMISSION", dRecord.getOrDefault("PERMISSION", "PUBLIC    "));
        addField(columns, values, placeholders, "LOCK_USER", "");
        addField(columns, values, placeholders, "LOCK_TIME", null);
        addField(columns, values, placeholders, "COMMENT", dRecord.getOrDefault("COMMENT", ""));
        // History: slot 1 = Rollback, slots 2-5 = empty
        historyService.addInitHistory(columns, values, placeholders, "Rollback", user);

        String sql = "INSERT INTO " + bTableName + " (" + String.join(", ", columns)
                + ") VALUES (" + String.join(", ", placeholders) + ")";
        jdbcTemplate.update(sql, values.toArray());

        // Event log
        StringBuilder keyStr = new StringBuilder();
        for (SmFieldDef kf : keyFields) {
            if (keyStr.length() > 0) keyStr.append("|");
            Object val = keys.get(kf.getFieldName());
            keyStr.append(val != null ? val.toString().trim() : "");
        }
        eventLogService.log("Rollback", userContext.getCurrentUser(), bTableName, keyStr.toString(), "");
    }

    private void addField(List<String> columns, List<Object> values, List<String> placeholders,
                          String name, Object value) {
        String quoted = "\"" + name + "\"";
        if (!columns.contains(quoted)) {
            columns.add(quoted);
            values.add(value);
            placeholders.add("?");
        }
    }

    private String getTableName(String tableId) {
        com.sm.entity.SmTableDef table = tableDefMapper.findByTableId(tableId);
        if (table == null) {
            throw new IllegalArgumentException("Table config not found: " + tableId);
        }
        return table.getTableName();
    }
}
