from flask import Flask, render_template_string
import requests

app = Flask(__name__)

# 一个极简的 HTML 模板，直接在字符串里定义
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Chollo-Radar-ES 本地看板</title></head>
<body style="font-family: sans-serif; padding: 20px;">
    <h1>🔥 Chollo-Radar-ES 实时监控看板</h1>
    <div id="content">{{ deals | safe }}</div>
</body>
</html>
"""

@app.route('/')
def index():
    # 这里通过 GitHub API 获取最新的汇总 Issue 内容
    # 逻辑：请求 API 获取最新 Issue 内容作为展示
    return render_template_string(HTML_TEMPLATE, deals="正在加载最新监控数据...")

if __name__ == '__main__':
    app.run(port=5000)