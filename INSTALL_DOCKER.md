# 🐳 安装 Docker Desktop

## macOS

### 方式 1：直接下载（推荐）
```bash
# 访问官网下载
https://www.docker.com/products/docker-desktop

# 下载后拖入 Applications 文件夹
# 然后在终端验证
docker --version
docker-compose --version
```

### 方式 2：Homebrew
```bash
brew install docker
brew install docker-compose
```

## Linux (Ubuntu/Debian)

```bash
# 更新包管理器
sudo apt update

# 安装 Docker
sudo apt install docker.io docker-compose

# 验证
docker --version
docker-compose --version

# 允许不用 sudo 运行 docker（可选）
sudo usermod -aG docker $USER
newgrp docker
```

## Windows

### 使用 WSL2（推荐）
```bash
# 1. 安装 WSL2
# https://docs.microsoft.com/en-us/windows/wsl/install

# 2. 安装 Docker Desktop for Windows
# https://www.docker.com/products/docker-desktop

# 3. 在 WSL2 终端验证
docker --version
docker-compose --version
```

## 验证安装

```bash
# 应该都有输出
docker --version
docker-compose --version

# 验证 Docker 能正常运行
docker run hello-world
# 应该看到: Hello from Docker!

# 验证 Docker Compose
docker-compose --version
# 应该看到: Docker Compose version ...
```

## 遇到问题？

| 问题 | 解决方案 |
|------|--------|
| `docker: command not found` | Docker 未安装或未添加到 PATH |
| `docker-compose: command not found` | 安装 docker-compose: `brew install docker-compose` |
| `Permission denied` | 需要 `sudo`，或添加用户到 docker 组 |
| Docker daemon 未运行 | macOS：启动 Docker Desktop app |

