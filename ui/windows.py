from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QDialog, QInputDialog, QMessageBox
from lanchat import networking
from lanchat import return_codes as codes


class MainWindow(QMainWindow):
    def __init__(self, client: networking.Client, server: networking.Server = None):
        super().__init__()
        uic.loadUi('ui/main.ui', self)
        self.client = client
        self.server = server
        self.closeEvent = self.on_window_close
        self.users = []

    def print(self, text):
        self.listWidget_chat.addItem(text)

    def load_users(self, users):
        for u in users:
            self.users.append(u)
            self.listWidget_users.addItem(u)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            text = self.lineEdit.text()
            if text != '':
                self.lineEdit.setText('')
                self.client.send(text)

    def on_receive(self, data):
        code = data['code']
        if code == codes.MESSAGE:
            author = '[' + data['author'] + ']'
            self.print(author + ' ' + data['message'])
        elif code == codes.CONNECT:
            username = data['username']
            self.print(f'{username} подключился')
            self.users.append(username)
            self.listWidget_users.addItem(username)
        elif code == codes.DISCONNECT:
            username = data['username']
            self.print(f'{username} отключился')
            i = self.users.index(username)
            del self.users[i]
            self.listWidget_users.takeItem(i)

    def on_connection_close(self):
        self.client.close()
        if self.server is not None:
            self.server.close()
        print('close')

    def on_window_close(self, event):
        self.on_connection_close()


class InputDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('ui/dialog.ui', self)
        # noinspection PyTypeChecker
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFixedSize(self.size())
        self.pushButton_connect.pressed.connect(self.on_connect_btn)
        self.pushButton_host.pressed.connect(self.on_host_btn)

    def get_addr(self):
        ip = self.lineEdit_ip.text()
        port = self.spinBox_port.value()
        return ip, port

    def on_connect_btn(self):
        cl = networking.Client()
        cl.connect(*self.get_addr())

        text = f'Введите имя пользовтеля (максимум символов: {cl.get_username_limit()})'
        username, ok_pressed = QInputDialog.getText(self, 'Имя пользовтеля', text)
        if not ok_pressed:
            cl.close()
            return

        main = MainWindow(cl)
        try:
            users = cl.authorize(username, main.on_receive, main.on_connection_close)
            main.load_users(users)
            main.show()
            self.close()
        except networking.NetworkingError as e:
            cl.close()
            main.close()
            QMessageBox.critical(self, 'Ошибка', e.args[0])

    def on_host_btn(self):
        pass # TODO
