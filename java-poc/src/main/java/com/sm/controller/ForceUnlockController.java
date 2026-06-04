package com.sm.controller;

import com.sm.service.ForceUnlockService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/force-unlock")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class ForceUnlockController {

    private final ForceUnlockService forceUnlockService;

    @PostMapping("/{tableId}")
    public String forceUnlock(@PathVariable String tableId, @RequestBody Map<String, Object> keys) {
        forceUnlockService.forceUnlock(tableId, keys);
        return "OK";
    }
}
