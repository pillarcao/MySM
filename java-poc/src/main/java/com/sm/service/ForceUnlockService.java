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

        // Build WHERE clause (match both REL_FLG='N' and 'Y' - any locked record)
        StringBuilder whereN = new StringBuilder("\"REL_FLG\" = 'N'");
        StringBuilder whereY = new StringBuilder("\"REL_FLG\" = 'Y'");
        List<Object> keyValues = new ArrayList<>();
        for (SmFieldDef kf : keyFields) {
            String cond = " AND \"" + kf.getFieldName() + "\" = ?";
            whereN.append(cond);
            whereY.append(cond);
            keyValues.add(keys.get(kf.getFieldName()));
        }

        // Check N record first, then Y
        List<Object> nVals = new ArrayList<>(keyValues);
        List<Map<String, Object>> rows = jdbcTemplate.queryForList(
                "SELECT * FROM " + tableName + " WHERE " + whereN, nVals.toArray());
        String foundRelFlg = "N";
        List<Object> foundVals = nVals;

        if (rows.isEmpty()) {
            List<Object> yVals = new ArrayList<>(keyValues);
            rows = jdbcTemplate.queryForList(
                    "SELECT * FROM " + tableName + " WHERE " + whereY, yVals.toArray());
            foundRelFlg = "Y";
            foundVals = yVals;
        }

        if (rows.isEmpty()) {
            throw new IllegalArgumentException("未找到该记录");
        }

        Map<String, Object> record = rows.get(0);
        String lockUser = (String) record.get("LOCK_USER");
        if (lockUser == null || lockUser.trim().isEmpty()) {
            throw new IllegalArgumentException("该记录未被锁定");
        }

        // Clear lock fields
        String sql = "UPDATE " + tableName
                + " SET \"LOCK_USER\" = '', \"LOCK_TIME\" = null WHERE \"REL_FLG\" = ?";
        for (SmFieldDef kf : keyFields) {
            sql += " AND \"" + kf.getFieldName() + "\" = ?";
        }
        List<Object> sqlVals = new ArrayList<>();
        sqlVals.add(foundRelFlg);
        sqlVals.addAll(keyValues);
        jdbcTemplate.update(sql, sqlVals.toArray());
    }

    private String getTableName(String tableId) {
        com.sm.entity.SmTableDef table = tableDefMapper.findByTableId(tableId);
        if (table == null) {
            throw new IllegalArgumentException("Table config not found: " + tableId);
        }
        return table.getTableName();
    }
}
