# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VTS (Vacadari Terminal System) is a Django 6 inventory management and payroll system for a small retail store (Thunderbluff). It runs on a local server at `http://thunderbluff.local:9000` or via Docker on port 9000.

## Commands

```bash
# Run development server (direct, outside Docker)
source venv/bin/activate
python manage.py runserver 0.0.0.0:9000

# Docker deployment
docker-compose up -d
docker exec -it vts_martillo_vil python manage.py <command>

# Django management commands
python manage.py migrate
python manage.py importar_csv          # Import inventory audit from CLI/AUDITORIA_VTS_*.csv
python manage.py importar_sumup        # Import SumUp sales CSV
python manage.py generar_inventario_pdf
python manage.py exportar_sumup
python manage.py backfill_sku_historial
python manage.py dump_vts_context      # Dump context for AI/debugging

# Static files
python manage.py collectstatic
```

## Architecture

**Django project root**: `martillo_vil/` (settings, urls, wsgi)  
**Main app**: `dashboard/` — contains all models, views, engines, and templates

### Models (`dashboard/models/`)

Split across four files, all re-exported from `models/__init__.py`:

- **`inventario.py`**: `AuditoriaVTS` (core — SKU as PK), `VarianteVTS` (child table for size/color variants), `HistorialStock`
- **`logs.py`**: `LogRetirosDeducibles` (Aporte Hogar withdrawals), `RegistroLogs` (general movements), `VentaRegistrada` (anti-double-discount lock), `HistorialVentas`
- **`personal.py`**: `Colaborador` (staff records with payroll fields)
- **`config.py`**: `ConfigVTS` (key-value cost factors), `PerfilVTS` (role-based access linked to Django User)

**SKU format**: `V-{PREFIX}-{NNN}` (e.g. `V-ABA-001`, `V-BOU-023`). Prefixes are defined in `AuditoriaVTS.SECCION_PREFIJOS`.

### Views (split by domain)

`views.py` is a pure router that re-exports from:
- `views_inventario.py` — dashboard home, inventory CRUD, PDF export, FelEngine analysis
- `views_movimientos.py` — La Triada (VENTA/INGRESO/MERMA), Aporte Hogar, HTMX endpoints
- `views_personal.py` — staff ficha, Sabana Digital, Mortaja (liquidation)
- `views_ventas.py` — SumUp CSV import and report

### Engines

- **`engine.py` → `FelEngine`**: Pandas-based financial report. Merges simple products and variants into a single DataFrame, calculates ROI by section. Called from `analisis_pro` view.
- **`eremita_engine.py` → `EremitaEngine`**: Payroll/liquidation calculator. Applies Chilean labor law (Art. 47 gratificación, movilización mínima with +10% lock).
- **`oraculo.py` → `OraculoSargerite`**: Fetches legal labor indicators (sueldo mínimo, UF, UTM).
- **`akama.py` → `AkamaStrategy`**: Parses staff CSV imports with RUT normalization and date parsing.

### Security Layer

- **`sargerite.py`**: `@sargerite_shield(permiso_requerido=...)` decorator for API endpoints. Validates UUID token (injected into session at login via signal) against `PerfilVTS`. In production, also requires a hardware key file at `/mnt/vts_key/vts_root.key`. Sends Telegram alerts on violations via `alertar_a_lannu()`.
- **`martillo_vil/pollofrito.py`**: Dead man's switch — if the hardware key at `/mnt/VTSCORE/vts_root.key` is absent for 30 minutes, it stops the service and shreds `db.sqlite3`. Uses env vars `GIGA_SLAVE_ABORT` and `GIGA_SLAVE_OVERRIDE` for emergency abort.

### Key Financial Logic

- Prices are always stored as **VENTA BRUTO** (includes 19% IVA). Net margin is calculated via `margen_valor` property.
- `margen_valor` reads cost factors from `ConfigVTS` (keys ending in `_pct`), applies them to `precio_costo`, then computes `(venta - costo_real) / venta`.
- Stock health thresholds use a baseline of 10 units: ≤0 = QUIEBRE, ≤25% = CRÍTICO, ≤60% = REVISAR, ≤100% = ÓPTIMO, >100% = SOBRESTOCK.
- Rentability tiers: PÉRDIDA (<0%), SOBREVIVENCIA (<10%), NEUTRO (<18%), SALUDABLE (<26%), ÓPTIMO (<36%), ILLIDARI (≥36%).

### Role System

Roles and their permissions are auto-mapped in `PerfilVTS.save()`:
| Role | Fotos | Stock | Dikbig | Ventas |
|---|---|---|---|---|
| Boss | ✓ | ✓ | ✓ | ✓ |
| Jefe-Local | ✓ | ✓ | ✗ | ✓ |
| Analista-Bodega | ✓ | ✓ | ✗ | ✗ |
| Vendedor | ✗ | ✗ | ✗ | ✓ |

### Image Handling

Product images are auto-converted to WebP (max 800px, quality 80) via Pillow in `AuditoriaVTS.save()` and `VarianteVTS.save()`. Media files live in `media/`.

### Environment Variables (`.env`)

Required: `SECRET_KEY`, `SARGERITE_EXPECTED_HASH`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `ALLOWED_HOSTS`.

### Legacy CLI (`CLI/`)

Pre-web Python scripts kept for reference and for CSV generation (audit files like `AUDITORIA_VTS_*.csv` that `importar_csv` reads). Not actively developed.
