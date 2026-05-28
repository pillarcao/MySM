package com.sm.entity;

import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * BCODE 表实体
 * 业务字段: CODE_CAT, CODE_ID, CODE_NAME, CODE_DESC
 * 控制字段继承自 BaseEntity
 */
@Data
@EqualsAndHashCode(callSuper = true)
public class BCode extends BaseEntity {
    private String codeCat;
    private String codeId;
    private String codeName;
    private String codeDesc;
}
