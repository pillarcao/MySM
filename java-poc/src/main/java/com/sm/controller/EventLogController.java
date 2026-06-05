package com.sm.controller;

import com.sm.service.EventLogService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/evtlog")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class EventLogController {

    private final EventLogService eventLogService;

    @PostMapping("/search")
    public List<Map<String, Object>> search(@RequestBody Map<String, Object> req) {
        String startDate = (String) req.get("startDate");
        String endDate = (String) req.get("endDate");
        String tableName = (String) req.get("tableName");
        String userId = (String) req.get("userId");
        int limit = req.containsKey("limit") ? ((Number) req.get("limit")).intValue() : 500;
        return eventLogService.search(startDate, endDate, tableName, userId, limit);
    }

    @GetMapping("/tables")
    public List<String> getTables() {
        return eventLogService.getDistinctTables();
    }

    @GetMapping("/users")
    public List<String> getUsers() {
        return eventLogService.getDistinctUsers();
    }
}
