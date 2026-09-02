import PyQt6.QtWidgets as qt
import PyQt6.QtCore as qt2
import PyQt6.QtGui as qt1
import custom_errors
import guiTools
from .data_loader import MotonDataLoader
from .favorites_manager import MotonFavoritesManager
from .category_widget import MotonCategoryWidget
from .favorites_widget import MotonFavoritesWidget

class IslamicMoton(qt.QWidget):
    def __init__(self):
        super().__init__()
        self.data_loader = MotonDataLoader()
        self.fav_manager = MotonFavoritesManager()
        self.category_widgets = []
        self.init_ui()

    def init_ui(self):
        self.moton_tab = qt.QTabWidget()
        self.moton_tab.setStyleSheet(
            "QTabWidget::pane { border: 1px solid #444; border-radius: 6px; background-color: #1e1e1e; } "
            "QTabBar::tab { background: #2b2b2b; color: white; padding: 10px 20px; border: 1px solid #444; "
            "border-top-left-radius: 8px; border-top-right-radius: 8px; margin: 2px; min-width: 100px; font-weight: bold; } "
            "QTabBar::tab:selected { background: #0078d7; color: white; border: 1px solid #0078d7; } "
            "QTabBar::tab:hover { background: #3a3a3a; }"
        )

        categories = self.data_loader.get_categories()
        for idx, cat_name in enumerate(categories):
            cat_widget = MotonCategoryWidget(idx, self.data_loader, self.handle_favorite_toggle)
            self.category_widgets.append(cat_widget)
            self.moton_tab.addTab(cat_widget, cat_name)

        self.favorites_widget = MotonFavoritesWidget(self.data_loader, self.fav_manager, self.handle_favorite_toggle)

        self.fav_info_label = guiTools.QNavigableLabel("لإضافة متن أو إزالته من قائمة المفضلة، نستخدم زر التطبيقات أو click الأيمن على المتن")
        self.fav_info_label.setFocusPolicy(qt2.Qt.FocusPolicy.StrongFocus)
        self.fav_info_label.setAlignment(qt2.Qt.AlignmentFlag.AlignCenter)

        self.fav_btn = guiTools.QPushButton("فتح قائمة المفضلة")
        self.fav_btn.setStyleSheet("background-color: #0000AA; color: white; min-height: 48px; padding: 0 20px; font-weight: bold;")
        self.fav_btn.clicked.connect(self.toggle_favorites)

        info_fav_layout = qt.QHBoxLayout()
        info_fav_layout.addStretch(1)
        info_fav_layout.addWidget(self.fav_btn)

        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.moton_tab)
        layout.addWidget(self.favorites_widget)
        layout.addSpacing(10)
        layout.addWidget(self.fav_info_label)
        layout.addSpacing(10)
        layout.addLayout(info_fav_layout)

        self.update_favorites_ui_state()

    def handle_favorite_toggle(self, matn_name):
        is_added = self.fav_manager.toggle_favorite(matn_name)
        if is_added:
            guiTools.qMessageBox.MessageBox.view(self, "تم", f"تم إضافة {matn_name} إلى المفضلة")
        else:
            guiTools.qMessageBox.MessageBox.view(self, "تم", f"تم إزالة {matn_name} من المفضلة")
        self.favorites_widget.refresh_favorites()

    def toggle_favorites(self):
        self.fav_manager.show_favorites_only = not self.fav_manager.show_favorites_only
        self.fav_manager.save_favorites()
        self.update_favorites_ui_state()

    def update_favorites_ui_state(self):
        if self.fav_manager.show_favorites_only:
            self.moton_tab.hide()
            self.favorites_widget.refresh_favorites()
            self.favorites_widget.show()
            self.fav_btn.setText("عرض جميع المتون")
        else:
            self.favorites_widget.hide()
            self.moton_tab.show()
            self.fav_btn.setText("فتح قائمة المفضلة")
