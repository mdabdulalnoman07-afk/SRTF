import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
import sqlite3
from datetime import datetime
import os

class ATMApp:
    DB_FILE = "atm.db"

    def __init__(self, root):
        self.root = root
        self.root.title("Premium Python ATM")
        self.root.geometry("820x620")
        self.root.resizable(False, False)
        self.bg = "#0f1724"
        self.panel = "#0b2238"
        self.accent = "#56de4a"
        self.btn = "#eb2525"
        self.text = "#e6eef8"
        self.warn = "#fb923c"
        self.root.configure(bg=self.bg)
        self.font_title = ("Segoe UI", 20, "bold")
        self.font_base = ("Segoe UI", 12)
        self.current_account = None
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.DB_FILE)
        self.conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
        self.create_tables()
        self.seed_accounts_if_empty()
        self.create_login_screen()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_tables(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                card TEXT PRIMARY KEY,
                pin TEXT NOT NULL,
                name TEXT NOT NULL,
                balance REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card TEXT NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                balance_after REAL NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY(card) REFERENCES accounts(card)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS login_logout (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card TEXT,
                name TEXT,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def seed_accounts_if_empty(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM accounts")
        (count,) = cur.fetchone()
        if count == 0:
            now = self.now()
            demo = [
                ("123456", "7890", "Anamul Haque", 5000.00, now),
            ]
            cur.executemany(
                "INSERT OR IGNORE INTO accounts(card,pin,name,balance,created_at) VALUES(?,?,?,?,?)",
                demo
            )
            self.conn.commit()

    def on_close(self):
        try:
            self.conn.commit()
            self.conn.close()
        finally:
            self.root.destroy()

    def now(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def clear_screen(self):
        for w in self.root.winfo_children():
            w.destroy()

    def create_header(self, parent, title):
        header = tk.Frame(parent, bg=self.panel, padx=12, pady=12)
        header.pack(fill=tk.X, pady=(6, 12), padx=12)
        tk.Label(header, text=title, bg=self.panel, fg=self.text, font=self.font_title).pack(side=tk.LEFT)
        return header

    def create_login_screen(self):
        self.clear_screen()
        frame = tk.Frame(self.root, bg=self.bg)
        frame.pack(fill=tk.BOTH, expand=True)
        self.create_header(frame, "Premium Python ATM — Login")
        card_row = tk.Frame(frame, bg=self.bg, pady=6)
        card_row.pack(pady=6)
        tk.Label(card_row, text="Card Number :", bg=self.bg, fg=self.text, font=self.font_base).pack(side=tk.LEFT, padx=6)
        self.card_entry = tk.Entry(card_row, font=self.font_base, width=28)
        self.card_entry.pack(side=tk.LEFT, padx=6)
        self.card_entry.focus_set()
        pin_row = tk.Frame(frame, bg=self.bg)
        pin_row.pack(pady=6)
        tk.Label(pin_row, text="PIN Number  :", bg=self.bg, fg=self.text, font=self.font_base).pack(side=tk.LEFT, padx=6)
        self.pin_entry = tk.Entry(pin_row, font=self.font_base, width=28, show="*")
        self.pin_entry.pack(side=tk.LEFT, padx=6)
        btns = tk.Frame(frame, bg=self.bg)
        btns.pack(pady=18)
        tk.Button(btns, text="Login", bg=self.btn, fg="white", font=self.font_base, width=18, command=self.login).pack(side=tk.LEFT, padx=8)
        tk.Button(btns, text="View Login/Logout History", bg=self.accent, fg="black", font=self.font_base, width=26, command=self.show_login_logout_history).pack(side=tk.LEFT, padx=8)
        footer = tk.Frame(frame, bg=self.bg)
        footer.pack(side=tk.BOTTOM, fill=tk.X, pady=12)
        demo = "Demo cards: 123456/7890  •  654321/1234  •  111222/0000  •  777888/1357  •  888999/9753"
        tk.Label(footer, text=demo, bg=self.bg, fg="#9fb1d6", font=("Segoe UI", 10)).pack()

    def create_main_menu(self):
        self.clear_screen()
        frame = tk.Frame(self.root, bg=self.bg)
        frame.pack(fill=tk.BOTH, expand=True)
        self.create_header(frame, f"Welcome — {self.account_get_name(self.current_account)}")
        bal = self.account_get_balance(self.current_account)
        bal_panel = tk.Frame(frame, bg=self.panel, padx=16, pady=12)
        bal_panel.pack(fill=tk.X, padx=12)
        tk.Label(bal_panel, text=f"Current Balance", bg=self.panel, fg="#a8bedb", font=("Segoe UI", 12)).pack(anchor="w")
        tk.Label(bal_panel, text=f"${bal:,.2f}", bg=self.panel, fg=self.accent, font=("Segoe UI", 22, "bold")).pack(anchor="w")
        grid = tk.Frame(frame, bg=self.bg)
        grid.pack(pady=18, padx=12, fill=tk.BOTH, expand=True)
        def make_btn(text, cmd, bg=None):
            b = tk.Button(grid, text=text, font=self.font_base, bg=bg or self.btn, fg="white", width=26, height=2, command=cmd)
            return b
        make_btn("Check Balance", lambda: messagebox.showinfo("Balance", f"Balance: ${self.account_get_balance(self.current_account):,.2f}")).grid(row=0, column=0, padx=12, pady=8)
        make_btn("Withdraw Cash", self.withdraw).grid(row=0, column=1, padx=12, pady=8)
        make_btn("Deposit Cash", self.deposit).grid(row=1, column=0, padx=12, pady=8)
        make_btn("My Transaction History", self.show_transaction_history, bg="#10b981").grid(row=1, column=1, padx=12, pady=8)
        make_btn("Logout", self.logout, bg=self.warn).grid(row=2, column=0, columnspan=2, pady=18)

    def account_exists(self, card):
        cur = self.conn.cursor()
        cur.execute("SELECT 1 FROM accounts WHERE card=?", (card,))
        return cur.fetchone() is not None

    def account_check_pin(self, card, pin):
        cur = self.conn.cursor()
        cur.execute("SELECT pin FROM accounts WHERE card=?", (card,))
        row = cur.fetchone()
        return (row and row[0] == pin)

    def account_get_balance(self, card):
        cur = self.conn.cursor()
        cur.execute("SELECT balance FROM accounts WHERE card=?", (card,))
        r = cur.fetchone()
        return float(r[0]) if r else 0.0

    def account_get_name(self, card):
        cur = self.conn.cursor()
        cur.execute("SELECT name FROM accounts WHERE card=?", (card,))
        r = cur.fetchone()
        return r[0] if r else "Unknown"

    def account_update_balance(self, card, new_balance):
        cur = self.conn.cursor()
        cur.execute("UPDATE accounts SET balance=? WHERE card=?", (new_balance, card))
        self.conn.commit()

    def insert_transaction(self, card, ttype, amount, balance_after):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO transactions(card,type,amount,balance_after,timestamp) VALUES(?,?,?,?,?)",
            (card, ttype, amount, balance_after, self.now())
        )
        self.conn.commit()

    def insert_login_logout(self, card, name, action):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO login_logout(card,name,action,timestamp) VALUES(?,?,?,?)",
            (card, name, action, self.now())
        )
        self.conn.commit()

    def login(self):
        card = self.card_entry.get().strip()
        pin = self.pin_entry.get().strip()
        if not card or not pin:
            messagebox.showwarning("Input", "Please enter card and PIN")
            return
        if not self.account_exists(card):
            messagebox.showerror("Error", "Card number not found")
            return
        if not self.account_check_pin(card, pin):
            messagebox.showerror("Error", "Incorrect PIN")
            self.pin_entry.delete(0, tk.END)
            return
        self.current_account = card
        self.insert_login_logout(card, self.account_get_name(card), "Login")
        messagebox.showinfo("Welcome", f"Login successful. Welcome {self.account_get_name(card)}")
        self.create_main_menu()

    def logout(self):
        if self.current_account:
            self.insert_login_logout(self.current_account, self.account_get_name(self.current_account), "Logout")
        self.current_account = None
        messagebox.showinfo("Logged out", "You have been logged out.")
        self.create_login_screen()

    def withdraw(self):
        if not self.current_account:
            return
        s = simpledialog.askstring("Withdraw", "Enter amount to withdraw:", parent=self.root)
        if s is None:
            return
        try:
            amt = float(s)
            if amt <= 0:
                raise ValueError
        except:
            messagebox.showerror("Error", "Invalid amount")
            return
        bal = self.account_get_balance(self.current_account)
        if amt > bal:
            messagebox.showerror("Error", "Insufficient balance")
            return
        new_bal = bal - amt
        self.account_update_balance(self.current_account, new_bal)
        self.insert_transaction(self.current_account, "Withdrawal", amt, new_bal)
        messagebox.showinfo("Done", f"Withdrew ${amt:,.2f}\nNew balance: ${new_bal:,.2f}")
        self.create_main_menu()

    def deposit(self):
        if not self.current_account:
            return
        s = simpledialog.askstring("Deposit", "Enter amount to deposit:", parent=self.root)
        if s is None:
            return
        try:
            amt = float(s)
            if amt <= 0:
                raise ValueError
        except:
            messagebox.showerror("Error", "Invalid amount")
            return
        bal = self.account_get_balance(self.current_account)
        new_bal = bal + amt
        self.account_update_balance(self.current_account, new_bal)
        self.insert_transaction(self.current_account, "Deposit", amt, new_bal)
        messagebox.showinfo("Done", f"Deposited ${amt:,.2f}\nNew balance: ${new_bal:,.2f}")
        self.create_main_menu()

    def show_transaction_history(self):
        if not self.current_account:
            return
        cur = self.conn.cursor()
        cur.execute("SELECT type,amount,balance_after,timestamp FROM transactions WHERE card=? ORDER BY id DESC", (self.current_account,))
        rows = cur.fetchall()
        win = tk.Toplevel(self.root)
        win.title("Transaction History")
        win.geometry("760x520")
        win.configure(bg=self.bg)
        self.create_header(win, f"Transactions — {self.account_get_name(self.current_account)}")
        st = scrolledtext.ScrolledText(win, font=("Consolas", 11), bg="#071126", fg=self.text, padx=8, pady=8)
        st.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        if not rows:
            st.insert(tk.END, "No transactions found.\n")
        else:
            for r in rows:
                st.insert(tk.END, f"{r[3]}  |  {r[0]:<10}  |  ${r[1]:>10,.2f}  |  Balance: ${r[2]:>10,.2f}\n")
        st.configure(state=tk.DISABLED)
        tk.Button(win, text="Close", bg=self.btn, fg="white", command=win.destroy).pack(pady=8)

    def show_login_logout_history(self):
        cur = self.conn.cursor()
        cur.execute("SELECT card,name,action,timestamp FROM login_logout ORDER BY id DESC")
        rows = cur.fetchall()
        win = tk.Toplevel(self.root)
        win.title("Login / Logout History")
        win.geometry("780x540")
        win.configure(bg=self.bg)
        self.create_header(win, "Login / Logout Activity")
        st = scrolledtext.ScrolledText(win, font=("Consolas", 11), bg="#071126", fg=self.text, padx=8, pady=8)
        st.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        if not rows:
            st.insert(tk.END, "No login/logout records.\n")
        else:
            for r in rows:
                st.insert(tk.END, f"{r[3]}  |  {r[2]:<6}  |  Card: {r[0] or 'N/A'}  |  Name: {r[1] or 'N/A'}\n")
        st.configure(state=tk.DISABLED)
        tk.Button(win, text="Close", bg=self.btn, fg="white", command=win.destroy).pack(pady=8)

if __name__ == "__main__":
    root = tk.Tk()
    app = ATMApp(root)
    root.mainloop()
