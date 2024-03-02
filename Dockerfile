# 使用官方 Python 基础镜像
FROM python:3.8-slim

# 设置工作目录
WORKDIR /app

# 将依赖安装需求复制到容器中
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 将当前目录下的所有文件复制到容器中
COPY . .

# 运行 Uvicorn 服务器
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
