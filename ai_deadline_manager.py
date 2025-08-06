import json
import threading
import time
import os
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
try:
    from plyer import notification
except ImportError:
    os.system('pip install plyer')
    from plyer import notification
try:
    import dateparser
except ImportError:
    os.system('pip install dateparser')
    import dateparser

TASKS_FILE = 'tasks.json'

def load_tasks():
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_tasks(tasks):
    with open(TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def calculate_status(deadline):
    deadline_dt = None
    try:
        deadline_dt = datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            deadline_dt = datetime.strptime(deadline, "%Y-%m-%d %H:%M")
        except ValueError:
            deadline_dt = dateparser.parse(deadline)
            if not deadline_dt:
                return "Invalid", "-"
    now = datetime.now()
    delta = deadline_dt - now
    if delta.total_seconds() < 0:
        return "Overdue", "0h 0m"
    elif delta.total_seconds() < 86400:
        return "Urgent", f"{delta.seconds//3600}h {((delta.seconds//60)%60)}m"
    else:
        days = delta.days
        hours = delta.seconds // 3600
        return "Pending", f"{days}d {hours}h"

def show_notification(tasks):
    urgent_tasks = [t for t in tasks if calculate_status(t['deadline'])[0] in ('Urgent', 'Overdue')]
    if urgent_tasks:
        details = "\n".join([
            f"{t['task_name']} | Deadline: {t['deadline']} | Status: {calculate_status(t['deadline'])[0]} | Time Left: {calculate_status(t['deadline'])[1]} | Priority: {t['priority']}"
            for t in urgent_tasks
        ])
        try:
            notification.notify(
                title="AI Deadline Management Reminder",
                message=f"You have {len(urgent_tasks)} urgent or overdue task(s):\n{details}",
                timeout=15
            )
        except Exception as e:
            print(f"(Notification error: {e})")

def background_reminder():
    notified = set()
    while True:
        tasks = load_tasks()
        urgent_tasks = [t for t in tasks if calculate_status(t['deadline'])[0] in ('Urgent', 'Overdue')]
        for t in urgent_tasks:
            key = (t['task_name'], t['deadline'])
            if key not in notified:
                try:
                    notification.notify(
                        title="AI Deadline Management Reminder",
                        message=f"Task: {t['task_name']}\nDeadline: {t['deadline']}\nStatus: {calculate_status(t['deadline'])[0]}\nTime Left: {calculate_status(t['deadline'])[1]}\nPriority: {t['priority']}",
                        timeout=15
                    )
                except Exception as e:
                    print(f"(Notification error: {e})")
                notified.add(key)
        time.sleep(60)

def add_task_gui(tasks, tree):
    task_name = simpledialog.askstring("Task Name", "Enter task name:")
    if not task_name:
        return
    description = simpledialog.askstring("Description", "Enter description:") or ""
    deadline = simpledialog.askstring("Deadline", "Enter deadline (YYYY-MM-DD HH:MM or natural language):")
    if not deadline:
        return
    priority = simpledialog.askstring("Priority", "Enter priority (High/Medium/Low):") or "Medium"
    status, time_left = calculate_status(deadline)
    task = {
        "task_name": task_name,
        "description": description,
        "deadline": deadline,
        "priority": priority,
        "status": status,
        "time_left": time_left
    }
    tasks.append(task)
    save_tasks(tasks)
    update_tree(tree, tasks)
    show_notification(tasks)

def delete_task_gui(tasks, tree):
    selected = tree.selection()
    if not selected:
        messagebox.showinfo("Delete Task", "No task selected.")
        return
    idx = int(selected[0])
    removed = tasks.pop(idx)
    save_tasks(tasks)
    update_tree(tree, tasks)
    messagebox.showinfo("Delete Task", f"Task '{removed['task_name']}' deleted.")

def update_tree(tree, tasks):
    tree.delete(*tree.get_children())
    for idx, t in enumerate(tasks):
        tree.insert('', 'end', iid=str(idx), values=(t['task_name'], t['deadline'], t['status'], t['time_left'], t['priority']))

def main_gui():
    tasks = load_tasks()
    root = tk.Tk()
    root.title("AI Deadline Management Agent")
    root.geometry("800x400")
    frame = tk.Frame(root)
    frame.pack(fill='both', expand=True)
    tree = ttk.Treeview(frame, columns=("Task Name", "Deadline", "Status", "Time Left", "Priority"), show='headings')
    for col in ("Task Name", "Deadline", "Status", "Time Left", "Priority"):
        tree.heading(col, text=col)
        tree.column(col, width=150)
    tree.pack(fill='both', expand=True)
    update_tree(tree, tasks)
    btn_frame = tk.Frame(root)
    btn_frame.pack(fill='x')
    tk.Button(btn_frame, text="Add Task", command=lambda: add_task_gui(tasks, tree)).pack(side='left', padx=10, pady=10)
    tk.Button(btn_frame, text="Delete Task", command=lambda: delete_task_gui(tasks, tree)).pack(side='left', padx=10, pady=10)
    tk.Button(btn_frame, text="Refresh", command=lambda: update_tree(tree, load_tasks())).pack(side='left', padx=10, pady=10)
    def on_closing():
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    threading.Thread(target=background_reminder, daemon=True).start()
    root.mainloop()

if __name__ == "__main__":
    main_gui()
