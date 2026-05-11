-- 种子数据脚本
-- 管理员用户: admin / admin123

INSERT INTO users (username, email, hashed_password, is_active, is_admin)
VALUES (
    'admin', 
    'admin@example.com', 
    '$2b$12$GpDCQh4fykZmpbVispHuUea7q0lHhInXDT4FnrlxILL5IcIGH36Xe',
    TRUE, 
    TRUE
);
