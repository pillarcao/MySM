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
public class RouteBatchService {

    private final SmTableDefMapper tableDefMapper;
    private final SmFieldDefMapper fieldDefMapper;
    private final JdbcTemplate jdbcTemplate;
    private final HistoryService historyService;
    private final com.sm.util.UserContext userContext;

    /**
     * Route batch operation tables (from original MFC system RouteCopy/RouteVerUp/RouteRelease).
     * Ordered by dependency: BROUTE first, then child tables.
     * Tables not yet configured in SM_TABLE_DEF are silently skipped.
     */
    private static final String[] ROUTE_BATCH_TABLES = {
        "TBLID_BROUTE",
        "TBLID_BROUTE_MROUTE",
        "TBLID_BROUTECNCT",
        "TBLID_BRECIP_LOOKUP",
        "TBLID_BMEAS_LOOKUP",
        "TBLID_BPROCDATA_LOOKUP",
        "TBLID_BQTIME",
        "TBLID_BMULTI_RECIP_SET"
    };

    /**
     * Copy all objects in Route to a new Route ID.
     * For each related table: SELECT source rows, INSERT with new ROUTE_ID.
     */
    @Transactional
    public Map<String, Object> routeCopy(String srcRouteId, String srcRouteVer, String newRouteId) {
        Map<String, Object> result = new LinkedHashMap<>();
        for (String tableId : ROUTE_BATCH_TABLES) {
            try {
                int count = copyTable(tableId, srcRouteId, srcRouteVer, newRouteId, srcRouteVer);
                result.put(tableId, count + " rows copied");
            } catch (Exception e) {
                result.put(tableId, "ERROR: " + e.getMessage());
                throw new RuntimeException("RouteCopy failed at " + tableId + ": " + e.getMessage(), e);
            }
        }
        return result;
    }

    /**
     * Revise version: increment ROUTE_VER for all objects in Route.
     * New version = old version + 1.
     */
    @Transactional
    public Map<String, Object> routeVerUp(String routeId, String srcRouteVer) {
        int newVer = Integer.parseInt(srcRouteVer.trim()) + 1;
        if (newVer > 999) newVer = 1;
        String newRouteVer = String.format("%03d", newVer);

        Map<String, Object> result = new LinkedHashMap<>();
        for (String tableId : ROUTE_BATCH_TABLES) {
            try {
                int count = copyTable(tableId, routeId, srcRouteVer, routeId, newRouteVer);
                result.put(tableId, count + " rows ver-up'd");
            } catch (Exception e) {
                result.put(tableId, "ERROR: " + e.getMessage());
                throw new RuntimeException("RouteVerUp failed at " + tableId + ": " + e.getMessage(), e);
            }
        }
        result.put("newVersion", newRouteVer);
        return result;
    }

    /**
     * Release all objects in Route: for each B table, release to D table.
     */
    @Transactional
    public Map<String, Object> routeRelease(String routeId, String routeVer) {
        Map<String, Object> result = new LinkedHashMap<>();
        for (String tableId : ROUTE_BATCH_TABLES) {
            try {
                releaseTable(tableId, routeId, routeVer);
                result.put(tableId, "released");
            } catch (Exception e) {
                result.put(tableId, "ERROR: " + e.getMessage());
                throw new RuntimeException("RouteRelease failed at " + tableId + ": " + e.getMessage(), e);
            }
        }
        return result;
    }

    // --- Private helpers ---

    private int copyTable(String tableId, String srcRouteId, String srcRouteVer,
                          String newRouteId, String newRouteVer) {
        SmTableDef tableDef = tableDefMapper.findByTableId(tableId);
        if (tableDef == null) return 0;
        String tableName = tableDef.getTableName();
        List<SmFieldDef> fields = fieldDefMapper.findByTableId(tableId);
        List<SmFieldDef> bizFields = fields.stream()
                .filter(f -> !"Y".equals(f.getIsDummy()) && !"Y".equals(f.getIsAuto()))
                .collect(Collectors.toList());

        // Determine route id/ver column names (ROUTE_ID or SPLIT_ROUTE_ID)
        String idCol = "ROUTE_ID";
        String verCol = "ROUTE_VER";
        if ("BROUTECNCT".equals(tableName)) {
            idCol = "SPLIT_ROUTE_ID";
            verCol = "SPLIT_ROUTE_VER";
        }

        // Build source WHERE
        String srcWhere = "\"" + idCol + "\" = ? AND \"" + verCol + "\" = ? AND \"REL_FLG\" = 'Y'";
        List<Map<String, Object>> srcRows = jdbcTemplate.queryForList(
                "SELECT * FROM " + tableName + " WHERE " + srcWhere, srcRouteId, srcRouteVer);
        if (srcRows.isEmpty()) return 0;

        // Build INSERT for each source row with new route id/ver
        int count = 0;
        for (Map<String, Object> srcRow : srcRows) {
            // Delete existing N record with same business keys to avoid PK conflict
            List<SmFieldDef> dbKeyFields = fields.stream()
                    .filter(f -> "Y".equals(f.getIsKey()) && !"REL_FLG".equals(f.getFieldName()))
                    .collect(Collectors.toList());
            if (!dbKeyFields.isEmpty()) {
                StringBuilder delWhere = new StringBuilder();
                List<Object> delVals = new ArrayList<>();
                for (SmFieldDef kf : dbKeyFields) {
                    if (delWhere.length() > 0) delWhere.append(" AND ");
                    delWhere.append("\"").append(kf.getFieldName()).append("\" = ?");
                    if (idCol.equals(kf.getFieldName())) {
                        delVals.add(newRouteId);
                    } else if (verCol.equals(kf.getFieldName())) {
                        delVals.add(newRouteVer);
                    } else {
                        delVals.add(srcRow.get(kf.getFieldName()));
                    }
                }
                jdbcTemplate.update("DELETE FROM " + tableName
                        + " WHERE " + delWhere + " AND \"REL_FLG\" = 'N'", delVals.toArray());
            }

            List<String> columns = new ArrayList<>();
            List<Object> values = new ArrayList<>();
            List<String> placeholders = new ArrayList<>();

            for (SmFieldDef f : bizFields) {
                String col = f.getFieldName();
                Object val = srcRow.get(col);
                if (idCol.equals(col)) {
                    val = newRouteId;
                } else if (verCol.equals(col)) {
                    val = newRouteVer;
                }
                // Also replace SUB_ROUTE_ID/RET_ROUTE_ID if they reference the source route
                if ("BROUTECNCT".equals(tableName)) {
                    if (("SUB_ROUTE_ID".equals(col) || "RET_ROUTE_ID".equals(col))
                            && srcRouteId.equals(val != null ? val.toString().trim() : "")) {
                        val = newRouteId;
                    }
                    if (("SUB_ROUTE_VER".equals(col) || "RET_ROUTE_VER".equals(col))
                            && srcRouteVer.equals(val != null ? val.toString().trim() : "")) {
                        val = newRouteVer;
                    }
                }
                if (val == null) {
                    if ("NUMBER".equals(f.getDbType())) val = 0;
                    else val = "";
                }
                columns.add("\"" + col + "\"");
                values.add(val);
                placeholders.add("?");
            }

            // B-table control fields
            addCtrlField(columns, values, placeholders, "REL_FLG", "N");
            addCtrlField(columns, values, placeholders, "COMP_FLG", srcRow.getOrDefault("COMP_FLG", "N"));
            addCtrlField(columns, values, placeholders, "CRE_DATE", new Timestamp(System.currentTimeMillis()));
            addCtrlField(columns, values, placeholders, "CRE_USER", userContext.getCurrentUser());
            addCtrlField(columns, values, placeholders, "OWNER", srcRow.getOrDefault("OWNER", "SYSTEM"));
            addCtrlField(columns, values, placeholders, "OWNERG", srcRow.getOrDefault("OWNERG", ""));
            addCtrlField(columns, values, placeholders, "PERMISSION", srcRow.getOrDefault("PERMISSION", "PUBLIC    "));
            addCtrlField(columns, values, placeholders, "LOCK_USER", "");
            addCtrlField(columns, values, placeholders, "LOCK_TIME", null);
            addCtrlField(columns, values, placeholders, "COMMENT", srcRow.getOrDefault("COMMENT", ""));
            // History: slot 1 = Create (copy), slots 2-5 = empty
            historyService.addInitHistory(columns, values, placeholders, "Create", userContext.getCurrentUser());

            String sql = "INSERT INTO " + tableName + " (" + String.join(", ", columns)
                    + ") VALUES (" + String.join(", ", placeholders) + ")";
            jdbcTemplate.update(sql, values.toArray());
            count++;
        }
        return count;
    }

    private void releaseTable(String tableId, String routeId, String routeVer) {
        SmTableDef tableDef = tableDefMapper.findByTableId(tableId);
        if (tableDef == null) return;
        String bTableName = tableDef.getTableName();
        String dTableName = bTableName.replaceFirst("^B", "D");

        List<SmFieldDef> fields = fieldDefMapper.findByTableId(tableId);

        // Determine route id/ver column names
        String idCol = "ROUTE_ID";
        String verCol = "ROUTE_VER";
        if ("BROUTECNCT".equals(bTableName)) {
            idCol = "SPLIT_ROUTE_ID";
            verCol = "SPLIT_ROUTE_VER";
        }

        // Find B-table N record
        String bWhere = "\"" + idCol + "\" = ? AND \"" + verCol + "\" = ? AND \"REL_FLG\" = 'N'";
        List<Map<String, Object>> bRows = jdbcTemplate.queryForList(
                "SELECT * FROM " + bTableName + " WHERE " + bWhere, routeId, routeVer);
        if (bRows.isEmpty()) return;
        Map<String, Object> bRecord = bRows.get(0);

        // Collect business fields (exclude control fields)
        Set<String> controlFields = new HashSet<>(Arrays.asList(
                "REL_FLG","COMP_FLG","CRE_DATE","CRE_USER",
                "LAST_DATE1","LAST_ACT1","LAST_USER1",
                "LAST_DATE2","LAST_ACT2","LAST_USER2",
                "LAST_DATE3","LAST_ACT3","LAST_USER3",
                "LAST_DATE4","LAST_ACT4","LAST_USER4",
                "LAST_DATE5","LAST_ACT5","LAST_USER5",
                "OWNER","OWNERG","PERMISSION","LOCK_USER","LOCK_TIME","COMMENT"));
        List<SmFieldDef> bizFields = fields.stream()
                .filter(f -> !"Y".equals(f.getIsDummy()) && !controlFields.contains(f.getFieldName()))
                .collect(Collectors.toList());
        List<SmFieldDef> keyFields = fields.stream()
                .filter(f -> "Y".equals(f.getIsKey()) && !"REL_FLG".equals(f.getFieldName()))
                .collect(Collectors.toList());

        // Build D-table record
        Map<String, Object> dRecord = new LinkedHashMap<>();
        for (SmFieldDef f : bizFields) {
            dRecord.put(f.getFieldName(), bRecord.get(f.getFieldName()));
        }
        // Ensure key fields are present
        for (SmFieldDef kf : keyFields) {
            if (!dRecord.containsKey(kf.getFieldName())) {
                dRecord.put(kf.getFieldName(), bRecord.get(kf.getFieldName()));
            }
        }

        // UPSERT D-table
        StringBuilder dWhere = new StringBuilder();
        List<Object> dKeyVals = new ArrayList<>();
        for (SmFieldDef kf : keyFields) {
            if (dWhere.length() > 0) dWhere.append(" AND ");
            dWhere.append("\"").append(kf.getFieldName()).append("\" = ?");
            dKeyVals.add(dRecord.get(kf.getFieldName()));
        }
        Integer dCount = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM " + dTableName + " WHERE " + dWhere,
                Integer.class, dKeyVals.toArray());
        if (dCount != null && dCount > 0) {
            // UPDATE D-table
            List<String> setParts = new ArrayList<>();
            List<Object> setVals = new ArrayList<>();
            for (Map.Entry<String, Object> e : dRecord.entrySet()) {
                if (keyFields.stream().anyMatch(kf -> kf.getFieldName().equals(e.getKey()))) continue;
                setParts.add("\"" + e.getKey() + "\" = ?");
                setVals.add(e.getValue());
            }
            if (!setParts.isEmpty()) {
                setVals.addAll(dKeyVals);
                jdbcTemplate.update("UPDATE " + dTableName + " SET " + String.join(", ", setParts)
                        + " WHERE " + dWhere, setVals.toArray());
            }
        } else {
            // INSERT D-table
            List<String> cols = new ArrayList<>();
            List<Object> vals = new ArrayList<>();
            List<String> phs = new ArrayList<>();
            for (Map.Entry<String, Object> e : dRecord.entrySet()) {
                cols.add("\"" + e.getKey() + "\"");
                vals.add(e.getValue());
                phs.add("?");
            }
            jdbcTemplate.update("INSERT INTO " + dTableName + " (" + String.join(", ", cols)
                    + ") VALUES (" + String.join(", ", phs) + ")", vals.toArray());
        }

        // Update B-table: delete ALL old Y records for this route, then update N→Y
        jdbcTemplate.update("DELETE FROM " + bTableName
                + " WHERE \"" + idCol + "\" = ? AND \"REL_FLG\" = 'Y'", routeId);
        jdbcTemplate.update("UPDATE " + bTableName
                + " SET \"REL_FLG\" = 'Y', \"COMP_FLG\" = 'Y' WHERE " + bWhere, routeId, routeVer);
    }

    private void addCtrlField(List<String> cols, List<Object> vals, List<String> phs,
                              String name, Object value) {
        String q = "\"" + name + "\"";
        if (!cols.contains(q)) {
            cols.add(q);
            vals.add(value);
            phs.add("?");
        }
    }
}
