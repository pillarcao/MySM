package com.sm.mapper;

import com.sm.entity.SmCheckDef;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

@Mapper
public interface SmCheckDefMapper {
    List<SmCheckDef> findByTableIdAndCheckType(@Param("tableId") String tableId, @Param("checkType") String checkType);
}
