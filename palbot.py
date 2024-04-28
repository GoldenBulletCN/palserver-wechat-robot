from wcferry import Wcf
from palworld import PalServer
from queue import Empty
from threading import Thread
from typing import List
import logging


class PalBot:

    def _process_request(self, msg):
        # 移除消息中的@群昵称
        my_name = self.wcf.get_alias_in_chatroom(self.wcf.get_self_wxid(), msg.roomid)
        request = str(msg.content).replace("@" + my_name, "")
        # 移除两端空格以及手机端@消息中包含的特殊字符"\u2005"(表示四分之一空格)
        request = request.replace("\u2005", "").strip()
        # 获取消息发送者的群昵称
        sender_name = self.wcf.get_alias_in_chatroom(msg.sender, msg.roomid)
        try:
            if "1" == request:  # 查看服务器信息
                server_info = self.pal_server.get_server_info()
                server_metrics = self.pal_server.get_server_metrics()
                server_settings = self.pal_server.load_server_settings()
                result = (f"服务器名: {server_info['servername']}\n"
                          f"版本号： {server_info['version']}\n"
                          f"服务器地址：{server_settings['PublicIP']}:{server_settings['PublicPort']}\n"
                          f"密码：{server_settings['ServerPassword']}\n"
                          f"当前玩家数：{server_metrics['currentplayernum']}\n"
                          f"服务器帧率：{server_metrics['serverfps']} fps\n"
                          f"服务器运行时长：{server_metrics['uptime']} s")
                self.wcf.send_text(result, msg.roomid)
            elif "2" == request:    # 更新服务器
                self.wcf.send_text("即将更新服务器，现在开始停止服务器", msg.roomid)
                self.pal_server.stop()
                self.wcf.send_text(f"@{sender_name} 服务器停止完成，开始更新服务器", msg.roomid, msg.sender)
                self.pal_server.update()
                self.wcf.send_text(f"@{sender_name} 服务器更新完成，开始启动服务器", msg.roomid, msg.sender)
                self.pal_server.start()
                self.wcf.send_text(f"@{sender_name} 服务器启动完成，开始当帕鲁吧", msg.roomid, msg.sender)
            elif "3" == request:    # 重启服务器
                self.wcf.send_text("服务器即将重启", msg.roomid)
                self.pal_server.restart()
                self.wcf.send_text(f"@{sender_name} 服务器重启完成，开始当帕鲁吧", msg.roomid, msg.sender)
            elif "4" == request:    # 查看在线玩家
                player_list = self.pal_server.get_player_list()['players']
                if len(player_list) == 0:
                    self.wcf.send_text("现在没人在当帕鲁", msg.roomid)
                else:
                    result = f"当前在线的帕鲁({len(player_list)}人)："
                    for player in player_list:
                        result += f"\n{player['name']} ({player['userId'].replace("steam_", "")})"
                    self.wcf.send_text(result, msg.roomid)
            elif "0" == request:
                if msg.sender in self.admin_wxid:
                    self.wcf.send_text("管理员特权指令，服务器即将强制停机", msg.roomid)
                    self.pal_server.kill()
                    self.wcf.send_text(f"@{sender_name} 服务器停止完成，开始启动服务器", msg.roomid, msg.sender)
                    self.pal_server.start()
                    self.wcf.send_text(f"@{sender_name} 服务器启动完成，开始当帕鲁吧", msg.roomid, msg.sender)
                else:
                    self.wcf.send_text("你不是管理员，无法使用特权指令", msg.roomid)
            else:
                # 拆分请求和参数
                request = request.split(maxsplit=2)
                if len(request) < 2:
                    request = [None, ""]
                arg1 = request[1]
                request = request[0]
                if "5" == request:  # 广播消息
                    self.pal_server.announce_msg(arg1)
                    self.wcf.send_text("广播消息完成", msg.roomid)
                elif "6" == request:    # 踢出玩家
                    self.pal_server.kick_player("steam_" + arg1)
                    self.wcf.send_text(f"玩家 {arg1} 已被踢出", msg.roomid)
                elif "7" == request:    # 封禁玩家
                    self.pal_server.ban_player("steam_" + arg1)
                    self.wcf.send_text(f"玩家 {arg1} 已被封禁", msg.roomid)
                elif "8" == request:    # 解封玩家
                    self.pal_server.unban_player("steam_" + arg1)
                    self.wcf.send_text(f"玩家 {arg1} 已解封", msg.roomid)
                else:
                    result = (
                        "你好，我是你的帕鲁小助手。请@我后输入以下指令序号，我试试能不能帮你，其他的老子就不会了。\n"
                        "【1】查看服务器信息\n"
                        "【2】更新服务器\n"
                        "【3】重启服务器\n"
                        "【4】查询在线玩家\n"
                        "【5】广播消息（示例：5 全民制作人们大家好）\n"
                        "【6】踢出玩家 （示例：6 玩家id）\n"
                        "【7】封禁玩家（示例：7 玩家id）\n"
                        "【8】解封玩家（示例：8 玩家id）\n")
                    self.wcf.send_text(result, msg.roomid)
        except Exception as e:
            logging.error(e)
            result = f"@{sender_name} 执行指令翻车了，检查指令是否正确，或者找我的运维爸爸帮忙"
            self.wcf.send_text(result, msg.roomid, msg.sender)

    def _process_msg(self, msg):
        # 仅处理被@的群消息
        if msg.from_group() and msg.is_at(self.wcf.get_self_wxid()):
            if self.msg_types[msg.type] == "文字":
                # 确保同一时间只有一个任务在执行，繁忙时直接拒绝任务，不使用排队策略
                if self.worker is None or not self.worker.is_alive():
                    self.worker = Thread(target=self._process_request, args=(msg,))
                    self.worker.start()
                else:
                    self.wcf.send_text("别吵，我在烧烤", msg.roomid)

    def listen_for_msg(self):
        self.wcf.enable_receiving_msg(True)
        logging.info("微信消息监听开始...")
        while self.wcf.is_receiving_msg():
            try:
                msg = self.wcf.get_msg()
                self._process_msg(msg)
            except Empty:
                continue  # Empty message
            except Exception as e:
                logging.error(f"Receiving message error: {e}")
            except KeyboardInterrupt:
                logging.info("帕鲁微信机器人退出")
                return

    def __init__(self, pal_server: PalServer, admin_wxid: List[str] = None):
        if admin_wxid is None:
            admin_wxid = []
        self.pal_server = pal_server
        self.admin_wxid = admin_wxid
        self.wcf = Wcf()
        self.msg_types = self.wcf.get_msg_types()
        self.worker = None
