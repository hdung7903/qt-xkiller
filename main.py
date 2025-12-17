
import sys
from PyQt6.QtWidgets import QApplication
from qt_material import apply_stylesheet
from src.app import TaskKillerApp

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Theme
    apply_stylesheet(app, theme='dark_cyan.xml')

    window = TaskKillerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
