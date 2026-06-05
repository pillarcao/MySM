package com.sm.service;

import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class EventLogService {

    private static final Logger log = LoggerFactory.getLogger(EventLogService.class);

    private final JdbcTemplate jdbcTemplate;

    /**
     * Record an event. Failures are logged but never propagated.
     */
    public void log(String evtCode, String userId, String tblName, String tblKey, String comment) {
        try {
            jdbcTemplate.update(
                    "INSERT INTO EVTLOG (EVT_TIME, EVT_CODE, USER_ID, TBL_NAME, TBL_KEY, \"COMMENT\") " +
                            "VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?, ?)",
                    evtCode,
                    userId != null ? userId : "",
                    tblName != null ? tblName : "",
                    tblKey != null ? tblKey : "",
                    comment != null ? comment : ""
            );
        } catch (Exception e) {
            log.error("Failed to write event log: evtCode={}, userId={}, tblName={}, error={}",
                    evtCode, userId, tblName, e.getMessage());
        }
    }

    /**
     * Search event logs with optional filters.
     */
    public List<Map<String, Object>> search(String startDate, String endDate,
                                            String tableName, String userId, int limit) {
        StringBuilder sql = new StringBuilder("SELECT * FROM EVTLOG WHERE 1=1");
        List<Object> params = new ArrayList<>();

        if (startDate != null && !startDate.isEmpty()) {
            sql.append(" AND EVT_TIME >= ?");
            params.add(startDate);
        }
        if (endDate != null && !endDate.isEmpty()) {
            sql.append(" AND EVT_TIME <= ?");
            params.add(endDate);
        }
        if (tableName != null && !tableName.isEmpty()) {
            sql.append(" AND TBL_NAME = ?");
            params.add(tableName);
        }
        if (userId != null && !userId.isEmpty()) {
            sql.append(" AND USER_ID = ?");
            params.add(userId);
        }

        sql.append(" ORDER BY EVT_TIME DESC");
        if (limit > 0) {
            sql.append(" LIMIT ?");
            params.add(limit);
        }

        return jdbcTemplate.queryForList(sql.toString(), params.toArray());
    }

    public List<String> getDistinctTables() {
        return jdbcTemplate.queryForList(
                "SELECT DISTINCT TRIM(TBL_NAME) AS TBL_NAME FROM EVTLOG WHERE TBL_NAME != '' ORDER BY TBL_NAME",
                String.class
        );
    }

    public List<String> getDistinctUsers() {
        return jdbcTemplate.queryForList(
                "SELECT DISTINCT TRIM(USER_ID) AS USER_ID FROM EVTLOG WHERE USER_ID != '' ORDER BY USER_ID",
                String.class
        );
    }
}
