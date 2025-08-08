import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

# Database setup
DB_NAME = "tasks.db"


def initialize_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'To Do',
            priority TEXT DEFAULT 'Medium',
            category TEXT DEFAULT 'General'    -- **Added category column**
        )
    ''')

    cursor.execute("PRAGMA table_info(tasks)")
    columns = [info[1] for info in cursor.fetchall()]
    if 'category' not in columns:
        cursor.execute("ALTER TABLE tasks ADD COLUMN category TEXT DEFAULT 'General'")
    conn.commit()
    conn.close()


class TaskManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Task Manager")
        self.geometry("1000x700")  

        # **Create Notebook for Tabs**
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # **Create Frames for Each Tab**
        self.all_tasks_frame = ttk.Frame(self.notebook)
        self.done_tasks_frame = ttk.Frame(self.notebook)

        # **Add Tabs to Notebook**
        self.notebook.add(self.all_tasks_frame, text="All Tasks")
        self.notebook.add(self.done_tasks_frame, text="Done Tasks")

        # **All Tasks Treeview**
        self.all_tasks_tree = ttk.Treeview(
            self.all_tasks_frame,
            columns=("ID", "Title", "Description", "Status", "Priority", "Category"),
            show="headings",
            selectmode="extended"
        )
        self.all_tasks_tree.heading("ID", text="ID")
        self.all_tasks_tree.heading("Title", text="Title")
        self.all_tasks_tree.heading("Description", text="Description")
        self.all_tasks_tree.heading("Status", text="Status")
        self.all_tasks_tree.heading("Priority", text="Priority")
        self.all_tasks_tree.heading("Category", text="Category")  

        self.all_tasks_tree.column("ID", width=50)
        self.all_tasks_tree.column("Priority", width=100)
        self.all_tasks_tree.column("Category", width=150)  

        self.all_tasks_tree.pack(fill=tk.BOTH, expand=True)

        # **Define Tag Styles for Priority Levels**
        self.all_tasks_tree.tag_configure('High', background='#E06666')      # Red
        self.all_tasks_tree.tag_configure('Medium', background='#FFD966')    # Yellow
        self.all_tasks_tree.tag_configure('Low', background='#93C47D')       # Green

        # **Done Tasks Treeview**
        self.done_tasks_tree = ttk.Treeview(
            self.done_tasks_frame,
            columns=("ID", "Title", "Description", "Status", "Priority", "Category"),
            show="headings",
            selectmode="extended"
        )
        self.done_tasks_tree.heading("ID", text="ID")
        self.done_tasks_tree.heading("Title", text="Title")
        self.done_tasks_tree.heading("Description", text="Description")
        self.done_tasks_tree.heading("Status", text="Status")
        self.done_tasks_tree.heading("Priority", text="Priority")
        self.done_tasks_tree.heading("Category", text="Category")  

        self.done_tasks_tree.column("ID", width=50)
        self.done_tasks_tree.column("Priority", width=100)
        self.done_tasks_tree.column("Category", width=150)  

        self.done_tasks_tree.pack(fill=tk.BOTH, expand=True)

        # **Priority Levels in Done Tasks**
        self.done_tasks_tree.tag_configure('High', background='#E06666')      # Red
        self.done_tasks_tree.tag_configure('Medium', background='#FFD966')    # Yellow
        self.done_tasks_tree.tag_configure('Low', background='#93C47D')       # Green

        self.button_frame = tk.Frame(self)
        self.button_frame.pack(fill=tk.X, padx=10, pady=5)

        self.add_button = tk.Button(self.button_frame, text="Add Task", command=self.open_add_task_window)
        self.add_button.pack(side=tk.LEFT, padx=5)

        self.edit_button = tk.Button(self.button_frame, text="Edit Task", command=self.open_edit_task_window)
        self.edit_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = tk.Button(self.button_frame, text="Delete Task(s)", command=self.delete_tasks)
        self.delete_button.pack(side=tk.LEFT, padx=5)

        self.mark_done_button = tk.Button(self.button_frame, text="Mark as Done", command=self.mark_as_done)
        self.mark_done_button.pack(side=tk.LEFT, padx=5)

        self.load_tasks()

    def load_tasks(self):
        for item in self.all_tasks_tree.get_children():
            self.all_tasks_tree.delete(item)
        for item in self.done_tasks_tree.get_children():
            self.done_tasks_tree.delete(item)

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM tasks
            ORDER BY 
                CASE 
                    WHEN priority = 'High' THEN 1
                    WHEN priority = 'Medium' THEN 2
                    WHEN priority = 'Low' THEN 3
                    ELSE 4
                END, id
        """)
        for row in cursor.fetchall():
            task_id, title, description, status, priority, category = row
            tags = (priority,)

            if status == "Done":
                self.done_tasks_tree.insert("", tk.END, values=row, tags=tags)
            else:
                self.all_tasks_tree.insert("", tk.END, values=row, tags=tags)

        conn.close()

    def open_add_task_window(self):
        TaskEditor(self, "Add Task", None)

    def open_edit_task_window(self):
        # **Determine Which Tab is Active**
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 0:
            selected_tree = self.all_tasks_tree
        elif current_tab == 1:
            selected_tree = self.done_tasks_tree
        else:
            selected_tree = self.all_tasks_tree  # **Default to All Tasks**

        selected_items = selected_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select a task to edit.")
            return
        if len(selected_items) > 1:
            messagebox.showwarning("Multiple Selection", "Please select only one task to edit.")
            return

        task_id = selected_tree.item(selected_items[0])["values"][0]
        TaskEditor(self, "Edit Task", task_id)

    def delete_tasks(self):
        # **Determine Which Tab is Active**
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 0:
            selected_tree = self.all_tasks_tree
            status_filter = None  # **All tasks**
        elif current_tab == 1:
            selected_tree = self.done_tasks_tree
            status_filter = "Done"  # **Only done tasks**
        else:
            selected_tree = self.all_tasks_tree
            status_filter = None

        selected_items = selected_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select task(s) to delete.")
            return

        if len(selected_items) == 1:
            confirm = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete the selected task?")
        else:
            confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete the selected {len(selected_items)} tasks?")

        if not confirm:
            return

        task_ids = [selected_tree.item(item)["values"][0] for item in selected_items]

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.executemany("DELETE FROM tasks WHERE id = ?", [(task_id,) for task_id in task_ids])
        conn.commit()
        conn.close()

        self.load_tasks()

    def mark_as_done(self):
        # **Determine Which Tab is Active**
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 0:
            selected_tree = self.all_tasks_tree
        elif current_tab == 1:
            selected_tree = self.done_tasks_tree
        else:
            selected_tree = self.all_tasks_tree  # **Default to All Tasks**

        selected_items = selected_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select task(s) to mark as done.")
            return

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        tasks_already_done = []
        tasks_to_mark = []

        for item in selected_items:
            task = selected_tree.item(item)["values"]
            task_id, title, description, status, priority, category = task
            if status == "Done":
                tasks_already_done.append(title)
            else:
                tasks_to_mark.append(task_id)

        if tasks_already_done:
            messagebox.showinfo("Already Done", f"The following task(s) are already marked as done:\n" + "\n".join(tasks_already_done))

        if tasks_to_mark:
            cursor.executemany("UPDATE tasks SET status = 'Done' WHERE id = ?", [(task_id,) for task_id in tasks_to_mark])
            conn.commit()
            messagebox.showinfo("Success", f"Marked {len(tasks_to_mark)} task(s) as done.")

        conn.close()
        self.load_tasks()


class TaskEditor(tk.Toplevel):
    def __init__(self, parent, title, task_id):
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.geometry("500x400")  
        self.task_id = task_id

        # Title
        tk.Label(self, text="Title:").pack(pady=5)
        self.title_entry = tk.Entry(self)
        self.title_entry.pack(fill=tk.X, padx=10)

        # Description
        tk.Label(self, text="Description:").pack(pady=5)
        self.description_entry = tk.Entry(self)
        self.description_entry.pack(fill=tk.X, padx=10)

        # Status
        tk.Label(self, text="Status:").pack(pady=5)
        self.status_var = tk.StringVar(value="To Do")
        self.status_combo = ttk.Combobox(self, textvariable=self.status_var, values=["To Do", "In Progress", "Done"])
        self.status_combo.pack(fill=tk.X, padx=10)

        # Priority
        tk.Label(self, text="Priority:").pack(pady=5)
        self.priority_var = tk.StringVar(value="Medium")
        self.priority_combo = ttk.Combobox(self, textvariable=self.priority_var, values=["High", "Medium", "Low"])
        self.priority_combo.pack(fill=tk.X, padx=10)

        # Category
        tk.Label(self, text="Category:").pack(pady=5)
        self.category_var = tk.StringVar(value="General")
        self.category_combo = ttk.Combobox(self, textvariable=self.category_var, values=["General", "Work", "Personal", "Urgent", "Others"])
        self.category_combo.pack(fill=tk.X, padx=10)
        self.category_combo.bind("<FocusIn>", self.show_category_options)

        # Buttons
        self.button_frame = tk.Frame(self)
        self.button_frame.pack(fill=tk.X, pady=10)

        self.save_button = tk.Button(self.button_frame, text="Save", command=self.save_task)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.cancel_button = tk.Button(self.button_frame, text="Cancel", command=self.destroy)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        if task_id:
            self.load_task()

    def show_category_options(self, event):
        pass  

    def load_task(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (self.task_id,))
        task = cursor.fetchone()
        conn.close()

        if task:
            self.title_entry.insert(0, task[1])
            self.description_entry.insert(0, task[2])
            self.status_var.set(task[3])
            self.priority_var.set(task[4])
            self.category_var.set(task[5])

    def save_task(self):
        title = self.title_entry.get().strip()
        description = self.description_entry.get().strip()
        status = self.status_var.get()
        priority = self.priority_var.get()
        category = self.category_var.get().strip()

        if not title:
            messagebox.showwarning("Validation Error", "Title cannot be empty.")
            return

        if priority not in ["High", "Medium", "Low"]:
            messagebox.showwarning("Validation Error", "Please select a valid priority level.")
            return

        if not category:
            category = "General"  

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        if self.task_id:
            cursor.execute(
                "UPDATE tasks SET title = ?, description = ?, status = ?, priority = ?, category = ? WHERE id = ?",
                (title, description, status, priority, category, self.task_id),
            )
        else:
            cursor.execute(
                "INSERT INTO tasks (title, description, status, priority, category) VALUES (?, ?, ?, ?, ?)",
                (title, description, status, priority, category),
            )

        conn.commit()
        conn.close()

        self.parent.load_tasks()
        self.destroy()


if __name__ == "__main__":
    initialize_database()
    app = TaskManagerApp()
    app.mainloop()