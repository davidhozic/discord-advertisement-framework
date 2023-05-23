"""
Modules contains storage container widgets.
"""
from typing import Union, Any, List
from .convert import ObjectInfo

import ttkbootstrap as ttk
import tkinter as tk
import ttkbootstrap.dialogs.dialogs as tkdiag


class Text(tk.Text):
    def get(self) -> str:
        return super().get("1.0", tk.END).strip()


class ComboBoxText(ttk.Frame):
    def __init__(self, text: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ttk.Label(self, text=text).pack(fill=tk.X, expand=True)
        self.combo = ComboBoxObjects(self)
        self.combo.pack(fill=tk.X, expand=True)


class ListBoxObjects(tk.Listbox):
    def __init__(self, *args, **kwargs):
        self._original_items = []
        super().__init__(*args, **kwargs)
        self.configure(selectmode=tk.EXTENDED)

    def get(self, original = True, *args, **kwargs) -> list:
        if original:
            return self._original_items

        return super().get(*args, **kwargs)

    def insert(self, index: Union[str, int], *elements: Union[str, float]) -> None:
        _ret = super().insert(index, *elements)
        self._original_items.extend(elements)
        return _ret

    def delete(self, *indexes: int) -> None:
        if indexes[-1] == "end":
            indexes = range(indexes[0], len(self._original_items))

        indexes = sorted(indexes, reverse=True)
        for index in indexes:
            super().delete(index)
            del self._original_items[index]

    def clear(self) -> None:
        super().delete(0, tk.END)
        self._original_items.clear()


class ListBoxScrolled(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent)
        listbox = ListBoxObjects(self, *args, **kwargs)

        listbox.pack(side="left", fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self)
        scrollbar.pack(side=tk.RIGHT, fill=tk.BOTH)
        scrollbar.config(command=listbox.yview)

        listbox.config(yscrollcommand=scrollbar.set)

        listbox.bind("<Control-c>", lambda e: self.listbox_copy_selected())
        listbox.bind("<BackSpace>", lambda e: self.listbox_delete_selected())
        listbox.bind("<Delete>", lambda e: self.listbox_delete_selected())

        self.listbox = listbox

    def see(self, *args, **kwargs):
        return self.listbox.see(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.listbox.get(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.listbox.delete(*args, **kwargs)

    def clear(self, *args, **kwargs):
        return self.listbox.clear(*args, **kwargs)

    def curselection(self, *args, **kwargs):
        return self.listbox.curselection(*args, **kwargs)

    def insert(self, *args, **kwargs):
        return self.listbox.insert(*args, **kwargs)

    def listbox_delete_selected(self):
        listbox = self.listbox
        selection = listbox.curselection()
        if len(selection):
            listbox.delete(*selection)
        else:
            tkdiag.Messagebox.show_error("Select atleast one item!", "Empty list!", parent=self)

    def listbox_copy_selected(self):
        listbox = self.listbox
        selection = self.listbox.curselection()
        if len(selection):
            object_: Union[ObjectInfo, Any] = listbox.get()[selection[0]]
            listbox.insert(tk.END, object_)
        else:
            tkdiag.Messagebox.show_error("Select atleast one item!", "Empty list!", parent=self)


class ComboBoxObjects(ttk.Combobox):
    def __init__(self, *args, **kwargs):
        self._original_items = []
        super().__init__(*args, **kwargs)

    def get(self, *args, **kwargs) -> Any:
        index = self.current()
        if isinstance(index, int) and index >= 0:
            return self._original_items[index]

        return super().get(*args, **kwargs)

    def delete(self, index: int) -> None:
        self["values"].pop(index)
        super().delete(index)
        self["values"] = self["values"]  # Update the text list, NOT a code mistake

    def insert(self, index: Union[int, str], element: Any) -> None:
        if index == tk.END:
            self._original_items.append(element)
            index = len(self._original_items)
        else:
            self._original_items.insert(index, element)

        self["values"] = self._original_items

    def __setitem__(self, key: str, value) -> None:
        if key == "values":
            self._original_items = list(value)
            value = [str(x)[:200] for x in value]

        return super().__setitem__(key, value)

    def __getitem__(self, key: str):
        if key == "values":
            return self._original_items

        return super().__getitem__(key)


class ComboEditFrame(ttk.Frame):
    def __init__(
            self,
            edit_method: Any,
            values: List[ObjectInfo] = [],
            master=None,
            *args,
            **kwargs
    ):
        super().__init__(*args, master=master, **kwargs)
        combo = ComboBoxObjects(self)
        ttk.Button(self, text="Edit", command=self._edit).pack(side="right")
        combo.pack(side="left", fill=tk.X, expand=True)
        self.combo = combo
        self.edit_method = edit_method
        self.set_values(values)

    def set_values(self, values: List[ObjectInfo] = []):
        self.combo["values"] = values
        self.combo.current(0)

    def _edit(self):
        selection = self.combo.current()
        if selection >= 0:
            object_: ObjectInfo = self.combo.get()
            self.edit_method(
                object_.class_,
                self.combo,
                old=object_,
            )
        else:
            tkdiag.Messagebox.show_error("Select atleast one item!", "Empty list!")
