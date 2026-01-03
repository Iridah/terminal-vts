# VTS - Vacadari Terminal System v1.5

Sistema de gestión de inventario basado en terminal (Estilo AS/400) para control de stock, valorización y aporte al hogar.

## 🚀 Inicio Rápido 2026
1. Asegurarse de tener `pandas` instalado: `pip install pandas`.
2. Mantener los archivos `data_s.csv` y `data_v.csv` en la raíz del proyecto.
3. Ejecutar con: `python main.py`.

## 📊 Estructura de Datos (Crucial para el funcionamiento)

Para que el modo **ONLINE** se active, los CSV locales deben seguir este esquema:

### Maestro (`data_s.csv`)
| PRODUCTO | Seccion | SKU | COSTO (SIN IVA) | PRECIO VENTA FINAL (CON IVA) |
| :--- | :--- | :--- | :--- | :--- |
| Nombre descriptivo | Categoria | V-XXX-000 | Valor neto unitario | Precio cobrado al cliente |

### Inventario (`data_v.csv`)
| SKU | Funcion | Inventario actual | Aporte Hogar | Subtotal |
| :--- | :--- | :--- | :--- | :--- |
| ID Unico | Alias producto | Stock comprado | Cantidad para casa | Stock real (Actual - Hogar) |

## 🛡️ Seguridad y Privacidad
Este repositorio utiliza un archivo `.gitignore` estricto. **Nunca** se deben subir los archivos `.csv` o `.xlsx` ya que contienen información sensible sobre costos unitarios y márgenes de ganancia.

## 🛠️ Roadmap Enero 2026
- [x] Persistencia de datos local (Aporte Hogar).
- [x] Búsqueda rápida con cruce de precios.
- [ ] Implementar módulo de Valorización de Activos (Costo Neto Total).
- [ ] Sincronización bidireccional con Google Sheets API.