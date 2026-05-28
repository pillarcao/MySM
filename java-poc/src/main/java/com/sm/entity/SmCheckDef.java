package com.sm.entity;

import lombok.Data;

@Data
public class SmCheckDef {
    private Long id;
    private String tableId;
    private String checkType;
    private int checkOrder;
    private String checkKind;
    private String fieldName;
    private String refTable;
    private String refField;
    private String expectValue;
    private String errMsg;
}
