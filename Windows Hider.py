import tkinter as tk
from tkinter import ttk
import win32gui, win32con
from pynput import keyboard
import threading
import sys

class WindowHiderApp:
    # Corrigido: __init__ precisa de dois underscores antes e depois
    def __init__(self, root):
        self.root = root
        self.root.title("Window Hider")
        self.root.geometry("300x210")
        self.root.resizable(False, False)

        # Configurações (indentação corrigida)
        self.hidden_windows = []
        self.status_text = "Pronto para ocultar janelas"

        # Interface
        self.setup_ui()

        # Listener de teclado (usando GlobalHotKeys para maior confiabilidade)
        self.setup_keyboard_listener()

        # Atualização periódica do status (removido loop explícito inicial, o after() cuida disso)
        # self.update_status() # update_status agora é chamado no final de setup_ui e se auto-reagenda

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

        # Instruções (Já estava correto no seu código original)
        ttk.Label(frame, text="Pressione Ctrl+Shift+A para ocultar a janela ativa\n"
                             "Pressione Ctrl+q para restaurar todas as janelas",
                 justify=tk.CENTER).pack(pady=10)

        # Botões
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10)

        # Expandir botões para preencher espaço
        ttk.Button(btn_frame, text="Ocultar Janela Ativa",
                  command=self.hide_active_window).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(btn_frame, text="Restaurar Janelas",
                  command=self.restore_windows).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(btn_frame, text="Sair",
                  command=self.exit_app).pack(side=tk.RIGHT, padx=5) # Botão sair pode ser menor

        # Inicia a atualização do status APÓS a UI ser criada
        self.update_status()

    def setup_keyboard_listener(self):
        # Definir atalhos diretamente
        hotkeys = {
            '<ctrl>+<shift>+a': self.hide_active_window,  # <<<--- ÚNICA ALTERAÇÃO FUNCIONAL AQUI
            '<ctrl>+q': self.restore_windows
        }
        try:
            # É boa prática rodar o listener em uma thread separada para não bloquear a GUI
            self.listener = keyboard.GlobalHotKeys(hotkeys)
            # O daemon=True faz a thread do listener fechar quando o programa principal fecha
            self.listener_thread = threading.Thread(target=self.listener.start, daemon=True)
            self.listener_thread.start()
        except Exception as e:
             print(f"Erro ao iniciar listener: {e}")
             self.status_text = "Erro no listener de teclado!"
             # Tenta atualizar o label se já existir
             if hasattr(self, 'status_label'):
                 self.status_label.config(text=self.status_text)


    def hide_active_window(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            # Não ocultar a própria interface ou janelas já ocultas
            if hwnd and hwnd != self.root.winfo_id() and hwnd not in self.hidden_windows:
                window_title = win32gui.GetWindowText(hwnd)
                # Ignorar janelas sem título ou que não sejam visíveis (pode evitar ocultar coisas do sistema)
                if window_title and win32gui.IsWindowVisible(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
                    self.hidden_windows.append(hwnd)
                    # Limita o tamanho do título exibido
                    display_title = (window_title[:35] + '...') if len(window_title) > 35 else window_title
                    self.status_text = f"Ocultada: {display_title}"
                    # Atualiza imediatamente o contador e status
                    self.update_counter()
                    self.status_label.config(text=self.status_text) # Atualiza o status label diretamente aqui
        except Exception as e:
            print(f"Erro ao ocultar janela: {e}")
            self.status_text = "Erro ao ocultar."
            if hasattr(self, 'status_label'):
                 self.status_label.config(text=self.status_text)


    def restore_windows(self):
        count = 0
        restored_hwnds = []
        failed_hwnds = []
        for hwnd in self.hidden_windows:
            try:
                # Verifica se a janela ainda existe
                if win32gui.IsWindow(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                    # Tenta trazer a janela para frente (pode não funcionar sempre)
                    try:
                         win32gui.SetForegroundWindow(hwnd)
                    except Exception: # Ignora erros ao trazer para frente
                         pass
                    restored_hwnds.append(hwnd)
                    count += 1
                else:
                    failed_hwnds.append(hwnd) # Marca para remover se não existe mais
            except Exception as e: # Captura erro específico ao tentar mostrar
                print(f"Erro ao restaurar HWND {hwnd}: {e}")
                failed_hwnds.append(hwnd) # Marca para remover se deu erro

        # Remove apenas as janelas processadas (restauradas ou falhas) da lista
        self.hidden_windows = [hwnd for hwnd in self.hidden_windows if hwnd not in restored_hwnds and hwnd not in failed_hwnds]

        if count > 0:
           self.status_text = f"Restauradas {count} janelas."
        elif not self.hidden_windows:
             self.status_text = "Nenhuma janela para restaurar."
        else:
             self.status_text = "Nenhuma janela foi restaurada (talvez já fechadas)."

        # Atualiza status e contador
        self.update_status()


    def update_status(self):
        # Garante que os widgets existam antes de configurar
        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
            self.status_label.config(text=self.status_text)
        if hasattr(self, 'counter_label') and self.counter_label.winfo_exists():
            self.counter_label.config(text=f"Janelas ocultas: {len(self.hidden_windows)}")
        # Reagenda a si mesmo para rodar novamente após 500ms
        # Isso garante atualizações periódicas caso o status mude por outros motivos
        # Mas cuidado para não sobrecarregar se as atualizações já acontecem nos métodos
        # self.root.after(500, self.update_status) # Comentado para evitar chamadas redundantes se status/contador já são atualizados diretamente

    def update_counter(self):
         # Função auxiliar para atualizar apenas o contador
         if hasattr(self, 'counter_label') and self.counter_label.winfo_exists():
             self.counter_label.config(text=f"Janelas ocultas: {len(self.hidden_windows)}")

    def exit_app(self):
        print("Tentando sair...")
        self.restore_windows()  # Restaurar janelas antes de sair
        if self.listener:
            print("Parando listener...")
            self.listener.stop()
            # Esperar a thread do listener terminar pode ser bom
            if hasattr(self, 'listener_thread') and self.listener_thread.is_alive():
                 self.listener_thread.join(timeout=0.5) # Espera um pouco
        print("Destruindo janela root...")
        self.root.destroy()
        print("Saindo do sistema.")
        sys.exit(0) # Termina o processo

# Corrigido: if __name__ == "__main__":
if __name__ == "__main__":
    root = tk.Tk()
    app = WindowHiderApp(root)

    # Ação ao fechar a janela (clicar no 'X') - chama exit_app para limpeza
    root.protocol("WM_DELETE_WINDOW", app.exit_app)

    # Remove a opção de minimizar para bandeja que pode ser confusa
    # root.protocol("WM_DELETE_WINDOW", lambda: root.iconify())

    root.mainloop()
