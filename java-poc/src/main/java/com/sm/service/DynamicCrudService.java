package com.sm.service;

import com.sm.entity.SmFieldDef;
import com.sm.entity.SmTableDef;
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
public class DynamicCrudService {

    private final SmTableDefMapper tableDefMapper;
    private final SmFieldDefMapper fieldDefMapper;
    private final JdbcTemplate jdbcTemplate;
    private final ValidationService validationService;

    public List<Map<String, Object>> list(String tableId, String status) {
        return search(tableId, status, new HashMap<>());
    }

    public List<Map<String, Object>> search(String tableId, String status, Map<String, Object> conditions) {
        String tableName = getTableName(tableId);
        List<SmFieldDef> fields = fieldDefMapper.findByTableId(tableId);

        StringBuilder sql = new StringBuilder("SELECT * FROM " + tableName + " WHERE 1=1");
        List<Object> values = new ArrayList<>();

        if (status != null && !status.isEmpty() && !"ALL".equals(status)) {
            switch (status) {
                case "EDIT":
                    sql.append(" AND \"REL_FLG\" = 'N' AND \"COMP_FLG\" = 'N'");
                    break;
                case "EDITCOMP":
                    sql.append(" AND \"REL_FLG\" = 'N' AND \"COMP_FLG\" = 'Y'");
                    break;
                case "RELEASE":
                    sql.append(" AND \"REL_FLG\" = 'Y'");
                    break;
                case "LOCK":
                    sql.append(" AND \"LOCK_USER\" IS NOT NULL AND \"LOCK_USER\" != ''");
                    break;
            }
        }

        for (SmFieldDef f : fields) {
            if ("Y".equals(f.getIsSearchItem()) && conditions.containsKey(f.getFieldName())) {
                Object val = conditions.get(f.getFieldName());
                if (val != null && !"".equals(val.toString().trim())) {
                    if ("NUMBER".equals(f.getDbType()) || "DOUBLE".equals(f.getDbType())) {
                        sql.append(" AND \"").append(f.getFieldName()).append("\" = ?");
                        values.add(val);
                    } else {
                        sql.append(" AND \"").append(f.getFieldName()).append("\" LIKE ?");
                        values.add("%" + val.toString().trim() + "%");
                    }
                }
            }
        }

        return jdbcTemplate.queryForList(sql.toString(), values.toArray());
    }

    @Transactional
    public void save(String tableId, Map<String, Object> data) {
        String tableName = getTableName(tableId);
        List<SmFieldDef> fields = fieldDefMapper.findByTableId(tableId);
        Map<String, Object> dbData = data;

        // Save 前校验
        validationService.validateForSave(tableId, dbData);

        List<SmFieldDef> keyFields = fields.stream()
                .filter(f -> "Y".equals(f.getIsKey()))
                .collect(Collectors.toList());

        String where = buildWhere(keyFields);
        List<Object> keyValues = buildValues(keyFields, dbData);

        // B 表主键含 REL_FLG，使用请求中的 REL_FLG 值
        if (tableName.startsWith("B")) {
            Object relFlgVal = dbData.get("REL_FLG");
            String relFlg = (relFlgVal != null && !relFlgVal.toString().trim().isEmpty())
                    ? relFlgVal.toString().trim() : "N";
            where += " AND \"REL_FLG\" = ?";
            keyValues.add(relFlg);
        }

        Integer count = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM " + tableName + " WHERE " + where,
                Integer.class, keyValues.toArray());

        if (count != null && count > 0) {
            update(tableName, fields, dbData, where, keyValues);
        } else {
            insert(tableName, fields, dbData);
        }
    }

    @Transactional
    public void delete(String tableId, Map<String, Object> data) {
        validationService.validateForDelete(tableId, data);
        String tableName = getTableName(tableId);
        List<SmFieldDef> keyFields = fieldDefMapper.findByTableId(tableId).stream()
                .filter(f -> "Y".equals(f.getIsKey()))
                .collect(Collectors.toList());
        Map<String, Object> dbData = data;

        String where = buildWhere(keyFields);
        List<Object> keyValues = buildValues(keyFields, dbData);

        // Delete: validateForDelete already checked STAT_Y, no need to filter REL_FLG
        String sql = "DELETE FROM " + tableName + " WHERE " + where;
        jdbcTemplate.update(sql, keyValues.toArray());
    }

    @Transactional
    public void lock(String tableId, Map<String, Object> keys) {
        String tableName = getTableName(tableId);
        List<SmFieldDef> keyFields = fieldDefMapper.findByTableId(tableId).stream()
                .filter(f -> "Y".equals(f.getIsKey()) && !"REL_FLG".equals(f.getFieldName()))
                .collect(Collectors.toList());

        StringBuilder where = new StringBuilder();
        List<Object> values = new ArrayList<>();
        for (SmFieldDef kf : keyFields) {
            if (where.length() > 0) where.append(" AND ");
            where.append("\"").append(kf.getFieldName()).append("\" = ?");
            values.add(keys.get(kf.getFieldName()));
        }
        // Lock either N or Y record: try N first, then Y
        String sqlN = "UPDATE " + tableName
                + " SET \"LOCK_USER\" = 'SYSTEM', \"LOCK_TIME\" = CURRENT_TIMESTAMP WHERE " + where;
        if (tableName.startsWith("B")) {
            sqlN += " AND \"REL_FLG\" = 'N'";
        }
        int updated = jdbcTemplate.update(sqlN, values.toArray());
        if (updated == 0 && tableName.startsWith("B")) {
            String sqlY = "UPDATE " + tableName
                    + " SET \"LOCK_USER\" = 'SYSTEM', \"LOCK_TIME\" = CURRENT_TIMESTAMP WHERE " + where
                    + " AND \"REL_FLG\" = 'Y'";
            jdbcTemplate.update(sqlY, values.toArray());
        }
    }

    @Transactional
    public void unlock(String tableId, Map<String, Object> keys) {
        String tableName = getTableName(tableId);
        List<SmFieldDef> keyFields = fieldDefMapper.findByTableId(tableId).stream()
                .filter(f -> "Y".equals(f.getIsKey()) && !"REL_FLG".equals(f.getFieldName()))
                .collect(Collectors.toList());

        StringBuilder where = new StringBuilder();
        List<Object> values = new ArrayList<>();
        for (SmFieldDef kf : keyFields) {
            if (where.length() > 0) where.append(" AND ");
            where.append("\"").append(kf.getFieldName()).append("\" = ?");
            values.add(keys.get(kf.getFieldName()));
        }
        // Unlock either N or Y record: try N first, then Y
        String sqlN = "UPDATE " + tableName
                + " SET \"LOCK_USER\" = '', \"LOCK_TIME\" = null WHERE " + where;
        if (tableName.startsWith("B")) {
            sqlN += " AND \"REL_FLG\" = 'N'";
        }
        int updated = jdbcTemplate.update(sqlN, values.toArray());
        if (updated == 0 && tableName.startsWith("B")) {
            String sqlY = "UPDATE " + tableName
                    + " SET \"LOCK_USER\" = '', \"LOCK_TIME\" = null WHERE " + where
                    + " AND \"REL_FLG\" = 'Y'";
            jdbcTemplate.update(sqlY, values.toArray());
        }
    }

    private void update(String tableName, List<SmFieldDef> fields,
                        Map<String, Object> dbData, String where, List<Object> keyValues) {
        List<String> setParts = new ArrayList<>();
        List<Object> setValues = new ArrayList<>();

        for (SmFieldDef f : fields) {
            if ("Y".equals(f.getIsKey()) || "Y".equals(f.getIsDummy())) continue;
            Object val = dbData.get(f.getFieldName());
            if (val != null) {
                setParts.add("\"" + f.getFieldName() + "\" = ?");
                setValues.add(val);
            }
        }
        if (tableName.startsWith("B")) {
            setParts.add("\"LAST_DATE1\" = CURRENT_TIMESTAMP");
            setParts.add("\"LAST_ACT1\" = 'UPDATE'");
            setParts.add("\"LAST_USER1\" = 'SYSTEM'");
        }

        String sql = "UPDATE " + tableName + " SET " + String.join(", ", setParts) + " WHERE " + where;
        setValues.addAll(keyValues);
        jdbcTemplate.update(sql, setValues.toArray());
    }

    private void insert(String tableName, List<SmFieldDef> fields, Map<String, Object> dbData) {
        List<String> columns = new ArrayList<>();
        List<Object> values = new ArrayList<>();
        List<String> placeholders = new ArrayList<>();

        for (SmFieldDef f : fields) {
            if ("Y".equals(f.getIsAuto()) || "Y".equals(f.getIsDummy())) continue;
            Object val = dbData.get(f.getFieldName());
            if (val == null || "".equals(val)) {
                if ("NUMBER".equals(f.getDbType())) {
                    val = 0;
                } else {
                    val = "";
                }
            }
            columns.add("\"" + f.getFieldName() + "\"");
            values.add(val);
            placeholders.add("?");
        }

        if (tableName.startsWith("B")) {
            if (!columns.contains("\"REL_FLG\"")) {
                columns.add("\"REL_FLG\"");
                values.add("N");
                placeholders.add("?");
            }
            addDefaultControlColumns(columns, values, placeholders);
        }

        String sql = "INSERT INTO " + tableName + " (" + String.join(", ", columns)
                + ") VALUES (" + String.join(", ", placeholders) + ")";
        jdbcTemplate.update(sql, values.toArray());
    }

    private String getTableName(String tableId) {
        SmTableDef table = tableDefMapper.findByTableId(tableId);
        if (table == null) {
            throw new IllegalArgumentException("Table config not found: " + tableId);
        }
        return table.getTableName();
    }

    private Map<String, Object> toUnderscoreMap(Map<String, Object> camelMap) {
        Map<String, Object> result = new LinkedHashMap<>();
        for (Map.Entry<String, Object> entry : camelMap.entrySet()) {
            result.put(camelToUnderscore(entry.getKey()), entry.getValue());
        }
        return result;
    }

    private String camelToUnderscore(String str) {
        if (str == null || str.isEmpty()) return str;
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < str.length(); i++) {
            char c = str.charAt(i);
            if (Character.isUpperCase(c)) {
                sb.append('_').append(c);
            } else {
                sb.append(Character.toUpperCase(c));
            }
        }
        return sb.toString();
    }

    private String buildWhere(List<SmFieldDef> keyFields) {
        StringBuilder sb = new StringBuilder();
        for (SmFieldDef kf : keyFields) {
            if (sb.length() > 0) sb.append(" AND ");
            sb.append("\"").append(kf.getFieldName()).append("\" = ?");
        }
        return sb.toString();
    }

    private List<Object> buildValues(List<SmFieldDef> fields, Map<String, Object> data) {
        List<Object> values = new ArrayList<>();
        for (SmFieldDef f : fields) {
            values.add(data.get(f.getFieldName()));
        }
        return values;
    }

    private void addDefaultControlColumns(List<String> columns, List<Object> values, List<String> placeholders) {
        String[][] defaults = {
                {"COMP_FLG", "N"},
                {"CRE_DATE", "__TS__"},
                {"CRE_USER", "SYSTEM"},
                {"LAST_ACT1", ""},
                {"LAST_USER1", ""},
                {"OWNER", "SYSTEM"},
                {"OWNERG", ""},
                {"PERMISSION", "PUBLIC    "},
                {"LOCK_USER", ""},
                {"COMMENT", ""}
        };
        for (String[] def : defaults) {
            String quoted = "\"" + def[0] + "\"";
            if (!columns.contains(quoted)) {
                columns.add(quoted);
                if ("__TS__".equals(def[1])) {
                    values.add(new Timestamp(System.currentTimeMillis()));
                } else {
                    values.add(def[1]);
                }
                placeholders.add("?");
            }
        }
    }
}
