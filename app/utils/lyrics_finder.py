import requests
import json
import re
import random
from urllib.parse import quote
from flask import current_app

class LyricsFinder:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        }

    def search_netease(self, song_name, artist_name=None):
        """从网易云音乐搜索歌词"""
        try:
            current_app.logger.info("Searching Netease Music...")
            query = song_name
            if artist_name:
                query = f"{song_name} {artist_name}"

            # 先搜索歌曲ID
            search_url = f"https://music.163.com/api/search/get?s={quote(query)}&type=1&limit=10"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            search_data = response.json()

            if 'result' not in search_data or 'songs' not in search_data['result'] or not search_data['result']['songs']:
                return None

            songs = search_data['result']['songs']
            song_id = songs[0]['id']  # 获取第一首歌的ID

            # 获取歌词
            lyric_url = f"https://music.163.com/api/song/lyric?id={song_id}&lv=1&kv=1&tv=-1"
            response = requests.get(lyric_url, headers=self.headers, timeout=10)
            lyric_data = response.json()

            if 'lrc' not in lyric_data or 'lyric' not in lyric_data['lrc']:
                return None

            lyrics = lyric_data['lrc']['lyric']

            # 处理歌词格式 - 移除时间标签 [00:00.000]
            cleaned_lyrics = re.sub(r'\[\d{2}:\d{2}.\d{2,3}\]', '', lyrics)

            # 添加标题和来源信息
            song_title = songs[0]['name']
            artist = songs[0]['artists'][0]['name']

            result = f"《{song_title}》 - {artist}\n"
            result += f"来源: 网易云音乐\n\n"
            result += cleaned_lyrics.strip()

            return {
                'title': song_title,
                'artist': artist,
                'source': '网易云音乐',
                'lyrics': cleaned_lyrics.strip(),
                'formatted': result
            }

        except Exception as e:
            current_app.logger.error(f"Netease Music error: {e}")
            return None

    def search_qq_music(self, song_name, artist_name=None):
        """从QQ音乐搜索歌词"""
        try:
            current_app.logger.info("Searching QQ Music...")
            query = song_name
            if artist_name:
                query = f"{song_name} {artist_name}"

            # 搜索歌曲
            search_url = f"https://c.y.qq.com/soso/fcgi-bin/client_search_cp?w={quote(query)}&format=json&p=1&n=10"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            search_data = response.json()

            if 'data' not in search_data or 'song' not in search_data['data'] or 'list' not in search_data['data']['song'] or not search_data['data']['song']['list']:
                return None

            song_list = search_data['data']['song']['list']
            song = song_list[0]  # 获取第一首歌

            song_mid = song['songmid']

            # 获取歌词
            lyric_url = f"https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_new.fcg?songmid={song_mid}&format=json&nobase64=1"
            headers = self.headers.copy()
            headers['Referer'] = 'https://y.qq.com/'  # QQ音乐需要Referer

            response = requests.get(lyric_url, headers=headers, timeout=10)
            lyric_data = response.json()

            if 'lyric' not in lyric_data:
                return None

            lyrics = lyric_data['lyric']

            # 处理歌词格式 - 移除HTML实体和时间标签
            lyrics = lyrics.replace('&#58;', ':').replace('&#46;', '.')
            cleaned_lyrics = re.sub(r'\[\d{2}:\d{2}.\d{2,3}\]', '', lyrics)
            cleaned_lyrics = re.sub(r'&#\d+;', '', cleaned_lyrics)

            # 添加标题和来源信息
            song_title = song['songname']
            artist = song['singer'][0]['name']

            result = f"《{song_title}》 - {artist}\n"
            result += f"来源: QQ音乐\n\n"
            result += cleaned_lyrics.strip()

            return {
                'title': song_title,
                'artist': artist,
                'source': 'QQ音乐',
                'lyrics': cleaned_lyrics.strip(),
                'formatted': result
            }

        except Exception as e:
            current_app.logger.error(f"QQ Music error: {e}")
            return None

    def search_kugou(self, song_name, artist_name=None):
        """从酷狗音乐搜索歌词"""
        try:
            current_app.logger.info("Searching Kugou Music...")
            query = song_name
            if artist_name:
                query = f"{song_name} {artist_name}"

            # 搜索歌曲
            search_url = f"https://songsearch.kugou.com/song_search_v2?keyword={quote(query)}&page=1&pagesize=10"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            search_data = response.json()

            if ('data' not in search_data or 'lists' not in search_data['data'] or
                    not search_data['data']['lists']):
                return None

            song_list = search_data['data']['lists']
            song = song_list[0]  # 获取第一首歌

            # 酷狗的API需要几个参数
            hash_value = song['FileHash']
            album_id = song.get('AlbumID', '')

            # 获取歌曲信息和歌词
            song_info_url = f"https://wwwapi.kugou.com/yy/index.php?r=play/getdata&hash={hash_value}&album_id={album_id}"
            response = requests.get(song_info_url, headers=self.headers, timeout=10)
            song_data = response.json()

            if ('data' not in song_data or 'lyrics' not in song_data['data'] or
                    not song_data['data']['lyrics']):
                return None

            lyrics = song_data['data']['lyrics']

            # 处理歌词格式 - 移除时间标签
            cleaned_lyrics = re.sub(r'\[\d{2}:\d{2}.\d{2,3}\]', '', lyrics)

            # 添加标题和来源信息
            song_title = song_data['data']['song_name']
            artist = song_data['data']['author_name']

            result = f"《{song_title}》 - {artist}\n"
            result += f"来源: 酷狗音乐\n\n"
            result += cleaned_lyrics.strip()

            return {
                'title': song_title,
                'artist': artist,
                'source': '酷狗音乐',
                'lyrics': cleaned_lyrics.strip(),
                'formatted': result
            }

        except Exception as e:
            current_app.logger.error(f"Kugou Music error: {e}")
            return None

    def search_migu(self, song_name, artist_name=None):
        """从咪咕音乐搜索歌词"""
        try:
            current_app.logger.info("Searching Migu Music...")
            query = song_name
            if artist_name:
                query = f"{song_name} {artist_name}"

            # 搜索歌曲
            search_url = f"https://m.music.migu.cn/migu/remoting/scr_search_tag?keyword={quote(query)}&type=2&rows=20&pgc=1"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            search_data = response.json()

            if 'musics' not in search_data or not search_data['musics']:
                return None

            song = search_data['musics'][0]  # 获取第一首歌
            song_id = song['copyrightId']

            # 获取歌词
            lyric_url = f"https://music.migu.cn/v3/api/music/audioPlayer/getLyric?copyrightId={song_id}"
            response = requests.get(lyric_url, headers=self.headers, timeout=10)
            lyric_data = response.json()

            if 'lyric' not in lyric_data or not lyric_data['lyric']:
                return None

            lyrics = lyric_data['lyric']

            # 处理歌词格式 - 移除时间标签
            cleaned_lyrics = re.sub(r'\[\d{2}:\d{2}.\d{2,3}\]', '', lyrics)

            # 添加标题和来源信息
            song_title = song['title']
            artist = song['singer']

            result = f"《{song_title}》 - {artist}\n"
            result += f"来源: 咪咕音乐\n\n"
            result += cleaned_lyrics.strip()

            return {
                'title': song_title,
                'artist': artist,
                'source': '咪咕音乐',
                'lyrics': cleaned_lyrics.strip(),
                'formatted': result
            }

        except Exception as e:
            current_app.logger.error(f"Migu Music error: {e}")
            return None

    def search_lyrics(self, song_name, artist_name=None):
        """搜索所有平台获取歌词"""
        # 随机选择搜索顺序，避免总是请求同一个平台
        platforms = [
            self.search_netease,
            self.search_qq_music,
            self.search_kugou,
            self.search_migu
        ]
        random.shuffle(platforms)

        # 尝试每个平台
        for platform in platforms:
            lyrics_data = platform(song_name, artist_name)
            if lyrics_data:
                return lyrics_data

        # 所有平台都失败了
        return {
            'title': song_name,
            'artist': artist_name if artist_name else "未知",
            'source': '未知',
            'lyrics': "未找到歌词",
            'formatted': "未找到歌词。请尝试提供歌手名称以获得更准确的结果。"
        }