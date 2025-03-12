import json
import time
import base64
import datetime
import hashlib
import hmac
import websocket
import ssl
import _thread as thread
from urllib.parse import urlparse
from wsgiref.handlers import format_date_time
from time import mktime
from urllib.parse import urlencode
from flask import current_app


class Ws_Param(object):
    """生成讯飞星火API请求URL的参数类"""

    def __init__(self, APPID, APIKey, APISecret, spark_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.host = urlparse(spark_url).netloc
        self.path = urlparse(spark_url).path
        self.spark_url = spark_url

    def create_url(self):
        """生成鉴权url"""
        # 生成RFC1123格式的时间戳
        now = datetime.datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"

        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'

        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        # 拼接鉴权参数，生成url
        url = self.spark_url + '?' + urlencode(v)
        return url


def gen_params(appid, query, domain, temperature=0.8):
    """
    通过appid和用户的提问来生成请参数
    """
    data = {
        "header": {
            "app_id": appid,
            "uid": "12345"
        },
        "parameter": {
            "chat": {
                "domain": domain,
                "temperature": temperature,
                "max_tokens": 2048,
                "auditing": "default"
            }
        },
        "payload": {
            "message": {
                "text": [{"role": "user", "content": query}]
            }
        }
    }
    return data


def generate_story_with_keywords(keywords):
    """使用讯飞星火API根据关键词生成故事"""
    # 从应用配置获取API信息
    APP_ID = current_app.config['SPARK_APP_ID']
    API_KEY = current_app.config['SPARK_API_KEY']
    API_SECRET = current_app.config['SPARK_API_SECRET']
    SPARK_URL = current_app.config['SPARK_URL']
    DOMAIN = current_app.config['SPARK_DOMAIN']

    # 用于存储结果的变量
    story_content = ""
    story_completed = False
    error_message = None

    # WebSocket回调函数
    def on_message(ws, message):
        nonlocal story_content, story_completed
        try:
            data = json.loads(message)
            code = data['header']['code']
            if code != 0:
                current_app.logger.error(f'Request error: {code}, {data}')
                ws.close()
            else:
                choices = data["payload"]["choices"]
                status = choices["status"]
                content = choices["text"][0]["content"]
                story_content += content
                current_app.logger.debug(f"Received content: {content[:50]}...")
                if status == 2:
                    current_app.logger.info("Story generation completed")
                    story_completed = True
                    ws.close()
        except Exception as e:
            current_app.logger.error(f"Error processing message: {e}")
            current_app.logger.error(f"Received message: {message}")
            ws.close()

    def on_error(ws, error):
        nonlocal error_message
        current_app.logger.error(f"Error: {error}")
        error_message = str(error)

    def on_close(ws, *args):
        nonlocal story_completed
        current_app.logger.info("Connection closed")
        story_completed = True

    def on_open(ws):
        def run(*args):
            try:
                # 创建请求的prompt
                query = f"请使用以下关键词创作一个有创意的短篇故事：{', '.join(keywords)}。故事应该包含所有这些关键词，并且要有一个有趣的情节和角色。故事长度控制在800-1200字。"
                current_app.logger.info(f"Generating story with keywords: {keywords}")

                data = json.dumps(gen_params(APP_ID, query, DOMAIN))
                ws.send(data)
            except Exception as e:
                current_app.logger.error(f"Error in on_open: {e}")
                ws.close()

        thread.start_new_thread(run, ())

    try:
        # 创建WebSocket连接参数
        wsParam = Ws_Param(APP_ID, API_KEY, API_SECRET, SPARK_URL)
        websocket.enableTrace(False)  # 线上模式不要启用trace
        wsUrl = wsParam.create_url()

        current_app.logger.info(f"Connecting to {SPARK_URL}")

        # 创建WebSocket连接
        ws = websocket.WebSocketApp(
            wsUrl,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )

        # 启动WebSocket连接，使用SSL但不验证证书
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

        # 等待故事完成或超时
        timeout = 60  # 最多等待60秒
        start_time = time.time()
        while not story_completed:
            time.sleep(0.1)
            if time.time() - start_time > timeout:
                current_app.logger.error("Story generation timed out")
                break

    except Exception as e:
        current_app.logger.error(f"Error generating story: {e}")
        return f"生成故事时出错: {str(e)}"

    # 检查是否有错误或内容为空
    if error_message:
        return f"生成故事时出错: {error_message}"

    if not story_content:
        return "无法生成故事，请检查API配置或网络连接"

    # 返回生成的故事
    return story_content