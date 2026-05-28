package com.sm.service;

import com.sm.entity.SmCheckDef;
import com.sm.entity.SmFieldDef;
import com.sm.entity.SmTableDef;
import com.sm.exception.ValidationException;
import com.sm.mapper.SmCheckDefMapper;
import com.sm.mapper.SmFieldDefMapper;
import com.sm.mapper.SmTableDefMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ValidationService {

    private final SmTableDefMapper tableDefMapper;
    private final SmFieldDefMapper fieldDefMapper;
    private final SmCheckDefMapper checkDefMapper;
    private final JdbcTemplate jdbcTemplate;

    public void validateForSave(String tableId, Map<String, Object> data) {
        validate(tableId, "SAVE", data);
    }

    public void validateForDelete(String tableId, Map<String, Object> data) {
        validate(tableId, "DELETE", data);
    }

    public void validateForRelease(String tableId, Map<String, Object> data) {
        validate(tableId, "RELEASE", data);
    }

    public void validateForEditComp(String tableId, Map<String, Object> data) {
        validate(tableId, "EDITCOMP", data);
    }

    private void validate(String tableId, String checkType, Map<String, Object> data) {
        SmTableDef table = tableDefMapper.findByTableId(tableId);
        if (table == null) {
            throw new ValidationException("表配置不存在: " + tableId);
        }
        String tableName = table.getTableName();
        List<SmCheckDef> checks = checkDefMapper.findByTableIdAndCheckType(tableId, checkType);
        if (checks == null || checks.isEmpty()) {
            return;
        }

        boolean isUpdate = isExistingRecord(tableName, tableId, data);

        for (SmCheckDef check : checks) {
            String kind = check.getCheckKind();
            String fieldName = check.getFieldName();
            String errMsg = check.getErrMsg();
            if (errMsg == null || errMsg.isEmpty()) {
                errMsg = "校验失败: " + kind;
            }

            switch (kind) {
                case "NOTNULL":
                    Object val = data.get(fieldName);
                    if (val == null || val.toString().trim().isEmpty()) {
                        throw new ValidationException(errMsg);
                    }
                    break;

                case "STAT_N":
                case "STAT_Y":
                case "STAT_W":
                    if (isUpdate) {
                        String expected = kind.replace("STAT_", "");
                        checkStatus(tableName, tableId, data, expected, errMsg);
                    }
                    break;

                case "LOCK_FREE":
                    if (isUpdate) {
                        checkLockFree(tableName, tableId, data, errMsg);
                    }
                    break;

                case "KEY":
                    Object keyVal = data.get(fieldName);
                    if (keyVal != null && !keyVal.toString().trim().isEmpty()) {
                        checkForeignKey(check, keyVal, errMsg);
                    }
                    break;

                case "STRING":
                    // Skip if field not in data (control fields not sent by frontend)
                    if (!data.containsKey(fieldName)) break;
                    Object strVal = data.get(fieldName);
                    String expect = check.getExpectValue();
                    if (strVal == null || !strVal.toString().trim().equals(expect)) {
                        throw new ValidationException(errMsg);
                    }
                    break;

                case "NULLCHK":
                    // Skip if field not in data
                    if (!data.containsKey(fieldName)) break;
                    Object nv = data.get(fieldName);
                    if (nv != null && !nv.toString().trim().isEmpty()) {
                        throw new ValidationException(errMsg);
                    }
                    break;

                case "COMP_N":
                    if (isUpdate) {
                        checkCompFlg(tableName, tableId, data, "N", errMsg);
                    }
                    break;

                case "REF_STAT_R":
                    if (isUpdate) {
                        checkRefStatR(check, data, errMsg);
                    }
                    break;

                case "ERRMSG":
                case "RELEASE_PARAM":
                case "RELEASE_WRITE":
                    break;

                default:
                    break;
            }
        }
    }

    private boolean isExistingRecord(String tableName, String tableId, Map<String, Object> data) {
        List<SmFieldDef> keyFields = fieldDefMapper.findByTableId(tableId).stream()
                .filter(f -> "Y".equals(f.getIsKey()))
                .collect(Collectors.toList());

        if (keyFields.isEmpty()) {
            return false;
        }

        StringBuilder where = new StringBuilder();
        List<Object> values = new ArrayList<>();
        for (SmFieldDef kf : keyFields) {
            if (where.length() > 0) where.append(" AND ");
            where.append("\"").append(kf.getFieldName()).append("\" = ?");
            values.add(data.get(kf.getFieldName()));
        }
        if (tableName.startsWith("B")) {
            where.append(" AND \"REL_FLG\" = 'N'");
        }

        String sql = "SELECT COUNT(*) FROM " + tableName + " WHERE " + where;
        Integer count = jdbcTemplate.queryForObject(sql, Integer.class, values.toArray());
        return count != null && count > 0;
    }

    private void checkStatus(String tableName, String tableId, Map<String, Object> data, String expectedStatus, String errMsg) {
        Map<String, Object> row = queryRecord(tableName, tableId, data);
        if (row == null) return;
        String relFlg = (String) row.get("REL_FLG");
        if (relFlg != null) relFlg = relFlg.trim();
        if (!expectedStatus.equals(relFlg)) {
            throw new ValidationException(errMsg);
        }
    }

    private void checkLockFree(String tableName, String tableId, Map<String, Object> data, String errMsg) {
        Map<String, Object> row = queryRecord(tableName, tableId, data);
        if (row == null) return;
        String lockUser = (String) row.get("LOCK_USER");
        Object lockTime = row.get("LOCK_TIME");
        if (lockUser != null && !lockUser.trim().isEmpty()) {
            throw new ValidationException(errMsg);
        }
        if (lockTime != null) {
            throw new ValidationException(errMsg);
        }
    }

    private void checkForeignKey(SmCheckDef check, Object keyVal, String errMsg) {
        String refTable = check.getRefTable();
        String refField = check.getRefField();
        if (refTable == null || refField == null) return;

        String sql = "SELECT COUNT(*) FROM " + refTable + " WHERE \"" + refField + "\" = ?";
        Integer count = jdbcTemplate.queryForObject(sql, Integer.class, keyVal.toString().trim());
        if (count == null || count == 0) {
            throw new ValidationException(errMsg);
        }
    }

    private void checkCompFlg(String tableName, String tableId, Map<String, Object> data, String expected, String errMsg) {
        Map<String, Object> row = queryRecord(tableName, tableId, data);
        if (row == null) return;
        String compFlg = (String) row.get("COMP_FLG");
        if (compFlg != null) compFlg = compFlg.trim();
        if (!expected.equals(compFlg)) {
            throw new ValidationException(errMsg);
        }
    }

    private void checkRefStatR(SmCheckDef check, Map<String, Object> data, String errMsg) {
        String refTable = check.getRefTable();
        String refField = check.getRefField();
        String fieldName = check.getFieldName();
        if (refTable == null || refField == null || fieldName == null) return;

        Object val = data.get(fieldName);
        if (val == null || val.toString().trim().isEmpty()) return;

        String sql = "SELECT COUNT(*) FROM " + refTable + " WHERE \"" + refField + "\" = ? AND \"REL_FLG\" = 'Y'";
        Integer count = jdbcTemplate.queryForObject(sql, Integer.class, val.toString().trim());
        if (count == null || count == 0) {
            throw new ValidationException(errMsg);
        }
    }

    private Map<String, Object> queryRecord(String tableName, String tableId, Map<String, Object> data) {
        List<SmFieldDef> keyFields = fieldDefMapper.findByTableId(tableId).stream()
                .filter(f -> "Y".equals(f.getIsKey()))
                .collect(Collectors.toList());

        StringBuilder where = new StringBuilder();
        List<Object> values = new ArrayList<>();
        for (SmFieldDef kf : keyFields) {
            if (where.length() > 0) where.append(" AND ");
            where.append("\"").append(kf.getFieldName()).append("\" = ?");
            values.add(data.get(kf.getFieldName()));
        }
        if (where.length() == 0) return null;
        if (tableName.startsWith("B")) {
            where.append(" AND \"REL_FLG\" = 'N'");
        }
        List<Map<String, Object>> rows = jdbcTemplate.queryForList(
                "SELECT * FROM " + tableName + " WHERE " + where, values.toArray());
        return rows.isEmpty() ? null : rows.get(0);
    }
}
