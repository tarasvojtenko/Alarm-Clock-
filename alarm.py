
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import threading
import time
from datetime import datetime, timedelta

try:
    import pygame
    pygame.mixer.init()
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False
    print("Для звука установите pygame: pip install pygame")

CONFIG_FILE = "alarm_config.json"

class AlarmClock:
    def __init__(self, root):
        self.root = root
        self.root.title("⏰ Будильник Pro")
        self.root.geometry("500x500")
        self.root.resizable(False, False)
        self.root.configure(bg="#2c3e50")
        
        self.alarm_time = None      # datetime.time
        self.repeat = "none"        # daily, weekdays, once
        self.sound_file = "beep.wav"
        self.active = False
        self.snooze_minutes = 5
        self.check_thread = None
        self.running = True
        
        self.load_config()
        self.create_widgets()
        self.update_clock()
        self.start_alarm_checker()
        
    def create_widgets(self):
        # Текущее время
        self.clock_label = tk.Label(self.root, font=('Digital', 48, 'bold'), bg="#2c3e50", fg="#ecf0f1")
        self.clock_label.pack(pady=20)
        
        # Фрейм установки времени
        frame_time = tk.Frame(self.root, bg="#2c3e50")
        frame_time.pack(pady=10)
        tk.Label(frame_time, text="Время будильника:", bg="#2c3e50", fg="white", font=('Arial', 12)).pack(side=tk.LEFT, padx=5)
        self.hour_spin = tk.Spinbox(frame_time, from_=0, to=23, width=3, font=('Arial', 14), format="%02.0f")
        self.hour_spin.pack(side=tk.LEFT, padx=2)
        tk.Label(frame_time, text=":", bg="#2c3e50", fg="white").pack(side=tk.LEFT)
        self.min_spin = tk.Spinbox(frame_time, from_=0, to=59, width=3, font=('Arial', 14), format="%02.0f")
        self.min_spin.pack(side=tk.LEFT, padx=2)
        tk.Label(frame_time, text=":", bg="#2c3e50", fg="white").pack(side=tk.LEFT)
        self.sec_spin = tk.Spinbox(frame_time, from_=0, to=59, width=3, font=('Arial', 14), format="%02.0f")
        self.sec_spin.pack(side=tk.LEFT, padx=2)
        
        # Повтор
        frame_repeat = tk.Frame(self.root, bg="#2c3e50")
        frame_repeat.pack(pady=5)
        tk.Label(frame_repeat, text="Повтор:", bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=5)
        self.repeat_var = tk.StringVar(value=self.repeat)
        for text, val in [("Один раз", "once"), ("Ежедневно", "daily"), ("По будням", "weekdays")]:
            rb = tk.Radiobutton(frame_repeat, text=text, variable=self.repeat_var, value=val,
                                bg="#2c3e50", fg="white", selectcolor="#2c3e50")
            rb.pack(side=tk.LEFT, padx=5)
        
        # Кнопки
        btn_frame = tk.Frame(self.root, bg="#2c3e50")
        btn_frame.pack(pady=15)
        self.set_btn = tk.Button(btn_frame, text="🔔 Установить", command=self.set_alarm,
                                 bg="#3498db", fg="white", font=('Arial', 12), width=12)
        self.set_btn.pack(side=tk.LEFT, padx=10)
        self.stop_btn = tk.Button(btn_frame, text="🔕 Выключить", command=self.stop_alarm,
                                  bg="#e74c3c", fg="white", font=('Arial', 12), width=12, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        self.snooze_btn = tk.Button(btn_frame, text="😴 Отложить (5 мин)", command=self.snooze,
                                    bg="#f39c12", fg="white", font=('Arial', 12), width=15, state=tk.DISABLED)
        self.snooze_btn.pack(side=tk.LEFT, padx=10)
        
        # Статус
        self.status_label = tk.Label(self.root, text="Будильник не установлен", bg="#2c3e50", fg="#bdc3c7", font=('Arial', 10))
        self.status_label.pack(pady=5)
        
        # Список предустановок
        preset_frame = tk.Frame(self.root, bg="#2c3e50")
        preset_frame.pack(pady=10)
        for label, (h,m,s) in [("07:00", (7,0,0)), ("08:30", (8,30,0)), ("21:00", (21,0,0))]:
            btn = tk.Button(preset_frame, text=label, command=lambda hh=h, mm=m, ss=s: self.set_preset(hh, mm, ss),
                            bg="#2ecc71", fg="white", width=8)
            btn.pack(side=tk.LEFT, padx=5)
        
    def update_clock(self):
        now = datetime.now().strftime("%H:%M:%S")
        self.clock_label.config(text=now)
        self.root.after(1000, self.update_clock)
    
    def set_preset(self, h, m, s):
        self.hour_spin.delete(0, tk.END)
        self.hour_spin.insert(0, f"{h:02d}")
        self.min_spin.delete(0, tk.END)
        self.min_spin.insert(0, f"{m:02d}")
        self.sec_spin.delete(0, tk.END)
        self.sec_spin.insert(0, f"{s:02d}")
        self.set_alarm()
    
    def set_alarm(self):
        try:
            h = int(self.hour_spin.get())
            m = int(self.min_spin.get())
            s = int(self.sec_spin.get())
            self.alarm_time = datetime.now().replace(hour=h, minute=m, second=s, microsecond=0)
            # если время уже прошло сегодня, переносим на завтра
            if self.alarm_time <= datetime.now():
                self.alarm_time += timedelta(days=1)
            self.repeat = self.repeat_var.get()
            self.active = True
            self.save_config()
            self.status_label.config(text=f"Будильник установлен на {self.alarm_time.strftime('%H:%M:%S')} | Повтор: {self.repeat}")
            self.set_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.snooze_btn.config(state=tk.NORMAL)
        except:
            messagebox.showerror("Ошибка", "Неверное время")
    
    def stop_alarm(self):
        self.active = False
        self.alarm_time = None
        self.set_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.snooze_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Будильник выключен")
        self.save_config()
    
    def snooze(self):
        if self.alarm_time:
            self.alarm_time += timedelta(minutes=self.snooze_minutes)
            self.status_label.config(text=f"Отложено до {self.alarm_time.strftime('%H:%M:%S')}")
            # Звук выключаем
            self.active = True   # остаётся активным
            self.save_config()
    
    def play_sound(self):
        def sound_loop():
            if SOUND_AVAILABLE:
                pygame.mixer.music.load(self.sound_file if os.path.exists(self.sound_file) else "beep.wav")
                pygame.mixer.music.play(loops=3)
            else:
                for _ in range(5):
                    print("\a")
                    time.sleep(0.5)
        threading.Thread(target=sound_loop, daemon=True).start()
    
    def check_alarm(self):
        while self.running:
            if self.active and self.alarm_time:
                now = datetime.now()
                # Проверка с учетом повторения
                should_ring = False
                if self.repeat == "once":
                    if now >= self.alarm_time:
                        should_ring = True
                elif self.repeat == "daily":
                    if now.time() >= self.alarm_time.time() and (now - self.alarm_time).seconds < 2:
                        should_ring = True
                elif self.repeat == "weekdays":
                    if now.weekday() < 5 and now.time() >= self.alarm_time.time() and (now - self.alarm_time).seconds < 2:
                        should_ring = True
                
                if should_ring:
                    self.active = False  # предотвращаем повторный звонок
                    self.root.after(0, self.ring_alarm)
                    # Для повтора "daily" или "weekdays" переустанавливаем на следующий день
                    if self.repeat in ("daily", "weekdays"):
                        next_day = self.alarm_time + timedelta(days=1)
                        self.alarm_time = next_day
                        self.active = True
                        self.save_config()
                        self.root.after(0, lambda: self.status_label.config(text=f"Следующий: {self.alarm_time.strftime('%H:%M:%S')}"))
                    else:
                        self.root.after(0, self.stop_alarm)
            time.sleep(0.5)
    
    def ring_alarm(self):
        self.play_sound()
        # Показываем окно с кнопками
        top = tk.Toplevel(self.root)
        top.title("Будильник!!!")
        top.geometry("300x150")
        top.configure(bg="#e74c3c")
        tk.Label(top, text="⏰ Просыпайтесь! ⏰", font=('Arial', 18, 'bold'), bg="#e74c3c", fg="white").pack(pady=20)
        def stop_and_close():
            self.stop_alarm()
            top.destroy()
        def snooze_and_close():
            self.snooze()
            top.destroy()
        tk.Button(top, text="Выключить", command=stop_and_close, bg="#2c3e50", fg="white", width=10).pack(side=tk.LEFT, padx=20)
        tk.Button(top, text="Отложить", command=snooze_and_close, bg="#f39c12", fg="white", width=10).pack(side=tk.RIGHT, padx=20)
    
    def start_alarm_checker(self):
        self.check_thread = threading.Thread(target=self.check_alarm, daemon=True)
        self.check_thread.start()
    
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                self.repeat = data.get("repeat", "once")
                self.snooze_minutes = data.get("snooze_minutes", 5)
                self.sound_file = data.get("sound_file", "beep.wav")
    
    def save_config(self):
        data = {
            "repeat": self.repeat,
            "snooze_minutes": self.snooze_minutes,
            "sound_file": self.sound_file
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f)
    
    def on_closing(self):
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AlarmClock(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
