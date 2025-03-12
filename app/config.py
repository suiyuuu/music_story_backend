import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()


class Config:
    # 应用配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG') == '1'

    # 数据库配置
    DATABASE_HOST = os.environ.get('DATABASE_HOST') or 'localhost'
    DATABASE_USER = os.environ.get('DATABASE_USER') or 'root'
    DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD') or 'password'
    DATABASE_NAME = os.environ.get('DATABASE_NAME') or 'music_story_db'
    DATABASE_PORT = int(os.environ.get('DATABASE_PORT') or 3306)

    # 讯飞星火API配置
    SPARK_APP_ID = os.environ.get('SPARK_APP_ID') or '322c02e9'
    SPARK_API_KEY = os.environ.get('SPARK_API_KEY') or '2bb92aab75d460d926ab795bee8585eb'
    SPARK_API_SECRET = os.environ.get('SPARK_API_SECRET') or 'NjOyNmUwZjNiNzI2MmFiNGE3YTk5MTNm'
    SPARK_URL = os.environ.get('SPARK_URL') or 'wss://spark-api.xf-yun.com/v4.0/chat'
    SPARK_DOMAIN = os.environ.get('SPARK_DOMAIN') or 'generalv4.0'