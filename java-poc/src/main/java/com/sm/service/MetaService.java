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

import java.util.*;
import java.util.stream.Collectors;

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

    public List<Map<String, Object>> getTreeData(String tableId, String status) {
        SmTableDef table = tableDefMapper.findByTableId(tableId);
        if (table == null) return Collections.emptyList();
        List<SmFieldDef> fields = fieldDefMapper.findByTableId(tableId);

        // Find tree fields (treeLevel >= 0) and key fields for label
        List<SmFieldDef> treeFields = fields.stream()
                .filter(f -> f.getTreeLevel() >= 0)
                .sorted(Comparator.comparingInt(SmFieldDef::getTreeLevel))
                .collect(Collectors.toList());

        if (treeFields.isEmpty()) {
            // No grouping: return flat list
            return buildFlatTree(table, fields, status);
        }
        return buildGroupedTree(table, fields, treeFields, status);
    }

    private List<Map<String, Object>> buildFlatTree(SmTableDef table, List<SmFieldDef> fields, String status) {
        List<Map<String, Object>> records = fetchRecords(table.getTableName(), status);
        List<Map<String, Object>> result = new ArrayList<>();
        List<SmFieldDef> keyFields = fields.stream()
                .filter(f -> "Y".equals(f.getIsKey()) && !"REL_FLG".equals(f.getFieldName()))
                .collect(Collectors.toList());
        for (Map<String, Object> row : records) {
            Map<String, Object> node = new LinkedHashMap<>();
            node.put("id", buildNodeId(row, keyFields));
            node.put("label", buildRecordLabel(row, keyFields));
            node.put("record", row);
            result.add(node);
        }
        return result;
    }

    private List<Map<String, Object>> buildGroupedTree(SmTableDef table, List<SmFieldDef> fields,
                                                        List<SmFieldDef> treeFields, String status) {
        List<Map<String, Object>> records = fetchRecords(table.getTableName(), status);
        List<SmFieldDef> keyFields = fields.stream()
                .filter(f -> "Y".equals(f.getIsKey()) && !"REL_FLG".equals(f.getFieldName()))
                .collect(Collectors.toList());

        // Group by tree level 0 field first
        SmFieldDef primaryTree = treeFields.get(0);
        Map<String, List<Map<String, Object>>> groups = new LinkedHashMap<>();
        for (Map<String, Object> row : records) {
            String groupKey = String.valueOf(row.get(primaryTree.getFieldName())).trim();
            groups.computeIfAbsent(groupKey, k -> new ArrayList<>()).add(row);
        }

        List<Map<String, Object>> result = new ArrayList<>();
        for (Map.Entry<String, List<Map<String, Object>>> entry : groups.entrySet()) {
            Map<String, Object> groupNode = new LinkedHashMap<>();
            groupNode.put("id", "g_" + entry.getKey());
            groupNode.put("label", entry.getKey());
            List<Map<String, Object>> children = new ArrayList<>();
            for (Map<String, Object> row : entry.getValue()) {
                Map<String, Object> leaf = new LinkedHashMap<>();
                leaf.put("id", buildNodeId(row, keyFields));
                leaf.put("label", buildRecordLabel(row, keyFields));
                leaf.put("record", row);
                children.add(leaf);
            }
            groupNode.put("children", children);
            result.add(groupNode);
        }
        return result;
    }

    private List<Map<String, Object>> fetchRecords(String tableName, String status) {
        StringBuilder sql = new StringBuilder("SELECT * FROM " + tableName + " WHERE 1=1");
        List<Object> params = new ArrayList<>();
        if (!"ALL".equals(status)) {
            switch (status) {
                case "EDIT": sql.append(" AND \"REL_FLG\" = 'N' AND \"COMP_FLG\" = 'N'"); break;
                case "EDITCOMP": sql.append(" AND \"REL_FLG\" = 'N' AND \"COMP_FLG\" = 'Y'"); break;
                case "RELEASE": sql.append(" AND \"REL_FLG\" = 'Y'"); break;
            }
        }
        return jdbcTemplate.queryForList(sql.toString(), params.toArray());
    }

    private String buildNodeId(Map<String, Object> row, List<SmFieldDef> keyFields) {
        return keyFields.stream()
                .map(f -> String.valueOf(row.get(f.getFieldName())).trim())
                .collect(Collectors.joining("|"));
    }

    private String buildRecordLabel(Map<String, Object> row, List<SmFieldDef> keyFields) {
        return keyFields.stream()
                .map(f -> String.valueOf(row.get(f.getFieldName())).trim())
                .collect(Collectors.joining(" / "));
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
