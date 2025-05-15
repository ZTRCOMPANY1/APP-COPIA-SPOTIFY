import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import pygame
import os
import json
import random
import threading
import yt_dlp

CAMINHO_PLAYLISTS = "playlists.json"
CAMINHO_MUSICAS = "musicas"

pygame.init()
pygame.mixer.init()

def salvar_playlists(playlists):
    with open(CAMINHO_PLAYLISTS, "w", encoding="utf-8") as f:
        json.dump(playlists, f, indent=4)

def carregar_playlists():
    if not os.path.exists(CAMINHO_PLAYLISTS):
        with open(CAMINHO_PLAYLISTS, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(CAMINHO_PLAYLISTS, "r", encoding="utf-8") as f:
        return json.load(f)

def baixar_musica(url, destino):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(destino, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'ffmpeg_location': 'ffmpeg'  # Certifique-se de que está no PATH
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

class MeuSpotifyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Meu Spotify")
        self.geometry("800x600")
        self.configure(bg="#121212")

        self.playlists = carregar_playlists()
        self.playlist_atual = None
        self.musica_atual_index = -1
        self.shuffle = False
        self.paused = False

        self.criar_interface()

    def criar_interface(self):
        # Lista de playlists
        self.lista_playlists = tk.Listbox(self, bg="#1DB954", fg="white", font=("Arial", 12))
        self.lista_playlists.pack(side="left", fill="y", padx=10, pady=10)
        self.lista_playlists.bind("<<ListboxSelect>>", self.selecionar_playlist)

        # Lista de músicas
        self.lista_musicas = tk.Listbox(self, bg="#222", fg="white", font=("Arial", 12))
        self.lista_musicas.pack(fill="both", expand=True, padx=10, pady=10)
        self.lista_musicas.bind("<<ListboxSelect>>", self.selecionar_musica)

        # Botões de controle
        controles = tk.Frame(self, bg="#121212")
        controles.pack(pady=10)

        self.btn_play_pause = tk.Button(controles, text="Play", command=self.play_pause_musica)
        self.btn_play_pause.grid(row=0, column=0, padx=5)

        tk.Button(controles, text="⏮️", command=self.musica_anterior).grid(row=0, column=1, padx=5)
        tk.Button(controles, text="⏭️", command=self.proxima_musica).grid(row=0, column=2, padx=5)
        tk.Button(controles, text="🔀", command=self.toggle_shuffle).grid(row=0, column=3, padx=5)

        # Volume
        self.slider_volume = tk.Scale(controles, from_=0, to=1, resolution=0.01, orient="horizontal", label="Volume")
        self.slider_volume.set(0.5)
        self.slider_volume.grid(row=0, column=4, padx=10)
        self.slider_volume.bind("<ButtonRelease-1>", lambda e: pygame.mixer.music.set_volume(self.slider_volume.get()))

        # Botões gerais
        botoes = tk.Frame(self, bg="#121212")
        botoes.pack(pady=5)

        tk.Button(botoes, text="Nova Playlist", command=self.criar_playlist).pack(side="left", padx=5)
        tk.Button(botoes, text="Adicionar Música", command=self.adicionar_musica).pack(side="left", padx=5)
        tk.Button(botoes, text="Adicionar por Link", command=self.adicionar_por_link).pack(side="left", padx=5)

        # Carregar playlists
        self.atualizar_lista_playlists()

    def criar_playlist(self):
        nome = simpledialog.askstring("Nova Playlist", "Nome da playlist:")
        if nome and nome not in self.playlists:
            self.playlists[nome] = {"musicas": []}
            salvar_playlists(self.playlists)
            self.atualizar_lista_playlists()

    def atualizar_lista_playlists(self):
        self.lista_playlists.delete(0, "end")
        for nome in self.playlists:
            self.lista_playlists.insert("end", nome)

    def selecionar_playlist(self, event):
        selecao = self.lista_playlists.curselection()
        if selecao:
            self.playlist_atual = self.lista_playlists.get(selecao[0])
            self.atualizar_lista_musicas()

    def atualizar_lista_musicas(self):
        self.lista_musicas.delete(0, "end")
        musicas = self.playlists[self.playlist_atual]["musicas"]
        for musica in musicas:
            self.lista_musicas.insert("end", os.path.basename(musica))

    def adicionar_musica(self):
        if not self.playlist_atual:
            messagebox.showerror("Erro", "Selecione uma playlist primeiro.")
            return
        arquivos = filedialog.askopenfilenames(filetypes=[("MP3 files", "*.mp3")])
        if arquivos:
            self.playlists[self.playlist_atual]["musicas"].extend(arquivos)
            salvar_playlists(self.playlists)
            self.atualizar_lista_musicas()

    def adicionar_por_link(self):
        if not self.playlist_atual:
            messagebox.showerror("Erro", "Selecione uma playlist primeiro.")
            return
        url = simpledialog.askstring("Link da Música", "Cole o link do YouTube ou Spotify:")
        if url:
            os.makedirs(CAMINHO_MUSICAS, exist_ok=True)
            threading.Thread(target=self.baixar_e_adicionar, args=(url,)).start()

    def baixar_e_adicionar(self, url):
        try:
            baixar_musica(url, CAMINHO_MUSICAS)
            novos_arquivos = [os.path.join(CAMINHO_MUSICAS, f) for f in os.listdir(CAMINHO_MUSICAS)]
            novos_arquivos.sort(key=os.path.getctime, reverse=True)
            ultimo_arquivo = novos_arquivos[0]
            self.playlists[self.playlist_atual]["musicas"].append(ultimo_arquivo)
            salvar_playlists(self.playlists)
            self.atualizar_lista_musicas()
        except Exception as e:
            messagebox.showerror("Erro ao baixar", str(e))

    def selecionar_musica(self, event):
        index = self.lista_musicas.curselection()
        if index:
            self.tocar_musica(index[0])

    def tocar_musica(self, index):
        try:
            musica = self.playlists[self.playlist_atual]["musicas"][index]
            pygame.mixer.music.load(musica)
            pygame.mixer.music.set_volume(self.slider_volume.get())
            pygame.mixer.music.play()
            self.musica_atual_index = index
            self.btn_play_pause.config(text="Pause")
            self.paused = False
        except:
            messagebox.showerror("Erro", "Não foi possível tocar a música.")

    def play_pause_musica(self):
        if not pygame.mixer.music.get_busy():
            if self.musica_atual_index == -1 and self.playlist_atual:
                if self.playlists[self.playlist_atual]["musicas"]:
                    self.tocar_musica(0)
            else:
                pygame.mixer.music.play()
                self.btn_play_pause.config(text="Pause")
                self.paused = False
        else:
            if self.paused:
                pygame.mixer.music.unpause()
                self.paused = False
                self.btn_play_pause.config(text="Pause")
            else:
                pygame.mixer.music.pause()
                self.paused = True
                self.btn_play_pause.config(text="Play")

    def proxima_musica(self):
        if self.playlist_atual:
            musicas = self.playlists[self.playlist_atual]["musicas"]
            if self.shuffle:
                novo_index = random.randint(0, len(musicas) - 1)
            else:
                novo_index = (self.musica_atual_index + 1) % len(musicas)
            self.tocar_musica(novo_index)

    def musica_anterior(self):
        if self.playlist_atual:
            musicas = self.playlists[self.playlist_atual]["musicas"]
            novo_index = (self.musica_atual_index - 1) % len(musicas)
            self.tocar_musica(novo_index)

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle
        estado = "Ativado" if self.shuffle else "Desativado"
        messagebox.showinfo("Modo Aleatório", f"Modo aleatório {estado}")

    def encerrar(self):
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        self.destroy()

if __name__ == "__main__":
    app = MeuSpotifyApp()
    app.protocol("WM_DELETE_WINDOW", app.encerrar)
    app.mainloop()
