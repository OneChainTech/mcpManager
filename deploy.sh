#!/bin/bash

# MCP金融服务管理平台部署脚本
# 用于生产环境部署，只包含主服务相关功能

set -e

# 日志函数
log_info() {
    echo "[INFO] $1"
}

log_success() {
    echo "[SUCCESS] $1"
}

log_warning() {
    echo "[WARNING] $1"
}

log_error() {
    echo "[ERROR] $1"
}

# 检查Python版本
check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装，请先安装Python 3.8+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log_info "检测到Python版本: $PYTHON_VERSION"
    
    # 检查版本是否 >= 3.8
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        log_success "Python版本检查通过"
    else
        log_error "需要Python 3.8或更高版本"
        exit 1
    fi
}

# 创建虚拟环境
create_venv() {
    if [ ! -d "venv" ]; then
        log_info "创建虚拟环境..."
        python3 -m venv venv
        log_success "虚拟环境创建完成"
    else
        log_info "虚拟环境已存在"
    fi
}

# 激活虚拟环境
activate_venv() {
    log_info "激活虚拟环境..."
    source venv/bin/activate
    log_success "虚拟环境已激活"
}

# 安装依赖
install_deps() {
    log_info "检查依赖包..."
    if [ ! -f "requirements.txt" ]; then
        log_error "requirements.txt 文件不存在"
        exit 1
    fi
    
    # 检查是否需要安装依赖
    if [ ! -f "venv/lib/python*/site-packages/fastapi" ]; then
        log_info "安装依赖包..."
        pip install -r requirements.txt
        log_success "依赖包安装完成"
    else
        log_info "依赖包已安装"
    fi
}

# 检查端口占用
check_ports() {
    local main_port=${PORT:-8000}
    
    log_info "检查端口占用..."
    
    if lsof -i :$main_port >/dev/null 2>&1; then
        log_warning "端口 $main_port 已被占用"
        lsof -i :$main_port
    else
        log_success "端口 $main_port 可用"
    fi
}

# 启动主服务
start_main_service() {
    log_info "启动MCP服务管理器..."
    log_info "主服务地址: http://127.0.0.1:${PORT:-8000}"
    log_info "管理界面: http://127.0.0.1:${PORT:-8000}/admin"
    
    # 后台启动主服务
    nohup python main.py > logs/main.log 2>&1 &
    echo $! > .main.pid
    
    log_success "主服务已启动 (PID: $(cat .main.pid))"
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    
    if [ -f ".main.pid" ]; then
        local main_pid=$(cat .main.pid)
        if kill -0 $main_pid 2>/dev/null; then
            kill $main_pid
            log_success "主服务已停止 (PID: $main_pid)"
        else
            log_warning "主服务进程不存在"
        fi
        rm -f .main.pid
    fi
}

# 检查服务状态
check_status() {
    log_info "检查服务状态..."
    
    if [ -f ".main.pid" ]; then
        local main_pid=$(cat .main.pid)
        if kill -0 $main_pid 2>/dev/null; then
            log_success "主服务运行中 (PID: $main_pid)"
        else
            log_error "主服务未运行"
        fi
    else
        log_warning "主服务PID文件不存在"
    fi
}

# 创建日志目录
create_logs_dir() {
    if [ ! -d "logs" ]; then
        mkdir -p logs
        log_info "创建日志目录"
    fi
}

# 环境配置
setup() {
    log_info "开始环境配置..."
    check_python
    create_venv
    activate_venv
    install_deps
    create_logs_dir
    log_success "环境配置完成"
}

# 启动服务
start() {
    log_info "启动服务..."
    setup
    check_ports
    start_main_service
    log_success "服务启动完成"
    
    echo ""
    echo "🌐 服务访问地址:"
    echo "   主服务: http://127.0.0.1:${PORT:-8000}"
    echo "   管理界面: http://127.0.0.1:${PORT:-8000}/admin"
    echo "   健康检查: http://127.0.0.1:${PORT:-8000}/health"
    echo ""
    echo "📝 查看日志:"
    echo "   主服务: tail -f logs/main.log"
    echo ""
}

# 重启服务
restart() {
    log_info "重启服务..."
    stop_services
    sleep 2
    start
}

# 显示帮助
show_help() {
    echo "MCP金融服务管理平台部署脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start     启动服务 (默认)"
    echo "  stop      停止服务"
    echo "  restart   重启服务"
    echo "  status    检查服务状态"
    echo "  setup     仅进行环境配置"
    echo "  help      显示此帮助信息"
    echo ""
    echo "环境变量:"
    echo "  PORT       主服务端口 (默认: 8000)"
    echo "  UPSTREAM_TIMEOUT 上游服务超时时间 (默认: 15秒)"
    echo ""
}

# 主函数
main() {
    local command=${1:-start}
    
    case $command in
        start)
            start
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart
            ;;
        status)
            check_status
            ;;
        setup)
            setup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
