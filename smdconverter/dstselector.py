import os
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askdirectory


class DestinationSelector(ttk.Frame):
    def __init__(self, master: tk.Misc, dst_var: tk.StringVar,
                 *args, **kwargs):
        kwargs['master'] = master
        super().__init__(*args, **kwargs)

        # variables
        self.__dst_dir = dst_var

        # grid configures
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=0)

        self.__create_widgets()

    def __create_widgets(self) -> None:
        label = ttk.Label(self, text="Save to:")
        label.grid(column=0, row=0, sticky=tk.E, padx=5)

        self.dst_entry = ttk.Entry(
            self, textvariable=self.__dst_dir)
        self.dst_entry.grid(column=1, row=0, sticky=tk.EW, padx=5)

        self.browse_btn = ttk.Button(
            self, text="Browse...", command=self.__handle_browsebtn)
        self.browse_btn.grid(column=2, row=0, sticky=tk.W, padx=5)

    def __handle_browsebtn(self) -> None:
        dst = askdirectory()
        if dst:
            self.__dst_dir.set(os.path.abspath(dst) + "/")

    def get(self) -> str:
        return self.__dst_dir.get()

    def reset(self) -> None:
        self.__dst_dir.set("")
