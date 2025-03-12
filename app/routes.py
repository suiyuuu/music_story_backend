from flask import Blueprint, request, jsonify, current_app
import re
import time
from app.utils.database import get_db
from app.utils.lyrics_finder import LyricsFinder
from app.utils.story_generator import generate_story_with_keywords
import jieba
from collections import Counter

# 创建Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')


def analyze_lyrics_frequency(lyrics, top_n=5, min_length=2):
    """分析歌词中词语出现的频率"""
    # 过滤停用词（常见的无意义词语）
    stopwords = set([
        '的', '了', '和', '是', '在', '我', '有', '不', '这', '也', '你', '都',
        '我们', '你们', '他们', '她们', '它们', '那', '就', '都', '还', '要', '人',
        '啊', '哦', '呢', '吧', '呀', '哎', '噢', '喔', '哇', '嗯', '嘿', '哼',
        'la', 'oh', 'yeah', 'hey', 'baby', 'ah', 'ooh', 'na'
    ])

    # 使用jieba分词
    words = jieba.cut(lyrics)

    # 过滤掉长度过短和停用词
    filtered_words = [
        word for word in words
        if len(word.strip()) >= min_length and
           word.strip() not in stopwords and
           not word.strip().isdigit() and
           not all(ord(c) < 128 for c in word.strip())  # 过滤纯英文单词
    ]

    # 统计词频
    word_counts = Counter(filtered_words)

    # 获取出现频率最高的词
    most_common = word_counts.most_common(top_n)
    return most_common


@api_bp.route('/process-song', methods=['POST'])
def process_song():
    """处理歌曲信息，获取歌词、关键词和故事"""
    # 获取请求数据
    data = request.get_json()

    if not data or 'file_name' not in data:
        return jsonify({'error': 'Missing file_name parameter'}), 400

    file_name = data['file_name']

    # 从文件名提取歌手名和歌曲名
    # 假设格式为: "歌手名 - 歌曲名.mp3"
    match = re.match(r'(.+?)\s*-\s*(.+?)\.mp3$', file_name)

    if not match:
        return jsonify({'error': 'File name format not recognized (expected: "Artist - Song.mp3")'}), 400

    artist_name = match.group(1).strip()
    song_name = match.group(2).strip()

    # 获取数据库连接
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        # 检查歌曲是否已存在
        cursor.execute("SELECT id FROM songs WHERE artist_name = %s AND song_name = %s",
                       (artist_name, song_name))
        existing_song = cursor.fetchone()

        if existing_song:
            song_id = existing_song['id']

            # 获取现有数据返回
            cursor.execute("SELECT * FROM songs WHERE id = %s", (song_id,))
            song_data = cursor.fetchone()

            cursor.execute("SELECT keyword FROM keywords WHERE song_id = %s ORDER BY frequency DESC LIMIT 5",
                           (song_id,))
            keywords = [item['keyword'] for item in cursor.fetchall()]

            cursor.execute("SELECT story_content FROM stories WHERE song_id = %s ORDER BY created_at DESC LIMIT 1",
                           (song_id,))
            story = cursor.fetchone()

            return jsonify({
                'song_id': song_id,
                'song_name': song_data['song_name'],
                'artist_name': song_data['artist_name'],
                'lyrics': song_data['lyrics'],
                'keywords': keywords,
                'story': story['story_content'] if story else None
            })

        # 获取歌词
        finder = LyricsFinder()
        current_app.logger.info(f"Searching lyrics for: {song_name} by {artist_name}")
        lyrics_data = finder.search_lyrics(song_name, artist_name)

        if lyrics_data['lyrics'] == "未找到歌词":
            lyrics = "未找到歌词"
        else:
            lyrics = lyrics_data['lyrics']

        # 插入歌曲信息
        cursor.execute(
            "INSERT INTO songs (file_name, song_name, artist_name, lyrics) VALUES (%s, %s, %s, %s)",
            (file_name, song_name, artist_name, lyrics)
        )
        song_id = cursor.lastrowid

        # 提取关键词
        keywords = []
        if lyrics != "未找到歌词":
            current_app.logger.info(f"Analyzing keywords for song ID: {song_id}")
            word_frequency = analyze_lyrics_frequency(lyrics)

            for word, count in word_frequency:
                keywords.append(word)
                cursor.execute(
                    "INSERT INTO keywords (song_id, keyword, frequency) VALUES (%s, %s, %s)",
                    (song_id, word, count)
                )

        # 生成故事
        story = "无法生成故事，因为没有足够的关键词"
        if keywords:
            current_app.logger.info(f"Generating story for song ID: {song_id} with keywords: {keywords}")
            try:
                story = generate_story_with_keywords(keywords)
                cursor.execute(
                    "INSERT INTO stories (song_id, story_content) VALUES (%s, %s)",
                    (song_id, story)
                )
            except Exception as e:
                current_app.logger.error(f"Error generating story: {e}")
                story = f"生成故事时出错: {str(e)}"

        db.commit()

        return jsonify({
            'song_id': song_id,
            'song_name': song_name,
            'artist_name': artist_name,
            'lyrics': lyrics,
            'keywords': keywords,
            'story': story
        })

    except Exception as e:
        db.rollback()
        current_app.logger.error(f"Error processing song: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()


@api_bp.route('/songs', methods=['GET'])
def list_songs():
    """获取所有歌曲列表"""
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("SELECT id, song_name, artist_name, file_name, created_at FROM songs ORDER BY created_at DESC")
        songs = cursor.fetchall()
        return jsonify(songs)
    except Exception as e:
        current_app.logger.error(f"Error fetching songs: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()


@api_bp.route('/songs/<int:song_id>', methods=['GET'])
def get_song(song_id):
    """获取指定歌曲的详细信息"""
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        # 获取歌曲基本信息
        cursor.execute("SELECT * FROM songs WHERE id = %s", (song_id,))
        song = cursor.fetchone()

        if not song:
            return jsonify({'error': 'Song not found'}), 404

        # 获取关键词
        cursor.execute("SELECT keyword FROM keywords WHERE song_id = %s ORDER BY frequency DESC", (song_id,))
        keywords = [item['keyword'] for item in cursor.fetchall()]

        # 获取故事
        cursor.execute("SELECT story_content FROM stories WHERE song_id = %s ORDER BY created_at DESC LIMIT 1",
                       (song_id,))
        story = cursor.fetchone()

        # 组合数据
        result = {
            **song,
            'keywords': keywords,
            'story': story['story_content'] if story else None
        }

        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error fetching song details: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()