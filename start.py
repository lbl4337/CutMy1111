#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import webbrowser
import socket
import threading
import time


def get_local_ip():
    """获取本机IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'


def open_browser():
    """延迟打开浏览器"""
    time.sleep(1.5)
    webbrowser.open('http://127.0.0.1:5000')


if __name__ == '__main__':
    # 检查依赖
    try:
        import flask
        import flask_sqlalchemy
        import flask_cors
    except ImportError:
        print('\n正在安装依赖包...')
        os.system('pip install -r requirements.txt')
        print('\n依赖安装完成！\n')

    local_ip = get_local_ip()

    print('\n' + '=' * 60)
    print('  🌿 CutMy 木材定制报价系统')
    print('=' * 60)
    print(f'  ✅ 服务启动中...')
    print(f'  📱 本机访问: http://127.0.0.1:5000')
    print(f'  🌐 局域网访问: http://{local_ip}:5000')
    print('  📋 订单管理: http://127.0.0.1:5000/admin')
    print('  ⚠️  请确保防火墙允许端口 5000 访问')
    print('=' * 60)
    print('  💡 按 Ctrl+C 停止服务\n')

    # 自动打开浏览器
    threading.Thread(target=open_browser, daemon=True).start()

    # 启动应用
    from app import app

    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)