package com.sm.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class SmTableDef {
    private String tableId;
    private String tableName;
    private String jpTitle;
    private String usTitle;
    private String releaseFlag;
    private String distributeFlag;
    private String permissionType;
    private String schemaType;
    private String hasDummy;
    private int sortNo;
    private String menuGroup;
    private LocalDateTime creDate;
    private String creUser;
}
