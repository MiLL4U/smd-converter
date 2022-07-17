import tkinter as tk
from tkinter import ttk
from typing import Callable

from .constants import PADDING_OPTIONS


class OKCancelButtonArray(ttk.Frame):
    def __init__(self, master: tk.Misc, ok_command: Callable,
                 cancel_command: Callable, *args, **kwargs) -> None:
        super().__init__(master=master, *args, **kwargs)
        self.__ok_cmd = ok_command
        self.__cancel_cmd = cancel_command

        self.__create_widgets()

    def __create_widgets(self):
        self.cancel_btn = ttk.Button(
            self, text="Cancel", command=self.__cancel_cmd)
        self.cancel_btn.pack(side=tk.RIGHT, **PADDING_OPTIONS)

        self.ok_btn = ttk.Button(
            self, text="OK", command=self.__ok_cmd)
        self.ok_btn.pack(side=tk.RIGHT, **PADDING_OPTIONS)