-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- 宠物数据表
CREATE TABLE IF NOT EXISTS pet_data (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    info_name VARCHAR(50) DEFAULT '',
    info_host VARCHAR(50) DEFAULT '',
    info_sex VARCHAR(2) DEFAULT 'GG',
    info_growth FLOAT DEFAULT 0.0,
    info_hunger INTEGER DEFAULT 3100,
    info_clean INTEGER DEFAULT 3100,
    info_health INTEGER DEFAULT 5,
    info_mood INTEGER DEFAULT 1000,
    info_yb INTEGER DEFAULT 300,
    info_intel INTEGER DEFAULT 100,
    info_charm INTEGER DEFAULT 215,
    info_strong INTEGER DEFAULT 123,
    info_birth_day VARCHAR(20) DEFAULT '',
    info_online_time FLOAT DEFAULT 0.0,
    info_last_login_time BIGINT DEFAULT 0,
    info_online_data_time FLOAT DEFAULT 0.0,
    
    max_level INTEGER DEFAULT 1,
    max_hunger INTEGER DEFAULT 3100,
    max_clean INTEGER DEFAULT 3100,
    max_mood INTEGER DEFAULT 1000,
    max_growth_rate INTEGER DEFAULT 260,
    max_up_growth INTEGER DEFAULT 0,
    max_next_growth INTEGER DEFAULT 100,
    max_stop_growth BOOLEAN DEFAULT FALSE,
    
    active_option JSONB DEFAULT '{}',
    active_value JSONB DEFAULT '{}',
    other_options JSONB DEFAULT '{}',
    fishing JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pet_data_user_id ON pet_data(user_id);

-- 背包表
CREATE TABLE IF NOT EXISTS pet_inventory (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    items JSONB DEFAULT '{"food": [], "commodity": [], "medicine": [], "background": []}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pet_inventory_user_id ON pet_inventory(user_id);

-- 会话表
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    token_jti VARCHAR(100) UNIQUE NOT NULL,
    device_info JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token_jti ON sessions(token_jti);
