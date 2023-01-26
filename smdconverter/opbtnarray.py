import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Union

from .constants import IMAGE_PATH


class OperationButtonArray(ttk.Frame):
    def __init__(self, master: tk.Misc,
                 commands: Dict[str, Callable[[], None]],
                 command_texts: Dict[str, str],
                 command_icons: Union[Dict[str, str], None] = None,
                 command_icons_disabled: Union[Dict[str, str], None] = None,
                 *args, **kwargs) -> None:
        """Frame which contain buttons for main operations

        Args:
            master (tk.Misc): container of this widget
            commmands (Dict[str, Callable[[], None]): names of commands and
                                        functions called with buttons
            command_texts (Dict[str, str]): button text for each command
        """
        kwargs['master'] = master
        super().__init__(*args, **kwargs)
        self.__commands = commands
        self.__command_texts = command_texts
        self.__command_icons = command_icons
        self.__command_icons_disabled = command_icons_disabled

        self.__create_buttons()

    def __create_buttons(self) -> None:
        """create button for each command"""
        self.__buttons: Dict[str, ttk.Button] = {}
        for i, cmd_name in enumerate(self.__commands.keys()):
            button = ttk.Button(
                self, text=self.__command_texts[cmd_name],
                command=self.__commands[cmd_name])
            self.__buttons[cmd_name] = button
            button.grid(column=i, row=0, padx=5)

        if self.__command_icons:
            self.__icons: Dict[str, tk.PhotoImage] = {}
            for i, cmd_name in enumerate(self.__command_icons.keys()):
                self.__icons[cmd_name] = tk.PhotoImage(
                    file=IMAGE_PATH+self.__command_icons[cmd_name])
                self.__buttons[cmd_name].configure(
                    image=self.__icons[cmd_name], compound=tk.LEFT)

    def enable(self, cmd_name: str) -> None:
        self.__buttons[cmd_name].configure(state=tk.NORMAL)
        if self.__command_icons:
            self.__icons[cmd_name].configure(
                file=IMAGE_PATH+self.__command_icons[cmd_name])

    def disable(self, cmd_name: str) -> None:
        self.__buttons[cmd_name].configure(state=tk.DISABLED)
        if self.__command_icons_disabled:
            self.__icons[cmd_name].configure(
                file=IMAGE_PATH+self.__command_icons_disabled[cmd_name])
