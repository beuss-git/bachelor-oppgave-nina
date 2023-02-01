# Only needed for access to command line arguments
from enum import Enum
import customtkinter as c_tk

c_tk.set_appearance_mode("System")
c_tk.set_default_color_theme("green")


class fileHandle(Enum):
    SAVE = "Save"
    LOAD = "Load"


def setFrame(parent: c_tk.CTk, padding: tuple[int, int]) -> c_tk.CTkFrame:
    frame = c_tk.CTkFrame(master=parent)
    frame.pack(pady=padding[1], padx=padding[0], fill="both")
    return frame


def setLabel(
    label: str, frame: c_tk.CTkFrame, padding: tuple[int, int]
) -> c_tk.CTkLabel:
    label = c_tk.CTkLabel(master=frame, text=label)
    label.pack(pady=padding[1], padx=padding[0])
    return label


def browseDir(label: c_tk.CTkLabel, type: fileHandle) -> str:
    dir = c_tk.filedialog.askdirectory()
    if len(dir) > 0:
        label.configure(text=f"{type} directory: {dir}")
    return dir


class App(c_tk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.geometry(f"{1100}x{580}")
        self.title("Dead time cleaner")

        frame_getdirs = setFrame(self, padding=(60, 20))
        label_load = setLabel("Load directory", frame_getdirs, padding=(10, 10))

        def browseLoad():
            browseDir(label_load, fileHandle.LOAD.value)

        button_get_load_dir = c_tk.CTkButton(
            master=frame_getdirs,
            text="Browse Directories",
            command=browseLoad,
        )
        button_get_load_dir.pack()

        label_save = setLabel("Save directory", frame_getdirs, padding=(10, 10))

        def browseSave():
            browseDir(label_save, fileHandle.SAVE.value)

        button_get_save_dir = c_tk.CTkButton(
            master=frame_getdirs,
            text="Browse Directories",
            command=browseSave,
        )
        button_get_save_dir.pack()


if __name__ == "__main__":
    app = App()
    app.mainloop()
