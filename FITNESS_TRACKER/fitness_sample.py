

import requests
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

DATA_DIR = "fitness_data"
os.makedirs(DATA_DIR, exist_ok=True)

# Nutritionix API credentials
NUTRITIONIX_ID = os.getenv("NUTRITIONIX_ID")
NUTRITIONIX_KEY = os.getenv("NUTRITIONIX_KEY")

# Exercise Categories + Calories table/min
EXERCISES = {
    "Cardio": { "Running": 10, "Cycling": 8, "Skipping Rope": 12,
                "Zumba": 9, "Aerobics": 7, "Treadmill Walk": 6 },

    "Strength / Muscle Training": { "Push-ups": 7, "Squats": 6, "Weight Training": 8, "Plank": 5,
                                    "Deadlift": 9,  "Bench Press": 8, "Lunges": 6 },

    "Yoga / Flexibility": { "Yoga": 4, "Surya Namaskar": 5 },

    "Swimming": { "Swimming": 9 }
}


def get_exercise_calories_from_api(exercise, duration):
    """Fetch calories from Open Food Facts API (free, no auth needed)"""
    try:
        response = requests.get(
            "https://world.openfoodfacts.org/api/v0/product/search",
            params={"q": exercise, "page_size": 1},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()

        if data.get('products'):
            product = data['products'][0]
            # Get energy in kcal per 100g
            energy = product.get('energy_kcal_100g')
            if energy:
                return round(energy * duration / 10, 1)
    except Exception as e:
        print(f"API error: {e}")

    return None


def get_exercise_calories(exercise, duration):
    """Get calories for exercise using API, fallback to hardcoded values"""
    # Try API first
    api_calories = get_exercise_calories_from_api(exercise, duration)
    if api_calories:
        return api_calories

    # Fallback to hardcoded values
    for cat in EXERCISES:
        if exercise in EXERCISES[cat]:
            return duration * EXERCISES[cat][exercise]

    return duration * 10

def login_window(root):
    login = tk.Toplevel(root)
    login.title("Login")
    login.geometry("260x160")
    login.resizable(False, False)

    tk.Label(login, text="Username").pack(pady=5)
    user_var = tk.StringVar()
    tk.Entry(login, textvariable=user_var).pack()

    def do_login():
        user = user_var.get().strip()
        if not user or not user.isalnum() or len(user) < 3:
            messagebox.showerror("Error", "Username: 3+ alphanumeric chars")
            return
        root.username = user
        login.destroy()

    tk.Button(login, text="Login", command=do_login).pack(pady=10)
    login.grab_set()
    login.wait_window()


class FitnessTrackerApp:
    def __init__(self, root, username):
        self.root = root
        self.username = username
        self.root.title(f"Fitness Tracker - {self.username}")
        self.root.geometry("750x600")

        file = os.path.join(DATA_DIR, f"{self.username}.csv")
        if os.path.exists(file):
            try:
                self.data = pd.read_csv(file)
            except Exception as e:
                messagebox.showerror("Error", "Failed to load data")
                self.data = pd.DataFrame(columns=['date', 'exercise', 'duration', 'calories'])
        else:
            self.data = pd.DataFrame(columns=['date', 'exercise', 'duration', 'calories'])

        # Category selection
        cat_frame = ttk.LabelFrame(root, text="Select Category")
        cat_frame.pack(fill='x', pady=5, padx=5)

        self.selected_category = tk.StringVar()
        self.selected_exercise = tk.StringVar()
        for cat in EXERCISES.keys():
            ttk.Button(cat_frame, text=cat, command=lambda c=cat: self.show_exercises(c)).pack(side='left', padx=3)

        # Exercise selection
        self.ex_frame = ttk.LabelFrame(root, text="Select Exercise")
        self.ex_frame.pack(fill='x', pady=5, padx=5)

        # Duration input
        duration_frame = ttk.LabelFrame(root, text="Duration (Minutes)")
        duration_frame.pack(fill='x', padx=5)
        self.duration_var = tk.StringVar()
        ttk.Entry(duration_frame, textvariable=self.duration_var).pack(pady=5)

        # Status label for API calls
        self.status_label = ttk.Label(duration_frame, text="", foreground="blue")
        self.status_label.pack()

        ttk.Button(duration_frame, text="Add Workout", command=self.add_workout).pack(pady=5)

        # Workout table
        table_frame = ttk.LabelFrame(root, text="Workout Log")
        table_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.tree = ttk.Treeview(table_frame, columns=('date', 'exercise', 'duration', 'calories'), show='headings',
                                 height=10)
        self.tree.heading('date', text='Date')
        self.tree.heading('exercise', text='Exercise')
        self.tree.heading('duration', text='Minutes')
        self.tree.heading('calories', text='Calories')
        self.tree.pack(fill='both', expand=True)
        self.show_data()

        # Buttons
        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Show Summary", command=self.show_summary).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Logout", command=self.logout).pack(side='left', padx=5)

    def show_exercises(self, category):
        for widget in self.ex_frame.winfo_children():
            widget.destroy()
        for ex in EXERCISES[category].keys():
            ttk.Button(self.ex_frame, text=ex, command=lambda e=ex: self.selected_exercise.set(e)).pack(side='left', padx=3, pady=3)

    def add_workout(self):
        exercise = self.selected_exercise.get()
        duration = self.duration_var.get().strip()

        if not exercise:
            messagebox.showerror("Error", "Select an exercise")
            return

        try:
            duration = int(duration)
            if duration <= 0:
                messagebox.showerror("Error", "Duration must be positive")
                return
        except ValueError:
            messagebox.showerror("Error", "Enter valid duration")
            return

        # Show loading status
        self.status_label.config(text="Fetching calorie data...", foreground="blue")
        self.root.update()

        # Get calories (with API fallback)
        calories = get_exercise_calories(exercise, duration)

        self.status_label.config(text="✓ Data fetched", foreground="green")

        today = datetime.now().strftime('%Y-%m-%d')
        self.data.loc[len(self.data)] = [today, exercise, duration, calories]
        self.data.to_csv(os.path.join(DATA_DIR, f"{self.username}.csv"), index=False)

        self.tree.insert('', 'end', values=(today, exercise, duration, calories))
        self.duration_var.set("")
        self.selected_exercise.set("")

        messagebox.showinfo("Success", f"{exercise}\n{duration} min → {calories} kcal")
        self.status_label.config(text="")

    def show_data(self):
        for i, row in self.data.iterrows():
            self.tree.insert('', 'end', values=(row['date'], row['exercise'], row['duration'], row['calories']))

    def show_summary(self):
        if self.data.empty:
            messagebox.showinfo("Summary", "No workouts yet.")
            return

        self.data['date'] = pd.to_datetime(self.data['date'], errors='coerce').dt.date
        last_week = (datetime.now() - timedelta(days=7)).date()
        week_total = self.data[self.data['date'] >= last_week]['duration'].sum()
        total_cal = self.data['calories'].sum()
        avg_cal = self.data['calories'].mean()

        messagebox.showinfo("Progress Summary",
                            f"Last 7 Days: {week_total} min\n"
                            f"Total Calories: {total_cal:.0f} kcal\n"
                            f"Avg per Session: {avg_cal:.1f} kcal")

    def logout(self):
        self.root.destroy()


if __name__ == "__main__":
    temp_root = tk.Tk()
    temp_root.withdraw()
    login_window(temp_root)
    temp_root.destroy()

    if hasattr(temp_root, 'username'):
        root = tk.Tk()
        app = FitnessTrackerApp(root, temp_root.username)
        root.mainloop()
