package com.sm.util;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;

import javax.servlet.http.HttpServletRequest;

@Component
public class UserContext {

    private final JwtUtil jwtUtil;
    private final HttpServletRequest request;

    public UserContext(JwtUtil jwtUtil, HttpServletRequest request) {
        this.jwtUtil = jwtUtil;
        this.request = request;
    }

    /**
     * Get current user ID from JWT token or SecurityContext.
     */
    public String getCurrentUser() {
        // Try SecurityContext first
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth != null && auth.getName() != null && !"anonymousUser".equals(auth.getName())) {
            return auth.getName();
        }
        // Fallback: extract from Authorization header
        String header = request.getHeader("Authorization");
        if (header != null && header.startsWith("Bearer ")) {
            try {
                return jwtUtil.extractUsername(header.substring(7));
            } catch (Exception ignored) {}
        }
        return "SYSTEM";
    }
}
