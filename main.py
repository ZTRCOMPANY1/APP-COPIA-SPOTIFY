import os
import json
import threading
import random
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import pygame
import yt_dlp

# Cria pasta data se não existir
if not os.path.exists("data"):
    os.makedirs("data")

# Funções para carregar e salvar playlists
def carregar_playlists():
    if os.path.exists("playlists.json"):
        try:
            with open("playlists.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def salvar_playlists(playlists):
    with open("playlists.json", "w", encoding="utf-8") as f:
        json.dump(playlists, f, indent=4, ensure_ascii=False)

class MeuSpotifyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Meu Spotify App")
        self.geometry("800x500")
        self.resizable(False, False)
        self.playlists = carregar_playlists()
        self.playlist_atual = None
        self.musica_atual_index = -1
        self.modo_aleatorio = False
        self.volume_atual = 1.0

        pygame.mixer.init()

        self.criar_layout()
        self.exibir_playlists()

        self.protocol("WM_DELETE_WINDOW", self.encerrar)

    def criar_layout(self):
        # Frames principais
        frame_playlists = tk.Frame(self, width=200, bg="#121212")
        frame_playlists.pack(side="left", fill="y")

        frame_musicas = tk.Frame(self, bg="#181818")
        frame_musicas.pack(side="left", fill="both", expand=True)

        # Título playlists
        tk.Label(frame_playlists, text="Playlists", fg="white", bg="#121212", font=("Arial", 14, "bold")).pack(pady=10)

        # Lista de playlists
        self.listbox_playlists = tk.Listbox(frame_playlists, bg="#1e1e1e", fg="white", font=("Arial", 12), activestyle="none")
        self.listbox_playlists.pack(fill="both", expand=True, padx=10, pady=5)
        self.listbox_playlists.bind("<<ListboxSelect>>", self.selecionar_playlist)

        # Botão nova playlist
        btn_nova_playlist = tk.Button(frame_playlists, text="Nova Playlist", command=self.criar_nova_playlist, bg="#2a2a2a", fg="white")
        btn_nova_playlist.pack(pady=10, padx=10, fill="x")

        # Título músicas
        self.label_musicas = tk.Label(frame_musicas, text="Selecione uma playlist", fg="white", bg="#181818", font=("Arial", 14, "bold"))
        self.label_musicas.pack(pady=10)

        # Lista músicas
        self.listbox_musicas = tk.Listbox(frame_musicas, bg="#222222", fg="white", font=("Arial", 12), activestyle="none")
        self.listbox_musicas.pack(fill="both", expand=True, padx=10, pady=5)
        self.listbox_musicas.bind("<Double-Button-1>", self.tocar_musica_selecionada)

        # Botões controle músicas
        frame_controles = tk.Frame(frame_musicas, bg="#181818")
        frame_controles.pack(pady=10)

        btn_retroceder = tk.Button(frame_controles, text="<<", command=self.musica_retroceder, width=5, bg="#2a2a2a", fg="white")
        btn_retroceder.grid(row=0, column=0, padx=5)

        self.btn_play_pause = tk.Button(frame_controles, text="Play", command=self.play_pause_musica, width=7, bg="#2a2a2a", fg="white")
        self.btn_play_pause.grid(row=0, column=1, padx=5)

        btn_avancar = tk.Button(frame_controles, text=">>", command=self.musica_avancar, width=5, bg="#2a2a2a", fg="white")
        btn_avancar.grid(row=0, column=2, padx=5)

        # Botão modo aleatório
        self.btn_aleatorio = tk.Button(frame_controles, text="Aleatório: OFF", command=self.toggle_aleatorio, width=15, bg="#2a2a2a", fg="white")
        self.btn_aleatorio.grid(row=0, column=3, padx=10)

        # Botão adicionar música por arquivo
        btn_add_arquivo = tk.Button(frame_controles, text="Adicionar Música (Arquivo)", command=self.adicionar_musica_arquivo, bg="#2a2a2a", fg="white")
        btn_add_arquivo.grid(row=1, column=0, columnspan=2, pady=10)

        # Botão adicionar música por link Youtube
        btn_add_link = tk.Button(frame_controles, text="Adicionar Música (YouTube)", command=self.adicionar_link_youtube, bg="#2a2a2a", fg="white")
        btn_add_link.grid(row=1, column=2, columnspan=2, pady=10)

        # Controle de volume
        volume_frame = tk.Frame(frame_musicas, bg="#181818")
        volume_frame.pack(pady=10)

        tk.Label(volume_frame, text="Volume", fg="white", bg="#181818").pack(side="left", padx=5)
        self.volume_slider = ttk.Scale(volume_frame, from_=0, to=1, orient="horizontal", command=self.ajustar_volume)
        self.volume_slider.set(self.volume_atual)
        self.volume_slider.pack(side="left", padx=5, fill="x", expand=True)

        # Mensagens
        self.label_status = tk.Label(self, text="", fg="white", bg="#121212", font=("Arial", 10))
        self.label_status.pack(side="bottom", fill="x")

    def nova_mensagem(self, texto):
        self.label_status.config(text=texto)
        self.after(5000, lambda: self.label_status.config(text=""))

    def exibir_playlists(self):
        self.listbox_playlists.delete(0, tk.END)
        for nome in self.playlists.keys():
            self.listbox_playlists.insert(tk.END, nome)

    def criar_nova_playlist(self):
        nome = simpledialog.askstring("Nova Playlist", "Digite o nome da playlist:")
        if nome:
            if nome in self.playlists:
                messagebox.showerror("Erro", "Playlist já existe.")
                return
            self.playlists[nome] = {"musicas": []}
            salvar_playlists(self.playlists)
            self.exibir_playlists()

    def selecionar_playlist(self, event):
        if not self.listbox_playlists.curselection():
            return
        idx = self.listbox_playlists.curselection()[0]
        nome = self.listbox_playlists.get(idx)
        self.playlist_atual = nome
        self.label_musicas.config(text=f"Músicas - {nome}")
        self.exibir_musicas(nome)
        self.musica_atual_index = -1
        self.btn_play_pause.config(text="Play")

    def exibir_musicas(self, playlist):
        self.listbox_musicas.delete(0, tk.END)
        for musica in self.playlists[playlist]["musicas"]:
            nome_musica = os.path.basename(musica)
            self.listbox_musicas.insert(tk.END, nome_musica)

    def tocar_musica_selecionada(self, event=None):
        if self.playlist_atual is None:
            return
        selecionados = self.listbox_musicas.curselection()
        if not selecionados:
            return
        idx = selecionados[0]
        self.tocar_musica(idx)

    def tocar_musica(self, idx):
        musicas = self.playlists[self.playlist_atual]["musicas"]
        if idx < 0 or idx >= len(musicas):
            return

        caminho = musicas[idx]
        if not os.path.exists(caminho):
            messagebox.showerror("Erro", f"Música não encontrada:\n{caminho}")
            return

        try:
            pygame.mixer.music.load(caminho)
            pygame.mixer.music.play()
            pygame.mixer.music.set_volume(self.volume_atual)
            self.musica_atual_index = idx
            self.btn_play_pause.config(text="Pause")
            self.nova_mensagem(f"Tocando: {os.path.basename(caminho)}")
        except Exception as e:
            messagebox.showerror("Erro ao tocar música", str(e))

    def play_pause_musica(self):
        if not pygame.mixer.music.get_busy():
            # Tocar a música atual, ou a primeira
            if self.musica_atual_index == -1 and self.playlist_atual:
                if self.playlists[self.playlist_atual]["musicas"]:
                    self.tocar_musica(0)
            else:
                pygame.mixer.music.play()
                self.btn_play_pause.config(text="Pause")
        else:
            pygame.mixer.music.pause()
            self.btn_play_pause.config(text="Play")

    def musica_avancar(self):
        if self.playlist_atual is None:
            return
        musicas = self.playlists[self.playlist_atual]["musicas"]
        if not musicas:
            return

        if self.modo_aleatorio:
            idx = random.randint(0, len(musicas) - 1)
        else:
            idx = (self.musica_atual_index + 1) % len(musicas)

        self.tocar_musica(idx)

    def musica_retroceder(self):
        if self.playlist_atual is None:
            return
        musicas = self.playlists[self.playlist_atual]["musicas"]
        if not musicas:
            return

        if self.modo_aleatorio:
            idx = random.randint(0, len(musicas) - 1)
        else:
            idx = (self.musica_atual_index - 1) % len(musicas)

        self.tocar_musica(idx)

    def toggle_aleatorio(self):
        self.modo_aleatorio = not self.modo_aleatorio
        texto = "Aleatório: ON" if self.modo_aleatorio else "Aleatório: OFF"
        self.btn_aleatorio.config(text=texto)
        self.nova_mensagem(f"Modo aleatório {'ativado' if self.modo_aleatorio else 'desativado'}")

    def adicionar_musica_arquivo(self):
        if self.playlist_atual is None:
            messagebox.showwarning("Aviso", "Selecione uma playlist antes.")
            return
        arquivos = filedialog.askopenfilenames(title="Selecione músicas", filetypes=[("Arquivos de áudio", "*.mp3 *.wav *.ogg")])
        if not arquivos:
            return
        for arquivo in arquivos:
            # Copiar arquivo para pasta data
            nome_arquivo = os.path.basename(arquivo)
            destino = os.path.join("data", nome_arquivo)
            try:
                if not os.path.exists(destino):
                    with open(arquivo, "rb") as src, open(destino, "wb") as dst:
                        dst.write(src.read())
                self.playlists[self.playlist_atual]["musicas"].append(destino)
            except Exception as e:
                self.nova_mensagem(f"Erro ao adicionar arquivo: {str(e)}")

        salvar_playlists(self.playlists)
        self.exibir_musicas(self.playlist_atual)
        self.nova_mensagem("Música(s) adicionada(s) com sucesso.")

    def adicionar_link_youtube(self):
        if self.playlist_atual is None:
            messagebox.showwarning("Aviso", "Selecione uma playlist antes.")
            return

        url = simpledialog.askstring("YouTube", "Cole o link do vídeo ou playlist do YouTube:")
        if not url:
            return

        def baixar_audio():
            self.nova_mensagem("Baixando áudio do YouTube...")

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'data/%(title)s.%(ext)s',
                'noplaylist': False,
                'quiet': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if 'entries' in info:
                        for video in info['entries']:
                            caminho = f"data/{video['title']}.mp3"
                            if caminho not in self.playlists[self.playlist_atual]["musicas"]:
                                self.playlists[self.playlist_atual]["musicas"].append(caminho)
                    else:
                        caminho = f"data/{info['title']}.mp3"
                        if caminho not in self.playlists[self.playlist_atual]["musicas"]:
                            self.playlists[self.playlist_atual]["musicas"].append(caminho)

                salvar_playlists(self.playlists)
                self.exibir_musicas(self.playlist_atual)
                self.nova_mensagem("Música(s) adicionada(s) com sucesso.")
            except yt_dlp.utils.PostProcessingError:
                self.nova_mensagem("Erro: FFmpeg não encontrado ou inválido. Instale e adicione FFmpeg no PATH.")
            except Exception as e:
                self.nova_mensagem(f"Erro ao baixar áudio: {str(e)}")

        threading.Thread(target=baixar_audio).start()

    def ajustar_volume(self, val):
        try:
            volume = float(val)
            pygame.mixer.music.set_volume(volume)
            self.volume_atual = volume
        except Exception as e:
            self.nova_mensagem(f"Erro ao ajustar volume: {str(e)}")
            
    def encerrar(self):
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        self.destroy()



if __name__ == "__main__":
    app = MeuSpotifyApp()
    app.mainloop()
