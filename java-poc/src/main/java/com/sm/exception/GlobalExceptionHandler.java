package com.sm.exception;

import org.springframework.dao.DataAccessException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.HashMap;
import java.util.Map;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ValidationException.class)
    public ResponseEntity<Map<String, String>> handleValidation(ValidationException ex) {
        return error(HttpStatus.BAD_REQUEST, ex.getMessage());
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<Map<String, String>> handleIllegalArgument(IllegalArgumentException ex) {
        String msg = ex.getMessage();
        if (msg != null && msg.contains("Table config not found")) {
            msg = "表配置不存在: " + msg.replace("Table config not found: ", "");
        }
        return error(HttpStatus.BAD_REQUEST, msg != null ? msg : "参数错误");
    }

    @ExceptionHandler(DataAccessException.class)
    public ResponseEntity<Map<String, String>> handleDataAccess(DataAccessException ex) {
        String msg = ex.getMessage();
        if (msg == null) msg = "数据库操作失败";
        else if (msg.contains("NULL not allowed")) msg = "必填字段不能为空";
        else if (msg.contains("Unique index") || msg.contains("primary key violation")) msg = "数据已存在，请勿重复添加";
        else if (msg.contains("Referential integrity")) msg = "数据被其他表引用，无法删除";
        else if (msg.contains("Column") && msg.contains("not found")) msg = "字段不存在，请联系管理员";
        else msg = "数据库操作失败: " + msg;
        return error(HttpStatus.INTERNAL_SERVER_ERROR, msg);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, String>> handleGeneral(Exception ex) {
        String msg = ex.getMessage();
        if (msg == null) msg = "服务器内部错误";
        else if (msg.contains("JWT")) msg = "登录信息无效，请重新登录";
        else if (msg.contains("expired")) msg = "登录已过期，请重新登录";
        else msg = "服务器内部错误: " + msg;
        return error(HttpStatus.INTERNAL_SERVER_ERROR, msg);
    }

    private ResponseEntity<Map<String, String>> error(HttpStatus status, String message) {
        Map<String, String> body = new HashMap<>();
        body.put("error", message);
        return ResponseEntity.status(status).body(body);
    }
}
