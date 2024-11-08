import os
import sys
import json
import signal
import pystray
import subprocess
from PIL import Image


class TinItem:
    def __init__(
            self, name: "str", root: "str", cmd: "list[str]",
            auto: "bool", log: "str", err: "str"
    ):
        self.name, self.root, self.cmd, self.auto = name, root, cmd, auto
        self.log, self.err = log, err
        self.log_f, self.err_f = open(log, "w"), open(err, "w")
        self.process: "subprocess.Popen" = None  # noqa

    def is_running(self) -> "bool":
        return self.process and self.process.poll() is None

    def do_start(self):
        self.log_f = open(self.log, "w")
        self.err_f = open(self.err, "w")
        self.process = subprocess.Popen(
            self.cmd,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=self.log_f,
            stderr=self.err_f,
        )

    def do_stop(self):
        self.process.send_signal(signal.CTRL_BREAK_EVENT)
        self.process.wait()
        self.process = None
        self.log_f.close()
        self.err_f.close()

    def on_start(self, icon: "pystray.Icon", item: "pystray.MenuItem"):  # noqa
        if self.is_running():
            return
        self.do_start()
        icon.update()

    def on_stop(self, icon: "pystray.Icon", item: "pystray.MenuItem"):  # noqa
        if not self.is_running():
            return
        self.do_stop()
        icon.update()

    def on_restart(self, icon: "pystray.Icon", item: "pystray.MenuItem"):
        self.do_stop()
        self.on_start(icon, item)

    def on_root(self, icon: "pystray.Icon", item: "pystray.MenuItem"):  # noqa
        os.startfile(self.root)


class TinManager:
    def __init__(self, title: "str", image: "str", tasks: "list[TinItem]"):
        self.tasks = tasks
        self.main = pystray.Icon(
            name=title,
            title=title,
            icon=Image.open(image),
            menu=self.getMenu(tasks)
        )
        self.main.update = self.update

    def getMenu(self, tasks: "list[TinItem]") -> "list[pystray.MenuItem]":
        arr = []
        for task in tasks:
            if task.is_running():
                menu = pystray.Menu(
                    pystray.MenuItem("重启", task.on_restart),
                    pystray.MenuItem("停止", task.on_stop),
                    pystray.MenuItem("文件位置", task.on_root)
                )
            else:
                menu = pystray.Menu(
                    pystray.MenuItem("启动", task.on_start),
                    pystray.MenuItem("文件位置", task.on_root)
                )
            arr.append(pystray.MenuItem(task.name, menu))
        arr.append(pystray.MenuItem("退出", self.on_exit))
        return arr

    def update(self):
        self.main.menu = self.getMenu(self.tasks)

    def setup(self, icon: "pystray.Icon"):
        for task in self.tasks:
            if task.auto:
                task.do_start()
        self.update()
        icon.visible = True

    def on_exit(self, icon: "pystray.Icon", item: "pystray.MenuItem"):  # noqa
        for task in self.tasks:
            task.do_stop()
        icon.visible = True
        icon.stop()


def main():
    confPath = "./config.json"
    if len(sys.argv) > 1:
        confPath = sys.argv[1]
    with open(confPath, "r", encoding="utf-8") as fp:
        conf = json.load(fp)
    tasks = [
        TinItem(
            itr["name"], itr["root"], itr["cmd"],
            itr["auto"], itr["log"], itr["err"]
        ) for itr in conf["tasks"]
    ]
    manager = TinManager(conf["title"], conf["image"], tasks)
    manager.main.run(manager.setup)


# pyinstaller -F -n TinStray -i favicon.ico TinStray.py
if __name__ == "__main__":
    main()
