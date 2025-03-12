from flask import Flask
from flask_cors import CORS
import os
from app.utils.database import init_app_db
from app.config import Config


def create_app(test_config=None):
    # 创建并配置app
    app = Flask(__name__, instance_relative_config=True)

    # 启用CORS，允许Android客户端访问
    CORS(app)

    # 加载配置
    if test_config is None:
        app.config.from_object(Config)
    else:
        app.config.from_mapping(test_config)

    # 确保实例文件夹存在
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # 初始化数据库
    init_app_db(app)

    # 注册路由
    from app.routes import api_bp
    app.register_blueprint(api_bp)

    @app.route('/health')
    def health_check():
        return {'status': 'healthy'}

    return app