import hashlib
import hmac
import os
import tempfile
from datetime import date

import streamlit as st

import db
from reports import generate_customer_receipt


APP_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(APP_DIR, "milk_billing.db")
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123"


def to_date(value):
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def date_to_str(value):
    return value.strftime("%Y-%m-%d")


def rows_to_dicts(rows):
    return [dict(r) for r in rows]


def fmt_name(row, suffix_keys=("contact",)):
    suffix = None
    for key in suffix_keys:
        if row.get(key):
            suffix = row.get(key)
            break
    if suffix:
        return f"{row['name']} ({suffix})"
    return row["name"]


def fmt_item(row):
    return f"{row['name']} (₹{row['price']:.2f})"


def set_db_path(path):
    db.DB_FILE = path
    db.init_db()


def load_settings():
    return {
        "shop_name": db.get_setting("shop_name", "Milk Billing System"),
        "shop_address": db.get_setting("shop_address", ""),
        "shop_contact": db.get_setting("shop_contact", ""),
        "app_username": db.get_setting("app_username", DEFAULT_USERNAME),
        "app_password_hash": db.get_setting("app_password_hash", ""),
    }


def hash_password(raw_password):
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


def get_username():
    return db.get_setting("app_username", DEFAULT_USERNAME)


def is_password_set():
    return bool(db.get_setting("app_password_hash", ""))


def verify_credentials(username, raw_password):
    stored_hash = db.get_setting("app_password_hash", "")
    stored_username = get_username()
    if not stored_hash:
        return (
            username == DEFAULT_USERNAME
            and raw_password == DEFAULT_PASSWORD
        )
    if username != stored_username:
        return False
    return hmac.compare_digest(stored_hash, hash_password(raw_password))


def enforce_login():
    if not is_password_set():
        return True
    if st.session_state.get("authenticated"):
        return True

    st.title("Milk Billing System")
    st.info("Login required.")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
    if submitted:
        if verify_credentials(username, password):
            st.session_state.authenticated = True
            st.success("Logged in.")
            st.rerun()
        else:
            st.error("Invalid password.")
    return False


def sidebar_data_access():
    st.sidebar.header("Data Access")
    if "db_path" not in st.session_state:
        st.session_state.db_path = DEFAULT_DB

    uploaded = st.sidebar.file_uploader(
        "Upload database (.db)", type=["db", "sqlite", "sqlite3"]
    )
    if uploaded:
        upload_dir = os.path.join(APP_DIR, "uploaded")
        os.makedirs(upload_dir, exist_ok=True)
        uploaded_path = os.path.join(upload_dir, "milk_billing.db")
        with open(uploaded_path, "wb") as f:
            f.write(uploaded.getbuffer())
        st.session_state.db_path = uploaded_path
        st.sidebar.success("Uploaded database is now in use.")
        st.rerun()

    if st.sidebar.button("Use local database"):
        st.session_state.db_path = DEFAULT_DB
        st.sidebar.success("Local database selected.")
        st.rerun()

    if os.path.exists(st.session_state.db_path):
        with open(st.session_state.db_path, "rb") as f:
            st.sidebar.download_button(
                "Download current database",
                f,
                file_name="milk_billing.db",
            )

    st.sidebar.caption(f"Active DB: {os.path.basename(st.session_state.db_path)}")


def render_masters_tab():
    st.subheader("Masters")
    customers_tab, partners_tab, items_tab, managers_tab, settings_tab = st.tabs(
        ["Customers", "Delivery Partners", "Items", "Managers", "Settings"]
    )

    with customers_tab:
        st.markdown("### Customers")
        search = st.text_input("Search", "")
        customer_rows = rows_to_dicts(db.list_customers_with_balance(search))
        st.dataframe(customer_rows, use_container_width=True)

        with st.expander("Add Customer", expanded=False):
            with st.form("add_customer_form"):
                name = st.text_input("Name")
                contact = st.text_input("Contact")
                address = st.text_input("Address")
                alt_contact = st.text_input("Alt Contact")
                submitted = st.form_submit_button("Add Customer")
            if submitted:
                if not name.strip():
                    st.error("Customer name is required.")
                else:
                    db.add_customer(name.strip(), contact.strip(), address.strip(), alt_contact.strip())
                    st.success("Customer added.")
                    st.rerun()

        active_customers = rows_to_dicts(db.list_customers())
        if active_customers:
            selection = st.selectbox(
                "Select customer to update/delete",
                options=active_customers,
                format_func=fmt_name,
            )
            st.markdown("#### Update Customer")
            with st.form("update_customer_form"):
                name = st.text_input("Name", value=selection["name"])
                contact = st.text_input("Contact", value=selection.get("contact") or "")
                address = st.text_input("Address", value=selection.get("address") or "")
                alt_contact = st.text_input(
                    "Alt Contact", value=selection.get("alt_contact") or ""
                )
                updated = st.form_submit_button("Update Customer")
            if updated:
                if not name.strip():
                    st.error("Customer name is required.")
                else:
                    db.update_customer(
                        selection["id"],
                        name.strip(),
                        contact.strip(),
                        address.strip(),
                        alt_contact.strip(),
                    )
                    st.success("Customer updated.")
                    st.rerun()

            if st.button("Delete Customer"):
                db.deactivate_customer(selection["id"])
                st.success("Customer deleted.")
                st.rerun()

    with partners_tab:
        st.markdown("### Delivery Partners")
        partners = rows_to_dicts(db.list_delivery_partners())
        st.dataframe(partners, use_container_width=True)

        with st.expander("Add Partner", expanded=False):
            with st.form("add_partner_form"):
                name = st.text_input("Name")
                contact = st.text_input("Contact")
                address = st.text_input("Address")
                submitted = st.form_submit_button("Add Partner")
            if submitted:
                if not name.strip():
                    st.error("Partner name is required.")
                else:
                    db.add_delivery_partner(name.strip(), contact.strip(), address.strip())
                    st.success("Partner added.")
                    st.rerun()

        if partners:
            selection = st.selectbox(
                "Select partner to update/delete",
                options=partners,
                format_func=fmt_name,
                key="partner_select",
            )
            st.markdown("#### Update Partner")
            with st.form("update_partner_form"):
                name = st.text_input("Name", value=selection["name"])
                contact = st.text_input("Contact", value=selection.get("contact") or "")
                address = st.text_input("Address", value=selection.get("address") or "")
                updated = st.form_submit_button("Update Partner")
            if updated:
                if not name.strip():
                    st.error("Partner name is required.")
                else:
                    db.update_delivery_partner(
                        selection["id"], name.strip(), contact.strip(), address.strip()
                    )
                    st.success("Partner updated.")
                    st.rerun()

            if st.button("Delete Partner"):
                db.deactivate_delivery_partner(selection["id"])
                st.success("Partner deleted.")
                st.rerun()

    with items_tab:
        st.markdown("### Items")
        items = rows_to_dicts(db.list_items())
        st.dataframe(items, use_container_width=True)

        with st.expander("Add Item", expanded=False):
            with st.form("add_item_form"):
                name = st.text_input("Item Name")
                price = st.number_input("Price", min_value=0.0, step=1.0, format="%.2f")
                submitted = st.form_submit_button("Add Item")
            if submitted:
                if not name.strip():
                    st.error("Item name is required.")
                else:
                    db.add_item(name.strip(), float(price))
                    st.success("Item added.")
                    st.rerun()

        if items:
            selection = st.selectbox(
                "Select item to update/delete",
                options=items,
                format_func=fmt_item,
                key="item_select",
            )
            st.markdown("#### Update Item")
            with st.form("update_item_form"):
                name = st.text_input("Item Name", value=selection["name"])
                price = st.number_input(
                    "Price", min_value=0.0, step=1.0, format="%.2f", value=float(selection["price"])
                )
                updated = st.form_submit_button("Update Item")
            if updated:
                if not name.strip():
                    st.error("Item name is required.")
                else:
                    db.update_item(selection["id"], name.strip(), float(price))
                    st.success("Item updated.")
                    st.rerun()

            if st.button("Delete Item"):
                db.delete_item(selection["id"])
                st.success("Item deleted.")
                st.rerun()

    with managers_tab:
        st.markdown("### Managers")
        managers = rows_to_dicts(db.list_managers())
        st.dataframe(managers, use_container_width=True)

        with st.expander("Add Manager", expanded=False):
            with st.form("add_manager_form"):
                name = st.text_input("Name")
                contact = st.text_input("Contact")
                submitted = st.form_submit_button("Add Manager")
            if submitted:
                if not name.strip():
                    st.error("Manager name is required.")
                else:
                    db.add_manager(name.strip(), contact.strip())
                    st.success("Manager added.")
                    st.rerun()

        if managers:
            selection = st.selectbox(
                "Select manager to update/delete",
                options=managers,
                format_func=fmt_name,
                key="manager_select",
            )
            st.markdown("#### Update Manager")
            with st.form("update_manager_form"):
                name = st.text_input("Name", value=selection["name"])
                contact = st.text_input("Contact", value=selection.get("contact") or "")
                updated = st.form_submit_button("Update Manager")
            if updated:
                if not name.strip():
                    st.error("Manager name is required.")
                else:
                    db.update_manager(selection["id"], name.strip(), contact.strip())
                    st.success("Manager updated.")
                    st.rerun()

            if st.button("Delete Manager"):
                db.delete_manager(selection["id"])
                st.success("Manager deleted.")
                st.rerun()

    with settings_tab:
        st.markdown("### Shop Settings")
        settings = load_settings()
        with st.form("settings_form"):
            shop_name = st.text_input("Shop Name", value=settings["shop_name"])
            shop_address = st.text_input("Shop Address", value=settings["shop_address"])
            shop_contact = st.text_input("Shop Contact", value=settings["shop_contact"])
            st.markdown("#### App Login")
            app_username = st.text_input("Username", value=settings["app_username"])
            st.markdown("#### App Login Password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            saved = st.form_submit_button("Save Settings")
        if saved:
            if not shop_name.strip():
                st.error("Shop name is required.")
            else:
                if new_password or confirm_password:
                    if new_password != confirm_password:
                        st.error("Passwords do not match.")
                        return
                    db.set_setting("app_password_hash", hash_password(new_password))
                if app_username.strip():
                    db.set_setting("app_username", app_username.strip())
                db.set_setting("shop_name", shop_name.strip())
                db.set_setting("shop_address", shop_address.strip())
                db.set_setting("shop_contact", shop_contact.strip())
                st.success("Settings saved.")
                st.rerun()

        if settings.get("app_password_hash"):
            if st.button("Remove App Password"):
                db.set_setting("app_password_hash", "")
                st.session_state.authenticated = False
                st.success("Password removed.")
                st.rerun()


def render_daily_delivery_tab():
    st.subheader("Daily Delivery")
    customers = rows_to_dicts(db.list_customers())
    partners = rows_to_dicts(db.list_delivery_partners())
    items = rows_to_dicts(db.list_items())
    managers = rows_to_dicts(db.list_managers())

    with st.expander("Record Delivery", expanded=True):
        with st.form("add_delivery_form"):
            delivery_date = st.date_input("Date", value=to_date(db.today_str()))
            customer = st.selectbox("Customer", options=customers, format_func=fmt_name)
            item = st.selectbox("Item", options=items, format_func=fmt_item)
            quantity = st.number_input("Quantity", min_value=1, step=1, value=1)
            partner = st.selectbox(
                "Delivery Partner", options=partners, format_func=fmt_name
            )
            manager = st.selectbox("Manager", options=managers, format_func=fmt_name)
            submitted = st.form_submit_button("Save Delivery")
        if submitted:
            if not all([customer, item, partner, manager]):
                st.error("Please fill all delivery fields.")
            else:
                db.add_daily_delivery(
                    date_to_str(delivery_date),
                    customer["id"],
                    item["id"],
                    int(quantity),
                    float(item["price"]),
                    partner["id"],
                    manager["id"],
                )
                st.success("Delivery recorded.")
                st.rerun()

    st.markdown("### Update / Delete Delivery")
    filter_date = st.date_input("Filter Date", value=to_date(db.today_str()), key="delivery_filter")
    show_all = st.checkbox("Show all deliveries", value=False)
    deliveries = rows_to_dicts(
        db.list_daily_deliveries(None if show_all else date_to_str(filter_date))
    )
    st.dataframe(deliveries, use_container_width=True)
    if deliveries:
        selection = st.selectbox(
            "Select delivery",
            options=deliveries,
            format_func=lambda r: f"{r['date']} - {r['customer_name']} - {r['item_name']} ({r['quantity']})",
        )
        with st.form("update_delivery_form"):
            delivery_date = st.date_input(
                "Date", value=to_date(selection["date"]), key="update_delivery_date"
            )
            customer = st.selectbox(
                "Customer",
                options=customers,
                format_func=fmt_name,
                index=next(
                    (i for i, c in enumerate(customers) if c["id"] == selection["customer_id"]),
                    0,
                ),
            )
            item = st.selectbox(
                "Item",
                options=items,
                format_func=fmt_item,
                index=next((i for i, it in enumerate(items) if it["id"] == selection["item_id"]), 0),
            )
            quantity = st.number_input(
                "Quantity", min_value=1, step=1, value=int(selection["quantity"])
            )
            partner = st.selectbox(
                "Delivery Partner",
                options=partners,
                format_func=fmt_name,
                index=next(
                    (i for i, p in enumerate(partners) if p["id"] == selection["delivery_partner_id"]),
                    0,
                ),
            )
            manager = st.selectbox(
                "Manager",
                options=managers,
                format_func=fmt_name,
                index=next(
                    (i for i, m in enumerate(managers) if m["id"] == selection["manager_id"]),
                    0,
                ),
            )
            updated = st.form_submit_button("Update Delivery")
        if updated:
            db.update_daily_delivery(
                selection["id"],
                date_to_str(delivery_date),
                customer["id"],
                item["id"],
                int(quantity),
                float(item["price"]),
                partner["id"],
                manager["id"],
            )
            st.success("Delivery updated.")
            st.rerun()

        if st.button("Delete Delivery"):
            db.delete_daily_delivery(selection["id"])
            st.success("Delivery deleted.")
            st.rerun()

    st.divider()
    st.markdown("### Advance Payments")
    with st.expander("Record Payment", expanded=True):
        with st.form("add_payment_form"):
            customer = st.selectbox("Customer", options=customers, format_func=fmt_name, key="pay_cust")
            amount = st.number_input("Amount", min_value=0.0, step=1.0, format="%.2f")
            payment_date = st.date_input("Date", value=to_date(db.today_str()), key="pay_date")
            notes = st.text_input("Notes")
            submitted = st.form_submit_button("Save Payment")
        if submitted:
            if not customer:
                st.error("Customer is required.")
            else:
                db.add_advance_payment(customer["id"], float(amount), date_to_str(payment_date), notes.strip())
                st.success("Payment recorded.")
                st.rerun()

    st.markdown("### Update / Delete Payment")
    payment_filter = st.date_input(
        "Filter Date", value=to_date(db.today_str()), key="payment_filter"
    )
    show_all_payments = st.checkbox("Show all payments", value=False)
    payments = rows_to_dicts(
        db.list_advance_payments(None if show_all_payments else date_to_str(payment_filter))
    )
    st.dataframe(payments, use_container_width=True)
    if payments:
        selection = st.selectbox(
            "Select payment",
            options=payments,
            format_func=lambda r: f"{r['date']} - {r['customer_name']} (₹{r['amount']:.2f})",
            key="payment_select",
        )
        with st.form("update_payment_form"):
            customer = st.selectbox(
                "Customer",
                options=customers,
                format_func=fmt_name,
                index=next(
                    (i for i, c in enumerate(customers) if c["id"] == selection["customer_id"]),
                    0,
                ),
                key="payment_customer_update",
            )
            amount = st.number_input(
                "Amount", min_value=0.0, step=1.0, format="%.2f", value=float(selection["amount"])
            )
            payment_date = st.date_input(
                "Date", value=to_date(selection["date"]), key="payment_date_update"
            )
            notes = st.text_input("Notes", value=selection.get("notes") or "")
            updated = st.form_submit_button("Update Payment")
        if updated:
            db.update_advance_payment(
                selection["id"],
                customer["id"],
                float(amount),
                date_to_str(payment_date),
                notes.strip(),
            )
            st.success("Payment updated.")
            st.rerun()

        if st.button("Delete Payment"):
            db.delete_advance_payment(selection["id"])
            st.success("Payment deleted.")
            st.rerun()


def render_partner_stock_tab():
    st.subheader("Partner Stock")
    partners = rows_to_dicts(db.list_delivery_partners())
    items = rows_to_dicts(db.list_items())
    managers = rows_to_dicts(db.list_managers())

    with st.expander("Record Allocation", expanded=True):
        with st.form("add_allocation_form"):
            allocation_date = st.date_input("Date", value=to_date(db.today_str()))
            partner = st.selectbox("Delivery Partner", options=partners, format_func=fmt_name)
            manager = st.selectbox("Manager", options=managers, format_func=fmt_name)
            item = st.selectbox("Item", options=items, format_func=fmt_item)
            quantity = st.number_input("Quantity", min_value=1, step=1, value=1)
            submitted = st.form_submit_button("Save Allocation")
        if submitted:
            if not all([partner, manager, item]):
                st.error("Please fill all allocation fields.")
            else:
                db.add_partner_allocation(
                    date_to_str(allocation_date),
                    partner["id"],
                    manager["id"],
                    item["id"],
                    int(quantity),
                )
                st.success("Allocation recorded.")
                st.rerun()

    st.markdown("### Update / Delete Allocation")
    alloc_filter = st.date_input(
        "Filter Date", value=to_date(db.today_str()), key="alloc_filter"
    )
    show_all_alloc = st.checkbox("Show all allocations", value=False)
    allocations = rows_to_dicts(
        db.list_partner_allocations_all(None if show_all_alloc else date_to_str(alloc_filter))
    )
    st.dataframe(allocations, use_container_width=True)
    if allocations:
        selection = st.selectbox(
            "Select allocation",
            options=allocations,
            format_func=lambda r: f"{r['date']} - {r['partner_name']} - {r['item_name']} ({r['quantity']})",
            key="allocation_select",
        )
        with st.form("update_allocation_form"):
            allocation_date = st.date_input(
                "Date", value=to_date(selection["date"]), key="allocation_date_update"
            )
            partner = st.selectbox(
                "Delivery Partner",
                options=partners,
                format_func=fmt_name,
                index=next(
                    (i for i, p in enumerate(partners) if p["id"] == selection["delivery_partner_id"]),
                    0,
                ),
            )
            manager = st.selectbox(
                "Manager",
                options=managers,
                format_func=fmt_name,
                index=next(
                    (i for i, m in enumerate(managers) if m["id"] == selection["manager_id"]),
                    0,
                ),
            )
            item = st.selectbox(
                "Item",
                options=items,
                format_func=fmt_item,
                index=next((i for i, it in enumerate(items) if it["id"] == selection["item_id"]), 0),
            )
            quantity = st.number_input(
                "Quantity", min_value=1, step=1, value=int(selection["quantity"])
            )
            updated = st.form_submit_button("Update Allocation")
        if updated:
            db.update_partner_allocation(
                selection["id"],
                date_to_str(allocation_date),
                partner["id"],
                manager["id"],
                item["id"],
                int(quantity),
            )
            st.success("Allocation updated.")
            st.rerun()

        if st.button("Delete Allocation"):
            db.delete_partner_allocation(selection["id"])
            st.success("Allocation deleted.")
            st.rerun()

    st.divider()
    st.markdown("### Partner Summary")
    if partners:
        summary_date = st.date_input(
            "Summary Date", value=to_date(db.today_str()), key="summary_date"
        )
        partner = st.selectbox(
            "Partner", options=partners, format_func=fmt_name, key="summary_partner"
        )
        if st.button("Load Summary", key="partner_load_summary"):
            allocations = db.list_partner_allocations(partner["id"], date_to_str(summary_date))
            deliveries = db.list_partner_deliveries(partner["id"], date_to_str(summary_date))
            remaining = db.partner_remaining(partner["id"], date_to_str(summary_date))
            lines = [
                f"Partner Summary for {date_to_str(summary_date)}",
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
            st.text("\n".join(lines))


def render_reports_tab():
    st.subheader("Reports")
    customers = rows_to_dicts(db.list_customers())
    settings = load_settings()

    st.markdown("### Customer Summary")
    if customers:
        customer = st.selectbox("Customer", options=customers, format_func=fmt_name, key="report_customer")
        start_date = st.date_input("From Date", value=to_date(db.today_str()), key="report_from")
        end_date = st.date_input("To Date", value=to_date(db.today_str()), key="report_to")
        if st.button("Load Summary", key="report_load_summary"):
            total_qty, total_amount, total_paid = db.customer_summary_range(
                customer["id"], date_to_str(start_date), date_to_str(end_date)
            )
            balance = total_amount - total_paid
            dues = balance if balance > 0 else 0.0
            credit = -balance if balance < 0 else 0.0
            lines = [
                f"Customer: {customer['name']}",
                f"Date Range: {date_to_str(start_date)} to {date_to_str(end_date)}",
                f"Total Qty: {total_qty}",
                f"Total Amount: {total_amount:.2f}",
                f"Total Paid: {total_paid:.2f}",
                f"Dues: {dues:.2f}    Credit: {credit:.2f}",
            ]
            st.text("\n".join(lines))

        st.markdown("### Customer Receipt (PDF)")
        if st.button("Generate Receipt PDF", key="report_generate_receipt"):
            deliveries, payments = db.customer_statement_range(
                customer["id"], date_to_str(start_date), date_to_str(end_date)
            )
            temp_dir = tempfile.mkdtemp()
            preview_path = os.path.join(temp_dir, "receipt_preview.pdf")
            generate_customer_receipt(
                preview_path,
                settings["shop_name"],
                settings["shop_address"],
                settings["shop_contact"],
                customer,
                f"{date_to_str(start_date)} to {date_to_str(end_date)}",
                deliveries,
                payments,
            )
            with open(preview_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                "Download Receipt",
                data=pdf_bytes,
                file_name="customer_receipt.pdf",
                mime="application/pdf",
            )


def render_lists_tab():
    st.subheader("Lists")
    deliveries_tab, payments_tab, allocations_tab = st.tabs(
        ["Deliveries", "Payments", "Allocations"]
    )

    with deliveries_tab:
        default_date = to_date(db.today_str())
        date_range = st.date_input(
            "Filter Date Range",
            value=(default_date, default_date),
            key="list_deliveries_date_range",
        )
        show_all = st.checkbox("Show all deliveries", value=False, key="list_deliveries_all")
        rows = rows_to_dicts(db.list_daily_deliveries())
        if not show_all and isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            rows = [
                row
                for row in rows
                if date_to_str(start_date) <= row["date"] <= date_to_str(end_date)
            ]
        display_rows = [
            {
                "date": row["date"],
                "customer": row["customer_name"],
                "item": row["item_name"],
                "qty": row["quantity"],
                "partner": row["partner_name"],
                "manager": row["manager_name"],
            }
            for row in rows
        ]
        st.dataframe(
            display_rows,
            use_container_width=True,
            column_config={
                "date": st.column_config.TextColumn("Date", width="medium"),
                "customer": st.column_config.TextColumn("Customer"),
                "item": st.column_config.TextColumn("Item"),
                "qty": st.column_config.NumberColumn("Qty"),
                "partner": st.column_config.TextColumn("Partner"),
                "manager": st.column_config.TextColumn("Manager"),
            },
        )

    with payments_tab:
        default_date = to_date(db.today_str())
        date_range = st.date_input(
            "Filter Date Range",
            value=(default_date, default_date),
            key="list_payments_date_range",
        )
        show_all = st.checkbox("Show all payments", value=False, key="list_payments_all")
        rows = rows_to_dicts(db.list_advance_payments())
        if not show_all and isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            rows = [
                row
                for row in rows
                if date_to_str(start_date) <= row["date"] <= date_to_str(end_date)
            ]
        display_rows = [
            {
                "date": row["date"],
                "customer": row["customer_name"],
                "amount": row["amount"],
                "notes": row.get("notes") or "",
            }
            for row in rows
        ]
        st.dataframe(
            display_rows,
            use_container_width=True,
            column_config={
                "date": st.column_config.TextColumn("Date", width="medium"),
                "customer": st.column_config.TextColumn("Customer"),
                "amount": st.column_config.NumberColumn("Amount", format="₹%.2f"),
                "notes": st.column_config.TextColumn("Notes"),
            },
        )

    with allocations_tab:
        default_date = to_date(db.today_str())
        date_range = st.date_input(
            "Filter Date Range",
            value=(default_date, default_date),
            key="list_allocations_date_range",
        )
        show_all = st.checkbox("Show all allocations", value=False, key="list_allocations_all")
        rows = rows_to_dicts(db.list_partner_allocations_all())
        if not show_all and isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            rows = [
                row
                for row in rows
                if date_to_str(start_date) <= row["date"] <= date_to_str(end_date)
            ]
        display_rows = [
            {
                "date": row["date"],
                "partner": row["partner_name"],
                "item": row["item_name"],
                "qty": row["quantity"],
                "manager": row["manager_name"],
            }
            for row in rows
        ]
        st.dataframe(
            display_rows,
            use_container_width=True,
            column_config={
                "date": st.column_config.TextColumn("Date", width="medium"),
                "partner": st.column_config.TextColumn("Partner"),
                "item": st.column_config.TextColumn("Item"),
                "qty": st.column_config.NumberColumn("Qty"),
                "manager": st.column_config.TextColumn("Manager"),
            },
        )


def main():
    st.set_page_config(page_title="Milk Billing System", layout="wide")
    sidebar_data_access()
    set_db_path(st.session_state.db_path)

    if not enforce_login():
        return

    st.title("Milk Billing System (Web & Mobile)")
    st.caption("Use this app from mobile by opening the Streamlit URL in your phone browser.")

    if is_password_set():
        if st.sidebar.button("Logout"):
            st.session_state.authenticated = False
            st.sidebar.success("Logged out.")
            st.rerun()

    masters, daily, stock, reports, lists = st.tabs(
        ["Masters", "Daily Delivery", "Partner Stock", "Reports", "Lists"]
    )
    with masters:
        render_masters_tab()
    with daily:
        render_daily_delivery_tab()
    with stock:
        render_partner_stock_tab()
    with reports:
        render_reports_tab()
    with lists:
        render_lists_tab()


if __name__ == "__main__":
    main()
