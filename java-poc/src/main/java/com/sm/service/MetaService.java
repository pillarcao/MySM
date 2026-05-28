package com.sm.service;

import com.sm.entity.SmDrillDef;
import com.sm.entity.SmFieldDef;
import com.sm.entity.SmTableDef;
import com.sm.mapper.SmFieldDefMapper;
import com.sm.mapper.SmTableDefMapper;
import com.sm.mapper.SmDrillDefMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class MetaService {

    private final SmTableDefMapper tableDefMapper;
    private final SmFieldDefMapper fieldDefMapper;
    private final SmDrillDefMapper drillDefMapper;
    private final JdbcTemplate jdbcTemplate;

    public List<SmTableDef> getAllTables() {
        return tableDefMapper.findAll();
    }

    public Map<String, Object> getTableMeta(String tableId) {
        Map<String, Object> result = new HashMap<>();

        SmTableDef table = tableDefMapper.findByTableId(tableId);
        List<SmFieldDef> fields = fieldDefMapper.findByTableId(tableId);

        result.put("table", table);
        result.put("fields", fields);
        return result;
    }

    public List<SmDrillDef> getDrillDefs(String tableId) {
        return drillDefMapper.findBySourceTableId(tableId);
    }

    public List<Map<String, Object>> getDropdownOptions(String retrievalTable, String format) {
        String sql = "SELECT FLD_VAL, FLD_STR FROM SYSDATA WHERE TBL_NAME = ? AND FLD_NAME = ? ORDER BY FLD_VAL";
        List<Map<String, Object>> rows = jdbcTemplate.queryForList(sql, retrievalTable, format);
        for (Map<String, Object> row : rows) {
            if (row.get("FLD_VAL") instanceof String) {
                row.put("FLD_VAL", ((String) row.get("FLD_VAL")).trim());
            }
            if (row.get("FLD_STR") instanceof String) {
                row.put("FLD_STR", ((String) row.get("FLD_STR")).trim());
            }
        }
        return rows;
    }
}
