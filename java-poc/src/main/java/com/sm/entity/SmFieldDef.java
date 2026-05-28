package com.sm.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class SmFieldDef {
    private Long id;
    private String tableId;
    private String fieldName;
    private String jpTitle;
    private String usTitle;
    private String dbType;
    private int dbLength;
    private String isKey;
    private String notBlank;
    private String isDummy;
    private String isSearchItem;
    private int sortNo;
    private int treeLevel;
    private int sheetNo;
    private int pageNo;
    private int propertyNo;
    private String isAuto;
    private String isMandatory;
    private String systemReadonly;
    private String fieldType;
    private int fieldLength;
    private String inputAlphabet;
    private int inputMultibyte;
    private String inputNumeric;
    private String inputSymbol;
    private String inputUppercase;
    private String retrievalTable;
    private String format;
    private String defaultValue;
    private String minValue;
    private String maxValue;
    private String calendarButton;
    private String jumpButton;
    private int openButton;
    private String refTableId;
    private String refFieldName;
    private int specialButton;
    private LocalDateTime creDate;
    private String creUser;
}
