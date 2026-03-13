#!/bin/bash

# SmartTutor 停止脚本
# 停止所有相关进程

echo "🛑 SmartTutor 停止脚本"
echo "========================"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 查找并停止进程
stop_processes() {
    local pattern=$1
    local name=$2

    echo -e "${YELLOW}查找 $name 进程...${NC}"

    # 获取进程PID
    local pids=$(ps aux | grep "$pattern" | grep -v grep | awk '{print $2}')

    if [ -z "$pids" ]; then
        echo -e "${GREEN}没有找到 $name 进程${NC}"
        return 0
    fi

    echo -e "${YELLOW}找到进程PID: $pids${NC}"

    # 停止进程
    echo "$pids" | xargs kill 2>/dev/null

    # 等待进程停止
    sleep 2

    # 检查是否还有进程在运行
    local remaining=$(ps aux | grep "$pattern" | grep -v grep | wc -l)
    if [ $remaining -eq 0 ]; then
        echo -e "${GREEN}$name 进程已停止${NC}"
    else
        echo -e "${RED}警告: 部分 $name 进程可能未完全停止${NC}"
    fi
}

# 主函数
main() {
    echo -e "${YELLOW}正在停止 SmartTutor 服务...${NC}"

    # 停止前端
    stop_processes "gradio_app" "前端界面"

    # 停止后端
    stop_processes "app.main" "后端API"

    # 检查端口是否已释放
    echo -e "${YELLOW}检查端口状态...${NC}"

    if lsof -i :8000 &> /dev/null; then
        echo -e "${RED}端口 8000 仍被占用${NC}"
    else
        echo -e "${GREEN}端口 8000 已释放${NC}"
    fi

    if lsof -i :7861 &> /dev/null; then
        echo -e "${RED}端口 7861 仍被占用${NC}"
    else
        echo -e "${GREEN}端口 7861 已释放${NC}"
    fi

    echo -e "${GREEN}SmartTutor 服务已停止${NC}"
}

# 运行主函数
main "$@"