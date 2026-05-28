package com.sm.mapper;

import com.sm.entity.SmDrillDef;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface SmDrillDefMapper {
    List<SmDrillDef> findBySourceTableId(@Param("sourceTableId") String sourceTableId);
    List<SmDrillDef> findAll();
}
