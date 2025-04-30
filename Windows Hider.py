import tkinter as tk
from tkinter import ttk
import win32gui, win32con
from pynput import keyboard
import threading
import sys
import os # Adicionado para lidar com caminhos de ícones no PyInstaller

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

        # Listener de teclado
        self.listener = None # Inicializa como None
        self.setup_keyboard_listener()

        # Atualização periódica do status (inicia após a UI)
        # self.update_status() # Movido para iniciar após o mainloop talvez? Não, aqui está ok.

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

        # Instruções (*** ALTERADO AQUI ***)
        ttk.Label(frame, text="Pressione Ctrl+w para ocultar a janela ativa\n"
                             "Pressione Ctrl+Q para restaurar todas as janelas",
                 justify=tk.CENTER).pack(pady=10)

        # Botões
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(btn_frame, text="Ocultar Janela Ativa",
                  command=self.hide_active_window).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(btn_frame, text="Restaurar Janelas",
                  command=self.restore_windows).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        # Removido o botão Sair para incentivar o uso do 'X' ou bandeja
        # ttk.Button(btn_frame, text="Sair",
        #           command=self.exit_app).pack(side=tk.RIGHT, padx=5)

        # Iniciar atualização do status DEPOIS que os labels foram criados
        self.update_status()

    def setup_keyboard_listener(self):
        # Definir atalhos diretamente (*** ALTERADO AQUI ***)
        hotkeys = {
            '<ctrl>+w': self.hide_active_window,  # Alterado de 'a' para 'z'
            '<ctrl>+q': self.restore_windows
        }
        try:
            self.listener = keyboard.GlobalHotKeys(hotkeys)
            self.listener_thread = threading.Thread(target=self.listener.start, daemon=True)
            self.listener_thread.start()
            print("Listener de teclado iniciado.")
        except Exception as e:
            print(f"Erro ao iniciar o listener de teclado: {e}")
            self.status_text = "Erro no listener de teclado!"
            # Tentar atualizar o status label se já existir
            if hasattr(self, 'status_label'):
                self.status_label.config(text=self.status_text)


    def hide_active_window(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            # Não ocultar a própria interface ou janelas já ocultas
            if hwnd and hwnd != self.root.winfo_id() and hwnd not in self.hidden_windows:
                window_title = win32gui.GetWindowText(hwnd)
                # Ignorar janelas sem título ou que sejam parte do sistema/background
                if window_title and win32gui.IsWindowVisible(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
                    self.hidden_windows.append(hwnd)
                    self.status_text = f"Ocultada: {window_title[:30]}..." if len(window_title) > 30 else f"Ocultada: {window_title}"
                    print(f"Ocultada: {window_title} (HWND: {hwnd})") # Log
                    self.update_counter() # Atualiza só o contador imediatamente
        except Exception as e:
            print(f"Erro ao ocultar janela: {e}")
            self.status_text = "Erro ao ocultar."
        # Atualiza o status label (mesmo em caso de erro)
        if hasattr(self, 'status_label'):
            self.status_label.config(text=self.status_text)


    def restore_windows(self):
        count = 0
        restored_hwnds = []
        failed_hwnds = []
        for hwnd in self.hidden_windows:
            try:
                # Verifica se a janela ainda existe antes de tentar mostrar
                if win32gui.IsWindow(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                    win32gui.SetForegroundWindow(hwnd) # Tenta trazer para frente
                    restored_hwnds.append(hwnd)
                    count += 1
                    print(f"Restaurada: {win32gui.GetWindowText(hwnd)} (HWND: {hwnd})") # Log
                else:
                    print(f"Janela não existe mais (HWND: {hwnd})") # Log
                    failed_hwnds.append(hwnd)
            except Exception as e:
                print(f"Erro ao restaurar HWND {hwnd}: {e}") # Log
                failed_hwnds.append(hwnd) # Marca para remover

        # Limpa a lista apenas das janelas que foram restauradas ou falharam
        self.hidden_windows = [hwnd for hwnd in self.hidden_windows if hwnd not in restored_hwnds and hwnd not in failed_hwnds]

        self.status_text = f"Restauradas {count} janelas."
        if not self.hidden_windows:
             self.status_text = "Todas as janelas restauradas."

        self.update_status() # Atualiza status e contador

    def update_status(self):
        # Garante que os widgets existem antes de tentar configurá-los
        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
            self.status_label.config(text=self.status_text)
        if hasattr(self, 'counter_label') and self.counter_label.winfo_exists():
             self.counter_label.config(text=f"Janelas ocultas: {len(self.hidden_windows)}")
        # Reagenda a atualização
        # self.root.after(1000, self.update_status) # Atualiza a cada 1 segundo

    def update_counter(self):
         if hasattr(self, 'counter_label') and self.counter_label.winfo_exists():
             self.counter_label.config(text=f"Janelas ocultas: {len(self.hidden_windows)}")

    def exit_app(self):
        print("Saindo da aplicação...")
        self.restore_windows()  # Tenta restaurar janelas antes de sair
        if self.listener:
            try:
                print("Parando listener...")
                self.listener.stop()
                # Esperar a thread do listener terminar pode ser uma boa ideia
                if hasattr(self, 'listener_thread') and self.listener_thread.is_alive():
                     self.listener_thread.join(timeout=1.0) # Espera 1 segundo
                     if self.listener_thread.is_alive():
                          print("Warning: Listener thread não terminou.")
            except Exception as e:
                 print(f"Erro ao parar o listener: {e}")

        if self.root:
            try:
                print("Destruindo janela root...")
                self.root.destroy()
            except tk.TclError as e:
                 print(f"Erro ao destruir root (provavelmente já fechado): {e}")
        print("Saindo do processo.")
        sys.exit(0) # Usa sys.exit(0) para indicar saída normal

# --- Funções Auxiliares para PyInstaller ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- Main ---
if __name__ == "__main__":
    root = tk.Tk()
    app = WindowHiderApp(root)

    # Ação ao fechar a janela (clicar no 'X')
    root.protocol("WM_DELETE_WINDOW", app.exit_app) # Chama a função de saída limpa

    # Tenta definir um ícone (opcional, crie um 'icon.ico' na mesma pasta)
    icon_path = "icon.ico" # Nome do arquivo do ícone
    try:
        # Usa resource_path se for empacotado com PyInstaller
        abs_icon_path = resource_path(icon_path)
        if os.path.exists(abs_icon_path):
             root.iconbitmap(abs_icon_path)
        else:
             print(f"Ícone '{icon_path}' não encontrado.")
    except Exception as e:
        print(f"Não foi possível definir o ícone: {e}")


    root.mainloop()

    # Código após mainloop (geralmente não é alcançado a menos que a janela seja fechada programaticamente sem sys.exit)
    print("Mainloop finalizado.")
    # Garante que o listener seja parado se o mainloop terminar por algum motivo inesperado
    if app.listener and app.listener.is_alive():
        app.listener.stop()
