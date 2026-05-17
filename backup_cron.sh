#!/bin/bash
cd /home/asilvaq/Programacion/VTS
source venv/bin/activate
python manage.py shell -c "from dashboard.xaequus import ejecutar_respaldo_completo; ejecutar_respaldo_completo()"
