# coding: utf-8

import asyncio
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog

import ffmpeg_helper
import subtitle_helper
from utils import async_callback, get_ext

class STSearchApp(tk.Tk):
    def __init__(self, interval=1/60):
        super().__init__()
        self.loop = asyncio.get_event_loop()
        self.tasks = []
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.loop.create_task(self.updater(interval))
        self.subtitles = []
        self.create_widgets()
        self.cancel_event = asyncio.Event()

    async def updater(self, interval):
        while True:
            self.update()
            await asyncio.sleep(interval)

    def cancel(self):
        self.cancel_event.set()
        self.cancel_event = asyncio.Event()

    @async_callback
    async def ask_extract_files(self):
        files = filedialog.askopenfilenames()
        if files and len(files):
            for name in files:
                print('loading ' + name + '...')
                tmp = await ffmpeg_helper.load_subtitles(file_input=name)
                for subtitle in tmp:
                    self.subtitles.append(subtitle_helper.Subtitle(
                        start=subtitle.start,
                        end=subtitle.end,
                        text=subtitle.text,
                        video=name
                    ))
        print('loaded {} subtitles'.format(len(self.subtitles)))

    def clear_subtitles(self):
        self.subtitles = []

    def search(self):
        # TODO: make search support multiple words
        self.audio = []
        self.results_box.delete(0, tk.END)
        self.results = list(subtitle_helper.search(self.subtitles, self.search_box.get()))
        for result in self.results:
            self.results_box.insert(tk.END, subtitle_helper.to_string(result))
            self.audio.append(False)

    @async_callback
    async def load_audio(self):
        idx = self.results_box.index(tk.ACTIVE)
        if not self.audio[idx]:
            r = self.results[idx]
            start, end, video = r.start, r.end, r.video
            self.audio[idx], _ = await ffmpeg_helper.trim(start, end, file_input=video, format=get_ext(video), format_out='matroska')
            print('loaded ' + video)

    @async_callback
    async def play_audio(self):
        idx = self.results_box.index(tk.ACTIVE)
        if not self.audio[idx]:
            print('Audio not loaded yet!')
            return
        sound, err = await ffmpeg_helper.trim(self.start_scale.get(), self.end_scale.get(), input=self.audio[idx], format='matroska', format_out='wav')
        await ffmpeg_helper.play_sound(input=sound, format='wav', event=self.cancel_event)

    @async_callback
    async def export_audio(self):
        idx = self.results_box.index(tk.ACTIVE)
        if not self.audio[idx]:
            print('Audio not loaded yet!')
            return
        out, err = await ffmpeg_helper.trim(self.start_scale.get(), self.end_scale.get(), input=self.audio[idx], format='matroska')
        n = filedialog.asksaveasfilename(filetypes=(('.mka files', '*.mka'),))
        if n is not None and len(n) > 0:
            if not n.endswith('.mka'):
                n = n + '.mka'
            with open(n, 'wb') as f:
                f.write(out)


    def create_extract_tab(self):
        tab = tk.Frame(master=self, bd=1, relief=tk.GROOVE)
        tab.grid()
        ttk.Label(master=tab, text='Extract').grid()
        e = ttk.Button(master=tab, text='Extract from files', command=self.ask_extract_files)
        e.grid(row=1, column=1, padx=10, pady=10)
        c = ttk.Button(master=tab, text='Clear', command=self.clear_subtitles)
        c.grid(row=1, column=2, padx=10, pady=10)
        return tab

    def create_search_tab(self):
        tab = tk.Frame(master=self, bd=1, relief=tk.GROOVE)
        tab.grid()
        ttk.Label(master=tab, text='Search').grid()
        self.search_box = ttk.Entry(master=tab)
        self.search_box.grid(row=1, column=1, padx=5, pady=10)
        b = ttk.Button(master=tab, text='Go', command=self.search)
        b.grid(row=1, column=2, padx=5, pady=10)
        self.results_box = tk.Listbox(master=tab)
        self.results_box.grid(row=2, column=1, padx=5, pady=10)
        return tab

    def create_audio_tab(self):
        tab = tk.Frame(master=self, bd=1, relief=tk.GROOVE)
        tab.grid()
        ttk.Label(master=tab, text='Clip').grid()
        ttk.Button(master=tab, text='Load audio segment', command=self.load_audio).grid(row=1, column=1, padx=10, pady=10)
        ttk.Button(master=tab, text='Play clip', command=self.play_audio).grid(row=2, column=1, padx=10, pady=10)
        ttk.Button(master=tab, text='Stop', command=self.cancel).grid(row=3, column=1, padx=10, pady=10)
        ttk.Button(master=tab, text='Export clip', command=self.export_audio).grid(row=4, column=1, padx=10, pady=10)
        self.start_scale = ttk.Scale(master=tab)
        self.start_scale.grid(row=5, column=1, padx=10, pady=10)
        self.end_scale = ttk.Scale(master=tab)
        self.end_scale.grid(row=6, column=1, padx=10, pady=10)
        return tab

    def create_widgets(self):
        self.create_extract_tab().grid(row=0, column=0, padx=10, pady=10)
        self.create_search_tab().grid(row=1, column=0, padx=10, pady=10)
        self.create_audio_tab().grid(row=0, rowspan=2, column=1, padx=10, pady=10)

    def close(self):
        self.loop.stop()
        self.destroy()

    def update(self):
        super().update()
        if self.results_box.size() > 0:
            idx = self.results_box.index(tk.ACTIVE)
            if idx >= 0 and len(self.results) > idx:
                s = self.results[idx]
                self.start_scale.config(from_=0, to_=s.end-s.start)
                self.end_scale.config(from_=0, to_=s.end-s.start)

if __name__ == '__main__':
    app = STSearchApp()
    app.loop.run_forever()
    app.loop.close()