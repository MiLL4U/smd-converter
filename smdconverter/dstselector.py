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

    def __create_widgets(self):
        label = ttk.Label(self, text="Save to:")
        label.grid(row=0, column=0, sticky=tk.E, padx=5)

        self.dst_entry = ttk.Entry(
            self, textvariable=self.__dst_dir)
        self.dst_entry.grid(row=0, column=1, sticky=tk.EW, padx=5)

        self.browse_btn = ttk.Button(
            self, text="Browse...", command=self.__handle_browsebtn,
            # state=tk.DISABLED
        )
        self.browse_btn.grid(row=0, column=2, sticky=tk.W, padx=5)

    def __handle_browsebtn(self):
        dst = askdirectory()
        if dst:
            self.__dst_dir.set(os.path.abspath(dst) + "/")

    def get(self) -> str:
        return self.__dst_dir.get()

    def reset(self):
        self.__dst_dir.set("")
        # self.browse_btn.configure(state=tk.DISABLED)
