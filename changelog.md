# 📜 Registro de Cambios (Changelog)
# 🔒 Martillo Vil - Parche de Seguridad (Filtración .env en GitHub) Estado: Cerrado 🟢

### 📋 Qué pasó
- El `.env` completo quedó comiteado en el historial de `terminal-vts` (commit del 17-may-2026) — repo **público** en GitHub. `SECRET_KEY`, token de Telegram (lannu-bot), credenciales B2 (Backblaze) y `SARGERITE_EXPECTED_HASH` quedaron expuestos. El `.gitignore` agregado después nunca limpió el historial ya empujado — los 3 secretos seguían vigentes 3 meses después.
- Agravante: ERPVS compartía bucket y key de Backblaze B2 con VTS — la key filtrada daba acceso a los backups de ambos sistemas.

### 🔧 Remediación
- `SECRET_KEY` rotada (recarga en caliente, sin downtime).
- Historial de `terminal-vts` reescrito con `git filter-repo` (purga del `.env` de los 9 commits) + force-push a Gitea y GitHub.
- Token de Telegram y B2 App Key revocados y regenerados.
- **B2 separado entre VTS y ERPVS** — cada uno con bucket y key propios, verificado con autenticación real.
- `.env` de todos los proyectos en el servidor: permisos cerrados a solo el dueño (antes eran legibles por cualquier usuario del sistema).
- De paso: Dozzle (visor de logs sin auth, expuesto a toda la LAN) restringido a localhost; n8n/Postiz/bapho-chan purgados por estar sin configurar y sin uso real.

### 🚀 Despliegue
- **Fecha**: 2026-08-25
- **Ambiente**: Producción (Thunderbluff)

### 📋 Cambios Principales
- **Chasis UI**: Implementación de Sidebar expandible inteligente y diseño minimalista v2.6.
- **Motor de Estabilidad**: Migración a Django 6 (Beta 1) con optimización de consultas `annotate` en SQLite.
- **La Forja Pro**: 
  - Buscador optimizado para scanners (evento `input`).
  - Termómetro visual de stock sin ruido de texto.
  - Sistema de "Suma Rápida" para ingreso de mercadería PM.
- **API Aporte Hogar**: Endpoint dedicado para retiros manuales con trazabilidad doble (Deducibles + Historial General).

### 📊 Métricas Actuales Monitoreadas (Cierre Refactorización)
- **Capital Real Auditado**
- **Ratio (ROI Proyectado)**
- **SKU Activos Totales**
- **Estado de Auditoría**

### 🚀 Despliegue
- **Rama**: `v2.6-modulo6-dj6`
- **Ambiente**: Local / Desplegando a produccion un viernes...

### 🧜‍♂️ Mapa Visual del Sistema (Actualizado)
```mermaid
graph TD
    User((Comandante VTS)) -->|Ingreso SKU| Admin[Admin Django]
    Admin -->|Update| DB[(SQLite: AuditoriaVTS)]
    
    User -->|Suma Rápida| Forja[La Forja: JS Engine]
    Forja -->|API Fetch| Views[views.actualizar_inventario]
    
    User -->|Retiro| AH[Aporte Hogar: Modal]
    AH -->|API Fetch| AH_View[views.registrar_aporte_hogar]
    
    AH_View -->|Create| LogAH[LogRetirosDeducibles]
    AH_View -->|Create| Hist[HistorialStock]
    
    DB -->|Crunching| Fel[FelEngine]
    Fel -->|Output| Dashboard[Panel de Control: Charts]
    Fel -->|Output| Analysis[Análisis Pro: ROI/Ratio]
```


_________________________________________________________________________________________
# 📜 Registro de Cambios (Changelog)
Estado: Estable 🟢 | Rama: v2.5

## 📸 Módulo 5: Identidad Visual y Remota (NUEVO)
+ Motor de Imágenes WebP: Integración de Pillow con algoritmo LANCZOS en el modelo para conversión automática de JPG/PNG a WebP (800px max).

+ Infraestructura Mardum: Migración exitosa a servidor remoto de pruebas con acceso Remote SSH y gestión de permisos de media/.

+ Sidebar Inteligente: Implementación de Sidebar comprimido definitivo con efecto hover para optimizar espacio en tablet.

+ Radar de Quiebres: Nuevo widget en Dashboard que desglosa automáticamente productos con stock cero, estilizando la estética de "La Forja".

+ Limpieza de Interfaz: Eliminación de columnas innecesarias en la Forja para favorecer la lectura de SKU y Barcode.

## 📈 Motor de Inteligencia Financiera
+ Lógica de IVA: Implementación del "Tercer Operador" en la propiedad margen_valor. Ahora descuenta el 19% automáticamente para mostrar rentabilidad neta real.

+ Gauges de Estado: Sincronización de colores y estados (PÉRDIDA, ILLIDARI) basados en márgenes netos sinceros.

## 🎨 Interfaz de Usuario (UI/UX)
+ Buscador jQuery Ninja: Filtro instantáneo en tiempo real por SKU, Producto o Barcode.

+ Dashboard Maestro: Reestructuración de tarjetas; Capital Total ahora domina el ancho completo (100%) para jerarquía visual.

## 🧜‍♂️ Mapa Visual del Sistema (Actualizado)
```mermaid
graph TD
    A[Cámara/Galería Tablet] -->|Upload Multipart| B(Django View request.FILES)
    B --> C{Procesamiento Pillow}
    C -->|LANCZOS Resize| D[WebP Storage]
    D --> E[Dashboard / Forja]
    
    subgraph Mardum Server
    B
    C
    D
    end
    
    F[SSH Remote Orgrimmar] -.->|Edit Code| B
```
__________________________________________________________________________________________
# 📜 Registro de Cambios (Changelog) 
Estado: Estable 🟢 | Rama: v2.3-hybrid-bridge

## 🔧 Infraestructura y Base de Datos
+ Reinicio de Forja: Se eliminó la base de datos db.sqlite3 y las migraciones antiguas para corregir errores de tipo (IntegrityError).

+ Modelo AuditoriaVTS: Se añadió soporte para variante (Tallas/Colores) y codigo_barras (Barcode).

+ Clave Primaria: El sku se estableció como PK, eliminando la dependencia del id automático de Django.

## 📈 Motor de Inteligencia Financiera
+ Lógica de IVA: Implementación del "Tercer Operador" en la propiedad margen_valor. Ahora descuenta el 19% automáticamente para mostrar rentabilidad neta real.

+ Gauges de Estado: Sincronización de colores y estados (PÉRDIDA, SOBREVIVENCIA, ILLIDARI) basados en márgenes netos sinceros.

## 🎨 Interfaz de Usuario (UI/UX)
+ Buscador jQuery Ninja: Filtro instantáneo en tiempo real por SKU, Producto o Barcode sin recargar la página.

+ Corrección de Modales: Ajuste de etiquetas HTML (data-bs-toggle) para que el Modal Maestro flote correctamente en el centro.

+ Glosas Transparentes: Los campos ahora indican explícitamente COSTO NETO y VENTA BRUTO para evitar errores de ingreso.

+ Alertas Dashboard: Sustitución del panel de "Progreso" por un contador de Margen Crítico (Pérdidas) y Quiebres.

# 🧜‍♂️ Mapa Visual del Sistema

```mermaid
graph LR
    A[Escáner Barcode] --> B[jQuery Filter]
    B --> C[Tabla Forja]
    C --> D{Análisis VTS}
    D -->|Venta Bruta| E[Cálculo IVA]
    E --> F[Dashboard Alertas]
```