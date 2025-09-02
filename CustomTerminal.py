import customtkinter as ctk
import tkinter as tk
import subprocess
import os
import threading
import sys
import re
from pathlib import Path

class Terminal(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Terminal")
        self.geometry("1000x600")
        self.minsize(600, 400)
        
        self.current_directory = os.getcwd()
        self.command_history = []
        self.history_index = -1
        self.running_process = None
        self.prompt_start_pos = "1.0"
        
        self.powershell_commands = frozenset({
            'get-', 'set-', 'new-', 'remove-', 'add-', 'clear-', 'start-', 'stop-',
            'restart-', 'test-', 'invoke-', 'select-', 'where-', 'sort-', 'group-',
            'measure-', 'compare-', 'foreach-', 'export-', 'import-', 'convert-',
            'join-', 'split-', 'format-', 'out-', 'write-', 'read-', 'enter-',
            'exit-', 'push-', 'pop-', 'show-', 'hide-', 'enable-', 'disable-',
            'update-', 'install-', 'uninstall-', 'save-', 'restore-', 'backup-'
        })
        
        self.cmd_commands = frozenset({
            'dir', 'copy', 'xcopy', 'move', 'del', 'rd', 'md', 'type', 'find', 
            'findstr', 'attrib', 'chkdsk', 'sfc', 'dism', 'reg', 'net', 'sc',
            'tasklist', 'taskkill', 'systeminfo', 'ipconfig', 'ping', 'tracert',
            'nslookup', 'netstat', 'arp', 'route', 'cipher', 'robocopy', 'tree',
            'fc', 'comp', 'diskpart', 'format', 'vol', 'label', 'subst', 'assoc',
            'ftype', 'doskey', 'more', 'sort', 'clip', 'where', 'whoami'
        })
        
        self.system_commands = frozenset({
            'python', 'pip', 'node', 'npm', 'git', 'docker', 'java', 'javac',
            'gcc', 'make', 'cmake', 'curl', 'wget', 'ssh', 'scp', 'rsync'
        })
        
        self.setup_ui()
        self.setup_bindings()
        self.setup_colors()
        self.show_prompt()
        
    def setup_ui(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.text_widget = tk.Text(
            main_frame,
            wrap="word",
            bg="#0c0c0c",
            fg="#ffffff",
            insertbackground="#ffffff",
            font=("Consolas", 12),
            selectbackground="#264f78",
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=10
        )
        
        scrollbar = tk.Scrollbar(main_frame, command=self.text_widget.yview)
        self.text_widget.config(yscrollcommand=scrollbar.set)
        
        self.text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def setup_colors(self):
        self.text_widget.tag_configure("success", foreground="#00d7ff")
        self.text_widget.tag_configure("error", foreground="#ff6b6b")
        self.text_widget.tag_configure("warning", foreground="#feca57")
        self.text_widget.tag_configure("info", foreground="#70a5fd")
        self.text_widget.tag_configure("command", foreground="#ffffff")
        self.text_widget.tag_configure("neutral", foreground="#c0c0c0")
        self.text_widget.tag_configure("prompt", foreground="#ffffff")
        self.text_widget.tag_configure("path", foreground="#ff9ff3")
        self.text_widget.tag_configure("number", foreground="#54a0ff")
        
    def setup_bindings(self):
        self.text_widget.bind("<Return>", self.on_enter)
        self.text_widget.bind("<Up>", self.history_up)
        self.text_widget.bind("<Down>", self.history_down)
        self.text_widget.bind("<Control-c>", self.cancel_command)
        self.text_widget.bind("<Control-l>", self.clear_terminal)
        self.text_widget.bind("<KeyPress>", self.on_key_press)
        self.text_widget.bind("<Button-1>", self.on_click)
        self.text_widget.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.text_widget.bind("<B1-Motion>", self.on_mouse_drag)
        self.text_widget.bind("<Button-3>", self.on_right_click)
        self.text_widget.bind("<Control-a>", self.on_select_current_line)
        self.text_widget.bind("<Control-A>", self.on_select_current_line)
        self.text_widget.bind("<Delete>", self.on_delete)
        self.text_widget.focus()
        
    def on_right_click(self, event):
        return "break"
        
    def on_select_current_line(self, event):
        prompt_end_pos = self.get_prompt_end_position()
        last_line = int(self.text_widget.index(tk.END).split('.')[0]) - 1
        line_end = f"{last_line}.end"
        
        self.text_widget.tag_add(tk.SEL, prompt_end_pos, line_end)
        self.text_widget.mark_set(tk.INSERT, line_end)
        return "break"
        
    def on_mouse_release(self, event):
        if self.text_widget.tag_ranges(tk.SEL):
            sel_start = self.text_widget.index(tk.SEL_FIRST)
            sel_end = self.text_widget.index(tk.SEL_LAST)
            prompt_end_pos = self.get_prompt_end_position()
            
            if self.text_widget.compare(sel_start, "<", prompt_end_pos):
                self.text_widget.tag_remove(tk.SEL, "1.0", tk.END)
                self.text_widget.mark_set(tk.INSERT, prompt_end_pos)
                
    def on_mouse_drag(self, event):
        pass
        
    def on_delete(self, event):
        if self.text_widget.tag_ranges(tk.SEL):
            sel_start = self.text_widget.index(tk.SEL_FIRST)
            prompt_end_pos = self.get_prompt_end_position()
            
            if self.text_widget.compare(sel_start, ">=", prompt_end_pos):
                return None
            else:
                return "break"
        return None
        
    def on_click(self, event):
        last_line = int(self.text_widget.index(tk.END).split('.')[0]) - 1
        prompt_end_pos = self.get_prompt_end_position()
        click_pos = self.text_widget.index(f"@{event.x},{event.y}")
        
        if self.text_widget.compare(click_pos, "<", prompt_end_pos):
            self.text_widget.mark_set(tk.INSERT, prompt_end_pos)
            return "break"
        
        current_line = int(click_pos.split('.')[0])
        if current_line < last_line:
            self.text_widget.mark_set(tk.INSERT, prompt_end_pos)
            return "break"
        
    def on_key_press(self, event):
        current_pos = self.text_widget.index(tk.INSERT)
        prompt_end_pos = self.get_prompt_end_position()
        last_line = int(self.text_widget.index(tk.END).split('.')[0]) - 1
        current_line = int(current_pos.split('.')[0])
        
        if current_line < last_line:
            if event.keysym in ['Up', 'Down', 'Control_L', 'Control_R', 'Shift_L', 'Shift_R']:
                return None
            self.text_widget.mark_set(tk.INSERT, prompt_end_pos)
            return "break"
        
        if event.keysym in ['BackSpace', 'Delete']:
            if self.text_widget.tag_ranges(tk.SEL):
                sel_start = self.text_widget.index(tk.SEL_FIRST)
                if self.text_widget.compare(sel_start, ">=", prompt_end_pos):
                    return None
                else:
                    return "break"
            elif self.text_widget.compare(current_pos, "<=", prompt_end_pos):
                return "break"
                
        if event.keysym == 'Left':
            if self.text_widget.compare(current_pos, "<=", prompt_end_pos):
                return "break"
                
        if event.keysym == 'Home':
            self.text_widget.mark_set(tk.INSERT, prompt_end_pos)
            return "break"
            
    def get_prompt_end_position(self):
        last_line = int(self.text_widget.index(tk.END).split('.')[0]) - 1
        line_content = self.text_widget.get(f"{last_line}.0", f"{last_line}.end")
        
        if "> " in line_content:
            prompt_end = line_content.find("> ") + 2
            return f"{last_line}.{prompt_end}"
        return f"{last_line}.0"
        
    def get_current_command(self):
        prompt_end_pos = self.get_prompt_end_position()
        last_line = int(self.text_widget.index(tk.END).split('.')[0]) - 1
        return self.text_widget.get(prompt_end_pos, f"{last_line}.end").strip()
        
    def show_prompt(self):
        prompt = f"{self.current_directory}> "
        self.text_widget.insert(tk.END, prompt, "prompt")
        self.text_widget.mark_set(tk.INSERT, tk.END)
        self.text_widget.see(tk.END)
        
    def on_enter(self, event):
        command = self.get_current_command()
        
        if not command:
            self.text_widget.insert(tk.END, "\n")
            self.show_prompt()
            return "break"
            
        self.text_widget.insert(tk.END, "\n")
        
        if command not in self.command_history:
            self.command_history.append(command)
        self.history_index = -1
        
        if self.handle_internal_commands(command):
            return "break"
            
        threading.Thread(target=self.execute_command, args=(command,), daemon=True).start()
        return "break"
        
    def handle_internal_commands(self, command):
        parts = command.strip().split()
        if not parts:
            return True
            
        cmd = parts[0].lower()
        
        if cmd == 'help':
            self.append_text("Available commands: help, clear, cd, history, exit\n", "info")
            self.show_prompt()
            return True
            
        elif cmd in ['clear', 'cls']:
            self.clear_terminal()
            return True
            
        elif cmd == 'cd':
            if len(parts) > 1:
                self.change_directory(' '.join(parts[1:]))
            else:
                self.append_text(f"{self.current_directory}\n", "info")
                self.show_prompt()
            return True
            
        elif cmd == 'history':
            if self.command_history:
                for i, hist_cmd in enumerate(self.command_history[-20:], 1):
                    self.append_text(f"  {i:2d}. {hist_cmd}\n", "neutral")
            self.show_prompt()
            return True
            
        elif cmd == 'exit':
            self.quit()
            return True
            
        return False
        
    def change_directory(self, path):
        try:
            if path == "..":
                new_path = Path(self.current_directory).parent
            else:
                new_path = Path(path).resolve()
                
            if new_path.exists() and new_path.is_dir():
                self.current_directory = str(new_path)
                os.chdir(self.current_directory)
                self.show_prompt()
            else:
                self.append_text("The system cannot find the path specified.\n", "error")
                self.show_prompt()
                
        except Exception:
            self.append_text("Access denied.\n", "error")
            self.show_prompt()
            
    def detect_command_type(self, command):
        if not command:
            return 'auto'
            
        cmd_lower = command.lower().strip()
        cmd_parts = cmd_lower.split()
        first_cmd = cmd_parts[0] if cmd_parts else ""
        
        internal_commands = {'help', 'clear', 'cd', 'history', 'exit'}
        if first_cmd in internal_commands:
            return 'internal'
            
        powershell_indicators = (
            any(cmd_lower.startswith(ps_cmd) for ps_cmd in self.powershell_commands) or
            '$' in command or
            ('|' in command and any(x in cmd_lower for x in ['select-', 'where-', 'sort-', 'group-', 'measure-'])) or
            'foreach' in cmd_lower or
            '.net' in cmd_lower or
            'system.' in cmd_lower or
            (cmd_lower.startswith('[') and ']' in cmd_lower) or
            any(x in cmd_lower for x in ['-property', '-filter', '-object']) or
            '::' in command or
            ('{' in command and '}' in command and '$_' in command)
        )
        
        if powershell_indicators:
            return 'powershell'
            
        if first_cmd in self.cmd_commands:
            return 'cmd'
            
        if first_cmd in self.system_commands:
            return 'system'
            
        python_indicators = (
            first_cmd in ['python', 'python3'] or
            'import ' in cmd_lower or
            any(x in cmd_lower for x in ['def ', 'class ', 'print(', 'for ', 'if ', 'while ', 'try:', 'except:']) or
            (cmd_lower.startswith('from ') and ' import ' in cmd_lower) or
            cmd_lower.endswith('.py')
        )
        
        if python_indicators:
            return 'python'
            
        if any(first_cmd.endswith(ext) for ext in ['.exe', '.bat', '.cmd', '.ps1', '.msi']):
            return 'system'
            
        return 'auto'
        
    def execute_command(self, command):
        execution_strategies = {
            'powershell': (["powershell.exe", "-NoProfile", "-Command", command], False),
            'cmd': (["cmd.exe", "/c", command], False),
            'python': (["python", "-c", command] if not command.startswith('python ') else command.split(), False),
            'system': (command, True)
        }
        
        try:
            command_type = self.detect_command_type(command)
            
            if command_type in execution_strategies:
                full_command, shell = execution_strategies[command_type]
            else:
                full_command, shell = command, True
            
            process_config = {
                'shell': shell,
                'cwd': self.current_directory,
                'stdout': subprocess.PIPE,
                'stderr': subprocess.PIPE,
                'text': True,
                'encoding': "cp850" if os.name == "nt" else "utf-8",
                'errors': "replace"
            }
            
            if os.name == "nt":
                process_config['creationflags'] = subprocess.CREATE_NO_WINDOW
            
            self.running_process = subprocess.Popen(full_command, **process_config)
            stdout, stderr = self.running_process.communicate(timeout=60)
            
            self.after(0, self.process_result, stdout, stderr, self.running_process.returncode)
            
        except subprocess.TimeoutExpired:
            if self.running_process:
                self.running_process.kill()
            self.after(0, self.append_text, "Command timed out (60s)\n", "warning")
            self.after(0, self.show_prompt)
        except FileNotFoundError:
            if command_type == 'auto':
                self.try_fallback_execution(command)
            else:
                self.after(0, self.append_text, f"'{command.split()[0]}' is not recognized as an internal or external command.\n", "error")
                self.after(0, self.show_prompt)
        except Exception as e:
            self.after(0, self.append_text, f"Error: {str(e)}\n", "error")
            self.after(0, self.show_prompt)
        finally:
            self.running_process = None
            
    def try_fallback_execution(self, command):
        fallback_strategies = [
            (["powershell.exe", "-NoProfile", "-Command", command], False),
            (["cmd.exe", "/c", command], False),
            (command, True)
        ]
        
        for full_command, shell in fallback_strategies:
            try:
                self.running_process = subprocess.Popen(
                    full_command,
                    shell=shell,
                    cwd=self.current_directory,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="cp850",
                    errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                )
                
                stdout, stderr = self.running_process.communicate(timeout=60)
                
                if stdout or (stderr and "not recognized" not in stderr.lower()):
                    self.after(0, self.process_result, stdout, stderr, self.running_process.returncode)
                    return
                    
            except Exception:
                continue
                
        self.after(0, self.append_text, f"'{command.split()[0]}' is not recognized as an internal or external command.\n", "error")
        self.after(0, self.show_prompt)
        self.running_process = None
        
    def process_result(self, stdout, stderr, return_code):
        if stdout:
            colored_output = self.colorize_output(stdout, return_code == 0)
            self.append_colored_text(colored_output)
            
        if stderr:
            self.append_text(stderr, "error")
            
        self.show_prompt()
        self.running_process = None
        
    def colorize_output(self, text, is_success):
        if not text.strip():
            return [("", "neutral")]
            
        lines = text.split('\n')
        colored_lines = []
        
        error_patterns = frozenset(['error', 'fail', 'exception', 'denied'])
        warning_patterns = frozenset(['warning', 'warn', 'caution', 'alert'])
        success_patterns = frozenset(['success', 'complete', 'done', 'ok', 'ready'])
        
        path_regex = re.compile(r'[A-Za-z]:\\|\/\w+\/|\.\\|\.\/')
        number_regex = re.compile(r'^\s*\d+\s*$')
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                colored_lines.append(("", "neutral"))
                continue
                
            line_lower = line.lower()
            
            if path_regex.search(line):
                colored_lines.append((line, "path"))
            elif number_regex.match(line_stripped):
                colored_lines.append((line, "number"))
            elif any(word in line_lower for word in error_patterns):
                colored_lines.append((line, "error"))
            elif any(word in line_lower for word in warning_patterns):
                colored_lines.append((line, "warning"))
            elif any(word in line_lower for word in success_patterns):
                colored_lines.append((line, "success"))
            else:
                colored_lines.append((line, "success" if is_success else "neutral"))
                
        return colored_lines
        
    def append_colored_text(self, colored_lines):
        for line_text, color_tag in colored_lines:
            if line_text or color_tag == "neutral":
                self.append_text(line_text + "\n", color_tag)
                
    def append_text(self, text, tag="neutral"):
        self.text_widget.insert(tk.END, text, tag)
        self.text_widget.see(tk.END)
        
    def clear_terminal(self, event=None):
        self.text_widget.delete(1.0, tk.END)
        self.show_prompt()
        return "break"
        
    def history_up(self, event):
        if self.command_history and self.history_index > -len(self.command_history):
            self.history_index -= 1
            self.replace_current_command(self.command_history[self.history_index])
        return "break"
        
    def history_down(self, event):
        if self.command_history:
            if self.history_index < -1:
                self.history_index += 1
                self.replace_current_command(self.command_history[self.history_index])
            else:
                self.history_index = -1
                self.replace_current_command("")
        return "break"
        
    def replace_current_command(self, command):
        prompt_end_pos = self.get_prompt_end_position()
        last_line = int(self.text_widget.index(tk.END).split('.')[0]) - 1
        self.text_widget.delete(prompt_end_pos, f"{last_line}.end")
        self.text_widget.insert(prompt_end_pos, command)
        
    def cancel_command(self, event):
        if self.running_process:
            try:
                self.running_process.terminate()
                self.append_text("\n^C\n", "warning")
                self.show_prompt()
            except:
                pass
        return "break"

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    app = Terminal()
    app.mainloop()
