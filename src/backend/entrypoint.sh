#!/bin/sh
# 等待数据库就绪后执行迁移，然后启动应用
flask db upgrade
exec python app.py
