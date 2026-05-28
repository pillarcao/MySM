package com.sm.security;

import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class UserDetailsServiceImpl implements UserDetailsService {

    private final JdbcTemplate jdbcTemplate;

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        Map<String, Object> user;
        try {
            user = jdbcTemplate.queryForMap(
                    "SELECT * FROM BUSER WHERE USER_ID = ? AND REL_FLG = 'N'",
                    username
            );
        } catch (Exception e) {
            throw new UsernameNotFoundException("User not found: " + username);
        }

        String passwd = (String) user.get("PASSWD");
        // 旧系统密码是 CHAR(10)，trim 后比对
        if (passwd != null) {
            passwd = passwd.trim();
        }

        return new User(username, passwd, Collections.emptyList());
    }
}
