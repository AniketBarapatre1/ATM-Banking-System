# fitness_tracker_sqlite.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
from datetime import datetime, timedelta
import storage_sqlite as storage

DATA_DIR = "fitness_data"  # not used now but kept for compatibility
EXERCISES = {
    "Cardio": { "Running": 10, "Cycling": 8, "Skipping Rope": 12,
                "Zumba": 9, "Aerobics": 7, "Treadmill Walk": 6 },

    "Strength / Muscle Training": { "Push-ups": 7, "Squats": 6, "Weight Training": 8, "Plank": 5,
                                    "Deadlift": 9,  "Bench Press": 8, "Lunges": 6 },

    "Yoga / Flexibility": { "Yoga": 4, "Surya Namaskar": 5 },

    "Swimming": { "Swimming": 9 }
}

CURRENT_USER = None

# initialize DB and seed exercises
storage.init_db(EXERCISES)

def login_window(root):
    login = tk.Toplevel(root)
    login.title("Login / Register")
    login.geometry("300x220")
    login.resizable(False, False)

    tk.Label(login, text="Username").pack(pady=5)
    user_var = tk.StringVar()
    tk.Entry(login, textvariable=user_var).pack()

    tk.Label(login, text="4-digit PIN").pack(pady=5)
    pin_var = tk.StringVar()
    tk.Entry(login, textvariable=pin_var, show="*").pack()

    def do_login():
        global CURRENT_USER
        username = user_var.get().strip()
        pin = pin_var.get().strip()
        if not username or not pin:
            messagebox.showerror("Error", "Username and PIN required")
            return
        uid = storage.authenticate_user(username, pin)
        if uid:
            CURRENT_USER = username
            login.destroy()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    def do_register():
        username = user_var.get().strip()
        pin = pin_var.get().strip()
        if not username or not pin:
            messagebox.showerror("Error", "Username and PIN required")
            return
        if not (pin.isdigit() and len(pin) == 4):
            messagebox.showerror("Error", "PIN must be 4 digits")
            return
        uid = storage.create_user(username, pin)
        if uid:
            messagebox.showinfo("Registered", "Account created. You can now login.")
        else:
            messagebox.showerror("Error", "Username already exists")

    btn_frame = tk.Frame(login)
    btn_frame.pack(pady=12)
    tk.Button(btn_frame, text="Login", width=10, command=do_login).pack(side="left", padx=6)
    tk.Button(btn_frame, text="Register", width=10, command=do_register).pack(side="left", padx=6)

    login.grab_set()
    login.wait_window()

class FitnessTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fitness Tracker")
        self.selected_exercise = tk.StringVar()
        self.duration_var = tk.StringVar()
        self.selected_category = tk.StringVar()

        # top: categories
        cat_frame = ttk.LabelFrame(root, text="Select Category")
        cat_frame.pack(fill='x', pady=5)
        for cat in EXERCISES.keys():
            ttk.Button(cat_frame, text=cat, command=lambda c=cat: self.show_exercises(c)).pack(side='left', padx=3, pady=3)

        # exercises frame
        self.ex_frame = ttk.LabelFrame(root, text="Select Exercise")
        self.ex_frame.pack(fill='x', pady=5)

        # duration input
        duration_frame = ttk.LabelFrame(root, text="Duration (Minutes)")
        duration_frame.pack(fill='x')
        ttk.Entry(duration_frame, textvariable=self.duration_var).pack(pady=5)
        ttk.Button(duration_frame, text="Add Workout", command=self.add_workout).pack(pady=5)

        # workout table + edit/delete
        table = ttk.LabelFrame(root, text="Workout Log", padding=6)
        table.pack(fill='both', expand=True)
        self.tree = ttk.Treeview(table, columns=('id','date','exercise','duration','calories'), show='headings')
        self.tree.heading('id', text='ID')
        self.tree.heading('date', text='Date')
        self.tree.heading('exercise', text='Exercise')
        self.tree.heading('duration', text='Minutes')
        self.tree.heading('calories', text='Calories')
        self.tree.column('id', width=40, anchor='center')
        self.tree.pack(fill='both', expand=True)

        btns = tk.Frame(root)
        btns.pack(fill='x', pady=6)
        ttk.Button(btns, text="Edit Selected", command=self.edit_selected).pack(side='left', padx=6)
        ttk.Button(btns, text="Delete Selected", command=self.delete_selected).pack(side='left', padx=6)
        ttk.Button(btns, text="Show Summary", command=self.show_summary).pack(side='right', padx=6)

        self.load_data()

    def show_exercises(self, category):
        for w in self.ex_frame.winfo_children():
            w.destroy()
        self.selected_category.set(category)
        for ex in EXERCISES[category].keys():
            ttk.Button(self.ex_frame, text=ex, command=lambda e=ex: self.selected_exercise.set(e)).pack(side='left', padx=3, pady=3)

    def add_workout(self):
        if not CURRENT_USER:
            messagebox.showerror("Error", "No user logged in")
            return
        exercise = self.selected_exercise.get()
        duration = self.duration_var.get().strip()
        if not exercise:
            messagebox.showerror("Error", "Select an exercise")
            return
        if not (duration.isdigit() and int(duration) > 0):
            messagebox.showerror("Error", "Enter positive duration in minutes")
            return
        wid, calories = storage.add_workout(CURRENT_USER, exercise, int(duration))
        # insert into tree using workout_id as iid
        self.tree.insert('', 'end', iid=str(wid), values=(wid, datetime.now().strftime('%Y-%m-%d'), exercise, int(duration), calories))
        self.duration_var.set("")
        self.selected_exercise.set("")
        messagebox.showinfo("Success", f"{exercise} added!")

    def load_data(self):
        # clear
        for i in self.tree.get_children():
            self.tree.delete(i)
        if not CURRENT_USER:
            return
        rows = storage.get_workouts(CURRENT_USER)
        for r in rows:
            self.tree.insert('', 'end', iid=str(r['workout_id']), values=(r['workout_id'], r['date'], r['exercise'], r['duration'], r['calories']))

    def edit_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Edit", "Select a workout first")
            return
        wid = int(sel[0])
        cur = self.tree.item(sel)['values']
        cur_duration = cur[3]
        new = simpledialog.askinteger("Edit Duration", "New duration (minutes):", initialvalue=cur_duration, minvalue=1)
        if new is None:
            return
        ok = storage.update_workout(wid, new)
        if ok:
            messagebox.showinfo("Updated", "Workout updated")
            self.load_data()
        else:
            messagebox.showerror("Error", "Could not update workout")

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Delete", "Select a workout first")
            return
        wid = int(sel[0])
        if messagebox.askyesno("Confirm", "Delete selected workout?"):
            ok = storage.delete_workout(wid)
            if ok:
                self.tree.delete(sel)
                messagebox.showinfo("Deleted", "Workout deleted")
            else:
                messagebox.showerror("Error", "Could not delete")

    def show_summary(self):
        if not CURRENT_USER:
            messagebox.showinfo("Summary", "No user logged in")
            return
        summary = storage.summary_last_7_days(CURRENT_USER)
        messagebox.showinfo("Progress Summary",
                            f" Last 7 Days: {summary['minutes']} min\n Total Calories: {summary['calories']:.1f} kcal")

if __name__ == "__main__":
    root = tk.Tk()
    # Login first
    login_window(root)
    if not CURRENT_USER:
        # if user didn't login or register, exit
        root.destroy()
    else:
        app = FitnessTrackerApp(root)
        root.mainloop()
