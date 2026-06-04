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
        com.sm.entity.SmTableDef table = tableDefMapper.findByTableId(tableId);
        if (table == null) {
            throw new IllegalArgumentException("Table config not found: " + tableId);
        }
        return table.getTableName();
    }
}
