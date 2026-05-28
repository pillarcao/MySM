package com.sm.mapper;

import com.sm.entity.SmFieldDef;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

@Mapper
public interface SmFieldDefMapper {
    List<SmFieldDef> findByTableId(@Param("tableId") String tableId);
}
