package com.sm.controller;

import com.sm.service.EditCompService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/editcomp")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class EditCompController {

    private final EditCompService editCompService;

    @PostMapping("/{tableId}")
    public String editComp(@PathVariable String tableId, @RequestBody Map<String, Object> keys) {
        editCompService.editComp(tableId, keys);
        return "OK";
    }
}
