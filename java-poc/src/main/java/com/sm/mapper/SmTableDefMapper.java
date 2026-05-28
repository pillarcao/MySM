package com.sm.mapper;

import com.sm.entity.SmTableDef;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface SmTableDefMapper {
    SmTableDef findByTableId(@Param("tableId") String tableId);
    List<SmTableDef> findAll();
}
