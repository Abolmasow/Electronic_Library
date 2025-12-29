import json
import csv
import io
from datetime import datetime
from django.http import HttpResponse
from django.db.models import Count, Avg
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import openpyxl
from openpyxl.styles import Font, Alignment
from docx import Document
from docx.shared import Inches

class DataExporter:
    @staticmethod
    def export_to_json(queryset, fields):
        data = list(queryset.values(*fields))
        response = HttpResponse(
            json.dumps(data, ensure_ascii=False, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="export.json"'
        return response
    
    @staticmethod
    def export_to_csv(queryset, fields, field_names):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(field_names)
        
        for item in queryset:
            row = [getattr(item, field) for field in fields]
            writer.writerow(row)
        
        return response
    
    @staticmethod
    def export_to_pdf(queryset, title, columns):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{title}.pdf"'
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        styles = getSampleStyleSheet()
        elements.append(Paragraph(title, styles['Title']))
        elements.append(Paragraph(f"Дата формирования: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                                 styles['Normal']))
        
        data = [columns]
        for item in queryset:
            row = []
            for column in columns:
                row.append(str(getattr(item, column.lower().replace(' ', '_'), '')))
            data.append(row)
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        
        return response
    
    @staticmethod
    def export_to_docx(queryset, title, columns):
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = f'attachment; filename="{title}.docx"'
        
        doc = Document()
        doc.add_heading(title, 0)
        doc.add_paragraph(f"Дата формирования: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        table = doc.add_table(rows=1, cols=len(columns))
        table.style = 'Table Grid'
        
        header_cells = table.rows[0].cells
        for i, column in enumerate(columns):
            header_cells[i].text = column
        
        for item in queryset:
            row_cells = table.add_row().cells
            for i, column in enumerate(columns):
                row_cells[i].text = str(getattr(item, column.lower().replace(' ', '_'), ''))
        
        doc.save(response)
        return response
    
    @staticmethod
    def export_to_xlsx(queryset, title, columns):
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{title}.xlsx"'
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = title[:31]  # Ограничение длины названия листа
        
        # Заголовок
        ws['A1'] = title
        ws['A1'].font = Font(size=16, bold=True)
        ws.merge_cells('A1:E1')
        
        # Дата формирования
        ws['A2'] = f"Дата формирования: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Заголовки столбцов
        for col_num, column in enumerate(columns, 1):
            cell = ws.cell(row=4, column=col_num)
            cell.value = column
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        # Данные
        for row_num, item in enumerate(queryset, 5):
            for col_num, column in enumerate(columns, 1):
                cell = ws.cell(row=row_num, column=col_num)
                cell.value = getattr(item, column.lower().replace(' ', '_'), '')
        
        # Автоматическая ширина столбцов
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        wb.save(response)
        return response