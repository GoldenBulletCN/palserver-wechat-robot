from fabric import Connection
import requests
from requests.auth import HTTPBasicAuth
import re
from io import StringIO
import configparser
import logging


class PalServer:

    def __init__(
            self,
            host: str,
            ssh_port: int = None,
            ssh_user: str = None,
            ssh_connect_kwargs: dict = None,
            api_port: int = None
    ):
        self.ssh = Connection(host=host, user=ssh_user, port=ssh_port,
                              connect_kwargs=ssh_connect_kwargs)
        self.settings = self.load_server_settings(False)
        if self.settings['RESTAPIEnabled'] != "True":
            raise Exception("Settings \"RESTAPIEnabled\" is False")
        if api_port is None:
            api_port = self.settings['RESTAPIPort']
        self.base_url = f"http://{host}:{api_port}/v1/api"
        self.api = requests.session()
        self.api.auth = HTTPBasicAuth("admin", self.settings['AdminPassword'])
        self.api.headers.update({
            'Accept': 'application/json'
        })

    def get_server_info(self):
        response = self.api.get(f"{self.base_url}/info")
        response.raise_for_status()
        return response.json()

    def get_server_settings(self):
        response = self.api.get(f"{self.base_url}/settings")
        response.raise_for_status()
        return response.json()

    def get_server_metrics(self):
        response = self.api.get(f"{self.base_url}/metrics")
        response.raise_for_status()
        return response.json()

    def announce_msg(self, msg: str):
        response = self.api.post(f"{self.base_url}/announce", json={'message': msg})
        response.raise_for_status()

    def get_player_list(self):
        response = self.api.get(f"{self.base_url}/players")
        response.raise_for_status()
        return response.json()

    def kick_player(self, player: str, msg: str = "You are kicked."):
        response = self.api.post(f"{self.base_url}/kick", json={'userid': player, 'message': msg})
        response.raise_for_status()

    def ban_player(self, player: str, msg: str = "You are banned."):
        response = self.api.post(f"{self.base_url}/ban", json={'userid': player, 'message': msg})
        response.raise_for_status()

    def unban_player(self, player: str):
        response = self.api.post(f"{self.base_url}/unban", json={'userid': player})
        response.raise_for_status()

    def save(self):
        response = self.api.post(f"{self.base_url}/save")
        response.raise_for_status()

    def async_shutdown(self, wait_time: int = 10, msg: str = None):
        if msg is None:
            msg = f"Server will shutdown in {wait_time} seconds."
        response = self.api.post(f"{self.base_url}/shutdown", json={'waittime': wait_time, 'message': msg})
        response.raise_for_status()

    def async_force_shutdown(self):
        response = self.api.post(f"{self.base_url}/stop")
        response.raise_for_status()

    def __ssh_cmd(self, cmd):
        logging.info(f"Execute command: {cmd}")
        stdout = StringIO()
        try:
            self.ssh.run(cmd, hide=True, encoding='utf-8', out_stream=stdout, err_stream=stdout)
        finally:
            logging.info(f"Execution result:\n{stdout.getvalue()}")
        return stdout.getvalue()

    def start(self):
        return self.__ssh_cmd("./run.sh -start")

    def stop(self):
        return self.__ssh_cmd("./run.sh -stop")

    def kill(self):
        return self.__ssh_cmd("./run.sh -kill")

    def restart(self):
        return self.__ssh_cmd("./run.sh -restart")

    def update(self):
        return self.__ssh_cmd("./run.sh -update")

    def load_server_settings(self, use_cache: bool = True):
        if use_cache:
            return self.settings
        result = self.__ssh_cmd("./run.sh -settings")
        config = configparser.ConfigParser()
        config.read_string(result)
        options = config['/Script/Pal.PalGameWorldSettings']['OptionSettings'].strip("()")
        pattern = re.compile(r'(\w+)=("[^"]*"|[^,]*)')
        return {match.group(1): match.group(2).strip('"')
                for match in pattern.finditer(options)}
