import sys
from PyQt5.QtWidgets import QApplication
from ui.windows import InputDialog
import cgitb
cgitb.enable(format='text')


DEBUG = False


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    d = InputDialog()
    d.show()
    if DEBUG:
        sys.excepthook = except_hook
    sys.exit(app.exec_())
