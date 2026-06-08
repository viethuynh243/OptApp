import os
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# Function to get pile forces for reporting
def calculate_pile_forces(coords, loads):
    n_piles = len(coords)
    if n_piles == 0: return {}
    
    cg_x, cg_y = np.mean(coords, axis=0)
    I_x = sum((y - cg_y)**2 for x,y in coords)
    I_y = sum((x - cg_x)**2 for x,y in coords)
    I_x = I_x if I_x > 0 else 1e-9
    I_y = I_y if I_y > 0 else 1e-9
    
    forces_by_load = {}
    for i, load in enumerate(loads):
        N, Mx, My = load.get('N', 0), load.get('Mx', 0), load.get('My', 0)
        piles_p = []
        for x, y in coords:
            dx, dy = x - cg_x, y - cg_y
            p = N / n_piles + Mx * dy / I_x + My * dx / I_y
            piles_p.append(p)
        forces_by_load[i] = piles_p
    return forces_by_load

def export_png(plot_canvas_instance, coords, params, out_dir, prefix):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    out_path = os.path.join(out_dir, f"{prefix}_plan.png")
    
    # We use the existing plot_canvas instance but save it
    # Note: plot_canvas_instance should already have the plot drawn!
    plot_canvas_instance.draw_simulation(coords, params)
    plot_canvas_instance.fig.savefig(out_path, dpi=300, bbox_inches='tight')
    return out_path

def export_excel(config, loads, params, out_dir, prefix):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    out_path = os.path.join(out_dir, f"{prefix}_result.xlsx")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ket Qua"
    
    # Styles
    bold_font = Font(bold=True)
    header_fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center")
    
    # Title
    ws.merge_cells('A1:G1')
    ws['A1'] = f"BAO CAO TOI UU HOA - {prefix}"
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = center_align
    
    # Parameters
    ws['A3'] = "Thong so dau vao:"
    ws['A3'].font = bold_font
    ws.append(['Lx (m)', params.get('L_X', 0), 'Ly (m)', params.get('L_Y', 0)])
    ws.append(['d (m)', params.get('D_PILE', 0), 'SAFE_D (m)', params.get('SAFE_D', 0)])
    ws.append(['P cho phep (kN)', params.get('P_LIMIT', 0), 'P nho (kN)', params.get('P_TENSION', 0)])
    
    ws.append([])
    ws['A8'] = "Phuong an kien nghi:"
    ws['A8'].font = bold_font
    ws.append(['Kieu', config.get('type', 'Unknown')])
    ws.append(['So luong coc', config.get('n', 0)])
    ws.append(['Pmax (kN)', round(config.get('pmax', 0), 2)])
    ws.append(['Pmin (kN)', round(config.get('pmin', 0), 2)])
    ws.append(['Trang thai', 'DAT' if config.get('ok') else 'KHONG DAT'])
    ws.append(['Ly do', config.get('msg', '')])
    
    # Forces Table
    ws.append([])
    row = ws.max_row + 1
    ws.merge_cells(f'A{row}:G{row}')
    ws[f'A{row}'] = "BANG KIEM TRA NOI LUC COC"
    ws[f'A{row}'].font = bold_font
    ws[f'A{row}'].alignment = center_align
    
    headers = ["Load Case", "N (kN)", "Mx (kNm)", "My (kNm)", "Pmax (kN)", "Pmin (kN)", "Trang thai"]
    ws.append(headers)
    for cell in ws[ws.max_row]:
        cell.font = bold_font
        cell.fill = header_fill
        cell.alignment = center_align
        
    forces_by_load = calculate_pile_forces(config['coords'], loads)
    for i, load in enumerate(loads):
        piles_p = forces_by_load.get(i, [])
        pmax = max(piles_p) if piles_p else 0
        pmin = min(piles_p) if piles_p else 0
        status = "DAT" if (pmax <= params.get('P_LIMIT', 900) and pmin >= -params.get('P_TENSION', 200)) else "FAIL"
        ws.append([i+1, load.get('N',0), load.get('Mx',0), load.get('My',0), round(pmax,2), round(pmin,2), status])
        
    # Coords Table
    ws.append([])
    row = ws.max_row + 1
    ws.merge_cells(f'A{row}:C{row}')
    ws[f'A{row}'] = "TOA DO COC"
    ws[f'A{row}'].font = bold_font
    ws[f'A{row}'].alignment = center_align
    
    ws.append(["Coc", "X (m)", "Y (m)"])
    for cell in ws[ws.max_row]: cell.font = bold_font
    
    for i, (x, y) in enumerate(config['coords']):
        ws.append([i+1, round(x,3), round(y,3)])
        
    wb.save(out_path)
    return out_path

def export_pdf(config, loads, params, out_dir, prefix, png_path=None):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    out_path = os.path.join(out_dir, f"{prefix}_report.pdf")
    c = pdf_canvas.Canvas(out_path, pagesize=A4)
    width, height = A4
    
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2.0, height - 50, f"BAO CAO TOI UU HOA - {prefix}")
    
    c.setFont("Helvetica", 12)
    y = height - 80
    
    c.drawString(50, y, "1. Thong so dau vao:"); y -= 20
    c.drawString(70, y, f"Kich thuoc be: {params.get('L_X')} x {params.get('L_Y')} m"); y -= 15
    c.drawString(70, y, f"Duong kinh coc: {params.get('D_PILE')} m"); y -= 15
    c.drawString(70, y, f"Suc chiu tai cho phep: Po = {params.get('P_LIMIT')} T, Ct = {params.get('P_TENSION')} T"); y -= 15
    if params.get('M_LIMIT', 0) > 0:
        c.drawString(70, y, f"Suc uon cho phep: Mmax = {params.get('M_LIMIT')} kNm"); y -= 15
    else:
        y -= 15
    
    c.drawString(50, y, "2. Phuong an kien nghi:"); y -= 20
    c.drawString(70, y, f"So luong coc: {config.get('n', 0)} coc"); y -= 15
    config_type = config.get('type', '')
    if config_type == 'Gốc': config_type = 'Goc'
    c.drawString(70, y, f"Kieu bo tri: {config_type}"); y -= 15
    c.drawString(70, y, f"Pmax = {config.get('pmax', 0):.2f} T"); y -= 15
    c.drawString(70, y, f"Pmin = {config.get('pmin', 0):.2f} T"); y -= 15
    if params.get('M_LIMIT', 0) > 0:
        c.drawString(70, y, f"Mmax = {max(config.get('mxmax', 0), config.get('mymax', 0)):.2f} kNm"); y -= 15
    c.drawString(70, y, f"Trang thai: {'DAT' if config.get('ok') else 'KHONG DAT'}"); y -= 15
    c.drawString(70, y, f"Ly do: {config.get('msg', '')}"); y -= 30
    
    if png_path and os.path.exists(png_path):
        c.drawString(50, y, "3. Hinh anh mat bang:"); y -= 10
        # Draw image, scale to fit width
        img_w = 400
        img_h = 300
        c.drawImage(png_path, (width - img_w)/2.0, y - img_h, width=img_w, height=img_h)
        y -= (img_h + 30)
        
    c.showPage()
    c.save()
    return out_path
