package com.sm.service;

import com.sm.entity.BCode;
import com.sm.mapper.BCodeMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
public class BCodeService {

    private final BCodeMapper mapper;

    public List<BCode> listAll() {
        return mapper.findAll();
    }

    public List<BCode> listByRelFlg(String relFlg) {
        return mapper.findByRelFlg(relFlg);
    }

    public BCode get(String codeCat, String codeId, String relFlg) {
        return mapper.findByKey(codeCat, codeId, relFlg);
    }

    @Transactional
    public void save(BCode record) {
        BCode exist = mapper.findByKey(record.getCodeCat(), record.getCodeId(), record.getRelFlg());
        if (exist == null) {
            mapper.insert(record);
        } else {
            mapper.update(record);
        }
    }

    @Transactional
    public void delete(String codeCat, String codeId, String relFlg) {
        mapper.delete(codeCat, codeId, relFlg);
    }
}
