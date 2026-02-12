"""Flask 扩展实例

将扩展实例集中在此模块，避免 `from app import db` 在 `python app.py`
启动时因 __main__ 与 app 模块身份不同而创建两个 SQLAlchemy 实例的问题。
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()
