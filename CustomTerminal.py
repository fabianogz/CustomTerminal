import customtkinter as ctk
import tkinter as tk
import subprocess

class TerminalApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Custom Terminal")
        self.geometry("800x600")

        self.output_text = tk.Text(self, wrap="word", bg="black", fg="white", insertbackground="white")
        self.output_text.pack(expand=True, fill="both", padx=10, pady=10)

        input_frame = ctk.CTkFrame(self)
        input_frame.pack(fill="x", padx=10, pady=10)

        self.command_entry = ctk.CTkEntry(input_frame)
        self.command_entry.pack(side="left", expand=True, fill="x", padx=(0, 10))
        self.command_entry.bind("<Return>", self.execute_command)

        execute_button = ctk.CTkButton(input_frame, text="Executar", command=self.execute_command)
        execute_button.pack(side="left")

        self.shell_type = "powershell"  

        self.setup_tags()

    def execute_command(self, event=None):
        command = self.command_entry.get().strip()
        if not command:
            return

        self.output_text.insert("end", f"> {command}\n", "neutral")

        try:
            if self.shell_type == "powershell":
                full_command = ["powershell", "-Command", command]
            else:
                full_command = command

            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                encoding="cp850",
                errors="replace"
            )


            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            if stdout:
                self.output_text.insert("end", stdout + "\n", "success")

            if stderr:
                self.output_text.insert("end", stderr + "\n", "error")

            if not stdout and not stderr:
                self.output_text.insert("end", "Comando executado sem saída.\n", "neutral")

            self.output_text.see("end")

        except Exception as e:
            self.output_text.insert("end", f"Erro ao executar comando: {str(e)}\n", "error")

        self.command_entry.delete(0, "end")

    def setup_tags(self):
        self.output_text.tag_configure("success", foreground="green")
        self.output_text.tag_configure("error", foreground="red")
        self.output_text.tag_configure("neutral", foreground="white")

if __name__ == "__main__":
    app = TerminalApp()
    app.mainloop()
