# Carteira Manager

Windows desktop tool for backlog control, PROG2 workflow, item pending issues, billing goals and exports.

## Features

* CSV import
* Order and item tracking
* PROG2 management
* Item pending reasons
* Blocked and billed order control
* Daily/monthly billing goals
* Bottleneck dashboard
* Excel/PDF exports
* Shared network-folder mode

## Run

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

## Build

```bat
pyinstaller --noconfirm --onefile --windowed --name CarteiraManager app.py
```

## Shared Mode

Create a local `config_local.json`:

```json
{
  "modo_compartilhado": true,
  "usuario": "UserName",
  "pasta_dados": "\\\\server-file\\PCP\\CarteiraManager\\data",
  "pasta_backups": "\\\\server-file\\PCP\\CarteiraManager\\backups",
  "pasta_exports": "\\\\server-file\\PCP\\CarteiraManager\\exports",
  "pasta_logs": "\\\\server-file\\PCP\\CarteiraManager\\logs"
}
```

## Deployment

```text
C:\CarteiraManager
├── CarteiraManager.exe
└── config_local.json
```

`config_local.json` must remain local and must not be committed.
