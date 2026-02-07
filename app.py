import calendar
import hashlib
import hmac
import os
import shutil
import tempfile
import tkinter as tk
import tkinter.font as tkfont
import webbrowser
from tkinter import ttk, messagebox, filedialog

import db
from reports import generate_customer_receipt
from tkcalendar import DateEntry


class MilkBillingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        db.init_db()
        self.shop_name = db.get_setting("shop_name", "Milk Billing System")
        self.shop_address = db.get_setting("shop_address", "")
        self.shop_contact = db.get_setting("shop_contact", "")
        self.title(f"{self.shop_name} (Offline)")
        self.geometry("1100x720")
        self.resizable(True, True)
        self._apply_styles()
        self._build_icons()
        self._prompt_login()
        self._combo_sources = {}
        self._combo_value_to_id = {}
        self._combo_id_to_value = {}
        self.selected_delivery_id = None
        self.selected_payment_id = None
        self.selected_allocation_id = None
        self.selected_customer_id = None
        self.selected_partner_id = None
        self.selected_item_id = None
        self.selected_manager_id = None

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self._build_masters_tab()
        self._build_daily_entry_tab()
        self._build_allocations_tab()
        self._build_reports_tab()
        self._build_lists_tab()

    def _build_masters_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Masters")

        header = ttk.Label(frame, text="Master Data", style="Header.TLabel")
        header.pack(anchor="w", padx=8, pady=(2, 8))

        master_notebook = ttk.Notebook(frame)
        master_notebook.pack(fill="both", expand=True)

        customers_box = ttk.Frame(master_notebook)
        partners_box = ttk.Frame(master_notebook)
        items_box = ttk.Frame(master_notebook)
        managers_box = ttk.Frame(master_notebook)
        settings_box = ttk.Frame(master_notebook)

        master_notebook.add(customers_box, text="Customers")
        master_notebook.add(partners_box, text="Delivery Partners")
        master_notebook.add(items_box, text="Items")
        master_notebook.add(managers_box, text="Managers")
        master_notebook.add(settings_box, text="Settings")

        self._build_customer_form(customers_box)
        self._build_partner_form(partners_box)
        self._build_item_form(items_box)
        self._build_manager_form(managers_box)
        self._build_settings_form(settings_box)

    def _apply_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        base_font = tkfont.Font(family="Segoe UI", size=11)
        header_font = tkfont.Font(family="Segoe UI", size=16, weight="bold")
        self.option_add("*Font", base_font)
        self.configure(bg="#ffffff")
        style.configure("TFrame", background="#ffffff")
        style.configure("TLabel", background="#ffffff", foreground="#1e3a8a")
        style.configure(
            "Header.TLabel",
            foreground="#1e3a8a",
            background="#ffffff",
            font=header_font,
        )
        style.configure("TLabelframe", background="#ffffff")
        style.configure(
            "TLabelframe.Label",
            background="#ffffff",
            foreground="#1e3a8a",
            font=("Segoe UI", 12, "bold"),
        )
        style.configure("TNotebook", background="#ffffff")
        style.configure(
            "TNotebook.Tab",
            padding=(12, 6),
            background="#ffffff",
            foreground="#1e3a8a",
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#e3f2fd")],
            foreground=[("selected", "#1e3a8a")],
        )
        style.configure("TEntry", fieldbackground="#ffffff", foreground="#1e3a8a")
        style.configure("TCombobox", fieldbackground="#ffffff", foreground="#1e3a8a")
        style.map("TCombobox", fieldbackground=[("readonly", "#ffffff")])
        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", foreground="#1e3a8a")
        style.configure("Treeview.Heading", background="#e3f2fd", foreground="#1e3a8a")
        style.configure("TButton", padding=8, font=("Segoe UI", 11, "bold"))
        style.configure("Primary.TButton", background="#1e88e5", foreground="white")
        style.map("Primary.TButton", background=[("active", "#1565c0")])
        style.configure("Secondary.TButton", background="#e3f2fd", foreground="#1e3a8a")
        style.map("Secondary.TButton", background=[("active", "#bbdefb")])
        style.configure("TCombobox", padding=4)

    def _build_icons(self):
        self.icons = {}
        self.icons["add"] = self._solid_icon("#1e88e5")
        self.icons["save"] = self._solid_icon("#2e7d32")
        self.icons["preview"] = self._solid_icon("#f9a825")
        self.icons["summary"] = self._solid_icon("#6a1b9a")
        self.icons["settings"] = self._solid_icon("#1565c0")
        self.icons["money"] = self._solid_icon("#2e7d32")

    def _solid_icon(self, color):
        img = tk.PhotoImage(width=16, height=16)
        img.put(color, to=(0, 0, 16, 16))
        return img

    def _build_customer_form(self, parent):
        ttk.Label(parent, text="Search").grid(row=0, column=0, sticky="w")
        self.customer_search = ttk.Entry(parent, width=30)
        self.customer_search.grid(row=0, column=1, padx=5, pady=6, sticky="w")
        self.customer_search.bind("<KeyRelease>", lambda _e: self._refresh_customers())

        ttk.Label(parent, text="Name").grid(row=1, column=0, sticky="w")
        ttk.Label(parent, text="Contact").grid(row=2, column=0, sticky="w")
        ttk.Label(parent, text="Address").grid(row=3, column=0, sticky="w")
        ttk.Label(parent, text="Alt Contact").grid(row=4, column=0, sticky="w")

        self.customer_name = ttk.Entry(parent, width=30)
        self.customer_contact = ttk.Entry(parent, width=30)
        self.customer_address = ttk.Entry(parent, width=30)
        self.customer_alt_contact = ttk.Entry(parent, width=30)

        self.customer_name.grid(row=1, column=1, padx=5, pady=6, sticky="w")
        self.customer_contact.grid(row=2, column=1, padx=5, pady=6, sticky="w")
        self.customer_address.grid(row=3, column=1, padx=5, pady=6, sticky="w")
        self.customer_alt_contact.grid(row=4, column=1, padx=5, pady=6, sticky="w")

        ttk.Button(
            parent,
            text="Add Customer",
            command=self._add_customer,
            style="Primary.TButton",
            image=self.icons.get("add"),
            compound="left",
        ).grid(row=5, column=1, sticky="e", padx=5, pady=6)
        ttk.Button(
            parent,
            text="Update Selected",
            command=self._update_customer,
            style="Secondary.TButton",
        ).grid(row=5, column=0, sticky="w", padx=5, pady=6)
        ttk.Button(
            parent,
            text="Delete Selected",
            command=self._delete_customer,
            style="Secondary.TButton",
        ).grid(row=5, column=0, sticky="e", padx=5, pady=6)

        self.customer_list = ttk.Treeview(
            parent,
            columns=("id", "name", "contact", "address", "alt_contact", "credit", "dues"),
            show="headings",
            height=8,
        )
        self.customer_list.heading("id", text="ID")
        self.customer_list.heading("name", text="Name")
        self.customer_list.heading("contact", text="Contact")
        self.customer_list.heading("address", text="Address")
        self.customer_list.heading("alt_contact", text="Alt Contact")
        self.customer_list.heading("credit", text="Credit")
        self.customer_list.heading("dues", text="Dues")
        self.customer_list.column("id", width=0, stretch=False)
        self.customer_list.grid(row=6, column=0, columnspan=2, sticky="nsew")
        self.customer_list.bind("<<TreeviewSelect>>", self._on_customer_select)
        parent.rowconfigure(6, weight=1)
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)

        self._refresh_customers()

    def _build_partner_form(self, parent):
        ttk.Label(parent, text="Name").grid(row=0, column=0, sticky="w")
        ttk.Label(parent, text="Contact").grid(row=1, column=0, sticky="w")
        ttk.Label(parent, text="Address").grid(row=2, column=0, sticky="w")

        self.partner_name = ttk.Entry(parent, width=30)
        self.partner_contact = ttk.Entry(parent, width=30)
        self.partner_address = ttk.Entry(parent, width=30)

        self.partner_name.grid(row=0, column=1, padx=5, pady=6, sticky="w")
        self.partner_contact.grid(row=1, column=1, padx=5, pady=6, sticky="w")
        self.partner_address.grid(row=2, column=1, padx=5, pady=6, sticky="w")

        ttk.Button(
            parent,
            text="Add Partner",
            command=self._add_partner,
            style="Primary.TButton",
            image=self.icons.get("add"),
            compound="left",
        ).grid(row=3, column=1, sticky="e", padx=5, pady=6)
        ttk.Button(
            parent,
            text="Update Selected",
            command=self._update_partner,
            style="Secondary.TButton",
        ).grid(row=3, column=0, sticky="w", padx=5, pady=6)
        ttk.Button(
            parent,
            text="Delete Selected",
            command=self._delete_partner,
            style="Secondary.TButton",
        ).grid(row=3, column=0, sticky="e", padx=5, pady=6)

        self.partner_list = ttk.Treeview(
            parent, columns=("id", "name", "contact"), show="headings", height=6
        )
        self.partner_list.heading("id", text="ID")
        self.partner_list.heading("name", text="Name")
        self.partner_list.heading("contact", text="Contact")
        self.partner_list.column("id", width=0, stretch=False)
        self.partner_list.grid(row=4, column=0, columnspan=2, sticky="nsew")
        self.partner_list.bind("<<TreeviewSelect>>", self._on_partner_select)
        parent.rowconfigure(4, weight=1)
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)

        self._refresh_partners()

    def _build_item_form(self, parent):
        ttk.Label(parent, text="Item").grid(row=0, column=0, sticky="w")
        ttk.Label(parent, text="Price").grid(row=1, column=0, sticky="w")

        self.item_name = ttk.Entry(parent, width=30)
        self.item_price = ttk.Entry(parent, width=30)

        self.item_name.grid(row=0, column=1, padx=5, pady=6, sticky="w")
        self.item_price.grid(row=1, column=1, padx=5, pady=6, sticky="w")

        ttk.Button(
            parent,
            text="Add Item",
            command=self._add_item,
            style="Primary.TButton",
            image=self.icons.get("add"),
            compound="left",
        ).grid(row=2, column=1, sticky="e", padx=5, pady=6)
        ttk.Button(
            parent,
            text="Update Selected",
            command=self._update_item,
            style="Secondary.TButton",
        ).grid(row=2, column=0, sticky="w", padx=5, pady=6)
        ttk.Button(
            parent,
            text="Delete Selected",
            command=self._delete_item,
            style="Secondary.TButton",
        ).grid(row=2, column=0, sticky="e", padx=5, pady=6)

        self.item_list = ttk.Treeview(
            parent, columns=("id", "name", "price"), show="headings", height=6
        )
        self.item_list.heading("id", text="ID")
        self.item_list.heading("name", text="Name")
        self.item_list.heading("price", text="Price")
        self.item_list.column("id", width=0, stretch=False)
        self.item_list.grid(row=3, column=0, columnspan=2, sticky="nsew")
        self.item_list.bind("<<TreeviewSelect>>", self._on_item_select)
        parent.rowconfigure(3, weight=1)
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)

        self._refresh_items()

    def _build_manager_form(self, parent):
        ttk.Label(parent, text="Name").grid(row=0, column=0, sticky="w")
        ttk.Label(parent, text="Contact").grid(row=1, column=0, sticky="w")

        self.manager_name = ttk.Entry(parent, width=30)
        self.manager_contact = ttk.Entry(parent, width=30)

        self.manager_name.grid(row=0, column=1, padx=5, pady=6, sticky="w")
        self.manager_contact.grid(row=1, column=1, padx=5, pady=6, sticky="w")

        ttk.Button(
            parent,
            text="Add Manager",
            command=self._add_manager,
            style="Primary.TButton",
            image=self.icons.get("add"),
            compound="left",
        ).grid(row=2, column=1, sticky="e", padx=5, pady=6)
        ttk.Button(
            parent,
            text="Update Selected",
            command=self._update_manager,
            style="Secondary.TButton",
        ).grid(row=2, column=0, sticky="w", padx=5, pady=6)
        ttk.Button(
            parent,
            text="Delete Selected",
            command=self._delete_manager,
            style="Secondary.TButton",
        ).grid(row=2, column=0, sticky="e", padx=5, pady=6)

        self.manager_list = ttk.Treeview(
            parent, columns=("id", "name", "contact"), show="headings", height=6
        )
        self.manager_list.heading("id", text="ID")
        self.manager_list.heading("name", text="Name")
        self.manager_list.heading("contact", text="Contact")
        self.manager_list.column("id", width=0, stretch=False)
        self.manager_list.grid(row=3, column=0, columnspan=2, sticky="nsew")
        self.manager_list.bind("<<TreeviewSelect>>", self._on_manager_select)
        parent.rowconfigure(3, weight=1)
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)

        self._refresh_managers()

    def _build_settings_form(self, parent):
        ttk.Label(parent, text="Shop Name").grid(row=0, column=0, sticky="w")
        ttk.Label(parent, text="Shop Address").grid(row=1, column=0, sticky="w")
        ttk.Label(parent, text="Shop Contact").grid(row=2, column=0, sticky="w")
        ttk.Label(parent, text="New Password").grid(row=3, column=0, sticky="w")
        ttk.Label(parent, text="Confirm Password").grid(row=4, column=0, sticky="w")
        self.shop_name_entry = ttk.Entry(parent, width=40)
        self.shop_name_entry.insert(0, self.shop_name)
        self.shop_address_entry = ttk.Entry(parent, width=40)
        self.shop_address_entry.insert(0, self.shop_address)
        self.shop_contact_entry = ttk.Entry(parent, width=40)
        self.shop_contact_entry.insert(0, self.shop_contact)
        self.app_password_entry = ttk.Entry(parent, width=40, show="*")
        self.app_password_confirm_entry = ttk.Entry(parent, width=40, show="*")
        self.shop_name_entry.grid(row=0, column=1, padx=5, pady=6, sticky="w")
        self.shop_address_entry.grid(row=1, column=1, padx=5, pady=6, sticky="w")
        self.shop_contact_entry.grid(row=2, column=1, padx=5, pady=6, sticky="w")
        self.app_password_entry.grid(row=3, column=1, padx=5, pady=6, sticky="w")
        self.app_password_confirm_entry.grid(row=4, column=1, padx=5, pady=6, sticky="w")
        ttk.Button(
            parent,
            text="Save Shop Details",
            command=self._save_shop_name,
            style="Primary.TButton",
            image=self.icons.get("settings"),
            compound="left",
        ).grid(row=5, column=1, sticky="e", padx=5, pady=8)
        ttk.Button(
            parent,
            text="Remove App Password",
            command=self._clear_app_password,
            style="Secondary.TButton",
        ).grid(row=5, column=0, sticky="w", padx=5, pady=8)
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)

    def _build_daily_entry_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Daily Delivery")

        ttk.Label(frame, text="Date").grid(row=0, column=0, sticky="w")
        ttk.Label(frame, text="Customer").grid(row=1, column=0, sticky="w")
        ttk.Label(frame, text="Item").grid(row=2, column=0, sticky="w")
        ttk.Label(frame, text="Quantity").grid(row=3, column=0, sticky="w")
        ttk.Label(frame, text="Delivery Partner").grid(row=4, column=0, sticky="w")
        ttk.Label(frame, text="Manager").grid(row=5, column=0, sticky="w")

        self.delivery_date_var = tk.StringVar(value=db.today_str())
        self.delivery_date_entry = self._build_date_dropdown(
            frame, 0, 1, self.delivery_date_var
        )
        self.delivery_customer = ttk.Combobox(frame, width=35)
        self.delivery_item = ttk.Combobox(frame, width=35)
        self.delivery_quantity = ttk.Entry(frame, width=20)
        self.delivery_partner = ttk.Combobox(frame, width=35)
        self.delivery_manager = ttk.Combobox(frame, width=35)

        self.delivery_customer.grid(row=1, column=1, padx=5, pady=4, sticky="w")
        self.delivery_item.grid(row=2, column=1, padx=5, pady=4, sticky="w")
        self.delivery_quantity.grid(row=3, column=1, padx=5, pady=4, sticky="w")
        self.delivery_partner.grid(row=4, column=1, padx=5, pady=4, sticky="w")
        self.delivery_manager.grid(row=5, column=1, padx=5, pady=4, sticky="w")

        ttk.Button(
            frame,
            text="Save Delivery",
            command=self._add_delivery,
            style="Primary.TButton",
            image=self.icons.get("save"),
            compound="left",
        ).grid(row=6, column=1, sticky="e", padx=5, pady=8)

        ttk.Separator(frame, orient="horizontal").grid(
            row=7, column=0, columnspan=2, sticky="ew", pady=8
        )

        ttk.Label(frame, text="Advance Payment").grid(row=8, column=0, sticky="w")
        ttk.Label(frame, text="Customer").grid(row=9, column=0, sticky="w")
        ttk.Label(frame, text="Amount").grid(row=10, column=0, sticky="w")
        ttk.Label(frame, text="Date").grid(row=11, column=0, sticky="w")
        ttk.Label(frame, text="Notes").grid(row=12, column=0, sticky="w")

        self.payment_customer = ttk.Combobox(frame, width=35)
        self.payment_amount = ttk.Entry(frame, width=20)
        self.payment_date_var = tk.StringVar(value=db.today_str())
        self.payment_date_entry = self._build_date_dropdown(
            frame, 11, 1, self.payment_date_var
        )
        self.payment_notes = ttk.Entry(frame, width=40)

        self.payment_customer.grid(row=9, column=1, padx=5, pady=4, sticky="w")
        self.payment_amount.grid(row=10, column=1, padx=5, pady=4, sticky="w")
        self.payment_notes.grid(row=12, column=1, padx=5, pady=4, sticky="w")

        ttk.Button(
            frame,
            text="Save Payment",
            command=self._add_payment,
            style="Primary.TButton",
            image=self.icons.get("money"),
            compound="left",
        ).grid(row=13, column=1, sticky="e", padx=5, pady=8)

        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)

        self._refresh_all_dropdowns()

    def _build_allocations_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Partner Stock")

        ttk.Label(frame, text="Date").grid(row=0, column=0, sticky="w")
        ttk.Label(frame, text="Delivery Partner").grid(row=1, column=0, sticky="w")
        ttk.Label(frame, text="Manager").grid(row=2, column=0, sticky="w")
        ttk.Label(frame, text="Item").grid(row=3, column=0, sticky="w")
        ttk.Label(frame, text="Quantity").grid(row=4, column=0, sticky="w")

        self.alloc_date_var = tk.StringVar(value=db.today_str())
        self.alloc_date_entry = self._build_date_dropdown(
            frame, 0, 1, self.alloc_date_var
        )
        self.alloc_partner = ttk.Combobox(frame, width=35)
        self.alloc_manager = ttk.Combobox(frame, width=35)
        self.alloc_item = ttk.Combobox(frame, width=35)
        self.alloc_quantity = ttk.Entry(frame, width=20)

        self.alloc_partner.grid(row=1, column=1, padx=5, pady=4, sticky="w")
        self.alloc_manager.grid(row=2, column=1, padx=5, pady=4, sticky="w")
        self.alloc_item.grid(row=3, column=1, padx=5, pady=4, sticky="w")
        self.alloc_quantity.grid(row=4, column=1, padx=5, pady=4, sticky="w")

        ttk.Button(
            frame,
            text="Save Allocation",
            command=self._add_allocation,
            style="Primary.TButton",
            image=self.icons.get("save"),
            compound="left",
        ).grid(row=5, column=1, sticky="e", padx=5, pady=8)

        ttk.Separator(frame, orient="horizontal").grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=8
        )

        ttk.Label(frame, text="View Partner Summary").grid(
            row=7, column=0, sticky="w"
        )
        ttk.Label(frame, text="Date").grid(row=8, column=0, sticky="w")
        ttk.Label(frame, text="Delivery Partner").grid(row=9, column=0, sticky="w")

        self.summary_date_var = tk.StringVar(value=db.today_str())
        self.summary_date_entry = self._build_date_dropdown(
            frame, 8, 1, self.summary_date_var
        )
        self.summary_partner = ttk.Combobox(frame, width=35)
        self.summary_partner.grid(row=9, column=1, padx=5, pady=4, sticky="w")

        ttk.Button(
            frame,
            text="Load Summary",
            command=self._load_partner_summary,
            style="Secondary.TButton",
            image=self.icons.get("summary"),
            compound="left",
        ).grid(row=10, column=1, sticky="e", padx=5, pady=8)

        self.partner_summary = tk.Text(
            frame,
            height=12,
            width=90,
            bg="#ffffff",
            fg="#1e3a8a",
            font=("Segoe UI", 11),
        )
        self.partner_summary.grid(row=11, column=0, columnspan=2, padx=5, pady=5)

        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)
        self._refresh_all_dropdowns()

    def _build_reports_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Reports")

        ttk.Label(frame, text="Customer Summary").grid(row=0, column=0, sticky="w")
        ttk.Label(frame, text="Customer").grid(row=1, column=0, sticky="w")
        ttk.Label(frame, text="From Date").grid(row=2, column=0, sticky="w")
        ttk.Label(frame, text="To Date").grid(row=3, column=0, sticky="w")

        self.report_customer = ttk.Combobox(frame, width=35)
        self.report_from_date_var = tk.StringVar(value=db.today_str())
        self.report_to_date_var = tk.StringVar(value=db.today_str())
        self.report_from_entry = self._build_date_dropdown(
            frame, 2, 1, self.report_from_date_var
        )
        self.report_to_entry = self._build_date_dropdown(
            frame, 3, 1, self.report_to_date_var
        )

        self.report_customer.grid(row=1, column=1, padx=5, pady=4, sticky="w")

        ttk.Button(
            frame,
            text="Load Summary",
            command=self._load_customer_summary,
            style="Secondary.TButton",
            image=self.icons.get("summary"),
            compound="left",
        ).grid(row=4, column=1, sticky="w", padx=5, pady=6)

        self.customer_summary_box = tk.Text(
            frame,
            height=6,
            width=60,
            bg="#ffffff",
            fg="#1e3a8a",
            font=("Segoe UI", 11),
        )
        self.customer_summary_box.grid(row=5, column=0, columnspan=2, padx=5, pady=6, sticky="w")

        ttk.Separator(frame, orient="horizontal").grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=10
        )

        ttk.Label(frame, text="Customer Receipt (Date Range)").grid(
            row=7, column=0, sticky="w"
        )
        ttk.Button(
            frame,
            text="Preview PDF",
            command=self._generate_receipt,
            style="Primary.TButton",
            image=self.icons.get("preview"),
            compound="left",
        ).grid(row=7, column=1, sticky="e", padx=5, pady=8)

        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)
        self._refresh_all_dropdowns()

    def _build_lists_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Lists")

        header = ttk.Label(frame, text="Delivery & Stock Lists", style="Header.TLabel")
        header.pack(anchor="w", padx=8, pady=(2, 8))

        lists_notebook = ttk.Notebook(frame)
        lists_notebook.pack(fill="both", expand=True)

        deliveries_box = ttk.Frame(lists_notebook)
        payments_box = ttk.Frame(lists_notebook)
        allocations_box = ttk.Frame(lists_notebook)

        lists_notebook.add(deliveries_box, text="Deliveries")
        lists_notebook.add(payments_box, text="Payments")
        lists_notebook.add(allocations_box, text="Allocations")

        self._build_deliveries_list(deliveries_box)
        self._build_payments_list(payments_box)
        self._build_allocations_list(allocations_box)

    def _build_deliveries_list(self, frame):
        ttk.Label(frame, text="Filter Date").grid(row=0, column=0, sticky="w")
        self.list_delivery_date_var = tk.StringVar(value=db.today_str())
        self.list_delivery_date_entry = self._build_date_dropdown(
            frame, 0, 1, self.list_delivery_date_var
        )
        ttk.Button(
            frame,
            text="Load By Date",
            command=self._load_deliveries_for_date,
            style="Secondary.TButton",
        ).grid(row=0, column=2, sticky="w", padx=5, pady=4)
        ttk.Button(
            frame,
            text="Load All",
            command=self._load_deliveries_all,
            style="Secondary.TButton",
        ).grid(row=0, column=2, sticky="e", padx=5, pady=4)

        self.delivery_list = ttk.Treeview(
            frame,
            columns=("id", "date", "customer", "item", "qty", "partner", "manager"),
            show="headings",
            height=12,
        )
        self.delivery_list.heading("id", text="ID")
        self.delivery_list.heading("date", text="Date")
        self.delivery_list.heading("customer", text="Customer")
        self.delivery_list.heading("item", text="Item")
        self.delivery_list.heading("qty", text="Qty")
        self.delivery_list.heading("partner", text="Partner")
        self.delivery_list.heading("manager", text="Manager")
        self.delivery_list.column("id", width=0, stretch=False)
        self.delivery_list.column("qty", width=60, anchor="center")
        self.delivery_list.column("date", width=110)
        self.delivery_list.column("customer", width=160)
        self.delivery_list.column("item", width=120)
        self.delivery_list.column("partner", width=140)
        self.delivery_list.column("manager", width=140)
        delivery_scroll = ttk.Scrollbar(frame, orient="vertical", command=self.delivery_list.yview)
        self.delivery_list.configure(yscrollcommand=delivery_scroll.set)
        self.delivery_list.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=5, pady=6)
        delivery_scroll.grid(row=1, column=3, sticky="ns", pady=6)
        self.delivery_list.bind("<<TreeviewSelect>>", self._on_delivery_select)

        ttk.Button(
            frame,
            text="Update Selected",
            command=self._update_delivery,
            style="Primary.TButton",
        ).grid(row=2, column=2, sticky="w", padx=5, pady=6)
        ttk.Button(
            frame,
            text="Delete Selected",
            command=self._delete_delivery,
            style="Secondary.TButton",
        ).grid(row=2, column=2, sticky="e", padx=5, pady=6)

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)

        self._load_deliveries_for_date()

    def _build_payments_list(self, frame):
        ttk.Label(frame, text="Filter Date").grid(row=0, column=0, sticky="w")
        self.list_payment_date_var = tk.StringVar(value=db.today_str())
        self.list_payment_date_entry = self._build_date_dropdown(
            frame, 0, 1, self.list_payment_date_var
        )
        ttk.Button(
            frame,
            text="Load By Date",
            command=self._load_payments_for_date,
            style="Secondary.TButton",
        ).grid(row=0, column=2, sticky="w", padx=5, pady=4)
        ttk.Button(
            frame,
            text="Load All",
            command=self._load_payments_all,
            style="Secondary.TButton",
        ).grid(row=0, column=2, sticky="e", padx=5, pady=4)

        self.payment_list = ttk.Treeview(
            frame,
            columns=("id", "date", "customer", "amount", "notes"),
            show="headings",
            height=12,
        )
        self.payment_list.heading("id", text="ID")
        self.payment_list.heading("date", text="Date")
        self.payment_list.heading("customer", text="Customer")
        self.payment_list.heading("amount", text="Amount")
        self.payment_list.heading("notes", text="Notes")
        self.payment_list.column("id", width=0, stretch=False)
        self.payment_list.column("amount", width=80, anchor="center")
        payment_scroll = ttk.Scrollbar(frame, orient="vertical", command=self.payment_list.yview)
        self.payment_list.configure(yscrollcommand=payment_scroll.set)
        self.payment_list.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=5, pady=6)
        payment_scroll.grid(row=1, column=3, sticky="ns", pady=6)
        self.payment_list.bind("<<TreeviewSelect>>", self._on_payment_select)

        ttk.Button(
            frame,
            text="Update Selected",
            command=self._update_payment,
            style="Primary.TButton",
        ).grid(row=2, column=2, sticky="w", padx=5, pady=6)
        ttk.Button(
            frame,
            text="Delete Selected",
            command=self._delete_payment,
            style="Secondary.TButton",
        ).grid(row=2, column=2, sticky="e", padx=5, pady=6)

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)

        self._load_payments_for_date()

    def _build_allocations_list(self, frame):
        ttk.Label(frame, text="Filter Date").grid(row=0, column=0, sticky="w")
        self.list_allocation_date_var = tk.StringVar(value=db.today_str())
        self.list_allocation_date_entry = self._build_date_dropdown(
            frame, 0, 1, self.list_allocation_date_var
        )
        ttk.Button(
            frame,
            text="Load By Date",
            command=self._load_allocations_for_date,
            style="Secondary.TButton",
        ).grid(row=0, column=2, sticky="w", padx=5, pady=4)
        ttk.Button(
            frame,
            text="Load All",
            command=self._load_allocations_all,
            style="Secondary.TButton",
        ).grid(row=0, column=2, sticky="e", padx=5, pady=4)

        self.allocation_list = ttk.Treeview(
            frame,
            columns=("id", "date", "partner", "item", "qty", "manager"),
            show="headings",
            height=12,
        )
        self.allocation_list.heading("id", text="ID")
        self.allocation_list.heading("date", text="Date")
        self.allocation_list.heading("partner", text="Partner")
        self.allocation_list.heading("item", text="Item")
        self.allocation_list.heading("qty", text="Qty")
        self.allocation_list.heading("manager", text="Manager")
        self.allocation_list.column("id", width=0, stretch=False)
        self.allocation_list.column("qty", width=60, anchor="center")
        alloc_scroll = ttk.Scrollbar(frame, orient="vertical", command=self.allocation_list.yview)
        self.allocation_list.configure(yscrollcommand=alloc_scroll.set)
        self.allocation_list.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=5, pady=6)
        alloc_scroll.grid(row=1, column=3, sticky="ns", pady=6)
        self.allocation_list.bind("<<TreeviewSelect>>", self._on_allocation_select)

        ttk.Button(
            frame,
            text="Update Selected",
            command=self._update_allocation,
            style="Primary.TButton",
        ).grid(row=2, column=2, sticky="w", padx=5, pady=6)
        ttk.Button(
            frame,
            text="Delete Selected",
            command=self._delete_allocation,
            style="Secondary.TButton",
        ).grid(row=2, column=2, sticky="e", padx=5, pady=6)

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)

        self._load_allocations_for_date()

    def _refresh_customers(self):
        search = self.customer_search.get().strip() if hasattr(self, "customer_search") else ""
        rows = db.list_customers_with_balance(search)
        self.customer_list.delete(*self.customer_list.get_children())
        for row in rows:
            balance = float(row["charges"]) - float(row["paid"])
            dues = balance if balance > 0 else 0.0
            credit = -balance if balance < 0 else 0.0
            self.customer_list.insert(
                "",
                "end",
                values=(
                    row["id"],
                    row["name"],
                    row["contact"],
                    row["address"] or "",
                    row["alt_contact"] or "",
                    f"{credit:.2f}",
                    f"{dues:.2f}",
                ),
            )

    def _refresh_partners(self):
        if not hasattr(self, "partner_list"):
            return
        rows = db.list_delivery_partners()
        self.partner_list.delete(*self.partner_list.get_children())
        for row in rows:
            self.partner_list.insert("", "end", values=(row["id"], row["name"], row["contact"]))

    def _refresh_items(self):
        rows = db.list_items()
        self.item_list.delete(*self.item_list.get_children())
        for row in rows:
            self.item_list.insert("", "end", values=(row["id"], row["name"], row["price"]))

    def _refresh_managers(self):
        rows = db.list_managers()
        self.manager_list.delete(*self.manager_list.get_children())
        for row in rows:
            self.manager_list.insert("", "end", values=(row["id"], row["name"], row["contact"]))

    def _refresh_all_dropdowns(self):
        customers = db.list_customers()
        partners = db.list_delivery_partners()
        items = db.list_items()
        managers = db.list_managers()

        if hasattr(self, "delivery_customer"):
            self._set_combo_values(self.delivery_customer, customers)
        if hasattr(self, "payment_customer"):
            self._set_combo_values(self.payment_customer, customers)
        if hasattr(self, "report_customer"):
            self._set_combo_values(self.report_customer, customers)
        if hasattr(self, "delivery_partner"):
            self._set_combo_values(self.delivery_partner, partners)
        if hasattr(self, "alloc_partner"):
            self._set_combo_values(self.alloc_partner, partners)
        if hasattr(self, "summary_partner"):
            self._set_combo_values(self.summary_partner, partners)
        if hasattr(self, "delivery_item"):
            self._set_combo_values(self.delivery_item, items)
        if hasattr(self, "alloc_item"):
            self._set_combo_values(self.alloc_item, items)
        if hasattr(self, "delivery_manager"):
            self._set_combo_values(self.delivery_manager, managers)
        if hasattr(self, "alloc_manager"):
            self._set_combo_values(self.alloc_manager, managers)

    def _fmt_choice(self, row, suffix=None):
        if suffix:
            return f"{row['name']} ({suffix})"
        return f"{row['name']}"

    def _set_combo_values(self, combo, rows):
        name_counts = {}
        for row in rows:
            name_counts[row["name"]] = name_counts.get(row["name"], 0) + 1
        values = []
        value_to_id = {}
        id_to_value = {}
        for row in rows:
            suffix = None
            if name_counts.get(row["name"], 0) > 1:
                if "contact" in row.keys() and row["contact"]:
                    suffix = row["contact"]
            display = self._fmt_choice(row, suffix=suffix)
            values.append(display)
            value_to_id[display] = row["id"]
            id_to_value[row["id"]] = display
        self._combo_sources[combo] = values
        self._combo_value_to_id[combo] = value_to_id
        self._combo_id_to_value[combo] = id_to_value
        combo["values"] = values
        if not getattr(combo, "_filter_bound", False):
            combo.bind("<KeyRelease>", self._on_combo_keyrelease)
            combo._filter_bound = True

    def _on_combo_keyrelease(self, event):
        combo = event.widget
        values = self._combo_sources.get(combo, [])
        typed = combo.get().lower()
        if not typed:
            combo["values"] = values
            return
        filtered = [v for v in values if typed in v.lower()]
        combo["values"] = filtered

    def _get_combo_id(self, combo):
        value = combo.get().strip()
        if not value:
            return None
        return self._combo_value_to_id.get(combo, {}).get(value)

    def _set_combo_by_id(self, combo, item_id):
        display = self._combo_id_to_value.get(combo, {}).get(item_id)
        if display:
            combo.set(display)

    def _add_customer(self):
        name = self.customer_name.get().strip()
        if not name:
            messagebox.showerror("Validation", "Customer name is required.")
            return
        db.add_customer(
            name,
            self.customer_contact.get().strip(),
            self.customer_address.get().strip(),
            self.customer_alt_contact.get().strip(),
        )
        self.customer_name.delete(0, tk.END)
        self.customer_contact.delete(0, tk.END)
        self.customer_address.delete(0, tk.END)
        self.customer_alt_contact.delete(0, tk.END)
        self.selected_customer_id = None
        self._refresh_customers()
        self._refresh_all_dropdowns()

    def _add_partner(self):
        name = self.partner_name.get().strip()
        if not name:
            messagebox.showerror("Validation", "Partner name is required.")
            return
        db.add_delivery_partner(
            name,
            self.partner_contact.get().strip(),
            self.partner_address.get().strip(),
        )
        self.partner_name.delete(0, tk.END)
        self.partner_contact.delete(0, tk.END)
        self.partner_address.delete(0, tk.END)
        self.selected_partner_id = None
        self._refresh_partners()
        self._refresh_all_dropdowns()

    def _add_item(self):
        name = self.item_name.get().strip()
        price_raw = self.item_price.get().strip()
        if not name or not price_raw:
            messagebox.showerror("Validation", "Item name and price are required.")
            return
        try:
            price = float(price_raw)
        except ValueError:
            messagebox.showerror("Validation", "Price must be a number.")
            return
        db.add_item(name, price)
        self.item_name.delete(0, tk.END)
        self.item_price.delete(0, tk.END)
        self.selected_item_id = None
        self._refresh_items()
        self._refresh_all_dropdowns()

    def _add_manager(self):
        name = self.manager_name.get().strip()
        if not name:
            messagebox.showerror("Validation", "Manager name is required.")
            return
        db.add_manager(name, self.manager_contact.get().strip())
        self.manager_name.delete(0, tk.END)
        self.manager_contact.delete(0, tk.END)
        self.selected_manager_id = None
        self._refresh_managers()
        self._refresh_all_dropdowns()

    def _add_delivery(self):
        delivery_date = self.delivery_date_var.get().strip()
        customer_id = self._get_combo_id(self.delivery_customer)
        item_id = self._get_combo_id(self.delivery_item)
        delivery_partner_id = self._get_combo_id(self.delivery_partner)
        manager_id = self._get_combo_id(self.delivery_manager)
        quantity_raw = self.delivery_quantity.get().strip()

        if not all(
            [delivery_date, customer_id, item_id, delivery_partner_id, manager_id]
        ):
            messagebox.showerror("Validation", "Please fill all delivery fields.")
            return
        try:
            quantity = int(quantity_raw)
        except ValueError:
            messagebox.showerror("Validation", "Quantity must be an integer.")
            return

        item_price = self._get_item_price(item_id)
        if item_price is None:
            messagebox.showerror("Validation", "Selected item has no price.")
            return

        db.add_daily_delivery(
            delivery_date,
            customer_id,
            item_id,
            quantity,
            item_price,
            delivery_partner_id,
            manager_id,
        )
        self.delivery_quantity.delete(0, tk.END)
        self.selected_delivery_id = None
        self._load_deliveries_for_date()
        messagebox.showinfo("Saved", "Delivery recorded.")

    def _build_date_dropdown(self, parent, row, column, date_var):
        wrapper = tk.Frame(
            parent,
            bg="#ffffff",
            highlightbackground="#cbd5e1",
            highlightthickness=1,
            bd=0,
        )
        wrapper.grid(row=row, column=column, padx=5, pady=4, sticky="w")
        entry = DateEntry(
            wrapper,
            textvariable=date_var,
            width=12,
            date_pattern="yyyy-mm-dd",
            background="#e3f2fd",
            foreground="#1e3a8a",
            borderwidth=0,
        )
        entry.pack(side="left", padx=(4, 2), pady=2)
        return entry

    def _add_payment(self):
        customer_id = self._get_combo_id(self.payment_customer)
        amount_raw = self.payment_amount.get().strip()
        payment_date = self.payment_date_var.get().strip()
        notes = self.payment_notes.get().strip()

        if not customer_id or not amount_raw or not payment_date:
            messagebox.showerror("Validation", "Please fill all payment fields.")
            return
        try:
            amount = float(amount_raw)
        except ValueError:
            messagebox.showerror("Validation", "Amount must be a number.")
            return
        db.add_advance_payment(customer_id, amount, payment_date, notes)
        self.payment_amount.delete(0, tk.END)
        self.payment_notes.delete(0, tk.END)
        self.selected_payment_id = None
        self._load_payments_for_date()
        messagebox.showinfo("Saved", "Payment recorded.")

    def _add_allocation(self):
        allocation_date = self.alloc_date_var.get().strip()
        partner_id = self._get_combo_id(self.alloc_partner)
        manager_id = self._get_combo_id(self.alloc_manager)
        item_id = self._get_combo_id(self.alloc_item)
        quantity_raw = self.alloc_quantity.get().strip()

        if not all([allocation_date, partner_id, manager_id, item_id, quantity_raw]):
            messagebox.showerror("Validation", "Please fill all allocation fields.")
            return
        try:
            quantity = int(quantity_raw)
        except ValueError:
            messagebox.showerror("Validation", "Quantity must be an integer.")
            return

        db.add_partner_allocation(allocation_date, partner_id, manager_id, item_id, quantity)
        self.alloc_quantity.delete(0, tk.END)
        self.selected_allocation_id = None
        self._load_allocations_for_date()
        messagebox.showinfo("Saved", "Allocation recorded.")

    def _load_partner_summary(self):
        summary_date = self.summary_date_var.get().strip()
        partner_id = self._get_combo_id(self.summary_partner)
        if not summary_date or not partner_id:
            messagebox.showerror("Validation", "Date and partner are required.")
            return
        allocations = db.list_partner_allocations(partner_id, summary_date)
        deliveries = db.list_partner_deliveries(partner_id, summary_date)
        remaining = db.partner_remaining(partner_id, summary_date)

        lines = [
            f"Partner Summary for {summary_date}",
            "-" * 60,
            "Allocations:",
        ]
        for row in allocations:
            lines.append(
                f"  {row['item_name']} x {row['quantity']} (Manager: {row['manager_name']})"
            )
        lines.append("")
        lines.append("Deliveries:")
        for row in deliveries:
            lines.append(
                f"  {row['customer_name']} - {row['item_name']} x {row['quantity']} "
                f"(Manager: {row['manager_name']})"
            )
        lines.append("")
        lines.append(f"Remaining packets: {remaining}")

        self.partner_summary.delete("1.0", tk.END)
        self.partner_summary.insert(tk.END, "\n".join(lines))

    def _load_deliveries_for_date(self):
        delivery_date = (
            self.list_delivery_date_var.get().strip()
            if hasattr(self, "list_delivery_date_var")
            else self.delivery_date_var.get().strip()
        )
        rows = db.list_daily_deliveries(delivery_date)
        self._refresh_delivery_list(rows)

    def _load_deliveries_all(self):
        rows = db.list_daily_deliveries()
        self._refresh_delivery_list(rows)

    def _refresh_delivery_list(self, rows):
        if not hasattr(self, "delivery_list"):
            return
        self.delivery_list.delete(*self.delivery_list.get_children())
        self._delivery_rows = {}
        for row in rows:
            iid = str(row["id"])
            self._delivery_rows[iid] = row
            self.delivery_list.insert(
                "",
                "end",
                iid=iid,
                values=(
                    row["id"],
                    row["date"],
                    row["customer_name"],
                    row["item_name"],
                    row["quantity"],
                    row["partner_name"],
                    row["manager_name"],
                ),
            )

    def _on_delivery_select(self, _event):
        selected = self.delivery_list.selection()
        if not selected:
            return
        iid = selected[0]
        row = self._delivery_rows.get(iid)
        if not row:
            return
        self.selected_delivery_id = row["id"]
        self.delivery_date_var.set(row["date"])
        self._set_combo_by_id(self.delivery_customer, row["customer_id"])
        self._set_combo_by_id(self.delivery_item, row["item_id"])
        self.delivery_quantity.delete(0, tk.END)
        self.delivery_quantity.insert(0, str(row["quantity"]))
        self._set_combo_by_id(self.delivery_partner, row["delivery_partner_id"])
        self._set_combo_by_id(self.delivery_manager, row["manager_id"])

    def _update_delivery(self):
        if not self.selected_delivery_id:
            messagebox.showerror("Validation", "Select a delivery to update.")
            return
        delivery_date = self.delivery_date_var.get().strip()
        customer_id = self._get_combo_id(self.delivery_customer)
        item_id = self._get_combo_id(self.delivery_item)
        delivery_partner_id = self._get_combo_id(self.delivery_partner)
        manager_id = self._get_combo_id(self.delivery_manager)
        quantity_raw = self.delivery_quantity.get().strip()

        if not all(
            [delivery_date, customer_id, item_id, delivery_partner_id, manager_id]
        ):
            messagebox.showerror("Validation", "Please fill all delivery fields.")
            return
        try:
            quantity = int(quantity_raw)
        except ValueError:
            messagebox.showerror("Validation", "Quantity must be an integer.")
            return

        item_price = self._get_item_price(item_id)
        if item_price is None:
            messagebox.showerror("Validation", "Selected item has no price.")
            return

        db.update_daily_delivery(
            self.selected_delivery_id,
            delivery_date,
            customer_id,
            item_id,
            quantity,
            item_price,
            delivery_partner_id,
            manager_id,
        )
        self.selected_delivery_id = None
        self.delivery_quantity.delete(0, tk.END)
        self.delivery_customer.set("")
        self.delivery_item.set("")
        self.delivery_partner.set("")
        self.delivery_manager.set("")
        self._load_deliveries_for_date()
        messagebox.showinfo("Saved", "Delivery updated.")

    def _delete_delivery(self):
        if not self.selected_delivery_id:
            messagebox.showerror("Validation", "Select a delivery to delete.")
            return
        if not messagebox.askyesno("Confirm", "Delete selected delivery?"):
            return
        db.delete_daily_delivery(self.selected_delivery_id)
        self.selected_delivery_id = None
        self._load_deliveries_for_date()
        messagebox.showinfo("Deleted", "Delivery deleted.")

    def _load_payments_for_date(self):
        payment_date = (
            self.list_payment_date_var.get().strip()
            if hasattr(self, "list_payment_date_var")
            else self.payment_date_var.get().strip()
        )
        rows = db.list_advance_payments(payment_date)
        self._refresh_payment_list(rows)

    def _load_payments_all(self):
        rows = db.list_advance_payments()
        self._refresh_payment_list(rows)

    def _refresh_payment_list(self, rows):
        if not hasattr(self, "payment_list"):
            return
        self.payment_list.delete(*self.payment_list.get_children())
        self._payment_rows = {}
        for row in rows:
            iid = str(row["id"])
            self._payment_rows[iid] = row
            self.payment_list.insert(
                "",
                "end",
                iid=iid,
                values=(
                    row["id"],
                    row["date"],
                    row["customer_name"],
                    f"{row['amount']:.2f}",
                    row["notes"] or "",
                ),
            )

    def _on_payment_select(self, _event):
        selected = self.payment_list.selection()
        if not selected:
            return
        iid = selected[0]
        row = self._payment_rows.get(iid)
        if not row:
            return
        self.selected_payment_id = row["id"]
        self._set_combo_by_id(self.payment_customer, row["customer_id"])
        self.payment_amount.delete(0, tk.END)
        self.payment_amount.insert(0, str(row["amount"]))
        self.payment_date_var.set(row["date"])
        self.payment_notes.delete(0, tk.END)
        self.payment_notes.insert(0, row["notes"] or "")

    def _update_payment(self):
        if not self.selected_payment_id:
            messagebox.showerror("Validation", "Select a payment to update.")
            return
        customer_id = self._get_combo_id(self.payment_customer)
        amount_raw = self.payment_amount.get().strip()
        payment_date = self.payment_date_var.get().strip()
        notes = self.payment_notes.get().strip()
        if not customer_id or not amount_raw or not payment_date:
            messagebox.showerror("Validation", "Please fill all payment fields.")
            return
        try:
            amount = float(amount_raw)
        except ValueError:
            messagebox.showerror("Validation", "Amount must be a number.")
            return
        db.update_advance_payment(
            self.selected_payment_id, customer_id, amount, payment_date, notes
        )
        self.selected_payment_id = None
        self.payment_amount.delete(0, tk.END)
        self.payment_notes.delete(0, tk.END)
        self.payment_customer.set("")
        self._load_payments_for_date()
        messagebox.showinfo("Saved", "Payment updated.")

    def _delete_payment(self):
        if not self.selected_payment_id:
            messagebox.showerror("Validation", "Select a payment to delete.")
            return
        if not messagebox.askyesno("Confirm", "Delete selected payment?"):
            return
        db.delete_advance_payment(self.selected_payment_id)
        self.selected_payment_id = None
        self._load_payments_for_date()
        messagebox.showinfo("Deleted", "Payment deleted.")

    def _load_allocations_for_date(self):
        allocation_date = (
            self.list_allocation_date_var.get().strip()
            if hasattr(self, "list_allocation_date_var")
            else self.alloc_date_var.get().strip()
        )
        rows = db.list_partner_allocations_all(allocation_date)
        self._refresh_allocation_list(rows)

    def _load_allocations_all(self):
        rows = db.list_partner_allocations_all()
        self._refresh_allocation_list(rows)

    def _refresh_allocation_list(self, rows):
        if not hasattr(self, "allocation_list"):
            return
        self.allocation_list.delete(*self.allocation_list.get_children())
        self._allocation_rows = {}
        for row in rows:
            iid = str(row["id"])
            self._allocation_rows[iid] = row
            self.allocation_list.insert(
                "",
                "end",
                iid=iid,
                values=(
                    row["id"],
                    row["date"],
                    row["partner_name"],
                    row["item_name"],
                    row["quantity"],
                    row["manager_name"],
                ),
            )

    def _on_allocation_select(self, _event):
        selected = self.allocation_list.selection()
        if not selected:
            return
        iid = selected[0]
        row = self._allocation_rows.get(iid)
        if not row:
            return
        self.selected_allocation_id = row["id"]
        self.alloc_date_var.set(row["date"])
        self._set_combo_by_id(self.alloc_partner, row["delivery_partner_id"])
        self._set_combo_by_id(self.alloc_manager, row["manager_id"])
        self._set_combo_by_id(self.alloc_item, row["item_id"])
        self.alloc_quantity.delete(0, tk.END)
        self.alloc_quantity.insert(0, str(row["quantity"]))

    def _update_allocation(self):
        if not self.selected_allocation_id:
            messagebox.showerror("Validation", "Select an allocation to update.")
            return
        allocation_date = self.alloc_date_var.get().strip()
        partner_id = self._get_combo_id(self.alloc_partner)
        manager_id = self._get_combo_id(self.alloc_manager)
        item_id = self._get_combo_id(self.alloc_item)
        quantity_raw = self.alloc_quantity.get().strip()
        if not all([allocation_date, partner_id, manager_id, item_id, quantity_raw]):
            messagebox.showerror("Validation", "Please fill all allocation fields.")
            return
        try:
            quantity = int(quantity_raw)
        except ValueError:
            messagebox.showerror("Validation", "Quantity must be an integer.")
            return
        db.update_partner_allocation(
            self.selected_allocation_id,
            allocation_date,
            partner_id,
            manager_id,
            item_id,
            quantity,
        )
        self.selected_allocation_id = None
        self.alloc_quantity.delete(0, tk.END)
        self.alloc_partner.set("")
        self.alloc_manager.set("")
        self.alloc_item.set("")
        self._load_allocations_for_date()
        messagebox.showinfo("Saved", "Allocation updated.")

    def _delete_allocation(self):
        if not self.selected_allocation_id:
            messagebox.showerror("Validation", "Select an allocation to delete.")
            return
        if not messagebox.askyesno("Confirm", "Delete selected allocation?"):
            return
        db.delete_partner_allocation(self.selected_allocation_id)
        self.selected_allocation_id = None
        self._load_allocations_for_date()
        messagebox.showinfo("Deleted", "Allocation deleted.")

    def _on_customer_select(self, _event):
        selected = self.customer_list.selection()
        if not selected:
            return
        item = self.customer_list.item(selected[0])
        customer_id = item["values"][0]
        row = db.get_customer(customer_id)
        if not row:
            return
        self.selected_customer_id = customer_id
        self.customer_name.delete(0, tk.END)
        self.customer_name.insert(0, row["name"])
        self.customer_contact.delete(0, tk.END)
        self.customer_contact.insert(0, row["contact"] or "")
        self.customer_address.delete(0, tk.END)
        self.customer_address.insert(0, row["address"] or "")
        self.customer_alt_contact.delete(0, tk.END)
        self.customer_alt_contact.insert(0, row["alt_contact"] or "")

    def _update_customer(self):
        if not self.selected_customer_id:
            messagebox.showerror("Validation", "Select a customer to update.")
            return
        name = self.customer_name.get().strip()
        if not name:
            messagebox.showerror("Validation", "Customer name is required.")
            return
        db.update_customer(
            self.selected_customer_id,
            name,
            self.customer_contact.get().strip(),
            self.customer_address.get().strip(),
            self.customer_alt_contact.get().strip(),
        )
        self.selected_customer_id = None
        self.customer_name.delete(0, tk.END)
        self.customer_contact.delete(0, tk.END)
        self.customer_address.delete(0, tk.END)
        self.customer_alt_contact.delete(0, tk.END)
        self._refresh_customers()
        self._refresh_all_dropdowns()
        messagebox.showinfo("Saved", "Customer updated.")

    def _delete_customer(self):
        if not self.selected_customer_id:
            messagebox.showerror("Validation", "Select a customer to delete.")
            return
        if not messagebox.askyesno("Confirm", "Delete selected customer?"):
            return
        db.deactivate_customer(self.selected_customer_id)
        self.selected_customer_id = None
        self._refresh_customers()
        self._refresh_all_dropdowns()
        messagebox.showinfo("Deleted", "Customer deleted.")

    def _on_partner_select(self, _event):
        selected = self.partner_list.selection()
        if not selected:
            return
        item = self.partner_list.item(selected[0])
        partner_id = item["values"][0]
        row = next(
            (r for r in db.list_delivery_partners() if r["id"] == partner_id),
            None,
        )
        if not row:
            return
        self.selected_partner_id = partner_id
        self.partner_name.delete(0, tk.END)
        self.partner_name.insert(0, row["name"])
        self.partner_contact.delete(0, tk.END)
        self.partner_contact.insert(0, row["contact"] or "")
        self.partner_address.delete(0, tk.END)
        self.partner_address.insert(0, row["address"] or "")

    def _update_partner(self):
        if not self.selected_partner_id:
            messagebox.showerror("Validation", "Select a partner to update.")
            return
        name = self.partner_name.get().strip()
        if not name:
            messagebox.showerror("Validation", "Partner name is required.")
            return
        db.update_delivery_partner(
            self.selected_partner_id,
            name,
            self.partner_contact.get().strip(),
            self.partner_address.get().strip(),
        )
        self.selected_partner_id = None
        self.partner_name.delete(0, tk.END)
        self.partner_contact.delete(0, tk.END)
        self.partner_address.delete(0, tk.END)
        self._refresh_partners()
        self._refresh_all_dropdowns()
        messagebox.showinfo("Saved", "Partner updated.")

    def _delete_partner(self):
        if not self.selected_partner_id:
            messagebox.showerror("Validation", "Select a partner to delete.")
            return
        if not messagebox.askyesno("Confirm", "Delete selected partner?"):
            return
        db.deactivate_delivery_partner(self.selected_partner_id)
        self.selected_partner_id = None
        self._refresh_partners()
        self._refresh_all_dropdowns()
        messagebox.showinfo("Deleted", "Partner deleted.")

    def _on_item_select(self, _event):
        selected = self.item_list.selection()
        if not selected:
            return
        item = self.item_list.item(selected[0])
        item_id = item["values"][0]
        row = next((r for r in db.list_items() if r["id"] == item_id), None)
        if not row:
            return
        self.selected_item_id = item_id
        self.item_name.delete(0, tk.END)
        self.item_name.insert(0, row["name"])
        self.item_price.delete(0, tk.END)
        self.item_price.insert(0, str(row["price"]))

    def _update_item(self):
        if not self.selected_item_id:
            messagebox.showerror("Validation", "Select an item to update.")
            return
        name = self.item_name.get().strip()
        price_raw = self.item_price.get().strip()
        if not name or not price_raw:
            messagebox.showerror("Validation", "Item name and price are required.")
            return
        try:
            price = float(price_raw)
        except ValueError:
            messagebox.showerror("Validation", "Price must be a number.")
            return
        db.update_item(self.selected_item_id, name, price)
        self.selected_item_id = None
        self.item_name.delete(0, tk.END)
        self.item_price.delete(0, tk.END)
        self._refresh_items()
        self._refresh_all_dropdowns()
        messagebox.showinfo("Saved", "Item updated.")

    def _delete_item(self):
        if not self.selected_item_id:
            messagebox.showerror("Validation", "Select an item to delete.")
            return
        if not messagebox.askyesno("Confirm", "Delete selected item?"):
            return
        db.delete_item(self.selected_item_id)
        self.selected_item_id = None
        self._refresh_items()
        self._refresh_all_dropdowns()
        messagebox.showinfo("Deleted", "Item deleted.")

    def _on_manager_select(self, _event):
        selected = self.manager_list.selection()
        if not selected:
            return
        item = self.manager_list.item(selected[0])
        manager_id = item["values"][0]
        row = next((r for r in db.list_managers() if r["id"] == manager_id), None)
        if not row:
            return
        self.selected_manager_id = manager_id
        self.manager_name.delete(0, tk.END)
        self.manager_name.insert(0, row["name"])
        self.manager_contact.delete(0, tk.END)
        self.manager_contact.insert(0, row["contact"] or "")

    def _update_manager(self):
        if not self.selected_manager_id:
            messagebox.showerror("Validation", "Select a manager to update.")
            return
        name = self.manager_name.get().strip()
        if not name:
            messagebox.showerror("Validation", "Manager name is required.")
            return
        db.update_manager(self.selected_manager_id, name, self.manager_contact.get().strip())
        self.selected_manager_id = None
        self.manager_name.delete(0, tk.END)
        self.manager_contact.delete(0, tk.END)
        self._refresh_managers()
        self._refresh_all_dropdowns()
        messagebox.showinfo("Saved", "Manager updated.")

    def _delete_manager(self):
        if not self.selected_manager_id:
            messagebox.showerror("Validation", "Select a manager to delete.")
            return
        if not messagebox.askyesno("Confirm", "Delete selected manager?"):
            return
        db.delete_manager(self.selected_manager_id)
        self.selected_manager_id = None
        self._refresh_managers()
        self._refresh_all_dropdowns()
        messagebox.showinfo("Deleted", "Manager deleted.")

    def _generate_receipt(self):
        customer_id = self._get_combo_id(self.report_customer)
        start_date = self.report_from_date_var.get().strip()
        end_date = self.report_to_date_var.get().strip()
        if not customer_id or not start_date or not end_date:
            messagebox.showerror("Validation", "Customer and date range are required.")
            return

        deliveries, payments = db.customer_statement_range(
            customer_id, start_date, end_date
        )
        customer = db.get_customer(customer_id)
        if not customer:
            messagebox.showerror("Validation", "Customer not found.")
            return

        temp_dir = tempfile.mkdtemp()
        preview_path = os.path.join(temp_dir, "receipt_preview.pdf")
        generate_customer_receipt(
            preview_path,
            self.shop_name,
            self.shop_address,
            self.shop_contact,
            customer,
            f"{start_date} to {end_date}",
            deliveries,
            payments,
        )
        webbrowser.open(preview_path)

        if not messagebox.askyesno("Save Receipt", "Preview opened. Save this receipt?"):
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Receipt",
        )
        if not file_path:
            return
        shutil.copyfile(preview_path, file_path)
        messagebox.showinfo("Done", f"Receipt saved: {file_path}")

    def _load_customer_summary(self):
        customer_id = self._get_combo_id(self.report_customer)
        start_date = self.report_from_date_var.get().strip()
        end_date = self.report_to_date_var.get().strip()
        if not customer_id or not start_date or not end_date:
            messagebox.showerror("Validation", "Customer and date range are required.")
            return

        total_qty, total_amount, total_paid = db.customer_summary_range(
            customer_id, start_date, end_date
        )
        balance = total_amount - total_paid
        dues = balance if balance > 0 else 0.0
        credit = -balance if balance < 0 else 0.0
        customer = db.get_customer(customer_id)
        lines = [
            f"Customer: {customer['name']}",
            f"Date Range: {start_date} to {end_date}",
            f"Total Qty: {total_qty}",
            f"Total Amount: {total_amount:.2f}",
            f"Total Paid: {total_paid:.2f}",
            f"Dues: {dues:.2f}    Credit: {credit:.2f}",
        ]
        self.customer_summary_box.delete("1.0", tk.END)
        self.customer_summary_box.insert(tk.END, "\n".join(lines))

    def _get_item_price(self, item_id):
        for row in db.list_items():
            if row["id"] == item_id:
                return row["price"]
        return None

    def _build_date_selector(self, parent, row, column):
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=column, padx=5, pady=4, sticky="w")
        today = db.today_str()
        year_val, month_val, day_val = today.split("-")
        year_values = [str(y) for y in range(int(year_val) - 2, int(year_val) + 3)]
        month_values = [f"{m:02d}" for m in range(1, 13)]
        day_values = self._get_month_days(int(year_val), int(month_val))

        year = ttk.Combobox(frame, width=4, state="readonly", values=year_values)
        month = ttk.Combobox(frame, width=3, state="readonly", values=month_values)
        day = ttk.Combobox(frame, width=3, state="readonly", values=day_values)
        year.set(year_val)
        month.set(month_val)
        day.set(day_val)

        year.grid(row=0, column=0, padx=(0, 4))
        month.grid(row=0, column=1, padx=(0, 4))
        day.grid(row=0, column=2)
        selector = {"year": year, "month": month, "day": day}
        year.bind("<<ComboboxSelected>>", lambda _e: self._update_day_values(selector))
        month.bind("<<ComboboxSelected>>", lambda _e: self._update_day_values(selector))
        return selector

    def _build_month_selector(self, parent, row, column):
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=column, padx=5, pady=4, sticky="w")
        today = db.today_str()
        year_val, month_val, _ = today.split("-")
        year_values = [str(y) for y in range(int(year_val) - 2, int(year_val) + 3)]
        month_values = [f"{m:02d}" for m in range(1, 13)]

        year = ttk.Combobox(frame, width=4, state="readonly", values=year_values)
        month = ttk.Combobox(frame, width=3, state="readonly", values=month_values)
        year.set(year_val)
        month.set(month_val)
        year.grid(row=0, column=0, padx=(0, 4))
        month.grid(row=0, column=1)
        return {"year": year, "month": month}

    def _get_date_value(self, selector):
        return f"{selector['year'].get()}-{selector['month'].get()}-{selector['day'].get()}"

    def _get_month_value(self, selector):
        return f"{selector['year'].get()}-{selector['month'].get()}"

    def _save_shop_name(self):
        name = self.shop_name_entry.get().strip()
        address = self.shop_address_entry.get().strip()
        contact = self.shop_contact_entry.get().strip()
        new_password = self.app_password_entry.get()
        confirm_password = self.app_password_confirm_entry.get()
        if not name:
            messagebox.showerror("Validation", "Shop name is required.")
            return
        if new_password or confirm_password:
            if new_password != confirm_password:
                messagebox.showerror("Validation", "Passwords do not match.")
                return
            db.set_setting("app_password_hash", self._hash_password(new_password))
        db.set_setting("shop_name", name)
        db.set_setting("shop_address", address)
        db.set_setting("shop_contact", contact)
        self.shop_name = name
        self.shop_address = address
        self.shop_contact = contact
        self.title(f"{self.shop_name} (Offline)")
        self.app_password_entry.delete(0, tk.END)
        self.app_password_confirm_entry.delete(0, tk.END)
        messagebox.showinfo("Saved", "Shop details updated.")

    def _clear_app_password(self):
        if not messagebox.askyesno("Confirm", "Remove app password?"):
            return
        db.set_setting("app_password_hash", "")
        messagebox.showinfo("Done", "App password removed.")

    def _hash_password(self, raw_password):
        return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()

    def _verify_password(self, raw_password):
        stored = db.get_setting("app_password_hash", "")
        if not stored:
            return True
        return hmac.compare_digest(stored, self._hash_password(raw_password))

    def _prompt_login(self):
        stored = db.get_setting("app_password_hash", "")
        if not stored:
            return
        dialog = tk.Toplevel(self)
        dialog.title("Login")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text="Enter Password").grid(row=0, column=0, padx=10, pady=8)
        password_entry = ttk.Entry(dialog, width=30, show="*")
        password_entry.grid(row=1, column=0, padx=10, pady=6)

        def attempt_login():
            password = password_entry.get()
            if self._verify_password(password):
                dialog.destroy()
            else:
                messagebox.showerror("Login Failed", "Invalid password.")
                password_entry.delete(0, tk.END)

        ttk.Button(dialog, text="Login", command=attempt_login).grid(
            row=2, column=0, padx=10, pady=10
        )
        dialog.protocol("WM_DELETE_WINDOW", self.destroy)
        password_entry.focus_set()
        self.wait_window(dialog)

    def _get_month_days(self, year, month):
        _, days = calendar.monthrange(year, month)
        return [f"{d:02d}" for d in range(1, days + 1)]

    def _update_day_values(self, selector):
        try:
            year = int(selector["year"].get())
            month = int(selector["month"].get())
        except ValueError:
            return
        days = self._get_month_days(year, month)
        selector["day"]["values"] = days
        if selector["day"].get() not in days:
            selector["day"].set(days[0])


if __name__ == "__main__":
    app = MilkBillingApp()
    app.mainloop()
