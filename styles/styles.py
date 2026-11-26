ACCENT = "#2563eb"

# one stylesheet for the whole app
APP_STYLE = f"""
QWidget {{ background: #f6f7f9; color: #1f2937; font-size: 14px; }}
QLabel#title {{ font-size: 22px; font-weight: 600; }}
QPushButton {{ background: white; border: 1px solid #d1d5db; border-radius: 6px; padding: 7px 14px; }}
QPushButton:hover {{ border-color: {ACCENT}; }}
QPushButton#primary {{ background: {ACCENT}; border-color: {ACCENT}; color: white; }}
QPushButton#row {{ padding: 4px 10px; font-size: 13px; }}
QLineEdit {{ background: white; border: 1px solid #d1d5db; border-radius: 6px; padding: 6px; }}
QLineEdit:focus {{ border-color: {ACCENT}; }}
QTableWidget {{ background: white; border: 1px solid #e5e7eb; border-radius: 8px; }}
QTableWidget::item {{ padding: 6px; border-bottom: 1px solid #f0f1f3; }}
QTableWidget::item:selected {{ background: #dbeafe; color: #1f2937; }}
QHeaderView::section {{ background: white; border: none; border-bottom: 1px solid #e5e7eb; padding: 8px; font-weight: 600; }}
"""
