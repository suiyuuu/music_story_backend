import mysql.connector
from mysql.connector import pooling
import click
from flask import current_app, g
import os
import pathlib


def get_db():
    """获取数据库连接"""
    if 'db' not in g:
        # 从应用配置获取数据库连接参数
        g.db = mysql.connector.connect(
            host=current_app.config['DATABASE_HOST'],
            user=current_app.config['DATABASE_USER'],
            password=current_app.config['DATABASE_PASSWORD'],
            database=current_app.config['DATABASE_NAME'],
            port=current_app.config['DATABASE_PORT']
        )
        # 设置自动提交
        g.db.autocommit = False

    return g.db


def close_db(e=None):
    """关闭数据库连接"""
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    """初始化数据库"""
    db = get_db()
    cursor = db.cursor()

    # 读取数据库初始化脚本
    with current_app.open_resource('static/sql/schema.sql') as f:
        cursor.execute(f.read().decode('utf8'))

    db.commit()
    cursor.close()


@click.command('init-db')
def init_db_command():
    """命令行初始化数据库"""
    init_db()
    click.echo('数据库初始化完成.')


def init_app_db(app):
    """初始化应用的数据库配置"""
    # 注册关闭连接的回调
    app.teardown_appcontext(close_db)

    # 注册命令行命令
    app.cli.add_command(init_db_command)

    # 定义初始化数据库的函数
    def initialize_database():
        try:
            # 尝试连接到MySQL服务器（不指定数据库）
            conn = mysql.connector.connect(
                host=app.config['DATABASE_HOST'],
                user=app.config['DATABASE_USER'],
                password=app.config['DATABASE_PASSWORD'],
                port=app.config['DATABASE_PORT']
            )
            cursor = conn.cursor()

            # 检查数据库是否存在
            cursor.execute(f"SHOW DATABASES LIKE '{app.config['DATABASE_NAME']}'")
            result = cursor.fetchone()

            # 如果数据库不存在，创建它
            if not result:
                app.logger.info(f"Creating database {app.config['DATABASE_NAME']}...")
                cursor.execute(
                    f"CREATE DATABASE {app.config['DATABASE_NAME']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                conn.commit()

                # 关闭当前连接
                cursor.close()
                conn.close()

                # 初始化数据库表
                with app.app_context():
                    init_db()
                app.logger.info("Database initialized successfully!")
            else:
                cursor.close()
                conn.close()
                app.logger.info(f"Database {app.config['DATABASE_NAME']} already exists.")

                # 检查表是否存在
                try:
                    with app.app_context():
                        db = get_db()
                        cursor = db.cursor()
                        cursor.execute("SHOW TABLES")
                        tables = cursor.fetchall()
                        cursor.close()

                        if not tables:
                            app.logger.info("Tables do not exist. Initializing database...")
                            init_db()
                except Exception as table_error:
                    app.logger.error(f"Error checking tables: {table_error}")
        except Exception as e:
            app.logger.error(f"Database initialization error: {e}")

    # 在应用上下文中执行初始化数据库的函数
    with app.app_context():
        try:
            initialize_database()
        except Exception as init_error:
            app.logger.error(f"Error during database initialization: {init_error}")