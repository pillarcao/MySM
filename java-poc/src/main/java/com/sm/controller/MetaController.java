package com.sm.controller;

import com.sm.entity.SmDrillDef;
import com.sm.entity.SmTableDef;
import com.sm.service.MetaService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/meta")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class MetaController {

    private final MetaService metaService;

    @GetMapping("/tables")
    public List<SmTableDef> getTables() {
        return metaService.getAllTables();
    }

    @GetMapping("/{tableId}")
    public Map<String, Object> getMeta(@PathVariable String tableId) {
        return metaService.getTableMeta(tableId);
    }

    @GetMapping("/dropdown/{retrievalTable}/{format}")
    public List<Map<String, Object>> getDropdown(
            @PathVariable String retrievalTable,
            @PathVariable String format) {
        return metaService.getDropdownOptions(retrievalTable, format);
    }

    @GetMapping("/drills/{tableId}")
    public List<SmDrillDef> getDrills(@PathVariable String tableId) {
        return metaService.getDrillDefs(tableId);
    }

    @GetMapping("/{tableId}/tree")
    public List<Map<String, Object>> getTree(@PathVariable String tableId,
                                              @RequestParam(defaultValue = "ALL") String status) {
        return metaService.getTreeData(tableId, status);
    }
}
