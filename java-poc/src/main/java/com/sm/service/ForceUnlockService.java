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

        if (keyFields.isEmpty()) {
            throw new IllegalArgumentException("表 " + tableId + " 未配置业务主键");
        }

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
        com.sm.entity.SmTableDef table = tableDefMapper.findByTableId(tableId);
        if (table == null) {
            throw new IllegalArgumentException("Table config not found: " + tableId);
        }
        return table.getTableName();
    }
}
