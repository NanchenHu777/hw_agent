#!/bin/bash

# SmartTutor 一键启动脚本
# 自动处理端口冲突，启动前后端服务

echo "🚀 SmartTutor 一键启动脚本"
echo "================================="

# 项目根目录
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SMARTTUTOR_DIR="$PROJECT_DIR/smarttutor"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}错误: $1 命令不存在${NC}"
        exit 1
    fi
}

# 检查端口占用并清理
cleanup_port() {
    local port=$1
    local name=$2

    echo -e "${YELLOW}检查 $name 端口 $port...${NC}"

    # 检查端口是否被占用
    if lsof -i :$port &> /dev/null; then
        echo -e "${YELLOW}端口 $port 被占用，正在清理...${NC}"

        # 获取占用进程的PID
        local pid=$(lsof -ti :$port)

        if [ ! -z "$pid" ]; then
            echo -e "${YELLOW}停止进程 PID: $pid${NC}"
            kill $pid 2>/dev/null

            # 等待进程完全停止
            sleep 2

            # 检查是否还有进程在占用
            if lsof -i :$port &> /dev/null; then
                echo -e "${RED}警告: 无法停止占用端口 $port 的进程${NC}"
                return 1
            else
                echo -e "${GREEN}端口 $port 已清理${NC}"
            fi
        fi
    else
        echo -e "${GREEN}端口 $port 可用${NC}"
    fi

    return 0
}

# 启动服务
start_service() {
    local name=$1
    local command=$2
    local log_file=$3

    echo -e "${YELLOW}启动 $name...${NC}"

    # 在后台启动服务
    cd "$SMARTTUTOR_DIR"
    source ../venv/bin/activate
    nohup $command > "$log_file" 2>&1 &

    local pid=$!
    echo -e "${GREEN}$name 已启动 (PID: $pid)${NC}"

    # 等待一下让服务启动
    sleep 3

    return $pid
}

# 检查服务是否启动成功
check_service() {
    local name=$1
    local url=$2
    local max_attempts=10
    local attempt=1

    echo -e "${YELLOW}检查 $name 启动状态...${NC}"

    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}$name 启动成功！${NC}"
            return 0
        fi

        echo -e "${YELLOW}等待 $name 启动... ($attempt/$max_attempts)${NC}"
        sleep 2
        ((attempt++))
    done

    echo -e "${RED}$name 启动失败${NC}"
    return 1
}

# 主函数
main() {
    # 检查必要命令
    check_command lsof
    check_command curl
    check_command nohup

    # 检查项目结构
    if [ ! -d "$SMARTTUTOR_DIR" ]; then
        echo -e "${RED}错误: 找不到 smarttutor 目录${NC}"
        exit 1
    fi

    if [ ! -f "$SMARTTUTOR_DIR/../venv/bin/activate" ]; then
        echo -e "${RED}错误: 找不到虚拟环境${NC}"
        exit 1
    fi

    # 创建日志目录
    mkdir -p "$PROJECT_DIR/logs"

    # 清理端口
    cleanup_port 8000 "后端API" || exit 1
    cleanup_port 7861 "前端界面" || exit 1

    # 启动后端
    start_service "后端API" "python -m app.main" "$PROJECT_DIR/logs/backend.log"
    backend_pid=$?

    # 检查后端启动
    check_service "后端API" "http://localhost:8000/health" || exit 1

    # 启动前端
    start_service "前端界面" "python -m ui.gradio_app" "$PROJECT_DIR/logs/frontend.log"
    frontend_pid=$?

    # 检查前端启动
    check_service "前端界面" "http://localhost:7861" || exit 1

    echo ""
    echo -e "${GREEN}🎉 SmartTutor 启动成功！${NC}"
    echo "================================="
    echo -e "${GREEN}📱 前端界面: http://localhost:7861${NC}"
    echo -e "${GREEN}🔧 API 文档: http://localhost:8000/docs${NC}"
    echo -e "${GREEN}💚 健康检查: http://localhost:8000/health${NC}"
    echo ""
    echo -e "${YELLOW}进程PID:${NC}"
    echo "  后端: $backend_pid"
    echo "  前端: $frontend_pid"
    echo ""
    echo -e "${YELLOW}日志文件:${NC}"
    echo "  后端: $PROJECT_DIR/logs/backend.log"
    echo "  前端: $PROJECT_DIR/logs/frontend.log"
    echo ""
    echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}"

    # 等待用户中断
    trap "echo -e '\n${YELLOW}正在停止服务...${NC}'; kill $backend_pid $frontend_pid 2>/dev/null; exit 0" INT
    wait
}

# 运行主函数
main "$@"