package com.sm.controller;

import com.sm.entity.BCode;
import com.sm.service.BCodeService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/bcode")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class BCodeController {

    private final BCodeService service;

    @GetMapping("/list")
    public List<BCode> list(@RequestParam(required = false) String relFlg) {
        if (relFlg != null && !relFlg.isEmpty()) {
            return service.listByRelFlg(relFlg);
        }
        return service.listAll();
    }

    @GetMapping("/get")
    public BCode get(@RequestParam String codeCat,
                     @RequestParam String codeId,
                     @RequestParam(defaultValue = "E") String relFlg) {
        return service.get(codeCat, codeId, relFlg);
    }

    @PostMapping("/save")
    public String save(@RequestBody BCode record) {
        service.save(record);
        return "OK";
    }

    @PostMapping("/delete")
    public String delete(@RequestParam String codeCat,
                         @RequestParam String codeId,
                         @RequestParam(defaultValue = "E") String relFlg) {
        service.delete(codeCat, codeId, relFlg);
        return "OK";
    }
}
