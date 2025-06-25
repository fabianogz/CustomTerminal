import customtkinter as ctk
import subprocess
import threading

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class TerminalApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.overrideredirect(True)
        self.geometry("900x520")
        self.minsize(600, 400)
        self.configure(bg="#000000")

        self._offsetx = 0
        self._offsety = 0
        self._resizing = False
        self._resize_border_size = 10

        self.title_bar = ctk.CTkFrame(self, height=35, fg_color="#111111", corner_radius=15)
        self.title_bar.pack(fill="x", side="top")
        self.title_bar.bind("<Button-1>", self.click_window)
        self.title_bar.bind("<B1-Motion>", self.move_window)

        self.close_button = ctk.CTkButton(
            self.title_bar, text="X", width=30, height=25, command=self.destroy,
            fg_color="red", hover_color="#aa0000", text_color="white", font=("Consolas", 13)
        )
        self.close_button.pack(side="right", padx=10, pady=5)

        self.output_box = ctk.CTkTextbox(self, wrap="word", font=("Consolas", 13), corner_radius=0)
        self.output_box.place(x=0, y=35, relwidth=1, relheight=0.85)
        self.output_box.configure(state="disabled", fg_color="#000000", text_color="#ffffff")

        self.entry = ctk.CTkEntry(self, font=("Consolas", 13), placeholder_text="Digite um comando...", corner_radius=0, height=35)
        self.entry.place(relx=0, rely=0.92, relwidth=1)
        self.entry.bind("<Return>", self.execute_command)

        self.bind("<Motion>", self.resize_cursor)
        self.bind("<ButtonPress-1>", self.start_resize)
        self.bind("<B1-Motion>", self.do_resize)

    def click_window(self, event):
        self._offsetx = event.x
        self._offsety = event.y

    def move_window(self, event):
        if not self._resizing:
            x = event.x_root - self._offsetx
            y = event.y_root - self._offsety
            self.geometry(f'+{x}+{y}')

    def execute_command(self, event=None):
        command = self.entry.get()
        self.entry.delete(0, "end")
        self.print_output(f"> {command}\n", "white")
        threading.Thread(target=self.run_command, args=(command,), daemon=True).start()

    def run_command(self, command):
        try:
            result = subprocess.run(
                ["powershell", "-Command", command],
                capture_output=True, text=True, shell=True
            )
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            if stdout:
                self.print_output(stdout + "\n", "green")
            if stderr:
                self.print_output(stderr + "\n", "red")

        except Exception as e:
            self.print_output(f"Erro: {e}\n", "red")

    # Exibir saída com cor
    def print_output(self, text, color="white"):
        self.output_box.configure(state="normal")
        tag_name = f"tag_{color}_{self.output_box.index('end')}"
        self.output_box.insert("end", text)
        self.output_box.tag_config(tag_name, foreground=color)
        start_index = f"end-{len(text)}c"
        self.output_box.tag_add(tag_name, start_index, "end")
        self.output_box.see("end")
        self.output_box.configure(state="disabled")

    # Redimensionamento visual
    def resize_cursor(self, event):
        x, y = event.x, event.y
        if x >= self.winfo_width() - self._resize_border_size and y >= self.winfo_height() - self._resize_border_size:
            self.config(cursor="size_nw_se")
        else:
            self.config(cursor="arrow")

    def start_resize(self, event):
        x, y = event.x, event.y
        if x >= self.winfo_width() - self._resize_border_size and y >= self.winfo_height() - self._resize_border_size:
            self._resizing = True
            self._resize_start_x = event.x
            self._resize_start_y = event.y
        else:
            self._resizing = False

    def do_resize(self, event):
        if self._resizing:
            dx = event.x - self._resize_start_x
            dy = event.y - self._resize_start_y
            new_width = self.winfo_width() + dx
            new_height = self.winfo_height() + dy
            self.geometry(f"{new_width}x{new_height}")

if __name__ == "__main_S_":
    app = TerminalApp()
    app.mainloop()
