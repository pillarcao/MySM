package com.sm.entity;

import lombok.Data;
import java.time.LocalDateTime;

/**
 * SM 系统所有 B 表的通用控制字段（21 个字段）
 * 对应 DB2 DDL 中的 REL_FLG, COMP_FLG, CRE_DATE...COMMENT
 */
@Data
public class BaseEntity {
    private String relFlg;
    private String compFlg;
    private LocalDateTime creDate;
    private String creUser;

    private LocalDateTime lastDate1;
    private String lastAct1;
    private String lastUser1;

    private LocalDateTime lastDate2;
    private String lastAct2;
    private String lastUser2;

    private LocalDateTime lastDate3;
    private String lastAct3;
    private String lastUser3;

    private LocalDateTime lastDate4;
    private String lastAct4;
    private String lastUser4;

    private LocalDateTime lastDate5;
    private String lastAct5;
    private String lastUser5;

    private String owner;
    private String ownerg;
    private String permission;
    private String lockUser;
    private LocalDateTime lockTime;
    private String comment;
}
