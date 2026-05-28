package com.sm;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.sm.mapper")
public class SmPocApplication {
    public static void main(String[] args) {
        SpringApplication.run(SmPocApplication.class, args);
    }
}
