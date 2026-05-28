package com.sm.controller;

import com.sm.util.JwtUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class AuthController {

    private final AuthenticationManager authenticationManager;
    private final JwtUtil jwtUtil;

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody Map<String, String> req) {
        String userId = req.get("userId");
        String passwd = req.get("passwd");

        try {
            authenticationManager.authenticate(
                    new UsernamePasswordAuthenticationToken(userId, passwd)
            );
        } catch (BadCredentialsException e) {
            Map<String, Object> err = new HashMap<>();
            err.put("error", "Invalid credentials");
            return ResponseEntity.status(401).body(err);
        }

        String token = jwtUtil.generateToken(userId);
        Map<String, Object> resp = new HashMap<>();
        resp.put("token", token);
        resp.put("userId", userId);
        return ResponseEntity.ok(resp);
    }
}
