import re

filepath = 'ui/main_window.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Add Checkbutton for merging PDF
old_png_cb = 'tk.Checkbutton(opts_frame, text="Xuất ảnh mặt bằng (PNG)", variable=self.var_export_png).pack(side=tk.LEFT, padx=10)'
new_png_cb = old_png_cb + '''
        self.var_merge_pdf = tk.BooleanVar(value=False)
        tk.Checkbutton(opts_frame, text="Gộp các báo cáo thành 1 file PDF tổng hợp", variable=self.var_merge_pdf).pack(side=tk.LEFT, padx=10)'''
content = content.replace(old_png_cb, new_png_cb)

# Add logic to merge PDF
old_run_loop = 'for i, f in enumerate(self.batch_files):'
new_run_loop = 'generated_pdfs = []\n            for i, f in enumerate(self.batch_files):'
content = content.replace(old_run_loop, new_run_loop)

old_export_pdf = 'export_pdf(rec, loads, params, out_dir, prefix, png_path)'
new_export_pdf = '''pdf_path = export_pdf(rec, loads, params, out_dir, prefix, png_path)
                            generated_pdfs.append(pdf_path)'''
content = content.replace(old_export_pdf, new_export_pdf)

old_finish = 'self.log_batch("=== HOÀN THÀNH ===")'
new_finish = '''
            if self.var_merge_pdf.get() and generated_pdfs:
                try:
                    self.log_batch("Đang gộp file PDF...")
                    from PyPDF2 import PdfMerger
                    merger = PdfMerger()
                    for pdf in generated_pdfs:
                        merger.append(pdf)
                    merged_path = os.path.join(out_dir, "TONG_HOP_REPORT.pdf")
                    merger.write(merged_path)
                    merger.close()
                    self.log_batch(f"Đã gộp thành công: TONG_HOP_REPORT.pdf")
                except Exception as e:
                    self.log_batch(f"Lỗi khi gộp PDF: {str(e)}")
                    
            self.log_batch("=== HOÀN THÀNH ===")'''
content = content.replace(old_finish, new_finish)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("PDF Merge patch applied.")
