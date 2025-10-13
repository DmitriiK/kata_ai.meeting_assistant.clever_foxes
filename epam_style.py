"""
EPAM-Inspired GUI Styles for Meeting Assistant
Professional, minimalist design with clean typography and modern UI elements
Based on EPAM Insights design principles
"""

# Color Palette - Exact EPAM Branding Colors
COLORS = {
    # Primary EPAM Colors (based on actual website)
    'epam_primary': '#00A3E0',         # EPAM signature blue/cyan
    'epam_dark': '#003366',            # EPAM dark blue
    'epam_black': '#0F0F0F',           # EPAM deep black
    'epam_gray': '#666666',            # EPAM medium gray
    
    # Background Colors - EPAM Style
    'bg_primary': '#FFFFFF',           # Pure white (EPAM uses lots of white space)
    'bg_secondary': '#F7F8FA',         # Very light gray (EPAM secondary bg)
    'bg_card': '#FFFFFF',              # Card background
    'bg_hover': '#F0F6FF',             # Subtle blue hover (EPAM style)
    'bg_section': '#FAFBFC',           # Section divider background
    
    # EPAM Accent Colors (sophisticated palette)
    'accent_primary': '#E6F7FF',       # Very light cyan/blue
    'accent_secondary': '#F0F6FF',     # Light blue tint  
    'accent_success': '#E8F5E9',       # Light green
    'accent_warning': '#FFF4E6',       # Light orange
    'accent_info': '#E3F2FD',          # Light blue
    'accent_neutral': '#F5F5F7',       # Light neutral gray
    
    # State Colors - EPAM Compatible
    'success': '#00B050',              # Professional green
    'warning': '#FF8C00',              # Professional orange  
    'error': '#DC3545',                # Professional red
    'info': '#00A3E0',                 # EPAM blue for info
    
    # Border Colors - Minimal EPAM Style
    'border_light': '#E8E8EA',         # Very subtle borders
    'border_medium': '#D1D1D6',        # Medium borders
    'border_focus': '#00A3E0',         # EPAM blue for focus
    'border_card': '#E0E0E3',          # Card borders
    
    # Text Colors - EPAM Typography
    'text_primary': '#0F0F0F',         # EPAM black for headers
    'text_secondary': '#666666',       # EPAM gray for body text
    'text_muted': '#999999',           # Muted text
    'text_white': '#FFFFFF',           # White text for dark backgrounds
    'text_link': '#00A3E0',            # EPAM blue for links
    'text_accent': '#003366',          # EPAM dark blue for emphasis
}

# Typography - Modern, Clean Fonts
FONTS = {
    'primary': 'Segoe UI, -apple-system, BlinkMacSystemFont, Roboto, "Helvetica Neue", Arial, sans-serif',
    'secondary': 'Segoe UI, system-ui, sans-serif',
    'mono': 'Consolas, Monaco, "Courier New", monospace'
}

# Main Window Stylesheet - EPAM Design
MAIN_WINDOW_STYLE = f"""
QMainWindow {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    font-family: {FONTS['primary']};
    font-size: 14px;
}}

QWidget {{
    background-color: transparent;
    color: {COLORS['text_primary']};
}}

/* Central widget with EPAM-style background */
QWidget#centralWidget {{
    background-color: {COLORS['bg_secondary']};
}}
"""

# Header Title Stylesheet - EPAM Typography
TITLE_STYLE = f"""
QLabel {{
    color: {COLORS['epam_black']};
    font-family: {FONTS['primary']};
    font-size: 28px;
    font-weight: 700;
    padding: 12px 0;
    margin: 0;
    letter-spacing: -0.5px;
    line-height: 1.2;
}}
"""

# Primary Button Stylesheet (Start/Stop) - EPAM Colors
PRIMARY_BUTTON_STYLE = f"""
QPushButton {{
    background-color: {COLORS['epam_primary']};
    color: {COLORS['text_white']};
    border: none;
    border-radius: 6px;
    padding: 14px 28px;
    font-family: {FONTS['primary']};
    font-size: 14px;
    font-weight: 600;
    min-height: 20px;
    letter-spacing: 0.25px;
}}

QPushButton:hover {{
    background-color: {COLORS['epam_dark']};
        /* box-shadow removed: not supported in Qt stylesheets */
}}

QPushButton:pressed {{
    background-color: {COLORS['epam_dark']};
        /* box-shadow removed: not supported in Qt stylesheets */
}}

QPushButton:disabled {{
    background-color: {COLORS['border_medium']};
    color: {COLORS['text_muted']};
        /* box-shadow removed: not supported in Qt stylesheets */
}}
"""

# Secondary Button Stylesheet - EPAM Style
SECONDARY_BUTTON_STYLE = f"""
QPushButton {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['epam_primary']};
    border: 1px solid {COLORS['epam_primary']};
    border-radius: 6px;
    padding: 12px 24px;
    font-family: {FONTS['primary']};
    font-size: 14px;
    font-weight: 500;
    min-height: 16px;
    letter-spacing: 0.25px;
}}

QPushButton:hover {{
    background-color: {COLORS['accent_primary']};
    border-color: {COLORS['epam_dark']};
    color: {COLORS['epam_dark']};
        /* box-shadow removed: not supported in Qt stylesheets */
}}

QPushButton:pressed {{
    background-color: {COLORS['accent_secondary']};
    border-color: {COLORS['epam_dark']};
}}

QPushButton:disabled {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_muted']};
    border-color: {COLORS['border_light']};
        /* box-shadow removed: not supported in Qt stylesheets */
}}
"""

# Action Button Stylesheet (smaller buttons) - EPAM Style
ACTION_BUTTON_STYLE = f"""
QPushButton {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 6px;
    padding: 10px 18px;
    font-family: {FONTS['primary']};
    font-size: 13px;
    font-weight: 500;
    min-height: 14px;
    letter-spacing: 0.2px;
}}

QPushButton:hover {{
    background-color: {COLORS['bg_hover']};
    border-color: {COLORS['epam_primary']};
    color: {COLORS['epam_primary']};
        /* box-shadow removed: not supported in Qt stylesheets */
}}

QPushButton:pressed {{
    background-color: {COLORS['accent_primary']};
    border-color: {COLORS['epam_primary']};
}}

QPushButton:disabled {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_muted']};
    border-color: {COLORS['border_light']};
        /* box-shadow removed: not supported in Qt stylesheets */
}}
"""

# GroupBox Stylesheet (Card-like sections) - EPAM Style
GROUPBOX_STYLE = f"""
QGroupBox {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border_card']};
    border-radius: 8px;
    padding-top: 20px;
    margin-top: 12px;
    font-family: {FONTS['primary']};
    font-size: 14px;
    font-weight: 600;
    color: {COLORS['text_primary']};
        /* box-shadow removed: not supported in Qt stylesheets */
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 12px;
    background-color: {COLORS['bg_card']};
    color: {COLORS['epam_black']};
    font-weight: 600;
    font-size: 15px;
    margin-left: 12px;
    letter-spacing: 0.3px;
}}
"""

# Text Edit Stylesheet with EPAM color coding
def get_textedit_style(accent_color):
    return f"""
QTextEdit {{
    background-color: {accent_color};
    border: 1px solid {COLORS['border_light']};
    border-radius: 6px;
    padding: 16px;
    font-family: {FONTS['primary']};
    font-size: 13px;
    line-height: 1.5;
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['epam_primary']};
    selection-color: {COLORS['text_white']};
        /* box-shadow removed: not supported in Qt stylesheets */
}}

QTextEdit:focus {{
    border-color: {COLORS['border_focus']};
    outline: none;
        /* box-shadow removed: not supported in Qt stylesheets */
}}

QScrollBar:vertical {{
    background-color: {COLORS['bg_secondary']};
    width: 6px;
    border-radius: 3px;
    margin: 2px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['border_medium']};
    border-radius: 3px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['epam_primary']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""

# ComboBox Stylesheet
COMBOBOX_STYLE = f"""
QComboBox {{
    background-color: {COLORS['bg_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 6px;
    padding: 8px 12px;
    font-family: {FONTS['primary']};
    font-size: 14px;
    color: {COLORS['text_primary']};
    min-height: 16px;
}}

QComboBox:hover {{
    border-color: {COLORS['epam_primary']};
}}

QComboBox:focus {{
    border-color: {COLORS['border_focus']};
    outline: none;
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 1px;
    border-left-color: {COLORS['border_light']};
    border-left-style: solid;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}}

QComboBox::down-arrow {{
    width: 12px;
    height: 12px;
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik02IDhMMCAwSDE4TDYgOFoiIGZpbGw9IiM0QTRBNEEiLz4KPC9zdmc+);
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 6px;
    padding: 4px;
    selection-background-color: {COLORS['accent_primary']};
    selection-color: {COLORS['epam_primary']};
}}
"""

# CheckBox Stylesheet
CHECKBOX_STYLE = f"""
QCheckBox {{
    font-family: {FONTS['primary']};
    font-size: 14px;
    font-weight: 500;
    color: {COLORS['text_primary']};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {COLORS['border_medium']};
    border-radius: 4px;
    background-color: {COLORS['bg_primary']};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS['epam_primary']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['epam_primary']};
    border-color: {COLORS['epam_primary']};
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xMSAxTDQgOEwxIDUiIHN0cm9rZT0iI0ZGRkZGRiIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
}}

QCheckBox::indicator:disabled {{
    background-color: {COLORS['bg_secondary']};
    border-color: {COLORS['border_light']};
}}
"""

# Tab Widget Stylesheet - EPAM Clean Design
TAB_WIDGET_STYLE = f"""
QTabWidget::pane {{
    border: 1px solid {COLORS['border_card']};
    border-radius: 8px;
    background-color: {COLORS['bg_card']};
    top: -1px;
        /* box-shadow removed: not supported in Qt stylesheets */
}}

QTabBar::tab {{
    background-color: transparent;
    border: none;
    border-bottom: 3px solid transparent;
    padding: 16px 28px;
    margin-right: 4px;
    font-family: {FONTS['primary']};
    font-size: 14px;
    font-weight: 500;
    color: {COLORS['text_secondary']};
    letter-spacing: 0.25px;
}}

QTabBar::tab:selected {{
    background-color: transparent;
    border-bottom-color: {COLORS['epam_primary']};
    color: {COLORS['epam_primary']};
    font-weight: 600;
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['epam_primary']};
    border-radius: 4px 4px 0 0;
}}
"""

# List Widget Stylesheet
LIST_WIDGET_STYLE = f"""
QListWidget {{
    background-color: {COLORS['bg_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 8px;
    padding: 4px;
    font-family: {FONTS['primary']};
    font-size: 13px;
    color: {COLORS['text_primary']};
    outline: none;
}}

QListWidget::item {{
    padding: 12px 16px;
    border-radius: 6px;
    margin: 2px 0;
    border: none;
}}

QListWidget::item:hover {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['epam_primary']};
}}

QListWidget::item:selected {{
    background-color: {COLORS['epam_primary']};
    color: {COLORS['text_white']};
    font-weight: 600;
}}
"""

# Line Edit Stylesheet
LINE_EDIT_STYLE = f"""
QLineEdit {{
    background-color: {COLORS['bg_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 6px;
    padding: 10px 12px;
    font-family: {FONTS['primary']};
    font-size: 14px;
    color: {COLORS['text_primary']};
}}

QLineEdit:hover {{
    border-color: {COLORS['epam_primary']};
}}

QLineEdit:focus {{
    border-color: {COLORS['border_focus']};
    outline: none;
}}

QLineEdit::placeholder {{
    color: {COLORS['text_muted']};
    font-style: italic;
}}
"""

# Date Edit Stylesheet
DATE_EDIT_STYLE = f"""
QDateEdit {{
    background-color: {COLORS['bg_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 6px;
    padding: 8px 12px;
    font-family: {FONTS['primary']};
    font-size: 14px;
    color: {COLORS['text_primary']};
    min-height: 16px;
}}

QDateEdit:hover {{
    border-color: {COLORS['epam_primary']};
}}

QDateEdit:focus {{
    border-color: {COLORS['border_focus']};
    outline: none;
}}

QDateEdit::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 1px;
    border-left-color: {COLORS['border_light']};
    border-left-style: solid;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}}
"""

# Status Labels
STATUS_LABEL_STYLE = f"""
QLabel {{
    font-family: {FONTS['primary']};
    font-size: 12px;
    color: {COLORS['text_muted']};
    padding: 4px 8px;
    border-radius: 4px;
    background-color: {COLORS['bg_secondary']};
}}
"""

# Timer Label - EPAM Style
TIMER_LABEL_STYLE = f"""
QLabel {{
    font-family: {FONTS['mono']};
    font-size: 18px;
    font-weight: 600;
    color: {COLORS['epam_primary']};
    padding: 12px 16px;
    background-color: {COLORS['accent_primary']};
    border-radius: 6px;
    border: 1px solid {COLORS['border_light']};
    letter-spacing: 1px;
    /* box-shadow removed: not supported in Qt stylesheets */
}}
"""

# Warning Label
WARNING_LABEL_STYLE = f"""
QLabel {{
    color: {COLORS['warning']};
    font-family: {FONTS['primary']};
    font-size: 14px;
    font-weight: 600;
    padding: 6px 10px;
    background-color: #FFF8E1;
    border-radius: 6px;
    border: 1px solid #FFE082;
}}
"""

# Splitter Stylesheet
SPLITTER_STYLE = f"""
QSplitter::handle {{
    background-color: {COLORS['border_light']};
    border-radius: 2px;
}}

QSplitter::handle:vertical {{
    height: 4px;
    margin: 2px 8px;
}}

QSplitter::handle:horizontal {{
    width: 4px;
    margin: 8px 2px;
}}

QSplitter::handle:hover {{
    background-color: {COLORS['epam_primary']};
}}
"""

# Special button for Live Mode - EPAM Style
LIVE_MODE_BUTTON_STYLE = f"""
QPushButton {{
    background-color: {COLORS['success']};
    color: {COLORS['text_white']};
    border: 1px solid {COLORS['success']};
    border-radius: 6px;
    padding: 14px 24px;
    font-family: {FONTS['primary']};
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}}

QPushButton:checked {{
    background-color: {COLORS['success']};
    border-color: #00A050;
        /* box-shadow removed: not supported in Qt stylesheets */
}}

QPushButton:hover {{
    background-color: #00A050;
    border-color: #00A050;
        /* box-shadow removed: not supported in Qt stylesheets */
}}

QPushButton:pressed {{
    background-color: #008040;
        /* box-shadow removed: not supported in Qt stylesheets */
}}
"""

def apply_modern_styles(widget):
    """Apply modern EPAM-inspired styles to the entire application"""
    # Apply the main window style
    widget.setStyleSheet(f"""
        {MAIN_WINDOW_STYLE}
        
        /* GroupBoxes (Cards) */
        QGroupBox {GROUPBOX_STYLE.replace('QGroupBox', '')}
        
        /* Tabs */
        {TAB_WIDGET_STYLE}
        
        /* Buttons */
        QPushButton[objectName="primary_button"] {PRIMARY_BUTTON_STYLE.replace('QPushButton', '')}
        QPushButton[objectName="secondary_button"] {SECONDARY_BUTTON_STYLE.replace('QPushButton', '')}
        QPushButton[objectName="action_button"] {ACTION_BUTTON_STYLE.replace('QPushButton', '')}
        QPushButton[objectName="live_mode_button"] {LIVE_MODE_BUTTON_STYLE.replace('QPushButton', '')}
        
        /* Form Elements */
        {COMBOBOX_STYLE}
        {CHECKBOX_STYLE}
        {LINE_EDIT_STYLE}
        {DATE_EDIT_STYLE}
        {LIST_WIDGET_STYLE}
        
        /* Splitter */
        {SPLITTER_STYLE}
    """)

# Style Helper Functions
def get_card_shadow():
    """Returns box-shadow style for cards"""
    return "QWidget { border: 1px solid #E0E0E0; border-radius: 12px; background-color: white; }"

def get_hover_animation():
    """Returns hover animation properties - transform not supported in PyQt6"""
    return """
    QWidget:hover {
        /* Transform animations not supported in PyQt6 stylesheets */
    }
    """