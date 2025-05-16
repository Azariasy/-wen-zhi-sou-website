import sys
import traceback

try:
    # 导入应用程序
    from search_gui_pyside import MainWindow
    from PySide6.QtWidgets import QApplication
    
    # 创建应用程序
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())
except Exception as e:
    # 打印错误信息
    print(f"错误: {e}")
    print("详细错误信息:")
    traceback.print_exc() 