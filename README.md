# Milk Billing System (Offline + Web)

Offline Windows desktop app plus Streamlit web app for daily milk delivery billing.
Built with Python + Tkinter/Streamlit and SQLite.

## Features
- Manage customers, delivery partners, items, and managers
- Record daily deliveries
- Record advance payments (credit)
- Track delivery partner allocations and remaining packets
- Generate monthly customer PDF receipts

## Setup
1. Create a virtual environment (optional).
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the desktop app:
   ```
   python app.py
   ```
4. Run the web/mobile app:
   ```
   streamlit run streamlit_app.py
   ```

The SQLite database file (`milk_billing.db`) is created locally in the project folder.

## Mobile Access
- Start the Streamlit app on your PC.
- On your phone (same Wi-Fi), open the Streamlit URL: `http://<pc-ip>:8501`.
- To use a different database from mobile, upload the `.db` file from the sidebar.

## Streamlit Cloud (Optional)
You can deploy `streamlit_app.py` to Streamlit Cloud and upload your database
from mobile using the sidebar uploader.

## Build EXE (Windows)
1. Build:
   ```
   powershell -ExecutionPolicy Bypass -File build_exe.ps1
   ```
2. Create Desktop shortcut:
   ```
   powershell -ExecutionPolicy Bypass -File create_shortcut.ps1
   ```
If the EXE exists, the shortcut points to it; otherwise it points to `run_app.bat`.
