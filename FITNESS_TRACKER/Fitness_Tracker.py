


import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
from datetime import datetime, timedelta

DATA_DIR = "fitness_data"
os.makedirs(DATA_DIR, exist_ok=True)

CURRENT_USER = None
# Exercise Categories + Calories table/min
EXERCISES = {
    "Cardio": { "Running": 10, "Cycling": 8, "Skipping Rope": 12,
                "Zumba": 9, "Aerobics": 7, "Treadmill Walk": 6 },

    "Strength / Muscle Training": { "Push-ups": 7, "Squats": 6, "Weight Training": 8, "Plank": 5,
                                    "Deadlift": 9,  "Bench Press": 8, "Lunges": 6 },

    "Yoga / Flexibility": { "Yoga": 4, "Surya Namaskar": 5 },

    "Swimming": { "Swimming": 9 }
}

def login_window(root):
    login = tk.Toplevel(root)
    login.title("Login")
    login.geometry("260x160")
    login.resizable(False, False)

    tk.Label(login, text="Username").pack(pady=5)
    user_var = tk.StringVar()
    tk.Entry(login, textvariable=user_var).pack()

    def do_login():
        global CURRENT_USER
        user = user_var.get().strip()
        if not user or user == "":
            messagebox.showerror("Error", "Username is required")
            return
        CURRENT_USER = user
        print(f"User logged in: {CURRENT_USER}")
        login.destroy()

    tk.Button(login, text="Login", command=do_login).pack(pady=10)
    login.grab_set()
    login.wait_window()


class FitnessTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Fitness Tracker - {CURRENT_USER}")

        # Load existing data or create new dataframe
        file = os.path.join(DATA_DIR, f"{CURRENT_USER}.csv")
        if os.path.exists(file):
            self.data = pd.read_csv(file)
            print(f"Loaded {len(self.data)} previous workouts")  # debugging print
        else:
            self.data = pd.DataFrame(columns=['date', 'exercise', 'duration', 'calories'])

        # Category selection buttons
        cat_frame = ttk.LabelFrame(root, text="Select Category")
        cat_frame.pack(fill='x', pady=5)

        self.selected_category = tk.StringVar()
        for cat in EXERCISES.keys():
            ttk.Button(cat_frame, text=cat,
                       command=lambda c=cat: self.show_exercises(c)).pack(side='left', padx=3, pady=3)

        self.ex_frame = ttk.LabelFrame(root, text="Select Exercise")
        self.ex_frame.pack(fill='x', pady=5)
        self.selected_exercise = tk.StringVar()

        # Duration input
        duration_frame = ttk.LabelFrame(root, text="Duration (Minutes)")
        duration_frame.pack(fill='x')

        self.duration_var = tk.StringVar()
        ttk.Entry(duration_frame, textvariable=self.duration_var).pack(pady=5)
        ttk.Button(duration_frame, text="Add Workout", command=self.add_workout).pack(pady=5)

        # Workout history table
        table = ttk.LabelFrame(root, text="Workout Log", padding=10)
        table.pack(fill='both', expand=True)
        self.tree = ttk.Treeview(table, columns=('date', 'exercise', 'duration', 'calories'), show='headings')

        self.tree.heading('date', text='Date')
        self.tree.heading('exercise', text='Exercise')
        self.tree.heading('duration', text='Minutes')
        self.tree.heading('calories', text='Calories Burned')

        self.tree.pack(fill='both', expand=True)

        # load previous workouts into table
        self.show_data()

        ttk.Button(root, text="Show Summary", command=self.show_summary).pack(pady=5)

    def show_exercises(self, category):
        for widget in self.ex_frame.winfo_children():
            widget.destroy()

        self.selected_category.set(category)
        print(f"Category selected: {category}")  # debug

        for ex in EXERCISES[category].keys():
            ttk.Button(self.ex_frame, text=ex,
                       command=lambda e=ex: self.selected_exercise.set(e)).pack(side='left', padx=3, pady=3)

    def add_workout(self):
        exercise = self.selected_exercise.get()
        duration = self.duration_var.get().strip()

        if not exercise:
            messagebox.showerror("Error", "Select an exercise")
            return

        if not duration.isdigit():
            messagebox.showerror("Error", "Enter valid duration")
            return

        #Fix Me: It breaks when user enters negative input
        duration = int(duration)

        for cat in EXERCISES:
            if exercise in EXERCISES[cat]:
                calories = duration * EXERCISES[cat][exercise]
                break

        # Using date as string to avoid timezone issues with pandas
        today = datetime.now().strftime('%Y-%m-%d')
        self.data.loc[len(self.data)] = [today, exercise, duration, calories]

        file = os.path.join(DATA_DIR, f"{CURRENT_USER}.csv")
        self.data.to_csv(file, index=False)
        print(f"Added {exercise} ({duration}min) → {calories} kcal")  # debug
        self.tree.insert('', 'end', values=(today, exercise, duration, calories))

        self.duration_var.set("")
        self.selected_exercise.set("")
        messagebox.showinfo("Success", f"{exercise} added!")

    def show_data(self):
        for i, row in self.data.iterrows():
            self.tree.insert('', 'end', values=(row['date'], row['exercise'], row['duration'], row['calories']))

    def show_summary(self):
        # TODO: Adding line chart that shows calories burned over last 30 days
        if self.data.empty:
            messagebox.showinfo("Summary", "No workouts yet.")
            return

        # note: pd.to_datetime might fail on corrupted dates, hence errors='coerce'
        self.data['date'] = pd.to_datetime(self.data['date'], errors='coerce').dt.date
        last_week = (datetime.now() - timedelta(days=7)).date()
        week_total = self.data[self.data['date'] >= last_week]['duration'].sum()

        calories = self.data['calories'].sum()
        avg_cal = self.data['calories'].mean()

        messagebox.showinfo("Progress Summary",
                            f" Last 7 Days: {week_total} min\n Total Calories: {calories} kcal\n "
                            f"Avg Calories/Session: {avg_cal:.1f} kcal")

if __name__ == "__main__":
    temp_root = tk.Tk()
    temp_root.withdraw()
    login_window(temp_root)
    temp_root.destroy()

    root = tk.Tk()
    app = FitnessTrackerApp(root)
    root.mainloop()










