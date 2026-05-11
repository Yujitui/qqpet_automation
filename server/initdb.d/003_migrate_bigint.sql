-- 迁移脚本：将 info_last_login_time 从 INTEGER 改为 BIGINT
-- 这个脚本会在 initdb.d 中按字母顺序执行（003 会在 001、002 之后）

DO $$
BEGIN
    -- 检查列是否存在且类型不是 BIGINT
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'pet_data' 
        AND column_name = 'info_last_login_time'
        AND data_type != 'bigint'
    ) THEN
        ALTER TABLE pet_data ALTER COLUMN info_last_login_time TYPE BIGINT;
        RAISE NOTICE 'Migration: Changed info_last_login_time to BIGINT';
    ELSE
        RAISE NOTICE 'Migration: info_last_login_time is already BIGINT or does not exist';
    END IF;
END $$;
