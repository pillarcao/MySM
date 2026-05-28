package com.sm.entity;

import lombok.Data;

@Data
public class SmDrillDef {
    private Long id;
    private String sourceTableId;
    private String targetTableId;
    private String label;
    private int sortNo;
}
