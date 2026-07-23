FROM python:3.11-slim

WORKDIR /app

# 使用清华 pip 镜像加速
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# Install only the minimal deps needed for the proxy routes
RUN pip install --no-cache-dir \
    fastapi uvicorn[standard] httpx

COPY app /app/app

ENV PYTHONPATH="/app"
ENV DBGPT_BASE="http://dbgpt:5670"

EXPOSE 8100

CMD ["uvicorn", "app.main_minimal:app", "--host", "0.0.0.0", "--port", "8100"]
