package com.sm.controller;

import com.sm.exception.ValidationException;
import com.sm.service.DynamicCrudService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/dynamic")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class DynamicCrudController {

    private final DynamicCrudService dynamicCrudService;

    @GetMapping("/{tableId}/list")
    public List<Map<String, Object>> list(@PathVariable String tableId,
                                             @RequestParam(required = false) String status) {
        return dynamicCrudService.list(tableId, status);
    }

    @PostMapping("/{tableId}/search")
    public List<Map<String, Object>> search(@PathVariable String tableId,
                                            @RequestParam(required = false) String status,
                                            @RequestBody Map<String, Object> conditions) {
        return dynamicCrudService.search(tableId, status, conditions);
    }

    @PostMapping("/{tableId}/save")
    public String save(@PathVariable String tableId, @RequestBody Map<String, Object> data) {
        dynamicCrudService.save(tableId, data);
        return "OK";
    }

    @PostMapping("/{tableId}/delete")
    public String delete(@PathVariable String tableId, @RequestBody Map<String, Object> data) {
        dynamicCrudService.delete(tableId, data);
        return "OK";
    }

    @PostMapping("/{tableId}/lock")
    public String lock(@PathVariable String tableId, @RequestBody Map<String, Object> keys) {
        dynamicCrudService.lock(tableId, keys);
        return "OK";
    }

    @PostMapping("/{tableId}/unlock")
    public String unlock(@PathVariable String tableId, @RequestBody Map<String, Object> keys) {
        dynamicCrudService.unlock(tableId, keys);
        return "OK";
    }

    @ExceptionHandler(ValidationException.class)
    public ResponseEntity<Map<String, String>> handleValidationException(ValidationException ex) {
        Map<String, String> body = new java.util.HashMap<>();
        body.put("error", ex.getMessage());
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(body);
    }
}
