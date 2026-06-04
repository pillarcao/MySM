package com.sm.controller;

import com.sm.service.RouteBatchService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/route")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class RouteBatchController {

    private final RouteBatchService routeBatchService;

    @PostMapping("/copy")
    public Map<String, Object> routeCopy(@RequestBody Map<String, String> req) {
        return routeBatchService.routeCopy(
                req.get("routeId"), req.get("routeVer"), req.get("newRouteId"));
    }

    @PostMapping("/verup")
    public Map<String, Object> routeVerUp(@RequestBody Map<String, String> req) {
        return routeBatchService.routeVerUp(req.get("routeId"), req.get("routeVer"));
    }

    @PostMapping("/release")
    public Map<String, Object> routeRelease(@RequestBody Map<String, String> req) {
        return routeBatchService.routeRelease(req.get("routeId"), req.get("routeVer"));
    }
}
