import logging
import sys
from palworld import PalServer
from palbot import PalBot

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    pal_server = PalServer(host="192.168.x.x", ssh_user="steam",
                           ssh_connect_kwargs={'password': "xxxxxx"})
    PalBot(pal_server, ["wxid_xxxxxxxxxxxx", "wxid_xxxxxxxxxxxx"]).listen_for_msg()
