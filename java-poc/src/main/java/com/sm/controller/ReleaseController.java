package com.sm.controller;

import com.sm.service.ReleaseService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/release")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class ReleaseController {

    private final ReleaseService releaseService;

    @PostMapping("/{tableId}")
    public String release(@PathVariable String tableId, @RequestBody Map<String, Object> keys) {
        releaseService.release(tableId, keys);
        return "OK";
    }
}
