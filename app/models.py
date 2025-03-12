class Song:
    """歌曲模型类"""

    def __init__(self, id=None, file_name=None, song_name=None, artist_name=None,
                 lyrics=None, created_at=None):
        self.id = id
        self.file_name = file_name
        self.song_name = song_name
        self.artist_name = artist_name
        self.lyrics = lyrics
        self.created_at = created_at
        self.keywords = []  # 关联的关键词
        self.story = None  # 关联的故事

    def to_dict(self):
        """转换为字典，用于JSON响应"""
        return {
            'id': self.id,
            'file_name': self.file_name,
            'song_name': self.song_name,
            'artist_name': self.artist_name,
            'lyrics': self.lyrics,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'keywords': [k.keyword for k in self.keywords] if self.keywords else [],
            'story': self.story.story_content if self.story else None
        }


class Keyword:
    """关键词模型类"""

    def __init__(self, id=None, song_id=None, keyword=None, frequency=None):
        self.id = id
        self.song_id = song_id
        self.keyword = keyword
        self.frequency = frequency


class Story:
    """故事模型类"""

    def __init__(self, id=None, song_id=None, story_content=None, created_at=None):
        self.id = id
        self.song_id = song_id
        self.story_content = story_content
        self.created_at = created_at