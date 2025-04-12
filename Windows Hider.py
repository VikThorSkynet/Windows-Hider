import tkinter as tk
from tkinter import ttk
import win32gui, win32con
from pynput import keyboard
import threading
import sys

class WindowHiderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Window Hider")
        self.root.geometry("300x210")
        self.root.resizable(False, False)

        # Configurações
        self.hidden_windows = []
        self.status_text = "Pronto para ocultar janelas"

        # Interface
        self.setup_ui()

        # Listener de teclado (usando GlobalHotKeys para maior confiabilidade)
        self.setup_keyboard_listener()

        # Atualização periódica do status
        self.update_status()

    def setup_ui(self):
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Título
        ttk.Label(frame, text="Window Hider", font=("Arial", 12, "bold")).pack(pady=(0, 10))

        # Status
        self.status_label = ttk.Label(frame, text=self.status_text, wraplength=280)
        self.status_label.pack(pady=5)

        # Contador
        self.counter_label = ttk.Label(frame, text="Janelas ocultas: 0")
        self.counter_label.pack(pady=5)

        # Instruções
        ttk.Label(frame, text="Pressione Ctrl+A para ocultar a janela ativa\n"
                             "Pressione Ctrl+Q para restaurar todas as janelas",
                 justify=tk.CENTER).pack(pady=10)

        # Botões
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(btn_frame, text="Ocultar Janela Ativa",
                  command=self.hide_active_window).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Restaurar Janelas",
                  command=self.restore_windows).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Sair",
                  command=self.exit_app).pack(side=tk.RIGHT, padx=5)

    def setup_keyboard_listener(self):
        # Definir atalhos diretamente
        hotkeys = {
            '<ctrl>+a': self.hide_active_window,
            '<ctrl>+q': self.restore_windows
        }

        self.listener = keyboard.GlobalHotKeys(hotkeys)
        self.listener.start()

    def hide_active_window(self):
        hwnd = win32gui.GetForegroundWindow()
        # Não ocultar a própria interface
        if hwnd and hwnd != self.root.winfo_id() and hwnd not in self.hidden_windows:
            window_title = win32gui.GetWindowText(hwnd)
            if window_title:  # Ignorar janelas sem título
                win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
                self.hidden_windows.append(hwnd)
                self.status_text = f"Ocultada: {window_title}"
                self.update_status()

    def restore_windows(self):
        count = 0
        for hwnd in self.hidden_windows:
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                count += 1
            except:
                pass  # Ignorar janelas que não existem mais

        self.hidden_windows.clear()
        self.status_text = f"Restauradas {count} janelas"
        self.update_status()

    def update_status(self):
        self.status_label.config(text=self.status_text)
        self.counter_label.config(text=f"Janelas ocultas: {len(self.hidden_windows)}")
        self.root.after(500, self.update_status)

    def exit_app(self):
        self.restore_windows()  # Restaurar janelas antes de sair
        if self.listener:
            self.listener.stop()
        self.root.destroy()
        sys.exit()

if __name__ == "__main__":
    root = tk.Tk()
    app = WindowHiderApp(root)

    # Minimizar para bandeja ao fechar
    root.protocol("WM_DELETE_WINDOW", lambda: root.iconify())

    root.mainloop()