#!/bin/bash

# 定义通用日志函数，日志输出包含时间戳
log() {
    # 使用date命令获取当前时间，格式为YYYY-MM-DD HH:MM:SS
    echo "$(date "+%Y-%m-%d %H:%M:%S") $1"
}

# 检查当前执行用户是否为steam，如果不是，则报错退出
if [ "$(whoami)" != "steam" ]; then
    log "错误：此脚本必须由用户'steam'执行"
    exit 1
fi

# 定义steam路径
steam_path=~/.steam/steam
# 定义进程名称
process_name="PalServer-Linux-Shipping"
# 定义PalServer配置文件路径
settings_file="${steam_path}/steamapps/common/PalServer/Pal/Saved/Config/LinuxServer/PalWorldSettings.ini"


# 检查进程是否存在的函数
check_process() {
    pgrep -f "${process_name}" > /dev/null
    return $?
}

# 启动进程的函数
start_process() {
    if check_process; then
        log "PalServer已经启动"
    else
        log "开始启动PalServer..."
        nohup "${steam_path}/steamapps/common/PalServer/PalServer.sh" -publiclobby -useperfthreads -NoAsyncLoadingThread -UseMultithreadForDS >> ~/PalServer.log 2>&1 &
        sleep 20
        if check_process; then
            log "PalServer启动成功"
        else
            log "错误：PalServer启动失败"
            exit 1
        fi
    fi
}

# 停止进程的函数
stop_process() {
    if check_process; then
        log "开始停止PalServer..."
        # 获取REST API的启用状态
        rest_api_enabled=$(grep -v '^;' "$settings_file" | grep "RESTAPIEnabled" | sed -e "s/.*RESTAPIEnabled=\(True\|False\).*/\1/")
        if [ "$rest_api_enabled" != "True" ]; then
            log "REST API未启用，无法请求关闭PalServer"
            exit 1
        fi
        # 获取REST API的端口
        rest_api_port=$(grep -v '^;' "$settings_file" | grep "RESTAPIPort" | sed -e "s/.*RESTAPIPort=\([0-9]*\).*/\1/")
        if [ -z "${rest_api_port}" ]; then
            log "获取REST API端口失败，无法请求关闭PalServer"
            exit 1
        fi
        # 获取REST API的鉴权密码
        admin_password=$(grep -v '^;' "$settings_file" | grep "AdminPassword" | sed -e "s/.*AdminPassword=\"\([^\"]*\)\".*/\1/")
        if [ -z "${admin_password}" ]; then
            log "获取REST API鉴权密码失败，无法请求关闭PalServer"
            exit 1
        fi
        # 生成Http Basic鉴权请求头
        auth=$(echo -n "admin:${admin_password}" | base64)
        # 请求REST API的shutdown接口
        api_response=$(curl -L -X POST "http://localhost:${rest_api_port}/v1/api/shutdown" \
            -H 'Content-Type: application/json' \
            -H "Authorization: Basic ${auth}" \
            --data-raw '{
            "waittime": 10,
            "message": "Server will shutdown in 10 seconds."
            }')
        if [ $? -ne 0 ]; then
            echo "错误：无法发送关闭请求至PalServer"
            exit 1
        fi
        echo "请求PalServer关闭接口：${api_response}"
        sleep 120
        if check_process; then
            log "错误：无法停止PalServer"
            exit 1
        else
            log "PalServer已成功停止"
        fi
    else
        log "PalServer已停止"
    fi
}

# 强制停止进程的函数
kill_process() {
    if check_process; then
        log "开始停止PalServer..."
        pkill -f -SIGTERM "${process_name}"
        sleep 60
        if check_process; then
            log "错误：无法停止PalServer，执行强制停止"
            pkill -f -SIGKILL "${process_name}"
            sleep 70
            if check_process; then
                log "强制停止PalServer失败"
                exit 1
            else
                log "强制停止PalServer完成"
            fi
        else
            # 等待端口状态超时清理
            sleep 60
            log "PalServer已成功停止"
        fi
    else
        log "PalServer已停止"
    fi
}

# 更新服务器的函数
update_server() {
    if check_process; then
        log "错误：PalServer未停止，无法更新"
        exit 1
    else
        ## 更新并拷贝steamclient.so依赖到~/.steam/sdk64/目录
        log "开始更新Steamworks SDK Redist(1007)..."
        steamcmd +login anonymous +app_update 1007 +quit
        mkdir -p ~/.steam/sdk64/
        cp "${steam_path}/steamapps/common/Steamworks\ SDK\ Redist/linux64/steamclient.so" ~/.steam/sdk64/
        log "Steamworks SDK Redist(1007)更新完成"

        ## 更新PalServer
        log "开始更新PalServer..."
        steamcmd +login anonymous +app_update 2394010 validate +quit
        log "PalServer更新完成"
    fi
}

# 输出帮助信息的函数
show_help() {
    echo "用法： ./run.sh [选项]"
    echo "选项:"
    echo "  -start    启动PalServer"
    echo "  -stop     停止PalServer"
    echo "  -kill     强制停止PalServer"
    echo "  -restart  重启PalServer"
    echo "  -check    检查PalServer状态"
    echo "  -update   更新PalServer"
    echo "  -settings 显示PalServer配置"
    echo "  -help     显示帮助信息"
}

# 解析命令行参数
case $1 in
    -start)
        start_process
        ;;
    -stop)
        stop_process
        ;;
    -kill)
        kill_process
        ;;
    -restart)
        stop_process
        start_process
        ;;
    -check)
        if check_process; then
            log "PalServer正在运行"
        else
            log "PalServer未运行"
        fi
        ;;
    -update)
        update_server
        ;;
    -settings)
        cat $settings_file
        ;;
    -help)
        show_help
        ;;
    *)
        echo "无效参数。使用 '-help' 查看用法"
        exit 1
        ;;
esac
