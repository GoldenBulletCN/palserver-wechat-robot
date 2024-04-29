# palserver-wechat-robot

palserver-wechat-robot是一款运维幻兽帕鲁服务器的开源微信群聊机器人，基于微信机器人工具[WeChatferry](https://github.com/lich0821/WeChatFerry)实现，因此**机器人需运行在Windows服务器上（幻兽帕鲁服务器仍运行在Linux服务器上）**。

目前支持以下群聊运维功能：

【0】强制重启服务器（运维管理员特权指令）

【1】查看服务器信息

【2】更新服务器

【3】重启服务器

【4】查询在线玩家

【5】广播消息（示例：5 全民制作人们大家好）

【6】踢出玩家 （示例：6 玩家id）

【7】封禁玩家（示例：7 玩家id）

【8】解封玩家（示例：8 玩家id）



## 环境要求

操作系统：Windows >= 10（推荐Windows Server 2022）

运行环境：Python >= 3.10（推荐Python 3.12）



## 快速开始

1. 上传Linux运维脚本

   在安装好幻兽帕鲁服务(PalServer)的服务器**用户目录**中上传Linux运维脚本run.sh，根据实际情况修改run.sh脚本中的steam路径和PalServer配置文件路径（以下示例为Debian 12.5的默认路径）；

   ```shell
   # 定义steam路径
   steam_path=~/.steam/steam
   # 定义PalServer配置文件路径
   settings_file="${steam_path}/steamapps/common/PalServer/Pal/Saved/Config/LinuxServer/PalWorldSettings.ini"
   ```

   赋予脚本可执行权限：

   ```cmd
   chmod +x ~/run.sh
   ```

   

2. 安装Wcferry微信客户端并登录微信

   到[WeChatFerry-v3.9.2.23-Release](https://github.com/lich0821/WeChatFerry/releases/tag/v39.0.14)下载**WeChatSetup-3.9.2.23.exe**并安装运行，使用微信小号扫码登录微信，同时**关闭微信自动更新**。

3. 安装依赖

   ```cmd
   # 升级 pip
   python -m pip install -U pip
   # 创建隔离的venv环境并激活（推荐）
   python -m venv .venv
   source .venv/Scripts/activate
   # 安装必要依赖
   pip install -r requirements.txt
   ```

3. 编辑main.py文件以下内容以配置基本参数

   ```python
   # 配置PalServer所在服务器的地址、ssh用户名、ssh密码
   pal_server = PalServer(host="192.168.x.x", ssh_user="steam",ssh_connect_kwargs={'password': "xxxxxx"})
   # 配置支持使用特权指令的运维人员微信号
   PalBot(pal_server, ["wxid_xxxxxxxxxxxx", "wxid_xxxxxxxxxxxx"]).listen_for_msg()
   ```

4. 运行项目

   ```cmd
   python main.py
   ```



**在微信群内@你的微信机器人试试吧**