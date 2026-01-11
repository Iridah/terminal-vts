# VTS - Vacadari Terminal System v2.5.0 (Edición Martillo Vil) 🐮🔨
Sistema de gestión de inventario táctico. Evolucionado de un orquestador CLI a una Arquitectura de Contenedores con Dashboard Web Interactivo.

## 🚀 Despliegue Docker (Enero 2026)
Infraestructura: docker-compose up -d (Levanta el entorno Django + DB).

Succión de Datos: docker exec -it vts_martillo_vil python PORTAL/manage.py importar_csv (Procesamiento blindado de reportes VTS).

Acceso Web: http://localhost:9000

## 🏗️ Arquitectura Evolucionada: Portal Web Django
El sistema ahora opera como un servicio persistente dentro de Docker:

vts_martillo_vil (Container): Entorno aislado en Python 3.12.

dashboard/ (App Django): Cerebro del sistema. Gestiona la lógica de auditoría y visualización.

importar_csv.py (Rimuru): Comando de gestión que neutraliza "Minas N2" (valores nulos y filas corruptas).

Chart.js: Motor de renderizado para analítica de capital en tiempo real.

## 📊 Ciclo de Vida del Inventario (Alimentación Dual)
El sistema integra la carga masiva por script y el ajuste quirúrgico vía web:

```mermaid
graph TD
    subgraph "Nivel 0: Entrada de Datos"
        A[CSV Auditoría VTS] --> B(Script: importar_csv.py)
        H[Auditor con Tablet/Web] --> I(GUI: actualizar_inventario)
    end

    subgraph "Nivel 1: El Cerebro (Django)"
        B -->|Succión Blindada| C{Rimuru: Filtro N2}
        I -->|POST Request| J{Ajuste Manual por SKU}
        C -->|Si SKU es V-| D[Base de Datos: PostgreSQL/SQLite]
        C -->|Si NaN| E[Asignar 0]
        C -->|Si Costo 0| F[Buscar Historial]
        J -->|Update SKU| D
    end

    subgraph "Nivel 2: Visualización"
        D --> G[Dashboard: Chart.js]
        G -->|Vista| K[Valor Costo Neto Inventario]
        G -->|Vista| L[Avance de Auditoría]
    end

    style C fill:#f39c12,stroke:#333,stroke-width:2px
    style J fill:#f39c12,stroke:#333,stroke-width:2px
    style D fill:#2c3e50,color:#fff
```

## 🛡️ Protocolo de Resguardo y Regularización
Costo Inteligente: Si un producto llega sin precio en el CSV, el sistema recupera el último costo histórico para no falsear el Valor Neto.

## 🛠️ Roadmap (Actualizado 11-01-2026)
[x] Migración a Docker y Arquitectura Web Django.

[x] Implementación de Dashboard con Chart.js (Visualización de Capital Neto).

[x] Script de succión blindada contra fallos de datos (Minas N2).

[ ] PRÓXIMO: Formulario de Ajuste Manual en la GUI (Regularización 11-01-26).

[ ] PRÓXIMO: Filtros dinámicos por Sección en el Dashboard.