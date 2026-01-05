# VTS - Vacadari Terminal System v1.7.6 🐮

Sistema de gestión de inventario táctico basado en terminal para control de stock, valorización y toma de decisiones ejecutivas.

## 🚀 Inicio Rápido 2026
1. Asegurarse de tener `pandas` instalado: `pip install pandas`.
2. Mantener los archivos `data_s.csv` y `data_v.csv` en la raíz del proyecto (Protegidos por .gitignore).
3. Ejecutar con: `python3 main.py`.

## 🖥️ Interfaz y Experiencia
- **Splash Screen**: Arte ASCII (66px) con carga perezosa de librerías.
- **Alertas Dinámicas**: El menú principal indica en tiempo real si existe stock crítico mediante el tag `[⚠️ REVISAR!]`.

## 📊 Estructura de Datos

Para que el modo **ONLINE** se active, los CSV locales deben seguir este esquema:

### Maestro (`data_s.csv`)
| PRODUCTO | Seccion | SKU | COSTO (SIN IVA) | PRECIO VENTA FINAL (CON IVA) | MARGEN REAL (%) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Nombre descriptivo | Categoria | V-XXX-000 | Valor neto unitario | Precio final | Margen operativo |

### Inventario (`data_v.csv`)
| SKU | Funcion | Inventario actual | Aporte Hogar | Subtotal |
| :--- | :--- | :--- | :--- | :--- |
| ID Unico | Alias producto | Stock comprado | Cantidad casa | Stock real disponible |

## 🛡️ Seguridad y Privacidad
Este repositorio utiliza un archivo `.gitignore` estricto. **Nunca** se deben subir archivos `.csv`, `.xlsx` o `.log` ya que contienen el modelo de negocios y costos confidenciales.

## 🛠️ Roadmap Enero 2026
- [x] Splash Screen v2 (66px).
- [x] Sistema de Kardex/Auditoría (`vts_movimientos.log`).
- [x] Calculadora de Combos/Packs con sugerencia de descuento.
- [x] Alertas de stock proactivas en menú principal.
- [ ] Migración de arquitectura CSV a **SQLite**.
- [ ] Módulo de Gráficos (Matplotlib) para visualización de capital.