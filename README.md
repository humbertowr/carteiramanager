# Carteira Manager

Carteira Manager is a desktop application built with Python for managing, consolidating, filtering, and scheduling customer order backlogs exported from ERP CSV files.

The system was designed for operational order management, allowing users to import a full order portfolio, identify available values for billing, block specific items or customers, manage overdue orders, and build a programmed billing list through the PROG 2 module.

---

## Features

### CSV Import

Import an ERP-generated CSV file containing the full order backlog.

The system processes the main order information, including:

- Order number
- Customer legal name
- Item code
- Item description
- Requested quantity
- Invoiced quantity
- Unit value
- Delivery date
- Billing group
- Order observations

The order backlog value is calculated using:

```txt
Backlog Quantity = Requested Quantity - Invoiced Quantity
Backlog Value = Backlog Quantity × Unit Value
```

---

## Order Management

The main order screen displays orders grouped by order number, with all related items shown underneath.

Each order includes:

- Order number
- Customer legal name
- Total order value
- Blocked value
- Released value
- Delivery date
- Billing group
- Status

Orders can be filtered, sorted, expanded, collapsed, and selected for programming.

When an order is added to PROG 2, it is removed from the main order backlog view to avoid duplicate handling.

---

## PROG 2

The PROG 2 tab is used to build a billing schedule.

Main capabilities:

- Add selected orders to PROG 2
- Remove selected orders from PROG 2
- View only programmed orders
- Calculate the total released billing value
- Define a daily billing target
- Display the remaining amount needed to reach the daily billing target
- Export programmed orders or items

The daily billing target calculation is based on:

```txt
Remaining Target = Daily Billing Target - Released PROG 2 Value
```

If the released PROG 2 value is greater than the target, the system displays the exceeded amount.

---

## Blocking Rules

Carteira Manager supports operational blocking rules to prevent specific orders, items, customers, or observations from being considered available for billing.

Supported blocking types:

- Item blocking
- Customer blocking
- Observation-based blocking
- Order blocking
- Global item blocking

Blocked values are automatically deducted from the released order value.

---

## Overdue Orders

The Atrasados tab displays overdue orders based on the delivery date column from the imported CSV.

It shows:

- Overdue orders
- Number of days overdue
- Total overdue value
- Released overdue value
- Items related to overdue orders

This helps prioritize delayed orders for operational follow-up.

---

## Export Options

Carteira Manager supports exporting data to:

- Excel
- PDF
- CSV

Available exports include:

- PROG 2 items
- PROG 2 orders
- Current tab data
- Full Excel report

PDF exports are opened automatically after generation.

---

## Local Data Storage

The application stores user preferences and saved operational state locally.

Examples of saved data:

- Last imported CSV path
- PROG 2 orders
- Blocked items
- Blocked customers
- Blocked observations
- Presets
- Daily billing target

Local configuration is stored in:

```txt
C:\Users\<USER>\.carteira_ops\config.json
```

Logs are stored in:

```txt
C:\Users\<USER>\.carteira_ops\logs\
```

---

## Project Structure

```txt
carteira/
│
├── app.py
│
├── core/
│   ├── app_state.py
│   ├── carteira_processor.py
│   ├── config_manager.py
│   ├── exporter.py
│   └── formatters.py
│
├── ui/
│   ├── main_window.py
│   ├── pedidos_tab.py
│   ├── prog2_tab.py
│   ├── atrasados_tab.py
│   ├── bloqueios_tab.py
│   ├── consolidacoes_tab.py
│   ├── sortable_tree.py
│   └── styles.py
│
├── requirements.txt
└── README.md
```

---

## Requirements

Recommended Python version:

```txt
Python 3.10+
```

Required packages:

```txt
pandas
openpyxl
reportlab
```

For building the executable:

```txt
pyinstaller
```

---

## Installation

Clone or copy the project folder, then open the terminal inside the project directory.

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate the virtual environment:

```powershell
.venv\Scripts\activate
```

Install the dependencies:

```powershell
pip install -r requirements.txt
```

If there is no `requirements.txt`, install manually:

```powershell
pip install pandas openpyxl reportlab
```

Run the application:

```powershell
python app.py
```

---

## Build Executable

To generate a Windows executable, install PyInstaller:

```powershell
pip install pyinstaller
```

Clean previous builds:

```powershell
rmdir /s /q build
rmdir /s /q dist
del CarteiraManager.spec
```

Build the application:

```powershell
pyinstaller --noconfirm --clean --onedir --windowed --name CarteiraManager app.py
```

The executable will be generated at:

```txt
dist\CarteiraManager\CarteiraManager.exe
```

To distribute the application, send the entire folder:

```txt
dist\CarteiraManager
```

Do not send only the `.exe` file, because the application depends on the files inside the generated folder.

---

## Debug Build

If the application does not open on another computer, generate a debug version:

```powershell
pyinstaller --noconfirm --clean --onedir --name CarteiraManagerDebug app.py
```

Then run:

```txt
dist\CarteiraManagerDebug\CarteiraManagerDebug.exe
```

This version opens with a console window and displays possible errors.

---

## CSV Requirements

The imported CSV must contain the required ERP columns or equivalent mapped columns.

Expected information:

- Order number
- Customer legal name
- Item code
- Item description
- Requested quantity
- Invoiced quantity
- Unit value
- Delivery date
- Billing group
- Observation

The application recalculates backlog quantity and backlog value internally to avoid relying only on the ERP exported backlog value.

---

## Operational Workflow

Recommended daily usage:

```txt
1. Import the ERP CSV file.
2. Review the backlog in the Orders tab.
3. Apply item, customer, or observation blocks if needed.
4. Review overdue orders.
5. Select orders to add to PROG 2.
6. Check the released PROG 2 value against the daily billing target.
7. Export the required PDF or Excel report.
```

---

## Main Goal

Carteira Manager was created to reduce manual work in order backlog analysis and billing preparation.

The system helps users:

- Consolidate large ERP order exports
- Identify what can actually be billed
- Remove blocked values from available totals
- Build a focused billing schedule
- Track overdue orders
- Export operational reports for billing and separation

---

## License

Internal use project.

---

## Status

Active development.
