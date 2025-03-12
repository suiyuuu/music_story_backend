-- 创建歌曲表 - 增加更多有用的元数据字段
CREATE TABLE IF NOT EXISTS songs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    song_name VARCHAR(255) NOT NULL,
    artist_name VARCHAR(255) NOT NULL,
    lyrics TEXT,
    lyrics_source VARCHAR(50),                         -- 歌词来源(网易、QQ音乐等)
    lyrics_language VARCHAR(20),                       -- 歌词主要语言(中文、英文等)
    duration INT DEFAULT 0,                            -- 歌曲时长(秒)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_song_artist (song_name, artist_name),
    INDEX idx_file_name (file_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建关键词表 - 添加权重和来源字段
CREATE TABLE IF NOT EXISTS keywords (
    id INT AUTO_INCREMENT PRIMARY KEY,
    song_id INT NOT NULL,
    keyword VARCHAR(100) NOT NULL,
    frequency INT DEFAULT 1,
    weight FLOAT DEFAULT 1.0,                         -- 关键词权重(可用于更高级的排序)
    source ENUM('auto', 'manual') DEFAULT 'auto',     -- 关键词来源(自动提取或用户手动添加)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE,
    UNIQUE KEY (song_id, keyword),                    -- 确保每首歌的关键词不重复
    INDEX idx_song_keyword (song_id, keyword)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建故事表 - 添加标题和提示词字段
CREATE TABLE IF NOT EXISTS stories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    song_id INT NOT NULL,
    title VARCHAR(255),                               -- 故事标题
    prompt TEXT,                                      -- 生成故事时使用的提示词
    story_content TEXT NOT NULL,
    user_edited BOOLEAN DEFAULT FALSE,                -- 用户是否编辑过
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE,
    INDEX idx_song_id (song_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建用户选择关键词记录表 - 记录用户选择过的关键词
CREATE TABLE IF NOT EXISTS user_keyword_selections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    song_id INT NOT NULL,
    keyword_ids TEXT NOT NULL,                        -- 存储用户选择的关键词ID，用逗号分隔
    story_id INT,                                     -- 关联的故事ID(如果有)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE,
    FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE SET NULL,
    INDEX idx_song_story (song_id, story_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;