# Only needed for access to command line arguments
from enum import Enum
import customtkinter as c_tk

# Setup of application configuration
c_tk.set_appearance_mode("System")
c_tk.set_default_color_theme("green")


class FileHandle(Enum):
    """Differentiates save and load

    Args:
        Enum (_type_): Enum handling
    """

    SAVE = "Save"
    LOAD = "Load"


def set_frame(parent: c_tk.CTk, padding: tuple[int, int]) -> c_tk.CTkFrame:
    """Creates a frame
    Args:
        parent (c_tk.CTk): parented container
        padding (tuple[int, int]): x, y : int, int padding

    Returns:
        c_tk.CTkFrame: the frame
    """
    frame = c_tk.CTkFrame(master=parent)
    frame.pack(pady=padding[1], padx=padding[0], fill="both")
    return frame


def set_label(
    label: str, frame: c_tk.CTkFrame, padding: tuple[int, int]
) -> c_tk.CTkLabel:
    """Creates a label

    Args:
        label (str): label name
        frame (c_tk.CTkFrame): parent frame
        padding (tuple[int, int]): x, y : int, int padding

    Returns:
        c_tk.CTkLabel: the label
    """
    label = c_tk.CTkLabel(master=frame, text=label)
    label.pack(pady=padding[1], padx=padding[0], side=c_tk.LEFT)
    return label


def browse_dir(label: c_tk.CTkLabel, handle_type: FileHandle) -> str:
    """Setup browsing of directories

    Args:
        label (c_tk.CTkLabel):parent label
        type (fileHandle): type of handling of directory

    Returns:
        str: the path to the directory
    """
    m_dir = c_tk.filedialog.askdirectory()
    # if len(m_dir) > 0:
    # label.configure(text=f"{handle_type} directory: {m_dir}")
    return m_dir


class App(c_tk.CTk):
    """The main class of the application

    Args:
        c_tk (_type_): customTkinter application type
    """

    load_dir = ""
    save_dir = ""

    buffer_time = 0

    def __init__(self) -> None:
        super().__init__()
        self.geometry(f"{800}x{480}")
        self.title("Dead time cleaner")

        main_frame = set_frame(self, padding=(60, 20))

        # Frame for load dir
        load_dir_frame = c_tk.CTkFrame(main_frame)
        label_load = set_label("Load directory:", load_dir_frame, padding=(10, 10))

        textbox_load_dir = c_tk.CTkTextbox(
            load_dir_frame, height=20, width=400, activate_scrollbars=False
        )
        textbox_load_dir.configure(state="normal")
        textbox_load_dir.pack(side=c_tk.LEFT)

        def browse_load():
            self.load_dir = browse_dir(label_load, FileHandle.LOAD.value)
            textbox_load_dir.insert("0.0", self.load_dir)

        button_get_load_dir = c_tk.CTkButton(
            master=load_dir_frame,
            text="Browse Directories",
            command=browse_load,
        )
        button_get_load_dir.pack(side=c_tk.LEFT)
        load_dir_frame.pack(fill="both")

        # Frame for save dir
        save_dir_frame = c_tk.CTkFrame(main_frame)
        label_save = set_label("Save directory:", save_dir_frame, padding=(10, 10))

        textbox_save_dir = c_tk.CTkTextbox(
            save_dir_frame, height=20, width=400, activate_scrollbars=False
        )
        textbox_save_dir.configure(state="normal")
        textbox_save_dir.pack(side=c_tk.LEFT)

        def browse_save():
            self.save_dir = browse_dir(label_save, FileHandle.SAVE.value)
            textbox_save_dir.insert("0.0", self.save_dir)

        button_get_save_dir = c_tk.CTkButton(
            master=save_dir_frame,
            text="Browse Directories",
            command=browse_save,
        )
        button_get_save_dir.pack(side=c_tk.LEFT)
        save_dir_frame.pack(fill="both")

        # Frame for buffer time
        buffer_time_frame = c_tk.CTkFrame(main_frame)
        label_buffer_time = set_label(
            "Buffer Time:", buffer_time_frame, padding=(10, 10)
        )

        def combobox_callback(choice):
            print("combobox dropdown clicked:", choice)

        combobox_buffer_time = c_tk.CTkComboBox(
            buffer_time_frame, values=["1", "2", "3"], command=combobox_callback
        )
        combobox_buffer_time.pack(side=c_tk.RIGHT)

        buffer_time_frame.pack()


if __name__ == "__main__":
    app = App()
    app.mainloop()
