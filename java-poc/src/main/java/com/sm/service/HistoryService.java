package com.sm.service;

import org.springframework.stereotype.Service;

import java.sql.Timestamp;
import java.util.List;

/**
 * Shared utility: generates the 5-tier shift-register SQL fragment
 * for B-table history fields (LAST_DATE1-5, LAST_ACT1-5, LAST_USER1-5).
 *
 * Pattern from original MFC system:
 *   New values go into slot 1, old values shift to slots 2→3→4→5 (discarded).
 *   Order matters: slot 1 set FIRST, then shift assignments read OLD values.
 */
@Service
public class HistoryService {

    /**
     * Generate SET clause that shifts history and writes new slot 1 values.
     * @param action  action name (e.g., "Save", "EditComp", "Release")
     * @param userId  user performing the action
     */
    public String shiftHistorySQL(String action, String userId) {
        return "\"LAST_DATE1\" = CURRENT_TIMESTAMP, \"LAST_ACT1\" = '" + escape(action) + "', \"LAST_USER1\" = '" + escape(userId) + "', "
                + "\"LAST_DATE2\" = \"LAST_DATE1\", \"LAST_ACT2\" = \"LAST_ACT1\", \"LAST_USER2\" = \"LAST_USER1\", "
                + "\"LAST_DATE3\" = \"LAST_DATE2\", \"LAST_ACT3\" = \"LAST_ACT2\", \"LAST_USER3\" = \"LAST_USER2\", "
                + "\"LAST_DATE4\" = \"LAST_DATE3\", \"LAST_ACT4\" = \"LAST_ACT3\", \"LAST_USER4\" = \"LAST_USER3\", "
                + "\"LAST_DATE5\" = \"LAST_DATE4\", \"LAST_ACT5\" = \"LAST_ACT4\", \"LAST_USER5\" = \"LAST_USER4\"";
    }

    /**
     * Add history columns and values to INSERT statement.
     * Slot 1 = action/timestamp/user, slots 2-5 = empty.
     */
    public void addInitHistory(List<String> columns, List<Object> values, List<String> placeholders,
                               String action, String userId) {
        // Slot 1: action
        columns.add("\"LAST_DATE1\""); values.add(new java.sql.Timestamp(System.currentTimeMillis())); placeholders.add("?");
        columns.add("\"LAST_ACT1\"");  values.add(action); placeholders.add("?");
        columns.add("\"LAST_USER1\""); values.add(userId); placeholders.add("?");
        // Slots 2-5: empty
        for (int i = 2; i <= 5; i++) {
            columns.add("\"LAST_DATE" + i + "\""); values.add(null); placeholders.add("?");
            columns.add("\"LAST_ACT" + i + "\"");  values.add("");  placeholders.add("?");
            columns.add("\"LAST_USER" + i + "\""); values.add("");  placeholders.add("?");
        }
    }

    private String escape(String s) {
        return (s != null) ? s.replace("'", "''") : "";
    }
}
