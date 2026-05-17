# dashboard/management/commands/generar_inventario_pdf.py
# Comando: python manage.py generar_inventario_pdf
# Genera PDF de inventario físico en formato horizontal
 
import os
import django
from datetime import datetime
from pathlib import Path
 
from django.core.management.base import BaseCommand
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
 
 
class Command(BaseCommand):
    help = 'Genera PDF de inventario físico para conteo manual'
 
    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            default=None,
            help='Ruta de salida del PDF (default: backups/inventario_FECHA.pdf)'
        )
        parser.add_argument(
            '--seccion',
            default=None,
            help='Filtrar por sección (opcional)'
        )
 
    def handle(self, *args, **options):
        from dashboard.models import AuditoriaVTS, VarianteVTS
 
        # ── Ruta de salida ────────────────────────────────────────
        BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
 
        if options['output']:
            ruta_pdf = Path(options['output'])
        else:
            ruta_pdf = BASE_DIR / 'backups' / f'inventario_{timestamp}.pdf'
 
        # ── Recolectar datos ──────────────────────────────────────
        qs = AuditoriaVTS.objects.filter(estado='activo').order_by('seccion', 'producto')
        if options['seccion']:
            qs = qs.filter(seccion=options['seccion'])
 
        # Construir filas: productos + sus variantes
        filas_data = []
        correlativo = 1
 
        for prod in qs:
            variantes = prod.variantes.filter(estado='activo').order_by('nombre_variante')
 
            if variantes.exists():
                # Producto con variantes
                for var in variantes:
                    valor = float(var.precio_costo) * var.inventario_real
                    filas_data.append({
                        'n':        correlativo,
                        'sku':      var.sku_variante,
                        'nombre':   prod.producto,
                        'variante': var.nombre_variante,
                        'stock':    var.inventario_real,
                        'valor':    valor,
                        'seccion':  prod.seccion,
                    })
                    correlativo += 1
            else:
                # Producto simple
                valor = float(prod.precio_costo) * prod.inventario_real
                filas_data.append({
                    'n':        correlativo,
                    'sku':      prod.sku,
                    'nombre':   prod.producto,
                    'variante': prod.variante or '—',
                    'stock':    prod.inventario_real,
                    'valor':    valor,
                    'seccion':  prod.seccion,
                })
                correlativo += 1
 
        # ── Construir PDF ─────────────────────────────────────────
        doc = SimpleDocTemplate(
            str(ruta_pdf),
            pagesize=landscape(A4),
            leftMargin=1.5*cm, rightMargin=1.5*cm,
            topMargin=2*cm,    bottomMargin=2*cm,
        )
 
        styles = getSampleStyleSheet()
        story  = []
 
        # Estilo encabezado
        estilo_titulo = ParagraphStyle(
            'titulo',
            parent=styles['Normal'],
            fontSize=14, fontName='Helvetica-Bold',
            alignment=TA_LEFT, spaceAfter=4,
        )
        estilo_sub = ParagraphStyle(
            'sub',
            parent=styles['Normal'],
            fontSize=9, fontName='Helvetica',
            alignment=TA_LEFT, spaceAfter=12, textColor=colors.grey,
        )
        estilo_seccion = ParagraphStyle(
            'seccion',
            parent=styles['Normal'],
            fontSize=10, fontName='Helvetica-Bold',
            alignment=TA_LEFT, spaceAfter=4, spaceBefore=8,
            textColor=colors.HexColor('#4B49AC'),
        )
 
        # Encabezado del documento
        story.append(Paragraph("INVERSIONES VACADARI SpA — INVENTARIO FÍSICO", estilo_titulo))
        story.append(Paragraph(
            f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}  |  "
            f"Total ítems activos: {len(filas_data)}",
            estilo_sub
        ))
 
        # Agrupar por sección
        secciones = {}
        for fila in filas_data:
            sec = fila['seccion']
            secciones.setdefault(sec, []).append(fila)
 
        # Anchos de columna (landscape A4 = ~27.7cm útil)
        col_widths = [
            1.0*cm,   # N°
            3.8*cm,   # SKU
            7.5*cm,   # Nombre
            3.5*cm,   # Variante
            2.0*cm,   # Stock VTS
            3.0*cm,   # Valor ($)
            4.5*cm,   # Conteo manual (espacio en blanco)
        ]
 
        header_row = [
            Paragraph('<b>N°</b>',          ParagraphStyle('h', fontSize=8, fontName='Helvetica-Bold', alignment=TA_CENTER)),
            Paragraph('<b>SKU</b>',         ParagraphStyle('h', fontSize=8, fontName='Helvetica-Bold', alignment=TA_LEFT)),
            Paragraph('<b>Producto</b>',    ParagraphStyle('h', fontSize=8, fontName='Helvetica-Bold', alignment=TA_LEFT)),
            Paragraph('<b>Variante</b>',    ParagraphStyle('h', fontSize=8, fontName='Helvetica-Bold', alignment=TA_LEFT)),
            Paragraph('<b>Stock VTS</b>',   ParagraphStyle('h', fontSize=8, fontName='Helvetica-Bold', alignment=TA_CENTER)),
            Paragraph('<b>Valor ($)</b>',   ParagraphStyle('h', fontSize=8, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
            Paragraph('<b>Conteo manual</b>', ParagraphStyle('h', fontSize=8, fontName='Helvetica-Bold', alignment=TA_CENTER)),
        ]
 
        estilo_celda     = ParagraphStyle('c',  fontSize=7.5, fontName='Helvetica',      alignment=TA_LEFT)
        estilo_num       = ParagraphStyle('cn', fontSize=7.5, fontName='Helvetica',      alignment=TA_CENTER)
        estilo_num_right = ParagraphStyle('cr', fontSize=7.5, fontName='Helvetica',      alignment=TA_RIGHT)
 
        table_style_base = TableStyle([
            # Encabezado
            ('BACKGROUND',   (0,0), (-1,0), colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR',    (0,0), (-1,0), colors.white),
            ('FONTNAME',     (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',     (0,0), (-1,0), 8),
            ('ALIGN',        (0,0), (-1,0), 'CENTER'),
            ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('GRID',         (0,0), (-1,-1), 0.3, colors.HexColor('#cccccc')),
            ('LINEBELOW',    (0,0), (-1,0),  0.8, colors.HexColor('#4B49AC')),
            ('TOPPADDING',   (0,0), (-1,-1), 3),
            ('BOTTOMPADDING',(0,0), (-1,-1), 3),
            ('LEFTPADDING',  (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
            # Columna conteo manual — borde más marcado
            ('BOX',          (6,1), (6,-1), 1.0, colors.HexColor('#888888')),
        ])
 
        total_valor = 0.0
 
        for seccion, filas in sorted(secciones.items()):
            story.append(Paragraph(f"▸ {seccion.upper()}", estilo_seccion))
 
            tabla_filas = [header_row]
            subtotal = 0.0
 
            for f in filas:
                subtotal    += f['valor']
                total_valor += f['valor']
                tabla_filas.append([
                    Paragraph(str(f['n']),                          estilo_num),
                    Paragraph(f['sku'],                             estilo_celda),
                    Paragraph(f['nombre'][:50],                     estilo_celda),
                    Paragraph(f['variante'][:30],                   estilo_celda),
                    Paragraph(str(f['stock']),                      estilo_num),
                    Paragraph(f"${f['valor']:,.0f}",                estilo_num_right),
                    Paragraph('',                                   estilo_celda),  # espacio en blanco
                ])
 
            # Fila subtotal sección
            tabla_filas.append([
                Paragraph('', estilo_celda),
                Paragraph('', estilo_celda),
                Paragraph(f'<b>Subtotal {seccion}</b>', ParagraphStyle('st', fontSize=7.5, fontName='Helvetica-Bold', alignment=TA_LEFT)),
                Paragraph('', estilo_celda),
                Paragraph('', estilo_celda),
                Paragraph(f'<b>${subtotal:,.0f}</b>', ParagraphStyle('st', fontSize=7.5, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
                Paragraph('', estilo_celda),
            ])
 
            t = Table(tabla_filas, colWidths=col_widths, repeatRows=1)
            t.setStyle(table_style_base)
            # Fila subtotal con fondo diferente
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, len(tabla_filas)-1), (-1, len(tabla_filas)-1), colors.HexColor('#e8e8f0')),
                ('LINEABOVE',  (0, len(tabla_filas)-1), (-1, len(tabla_filas)-1), 0.8, colors.HexColor('#4B49AC')),
            ]))
 
            story.append(t)
            story.append(Spacer(1, 0.3*cm))
 
        # ── Total general ─────────────────────────────────────────
        story.append(Spacer(1, 0.5*cm))
        total_tabla = Table([[
            Paragraph('VALORIZACIÓN TOTAL INVENTARIO:', ParagraphStyle('tot', fontSize=11, fontName='Helvetica-Bold', alignment=TA_LEFT)),
            Paragraph(f'${total_valor:,.0f}', ParagraphStyle('tot', fontSize=11, fontName='Helvetica-Bold', alignment=TA_RIGHT, textColor=colors.HexColor('#4B49AC'))),
        ]], colWidths=[20*cm, 7*cm])
        total_tabla.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR',     (0,0), (-1,-1), colors.white),
            ('TOPPADDING',    (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING',   (0,0), (-1,-1), 8),
            ('RIGHTPADDING',  (0,0), (-1,-1), 8),
        ]))
        story.append(total_tabla)
 
        # ── Pie de página con número de página ───────────────────
        def pie_pagina(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica', 7)
            canvas.setFillColor(colors.grey)
            canvas.drawString(
                1.5*cm,
                1.2*cm,
                f"VTS — Inventario Físico  |  {datetime.now().strftime('%d/%m/%Y')}  |  Página {doc.page}"
            )
            canvas.restoreState()
 
        doc.build(story, onFirstPage=pie_pagina, onLaterPages=pie_pagina)
 
        self.stdout.write(self.style.SUCCESS(
            f"✓ PDF generado: {ruta_pdf} ({ruta_pdf.stat().st_size // 1024} KB)"
        ))
        return str(ruta_pdf)