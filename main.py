import os
import json
from datetime import datetime, timedelta
from tkinter import *
from tkinter import messagebox, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

DISTRACTION_FILE = "distractions.json"

class DistractionTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WorkWise - Pomodoro with Distraction Tracker")
        self.root.geometry("800x600")

        self.session_duration = IntVar(value=25)  # in minutes
        self.timer_label = None
        self.remaining_time = 0
        self.timer_running = False
        self.after_id = None

        self.distraction_text = StringVar()
        self.distraction_category = StringVar(value="Future")
        self.session_notes = []
        self.report_option = StringVar(value="Today")

        self.init_ui()

    def init_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill='both')

        self.home_tab = Frame(notebook)
        self.history_tab = Frame(notebook)
        self.report_tab = Frame(notebook)
        self.help_tab = Frame(notebook)

        notebook.add(self.home_tab, text="Home")
        notebook.add(self.history_tab, text="History")
        notebook.add(self.report_tab, text="Report")
        notebook.add(self.help_tab, text="Help")

        self.build_home_tab()
        self.build_history_tab()
        self.build_report_tab()
        self.build_help_tab()

    def build_home_tab(self):
        # Pomodoro section
        pomodoro_frame = Frame(self.home_tab)
        pomodoro_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=10, pady=10)

        Label(pomodoro_frame, text="Pomodoro Timer", font=("Helvetica", 16)).pack(pady=10)

        timer_settings = Frame(pomodoro_frame)
        timer_settings.pack(pady=5)
        Radiobutton(timer_settings, text="25 / 5", variable=self.session_duration, value=25).pack(side=LEFT)
        Radiobutton(timer_settings, text="50 / 10", variable=self.session_duration, value=50).pack(side=LEFT)

        self.timer_label = Label(pomodoro_frame, text="00:00", font=("Helvetica", 32))
        self.timer_label.pack(pady=10)

        Button(pomodoro_frame, text="Start", command=self.start_timer).pack(pady=5)
        Button(pomodoro_frame, text="Stop", command=self.stop_timer).pack(pady=5)

        # Distraction section
        distraction_frame = Frame(self.home_tab)
        distraction_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=10, pady=10)

        Label(distraction_frame, text="Track Distractions", font=("Helvetica", 16)).pack(pady=10)

        category_frame = Frame(distraction_frame)
        category_frame.pack()
        for cat in ["Future", "Past", "Wishes/Imagination"]:
            Radiobutton(category_frame, text=cat, variable=self.distraction_category, value=cat).pack(side=LEFT)

        self.note_text = Text(distraction_frame, height=8, width=50)
        self.note_text.pack(pady=10)

        Button(distraction_frame, text="Log Distraction", command=self.save_distraction).pack(pady=5)
        Button(distraction_frame, text="Clear Text", command=lambda: self.note_text.delete("1.0", END)).pack()

    def start_timer(self):
        if not self.timer_running:
            self.remaining_time = self.session_duration.get() * 60
            self.update_timer()
            self.timer_running = True

    def stop_timer(self):
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.timer_running = False
        self.timer_label.config(text="00:00")

    def update_timer(self):
        mins, secs = divmod(self.remaining_time, 60)
        self.timer_label.config(text=f"{mins:02d}:{secs:02d}")
        if self.remaining_time > 0:
            self.remaining_time -= 1
            self.after_id = self.root.after(1000, self.update_timer)
        else:
            messagebox.showinfo("Pomodoro", "Session Completed!")
            self.show_session_notes()

    def show_session_notes(self):
        if self.session_notes:
            notes_text = "\n\n".join([f"{n['category']}: {n['note']}" for n in self.session_notes])
            messagebox.showinfo("Session Notes", notes_text)
            self.session_notes.clear()

    def save_distraction(self):
        note = self.note_text.get("1.0", END).strip()
        category = self.distraction_category.get()
        if not note:
            return messagebox.showwarning("Empty Note", "Please enter a note before saving.")

        entry = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "note": note
        }

        self.session_notes.append(entry)

        if os.path.exists(DISTRACTION_FILE):
            with open(DISTRACTION_FILE, "r") as f:
                data = json.load(f)
        else:
            data = []

        data.append(entry)
        with open(DISTRACTION_FILE, "w") as f:
            json.dump(data, f, indent=2)

        self.note_text.delete("1.0", END)
        self.load_history()

    def build_history_tab(self):
        Label(self.history_tab, text="Distraction History", font=("Helvetica", 16)).pack(pady=10)
        self.history_box = Text(self.history_tab, wrap=WORD, width=80, height=25)
        self.history_box.pack(padx=10, pady=5)
        Button(self.history_tab, text="Clear History", command=self.clear_history).pack(pady=5)
        self.load_history()

    def load_history(self):
        self.history_box.delete("1.0", END)
        if os.path.exists(DISTRACTION_FILE):
            with open(DISTRACTION_FILE, "r") as f:
                try:
                    data = json.load(f)
                    for entry in data[-100:]:
                        self.history_box.insert(END, f"[{entry['timestamp'][:16]}] {entry['category']} -> {entry['note']}\n\n")
                except:
                    pass

    def clear_history(self):
        if os.path.exists(DISTRACTION_FILE):
            os.remove(DISTRACTION_FILE)
        self.load_history()

    def build_report_tab(self):
        Label(self.report_tab, text="Generate Report", font=("Helvetica", 16)).pack(pady=10)
        options = ["Today", "7 Days", "15 Days", "30 Days"]
        for opt in options:
            Radiobutton(self.report_tab, text=opt, variable=self.report_option, value=opt).pack(anchor=W)

        Button(self.report_tab, text="Generate", command=self.generate_report).pack(pady=10)
        self.report_chart_frame = Frame(self.report_tab)
        self.report_chart_frame.pack()

    def generate_report(self):
        if not os.path.exists(DISTRACTION_FILE):
            return messagebox.showinfo("No Data", "No distractions to report.")

        with open(DISTRACTION_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return messagebox.showerror("Error", "Unable to read JSON.")

        option = self.report_option.get()
        now = datetime.now()
        delta_days = {"Today": 0, "7 Days": 7, "15 Days": 15, "30 Days": 30}
        start_time = now - timedelta(days=delta_days.get(option, 0))

        categories = {"Future": 0, "Past": 0, "Wishes/Imagination": 0}
        for entry in data:
            try:
                timestamp = datetime.fromisoformat(entry["timestamp"])
                if timestamp >= start_time:
                    cat = entry["category"]
                    if cat in categories:
                        categories[cat] += 1
            except:
                continue

        for widget in self.report_chart_frame.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots(figsize=(5, 3))
        ax.bar(categories.keys(), categories.values(), color=["#f39c12", "#3498db", "#9b59b6"])
        ax.set_title("Distraction Summary")
        ax.set_ylabel("Count")
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.report_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=10)

    def build_help_tab(self):
        text = Text(self.help_tab, wrap=WORD)
        text.pack(fill=BOTH, expand=True)
        text.insert(END, "🧠 MindFocus Usage Guide:\n\n")
        text.insert(END, "1. Select Pomodoro duration (25 or 50 minutes).\n")
        text.insert(END, "2. Click 'Start' to begin session.\n")
        text.insert(END, "3. If a distraction occurs, choose its category and write a note.\n")
        text.insert(END, "4. Submit the distraction. Notes appear after session ends.\n")
        text.insert(END, "5. View distraction history, clear if needed.\n")
        text.insert(END, "6. Generate visual reports from the 'Report' tab.\n")

if __name__ == "__main__":
    root = Tk()
    app = DistractionTrackerApp(root)
    root.mainloop()

