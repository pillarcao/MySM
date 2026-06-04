package com.sm.controller;

import com.sm.service.RollbackService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/rollback")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class RollbackController {

    private final RollbackService rollbackService;

    @PostMapping("/{tableId}")
    public String rollback(@PathVariable String tableId, @RequestBody Map<String, Object> keys) {
        rollbackService.rollback(tableId, keys);
        return "OK";
    }
}
