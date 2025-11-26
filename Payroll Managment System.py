import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import csv
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "payroll.db")

SAMPLE_EMPLOYEES = [
    ("E0001","Rana Hossain","HR","Manager",6500,500,200),
    ("E0002","Karim Ahmed","Finance","Analyst",4800,300,150),
    ("E0003","Fatima Begum","IT","Developer",5200,400,180),
    ("E0004","Arif Khan","IT","SysAdmin",5000,350,120),
    ("E0005","Nasrin Akter","Marketing","Executive",4200,250,100),
    ("E0006","Jamal Hassan","Sales","Sales Rep",3900,300,90),
    ("E0007","Lina Sultana","R&D","Engineer",5600,450,200),
    ("E0008","Sajeda Sultana Syma","Operations","Supervisor",4700,300,130),
    ("E0009","Nadia Islam","Design","Designer",4300,200,110),
    ("E0010","Rashed Ali","Support","Support Eng",3800,150,80),
    ("E0011","Sumaiya Khan","HR","Recruiter",3600,180,70),
    ("E0012","Rafiq Uddin","Finance","Controller",7000,600,250),
    ("E0013","Priya Das","IT","QA",4100,220,90),
    ("E0014","Tarek Rahman","Sales","Sales Lead",6000,450,200),
    ("E0015","Nusrat Jahan","Legal","Counsel",7500,700,300),
    ("E0016","Habib Mridha","Logistics","Coordinator",3500,120,60),
    ("E0017","Sakib Hossain","R&D","Scientist",6800,500,220),
    ("E0018","Mina Yasmin","Marketing","Manager",5900,400,180),
    ("E0019","Saiful Islam","Support","Team Lead",4500,300,120),
    ("E0020","Ruma Dey","Admin","Office Admin",3200,100,50),
]

TAX_RATE = 0.10

def get_conn():
    return sqlite3.connect(DB_PATH, timeout=10)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS employees (
        emp_id TEXT PRIMARY KEY, name TEXT, department TEXT, position TEXT,
        base_salary REAL, allowances REAL, deductions REAL, created_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS payroll (
        id INTEGER PRIMARY KEY, emp_id TEXT, pay_period TEXT, gross_pay REAL,
        tax REAL, net_pay REAL, timestamp TEXT, FOREIGN KEY(emp_id) REFERENCES employees(emp_id))""")
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM employees")
    if cur.fetchone()[0] == 0:
        now = datetime.now().isoformat()
        cur.executemany(
            "INSERT INTO employees VALUES(?,?,?,?,?,?,?,?)",
            [(e[0],e[1],e[2],e[3],e[4],e[5],e[6],now) for e in SAMPLE_EMPLOYEES]
        )
        conn.commit()
    conn.close()

class PayrollApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Payroll Management System")
        self.root.geometry("900x500")
        self.root.config(padx=8, pady=8)
        
        # Main container
        main = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True)
        
        # Left: Employee list
        left = ttk.Frame(main)
        main.add(left, weight=1)
        
        ttk.Label(left, text="Employees", font=("Arial",12,"bold")).pack()
        cols = ("ID","Name","Dept")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", height=20)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=80)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        
        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill=tk.X, pady=4)
        ttk.Button(btn_frame, text="Add", command=self.add_emp, width=8).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Edit", command=self.edit_emp, width=8).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Delete", command=self.del_emp, width=8).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Export", command=self.export_csv, width=8).pack(side=tk.LEFT)
        
        # Right: Details & Payroll
        right = ttk.Frame(main)
        main.add(right, weight=1)
        
        self.header = ttk.Label(right, text="Select employee", font=("Arial",11,"bold"))
        self.header.pack(anchor="w")
        
        form = ttk.Frame(right)
        form.pack(fill=tk.X, pady=4)
        
        self.fields = {}
        for i, lbl in enumerate(["ID","Name","Dept","Position","Base","Allow","Ded"]):
            ttk.Label(form, text=lbl, width=7).grid(row=i,column=0,sticky="w",pady=2)
            v = tk.StringVar()
            ttk.Entry(form, textvariable=v, width=20).grid(row=i,column=1,padx=4,pady=2)
            self.fields[lbl] = v
        
        pay_frame = ttk.LabelFrame(right, text="Payroll")
        pay_frame.pack(fill=tk.X, pady=4)
        ttk.Button(pay_frame, text="Compute & Save", command=self.compute_payroll).pack(side=tk.LEFT,padx=4,pady=4)
        ttk.Button(pay_frame, text="Payslip", command=self.gen_payslip).pack(side=tk.LEFT,padx=4,pady=4)
        
        self.result = tk.Text(right, height=8, width=40)
        self.result.pack(fill=tk.BOTH, expand=True)
        
        # Bottom: History
        bottom = ttk.LabelFrame(self.root, text="Recent Payroll (height=5)")
        bottom.pack(fill=tk.X, pady=(4,0))
        cols_h = ("Emp","Period","Gross","Tax","Net")
        self.hist = ttk.Treeview(bottom, columns=cols_h, show="headings", height=5)
        for c in cols_h:
            self.hist.heading(c, text=c)
            self.hist.column(c, width=110)
        self.hist.pack(fill=tk.X)
        
        self.refresh_list()
    
    def refresh_list(self):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT emp_id,name,department FROM employees ORDER BY emp_id")
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in cur.fetchall(): self.tree.insert("",tk.END,values=r)
        conn.close()
        self.clear_detail()
    
    def on_select(self, event):
        sel = self.tree.selection()
        if sel:
            emp_id = self.tree.item(sel[0])["values"][0]
            self.load_emp(emp_id)
    
    def load_emp(self, emp_id):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT emp_id,name,department,position,base_salary,allowances,deductions FROM employees WHERE emp_id=?", (emp_id,))
        r = cur.fetchone()
        conn.close()
        if r:
            self.header.config(text=f"Employee: {r[1]} ({r[0]})")
            for i, lbl in enumerate(["ID","Name","Dept","Position","Base","Allow","Ded"]):
                self.fields[lbl].set(str(r[i]) if r[i] else "")
            self.refresh_hist()
    
    def clear_detail(self):
        self.header.config(text="Select employee")
        for v in self.fields.values(): v.set("")
        self.result.delete("1.0",tk.END)
    
    def add_emp(self):
        self.emp_dialog(mode="add")
    
    def edit_emp(self):
        sel = self.tree.selection()
        if not sel: messagebox.showwarning("Select","Pick employee")
        else: self.emp_dialog(mode="edit", emp_id=self.tree.item(sel[0])["values"][0])
    
    def del_emp(self):
        sel = self.tree.selection()
        if not sel: messagebox.showwarning("Select","Pick employee")
        elif messagebox.askyesno("Delete",f"Delete {self.tree.item(sel[0])['values'][0]}?"):
            emp_id = self.tree.item(sel[0])["values"][0]
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM payroll WHERE emp_id=?", (emp_id,))
            cur.execute("DELETE FROM employees WHERE emp_id=?", (emp_id,))
            conn.commit()
            conn.close()
            self.refresh_list()
    
    def emp_dialog(self, mode="add", emp_id=None):
        w = tk.Toplevel(self.root)
        w.title(f"{mode.upper()} Employee")
        fields = {}
        for i,lbl in enumerate(["ID","Name","Dept","Position","Base","Allow","Ded"]):
            ttk.Label(w,text=lbl).grid(row=i,column=0,sticky="w",padx=4,pady=4)
            v = tk.StringVar()
            ttk.Entry(w,textvariable=v,width=30).grid(row=i,column=1,padx=4,pady=4)
            fields[lbl] = v
        
        if mode=="edit" and emp_id:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT emp_id,name,department,position,base_salary,allowances,deductions FROM employees WHERE emp_id=?", (emp_id,))
            r = cur.fetchone()
            conn.close()
            if r:
                for i,lbl in enumerate(["ID","Name","Dept","Position","Base","Allow","Ded"]):
                    fields[lbl].set(str(r[i]) if r[i] else "")
        
        def save():
            try:
                vals = [fields[l].get().strip() for l in ["ID","Name","Dept","Position","Base","Allow","Ded"]]
                if not vals[0] or not vals[1]: messagebox.showwarning("Missing","ID & Name needed")
                else:
                    base, allo, ded = float(vals[4]or 0), float(vals[5]or 0), float(vals[6]or 0)
                    conn = get_conn()
                    cur = conn.cursor()
                    now = datetime.now().isoformat()
                    if mode=="add":
                        try:
                            cur.execute("INSERT INTO employees VALUES(?,?,?,?,?,?,?,?)",
                                        (vals[0],vals[1],vals[2],vals[3],base,allo,ded,now))
                        except sqlite3.IntegrityError:
                            messagebox.showerror("Error","ID exists")
                            conn.close()
                            return
                    else:
                        cur.execute("UPDATE employees SET name=?,department=?,position=?,base_salary=?,allowances=?,deductions=? WHERE emp_id=?",
                                    (vals[1],vals[2],vals[3],base,allo,ded,vals[0]))
                    conn.commit()
                    conn.close()
                    w.destroy()
                    self.refresh_list()
            except ValueError:
                messagebox.showerror("Error","Salary must be numbers")
        
        ttk.Button(w,text="Save",command=save).grid(row=7,column=0,columnspan=2,pady=10)
    
    def compute_payroll(self):
        emp_id = self.fields["ID"].get().strip()
        if not emp_id: messagebox.showwarning("Select","Pick employee first")
        else:
            try:
                base, allo, ded = float(self.fields["Base"].get() or 0), float(self.fields["Allow"].get() or 0), float(self.fields["Ded"].get() or 0)
                gross = base + allo
                tax = gross * TAX_RATE
                net = gross - tax - ded
                period = datetime.now().strftime("%Y-%m")
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("INSERT INTO payroll VALUES(NULL,?,?,?,?,?,?)",
                            (emp_id,period,gross,tax,net,datetime.now().isoformat()))
                conn.commit()
                conn.close()
                self.result.delete("1.0",tk.END)
                self.result.insert(tk.END,f"Gross: ${gross:.2f}\nTax: ${tax:.2f}\nDeductions: ${ded:.2f}\nNet: ${net:.2f}\nSaved!")
                self.refresh_hist()
            except ValueError:
                messagebox.showerror("Error","Invalid salary")
    
    def gen_payslip(self):
        emp_id = self.fields["ID"].get().strip()
        if not emp_id: messagebox.showwarning("Select","Pick employee")
        else:
            try:
                base, allo, ded = float(self.fields["Base"].get() or 0), float(self.fields["Allow"].get() or 0), float(self.fields["Ded"].get() or 0)
                gross, tax, net = base+allo, (base+allo)*TAX_RATE, (base+allo)-(base+allo)*TAX_RATE-ded
                slip = f"PAYSLIP\n{self.fields['Name'].get()} ({emp_id})\nBase: ${base:.2f}\nAllow: ${allo:.2f}\nGross: ${gross:.2f}\nTax: ${tax:.2f}\nDed: ${ded:.2f}\nNet: ${net:.2f}"
                p = filedialog.asksaveasfilename(defaultextension=".txt",filetypes=[("Text","*.txt")])
                if p:
                    with open(p,"w") as f: f.write(slip)
                    messagebox.showinfo("Saved",f"Payslip saved")
            except: messagebox.showerror("Error","Invalid salary")
    
    def export_csv(self):
        p = filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV","*.csv")])
        if not p: return
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM employees ORDER BY emp_id")
        with open(p,"w",newline='',encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["emp_id","name","department","position","base_salary","allowances","deductions","created_at"])
            w.writerows(cur.fetchall())
        conn.close()
        messagebox.showinfo("Exported","CSV saved")
    
    def refresh_hist(self):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT emp_id,pay_period,gross_pay,tax,net_pay FROM payroll ORDER BY id DESC LIMIT 10")
        for i in self.hist.get_children(): self.hist.delete(i)
        for r in cur.fetchall():
            self.hist.insert("",tk.END,values=(r[0],r[1],f"{r[2]:.2f}",f"{r[3]:.2f}",f"{r[4]:.2f}"))
        conn.close()

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    PayrollApp(root)
    root.mainloop()