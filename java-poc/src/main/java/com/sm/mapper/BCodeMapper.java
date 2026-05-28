package com.sm.mapper;

import com.sm.entity.BCode;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

@Mapper
public interface BCodeMapper {
    List<BCode> findAll();
    List<BCode> findByRelFlg(@Param("relFlg") String relFlg);
    BCode findByKey(@Param("codeCat") String codeCat,
                    @Param("codeId") String codeId,
                    @Param("relFlg") String relFlg);
    int insert(BCode record);
    int update(BCode record);
    int delete(@Param("codeCat") String codeCat,
               @Param("codeId") String codeId,
               @Param("relFlg") String relFlg);
}
