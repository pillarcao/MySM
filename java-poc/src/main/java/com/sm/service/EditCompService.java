package com.sm.service;

import com.sm.entity.SmFieldDef;
import com.sm.mapper.SmFieldDefMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class EditCompService {

    private final SmFieldDefMapper fieldDefMapper;
    private final JdbcTemplate jdbcTemplate;
    private final ValidationService validationService;
    private final HistoryService historyService;
    private final com.sm.util.UserContext userContext;

    @Transactional
    public void editComp(String tableId, Map<String, Object> keys) {
        // 1. EditComp 前校验
        validationService.validateForEditComp(tableId, keys);

        // 2. 获取表名
        String tableName = getTableName(tableId);

        // 3. 构建 WHERE（排除 REL_FLG，固定 E）
        List<SmFieldDef> keyFields = fieldDefMapper.findByTableId(tableId).stream()
                .filter(f -> "Y".equals(f.getIsKey()) && !"REL_FLG".equals(f.getFieldName()))
                .collect(Collectors.toList());

        StringBuilder where = new StringBuilder("\"REL_FLG\" = 'N'");
        List<Object> values = new ArrayList<>();
        for (SmFieldDef kf : keyFields) {
            where.append(" AND \"").append(kf.getFieldName()).append("\" = ?");
            values.add(keys.get(kf.getFieldName()));
        }

        // 4. Update COMP_FLG='Y' with history shift (slot1=EditComp, old→slots 2-5)
        String sql = "UPDATE " + tableName + " SET \"COMP_FLG\" = 'Y', "
                + historyService.shiftHistorySQL("EditComp", userContext.getCurrentUser()) + " WHERE " + where;
        jdbcTemplate.update(sql, values.toArray());
    }

    private String getTableName(String tableId) {
        return tableId.replaceFirst("^TBLID_", "");
    }
}
