from abc import ABCMeta, abstractmethod
import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Tuple, Union, cast

from .constants import PADDING_OPTIONS
from .changevaluedlg import DEFAULT_LENGTH, DEFAULT_TITLE, ChangeValueDialog

BUTTON_WIDTH = 6


class ChangeableTreeFrame(ttk.LabelFrame):
    def __init__(self, master: tk.Misc, columns: Tuple[str, ...],
                 column_texts: Dict[str, str], values_dict: Dict[str, str],
                 default_values: Dict[str, str] = None,
                 height: int = 5, changeable_flags: Tuple[bool, ...] = None,
                 dialog_title: str = DEFAULT_TITLE,
                 entry_length: int = DEFAULT_LENGTH,
                 empty_ok: bool = False,
                 *args, **kwargs) -> None:
        kwargs['master'] = master
        super().__init__(*args, **kwargs)
        self.__columns = columns
        self.__column_texts = column_texts
        self.__height = height
        self.changeable_flags = changeable_flags
        self.dialog_title = dialog_title
        self.entry_length = entry_length
        self.empty_ok = empty_ok

        # grid settings
        self.columnconfigure(0, weight=1)  # Treeview
        self.columnconfigure(1, weight=0)  # scroll bar
        self.rowconfigure(0, weight=1)  # Treeview
        self.rowconfigure(1, weight=0)  # EditTreeButtonArray

        # variables
        self.__values_dict = values_dict
        self.__default_values = default_values

        self.tree: Union[ChangeableTree, None] = None  # prototype
        self.create_buttons()
        self.__create_widgets()

    @property
    def column_num(self) -> int:
        return len(self.__columns)

    @property
    def column_texts(self) -> Tuple[str, ...]:
        return tuple(self.__column_texts.values())

    @property
    def values_dict(self) -> Dict[str, str]:
        return self.__values_dict

    def __create_widgets(self) -> None:
        self.tree = ChangeableTree(
            master=self, columns=self.__columns,
            column_texts=self.__column_texts,
            values_dict=self.__values_dict, height=self.__height,
            select_cmd=self.btn_array.enable_buttons)
        self.tree.grid(
            column=0, row=0, sticky=tk.NSEW)

        self.tree_scrl = ttk.Scrollbar(
            self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree_scrl.grid(row=0, column=1, sticky=tk.NS)
        self.tree.config(yscrollcommand=self.tree_scrl.set)

    def create_buttons(self) -> None:
        # because prototype is used
        self.tree = cast(ChangeableTree, self.tree)
        is_resettable = True if self.__default_values else False
        self.btn_array: TreeButtonArray = ChangeTreeButtonArray(
            master=self, target_tree=self.tree,
            edit_cmd=self.edit_item, reset_cmd=self.reset_selected_item,
            is_resettable=is_resettable)
        self.btn_array.grid(
            column=0, columnspan=2, row=1, sticky=tk.NSEW, **PADDING_OPTIONS)

    def reset_selected_item(self) -> None:
        if self.tree and self.__default_values:
            key = self.tree.selected_content[0]
            try:
                self.values_dict[key] = self.__default_values[key]
            except KeyError:
                print(f"Warning: Default value for {key} is not found")
            self.tree.update_contents()
        self.btn_array.disable_buttons()

    def edit_item(self) -> None:
        if self.tree:
            selected_content = self.tree.selected_content
            selected_key = selected_content[0]
            dialog = ChangeValueDialog(
                master=self, descriptions=self.column_texts,
                values=selected_content, changeable_flags=self.changeable_flags,
                title=self.dialog_title, entry_length=self.entry_length,
                empty_ok=self.empty_ok)
            dialog_input = dialog.show()
            if dialog_input is None:
                return
            if dialog_input[0] == selected_key:
                self.values_dict[selected_key] = dialog_input[1]
            else:
                del self.values_dict[selected_key]
                self.values_dict[dialog_input[0]] = dialog_input[1]
            self.tree.update_contents()
        self.btn_array.disable_buttons()


class EditableTreeFrame(ChangeableTreeFrame):
    # with add and remove button
    def __init__(self, master: tk.Misc, columns: Tuple[str, ...],
                 column_texts: Dict[str, str], values_dict: Dict[str, str],
                 height: int = 5, changeable_flags: Tuple[bool, ...] = None,
                 dialog_title: str = DEFAULT_TITLE,
                 entry_length: int = DEFAULT_LENGTH,
                 empty_ok: bool = False, *args, **kwargs) -> None:
        kwargs['master'] = master
        kwargs['columns'] = columns
        kwargs['column_texts'] = column_texts
        kwargs['values_dict'] = values_dict
        kwargs['height'] = height
        kwargs['changeable_flags'] = changeable_flags
        kwargs['dialog_title'] = dialog_title
        kwargs['entry_length'] = entry_length
        kwargs['empty_ok'] = empty_ok
        super().__init__(*args, **kwargs)

    def create_buttons(self) -> None:  # override
        # because prototype is used
        self.tree = cast(ChangeableTree, self.tree)
        self.btn_array = EditTreeButtonArray(
            master=self, target_tree=self.tree,
            edit_cmd=self.edit_item, add_cmd=self.add_item,
            del_cmd=self.delete_selected_item)
        self.btn_array.grid(
            column=0, columnspan=2, row=1, sticky=tk.NSEW, **PADDING_OPTIONS)

    def add_item(self) -> None:
        empty_values = tuple(("" for _ in range(self.column_num)))
        dialog = ChangeValueDialog(
            master=self, descriptions=self.column_texts, values=empty_values,
            changeable_flags=self.changeable_flags, title=self.dialog_title,
            entry_length=self.entry_length,
            empty_ok=self.empty_ok)
        dialog_input = dialog.show()
        if dialog_input is None:
            return
        if dialog_input[0] in self.values_dict.keys():
            raise KeyError(f"Key {dialog_input[0]} already exists")
        self.values_dict[dialog_input[0]] = dialog_input[1]
        if self.tree:
            self.tree.update_contents()
            self.btn_array.disable_buttons()

    def delete_selected_item(self) -> None:
        if self.tree:
            selected_key = self.tree.selected_content[0]
            del self.values_dict[selected_key]
            self.tree.update_contents()
            self.btn_array.disable_buttons()


class ChangeableTree(ttk.Treeview):
    # open value change window when items are double-clicked
    def __init__(self, master: tk.Misc, columns: Tuple[str, ...],
                 column_texts: Dict[str, str], values_dict: Dict[str, str],
                 select_cmd: Callable[[], None] = None,
                 *args, **kwargs) -> None:
        self.__columns = columns
        self.__column_texts = column_texts
        self.__select_cmd = select_cmd

        kwargs['master'] = master
        kwargs['columns'] = self.__columns
        super().__init__(
            selectmode=tk.BROWSE,
            show='headings', *args, **kwargs)
        self.bind('<<TreeviewSelect>>', self.__handle_item_select)

        # variables
        self.__values_dict = values_dict

        self.__layout_columns()
        self.update_contents()

    def __layout_columns(self) -> None:
        for column in self.__columns:
            self.heading(column, text=self.__column_texts[column])
            self.column(column)

    def update_contents(self) -> None:
        self.reset_contents()
        for key in self.__values_dict:
            row = (key, self.__values_dict[key])
            self.insert('', tk.END, values=row)

    @property
    def selected_content(self) -> Tuple[str, str]:
        res = self.item(self.selection()[0], 'values')
        return cast(Tuple[str, str], res)  # returns (key, value)

    def reset_contents(self) -> None:
        self.delete(*self.get_children())

    def __handle_item_select(self, event: tk.Event) -> None:
        if self.__select_cmd:
            self.__select_cmd()

    def __open_change_value_window(self) -> None:
        # self.change_window = ChangeValueDialog(
        #     master=self, labels=self.__columns,
        #     values=("spam", "ham"))
        # self.change_window.focus()
        pass


class TreeButtonArray(ttk.Frame, metaclass=ABCMeta):
    def __init__(self, master: tk.Misc, target_tree: ChangeableTree,
                 edit_cmd: Callable[[], None] = None,
                 *args, **kwargs) -> None:
        kwargs['master'] = master
        super().__init__(*args, **kwargs)
        self.__target_tree = target_tree
        self.__edit_cmd = edit_cmd

        self.create_additional_widgets()
        self.__create_widgets()

    def __create_widgets(self) -> None:
        self.edit_btn = ttk.Button(
            self, text="Edit", command=self.__handle_edit_btn,
            state=tk.DISABLED, width=BUTTON_WIDTH)
        self.edit_btn.pack(side=tk.RIGHT)

    @abstractmethod
    def create_additional_widgets(self) -> None:
        raise NotImplementedError

    def enable_buttons(self) -> None:
        self.edit_btn.configure(state=tk.NORMAL)
        self.enable_additional_buttons()

    @abstractmethod
    def enable_additional_buttons(self) -> None:
        raise NotImplementedError

    def disable_buttons(self) -> None:
        self.edit_btn.configure(state=tk.DISABLED)
        self.disable_additional_buttons()

    @abstractmethod
    def disable_additional_buttons(self):
        raise NotImplementedError

    def __handle_edit_btn(self) -> None:
        if self.__edit_cmd:
            self.__edit_cmd()


class ChangeTreeButtonArray(TreeButtonArray):
    def __init__(self, master: tk.Misc, target_tree: ChangeableTree,
                 edit_cmd: Callable[[], None] = None,
                 reset_cmd: Callable[[], None] = None,
                 is_resettable: bool = True,
                 *args, **kwargs) -> None:
        kwargs['master'] = master
        kwargs['target_tree'] = target_tree
        kwargs['edit_cmd'] = edit_cmd
        super().__init__(*args, **kwargs)

        self.__reset_cmd = reset_cmd
        # whether default values exist and can be reset
        self.__is_resettable = is_resettable

    def create_additional_widgets(self) -> None:
        self.reset_btn = ttk.Button(
            self, text="Reset", command=self.__handle_reset_btn,
            state=tk.DISABLED, width=BUTTON_WIDTH)
        self.reset_btn.pack(side=tk.RIGHT)

    def enable_additional_buttons(self) -> None:
        if self.__is_resettable:
            self.reset_btn.configure(state=tk.NORMAL)

    def disable_additional_buttons(self):
        self.reset_btn.configure(state=tk.DISABLED)

    def __handle_reset_btn(self) -> None:
        if self.__reset_cmd:
            self.__reset_cmd()


class EditTreeButtonArray(TreeButtonArray):
    def __init__(self, master: tk.Misc, target_tree: ChangeableTree,
                 edit_cmd: Callable[[], None] = None,
                 add_cmd: Callable[[], None] = None,
                 del_cmd: Callable[[], None] = None,
                 *args, **kwargs) -> None:
        kwargs['master'] = master
        kwargs['target_tree'] = target_tree
        kwargs['edit_cmd'] = edit_cmd
        super().__init__(*args, **kwargs)

        self.__add_cmd = add_cmd
        self.__del_cmd = del_cmd

    def create_additional_widgets(self) -> None:
        self.del_btn = ttk.Button(
            self, text="-", command=self.__handle_del_btn,
            state=tk.DISABLED, width=BUTTON_WIDTH)
        self.del_btn.pack(side=tk.RIGHT)

        self.add_btn = ttk.Button(
            self, text="+", command=self.__handle_add_btn,
            width=BUTTON_WIDTH)
        self.add_btn.pack(side=tk.RIGHT)

    def enable_additional_buttons(self) -> None:
        self.del_btn.configure(state=tk.NORMAL)

    def disable_additional_buttons(self):
        self.del_btn.configure(state=tk.DISABLED)

    def __handle_add_btn(self) -> None:
        if self.__add_cmd:
            self.__add_cmd()

    def __handle_del_btn(self) -> None:
        if self.__del_cmd:
            self.__del_cmd()
