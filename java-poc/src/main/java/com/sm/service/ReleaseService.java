package com.sm.service;

import com.sm.entity.SmCheckDef;
import com.sm.entity.SmFieldDef;
import com.sm.entity.SmTableDef;
import com.sm.mapper.SmCheckDefMapper;
import com.sm.mapper.SmFieldDefMapper;
import com.sm.mapper.SmTableDefMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ReleaseService {

    private final SmTableDefMapper tableDefMapper;
    private final SmFieldDefMapper fieldDefMapper;
    private final SmCheckDefMapper checkDefMapper;
    private final JdbcTemplate jdbcTemplate;
    private final ValidationService validationService;
    private final HistoryService historyService;
    private final com.sm.util.UserContext userContext;

    private static final Set<String> CONTROL_FIELDS;
    static {
        Set<String> set = new HashSet<>();
        set.add("REL_FLG");
        set.add("COMP_FLG");
        set.add("CRE_DATE");
        set.add("CRE_USER");
        set.add("LAST_DATE1");
        set.add("LAST_ACT1");
        set.add("LAST_USER1");
        set.add("LAST_DATE2");
        set.add("LAST_ACT2");
        set.add("LAST_USER2");
        set.add("LAST_DATE3");
        set.add("LAST_ACT3");
        set.add("LAST_USER3");
        set.add("LAST_DATE4");
        set.add("LAST_ACT4");
        set.add("LAST_USER4");
        set.add("LAST_DATE5");
        set.add("LAST_ACT5");
        set.add("LAST_USER5");
        set.add("OWNER");
        set.add("OWNERG");
        set.add("PERMISSION");
        set.add("LOCK_USER");
        set.add("LOCK_TIME");
        set.add("COMMENT");
        CONTROL_FIELDS = Collections.unmodifiableSet(set);
    }

    @Transactional
    public void release(String tableId, Map<String, Object> keys) {
        String bTableName = getTableName(tableId);
        String dTableName = bTableName.replaceFirst("^B", "D");

        // 1. Release 前校验
        validationService.validateForRelease(tableId, keys);

        // 2. 查询 B 表记录（REL_FLG='N'）
        List<SmFieldDef> fields = fieldDefMapper.findByTableId(tableId);
        Map<String, Object> dbKeys = keys;

        String bWhere = buildWhereWithRelFlg(fields, dbKeys);
        List<Object> bWhereValues = buildKeyValuesWithRelFlg(fields, dbKeys);

        Map<String, Object> bRecord = jdbcTemplate.queryForMap(
                "SELECT * FROM " + bTableName + " WHERE " + bWhere,
                bWhereValues.toArray()
        );

        // 3. 读取 RELEASE 配置
        List<SmCheckDef> releaseChecks = checkDefMapper.findByTableIdAndCheckType(tableId, "RELEASE");
        List<String> releaseWriteFields = releaseChecks.stream()
                .filter(c -> "RELEASE_WRITE".equals(c.getCheckKind()))
                .map(SmCheckDef::getFieldName)
                .collect(Collectors.toList());
        List<String> releaseParamFields = releaseChecks.stream()
                .filter(c -> "RELEASE_PARAM".equals(c.getCheckKind()))
                .map(SmCheckDef::getFieldName)
                .collect(Collectors.toList());

        // 4. 构建 D 表数据
        Map<String, Object> dRecord = new LinkedHashMap<>();
        if (!releaseWriteFields.isEmpty()) {
            // 按配置映射
            for (String fn : releaseWriteFields) {
                dRecord.put(fn, bRecord.get(fn));
            }
        } else {
            // 回退到白名单排除
            for (Map.Entry<String, Object> entry : bRecord.entrySet()) {
                if (!CONTROL_FIELDS.contains(entry.getKey())) {
                    dRecord.put(entry.getKey(), entry.getValue());
                }
            }
        }
        // INSERT 时需要主键字段，补充 RELEASE_PARAM
        for (String fn : releaseParamFields) {
            if (!dRecord.containsKey(fn)) {
                dRecord.put(fn, bRecord.get(fn));
            }
        }

        // 5. D 表主键
        List<String> dKeyColumns;
        if (!releaseParamFields.isEmpty()) {
            dKeyColumns = releaseParamFields;
        } else {
            dKeyColumns = fields.stream()
                    .filter(f -> "Y".equals(f.getIsKey()) && !"REL_FLG".equals(f.getFieldName()))
                    .map(SmFieldDef::getFieldName)
                    .collect(Collectors.toList());
        }

        // 6. D 表 UPSERT
        int updated = updateDTable(dTableName, dRecord, dKeyColumns);
        if (updated == 0) {
            insertDTable(dTableName, dRecord);
        }

        // 7. 更新 B 表：先删除旧的 R 记录（如果存在），再将当前 E 记录更新为 R
        deleteOldBReleased(bTableName, fields, dbKeys);
        updateBToReleased(bTableName, fields, dbKeys);
    }

    private int updateDTable(String dTableName, Map<String, Object> dRecord, List<String> dKeyColumns) {
        List<String> setParts = new ArrayList<>();
        List<Object> setValues = new ArrayList<>();

        for (Map.Entry<String, Object> entry : dRecord.entrySet()) {
            if (dKeyColumns.contains(entry.getKey())) continue;
            setParts.add("\"" + entry.getKey() + "\" = ?");
            setValues.add(entry.getValue());
        }

        if (setParts.isEmpty()) return 0;

        StringBuilder where = new StringBuilder();
        List<Object> whereValues = new ArrayList<>();
        for (String kc : dKeyColumns) {
            if (where.length() > 0) where.append(" AND ");
            where.append("\"").append(kc).append("\" = ?");
            whereValues.add(dRecord.get(kc));
        }

        String sql = "UPDATE " + dTableName + " SET " + String.join(", ", setParts) + " WHERE " + where;
        setValues.addAll(whereValues);
        return jdbcTemplate.update(sql, setValues.toArray());
    }

    private void insertDTable(String dTableName, Map<String, Object> dRecord) {
        List<String> columns = new ArrayList<>();
        List<Object> values = new ArrayList<>();
        List<String> placeholders = new ArrayList<>();

        for (Map.Entry<String, Object> entry : dRecord.entrySet()) {
            columns.add("\"" + entry.getKey() + "\"");
            values.add(entry.getValue());
            placeholders.add("?");
        }

        String sql = "INSERT INTO " + dTableName + " (" + String.join(", ", columns)
                + ") VALUES (" + String.join(", ", placeholders) + ")";
        jdbcTemplate.update(sql, values.toArray());
    }

    private void deleteOldBReleased(String bTableName, List<SmFieldDef> fields, Map<String, Object> dbKeys) {
        List<SmFieldDef> keyFields = fields.stream()
                .filter(f -> "Y".equals(f.getIsKey()) && !"REL_FLG".equals(f.getFieldName()))
                .collect(Collectors.toList());

        StringBuilder where = new StringBuilder("\"REL_FLG\" = 'Y'");
        List<Object> values = new ArrayList<>();
        for (SmFieldDef kf : keyFields) {
            where.append(" AND \"").append(kf.getFieldName()).append("\" = ?");
            values.add(dbKeys.get(kf.getFieldName()));
        }

        jdbcTemplate.update("DELETE FROM " + bTableName + " WHERE " + where, values.toArray());
    }

    private void updateBToReleased(String bTableName, List<SmFieldDef> fields, Map<String, Object> dbKeys) {
        List<SmFieldDef> keyFields = fields.stream()
                .filter(f -> "Y".equals(f.getIsKey()))
                .collect(Collectors.toList());

        StringBuilder where = new StringBuilder();
        List<Object> values = new ArrayList<>();
        for (SmFieldDef kf : keyFields) {
            if (where.length() > 0) where.append(" AND ");
            where.append("\"").append(kf.getFieldName()).append("\" = ?");
            values.add(dbKeys.get(kf.getFieldName()));
        }

        String sql = "UPDATE " + bTableName + " SET \"REL_FLG\" = 'Y', \"COMP_FLG\" = 'Y', "
                + historyService.shiftHistorySQL("Release", userContext.getCurrentUser()) + " WHERE " + where;
        jdbcTemplate.update(sql, values.toArray());
    }

    private String buildWhereWithRelFlg(List<SmFieldDef> fields, Map<String, Object> dbKeys) {
        StringBuilder sb = new StringBuilder("\"REL_FLG\" = 'N'");
        for (SmFieldDef f : fields) {
            if ("Y".equals(f.getIsKey()) && !"REL_FLG".equals(f.getFieldName())) {
                sb.append(" AND \"").append(f.getFieldName()).append("\" = ?");
            }
        }
        return sb.toString();
    }

    private List<Object> buildKeyValuesWithRelFlg(List<SmFieldDef> fields, Map<String, Object> dbKeys) {
        List<Object> values = new ArrayList<>();
        for (SmFieldDef f : fields) {
            if ("Y".equals(f.getIsKey()) && !"REL_FLG".equals(f.getFieldName())) {
                values.add(dbKeys.get(f.getFieldName()));
            }
        }
        return values;
    }

    private String getTableName(String tableId) {
        SmTableDef table = tableDefMapper.findByTableId(tableId);
        if (table == null) {
            throw new IllegalArgumentException("Table config not found: " + tableId);
        }
        return table.getTableName();
    }
}
