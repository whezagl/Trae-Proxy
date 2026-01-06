FROM python:3.9-slim

WORKDIR /app

# Replace apt sources with China mirrors
RUN echo "deb https://mirrors.aliyun.com/debian/ bullseye main non-free contrib" > /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian/ bullseye-updates main non-free contrib" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian-security bullseye-security main non-free contrib" >> /etc/apt/sources.list

# Install dependencies
RUN apt-get update && apt-get install -y \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Configure pip to use China mirrors
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/ && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY generate_certs.py .
COPY trae_proxy.py .
COPY trae_proxy_cli.py .
COPY config.yaml .

# Create certificate directory
RUN mkdir -p ca

# Expose port 8443 (HTTP mode, for use behind reverse proxy)
EXPOSE 8443

# Set startup command - HTTP mode (can be overridden by docker-compose.yml)
CMD ["python", "trae_proxy_cli.py", "start", "--http-mode", "--port", "8443"]