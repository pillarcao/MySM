package com.sm.controller;

import com.sm.service.RollbackService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Collections;
import java.util.Map;

@RestController
@RequestMapping("/api/rollback")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class RollbackController {

    private final RollbackService rollbackService;

    @PostMapping("/{tableId}")
    public ResponseEntity<?> rollback(@PathVariable String tableId, @RequestBody Map<String, Object> keys) {
        try {
            rollbackService.rollback(tableId, keys);
            return ResponseEntity.ok(Collections.singletonMap("message", "回滚成功"));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Collections.singletonMap("error", e.getMessage()));
        }
    }
}
