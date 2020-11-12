import time
from threading import Lock
from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QDialog, QInputDialog, QMessageBox
from lanchat import networking
from lanchat import return_codes as codes
from sql.helpers import SQLHelper


MAX_UNSAVED = 10


class MainWindow(QMainWindow):
    error = pyqtSignal(str)

    def __init__(self, client: networking.Client):
        super().__init__()
        uic.loadUi('ui/main.ui', self)
        self.closeLock = Lock()
        self.closed = False
        self.closeEvent = self.on_window_close
        self.pushButton_deleteHistory.pressed.connect(self.on_history_delete_btn)
        self.pushButton_exit.pressed.connect(lambda: self.close())
        self.error.connect(self.show_error)

        self.client = client
        self.server = None
        self.users = []

        self.sql_helper = SQLHelper()
        self.unsaved = 0
        self.server_name = ':'.join(map(str, self.client.get_addr()))
        for elem in self.sql_helper.load_history(self.server_name):
            self.print_message(elem[0], elem[1], elem[2], True)

    def attach_server(self, server):
        self.server = server

    def print(self, text, darken=False):
        self.listWidget_chat.addItem(text)
        if darken:
            i = self.listWidget_chat.count() - 1
            self.listWidget_chat.item(i).setForeground(Qt.gray)

    def print_message(self, author, message, message_time, from_history=False):
        timestamp = time.strftime('%H:%M', time.localtime(message_time))
        self.print(f'[{timestamp}] [{author}] {message}', from_history)

    def load_users(self, users):
        for u in users:
            self.users.append(u)
            self.listWidget_users.addItem(u)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and self.lineEdit.isEnabled():
            text = self.lineEdit.text()
            if text != '':
                self.lineEdit.setText('')
                self.client.send(text)

    def on_receive(self, data):
        code = data['code']
        if code == codes.MESSAGE:
            self.print_message(data['author'], data['message'], data['time'])
            self.sql_helper.add_message(self.server_name, data['author'], data['message'])
            self.unsaved += 1
            if self.unsaved > MAX_UNSAVED:
                self.sql_helper.commit()
                self.unsaved = 0
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

    def on_history_delete_btn(self):
        res = QMessageBox.question(self,
                                   'Очистить историю',
                                   'Вы действительно хотите очистить историю сообщений для этого '
                                   'сервера? Это дейтсвие нельзя будет отменить.',
                                   QMessageBox.Yes | QMessageBox.No)
        if res == QMessageBox.Yes:
            self.sql_helper.delete_from_server_and_commit(self.server_name)
            self.listWidget_chat.clear()

    def on_connection_close(self, show_error=True):
        if self.closed:
            return
        with self.closeLock:
            self.closed = True
            self.lineEdit.setEnabled(False)
            self.client.close()
            if self.server is not None:
                self.server.close()
            if not self.sql_helper.get_closed():
                self.sql_helper.commit()
                self.sql_helper.close()
            if show_error and self.server is None:
                self.error.emit('Сервер закрыл подключение')

    def on_window_close(self, event):
        self.on_connection_close(False)

    def show_error(self, string):
        QMessageBox.critical(self, 'Ошибка', string)


class InputDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('ui/dialog.ui', self)
        # noinspection PyTypeChecker
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFixedSize(self.size())
        self.pushButton_connect.pressed.connect(self.on_connect_btn)
        self.pushButton_host.pressed.connect(self.on_host_btn)
        self.pushButton_deleteHistoryOlderThan.pressed.connect(self.on_del_history_older_than_btn)
        self.pushButton_deleteHistoryAll.pressed.connect(self.on_del_history_all_btn)

    def get_addr(self):
        ip = self.lineEdit_ip.text()
        port = self.spinBox_port.value()
        return ip, port

    def switch_to_main(self, srv: networking.Server = None):
        cl = networking.Client()
        addr = self.get_addr()
        try:
            cl.connect(*addr)
        except OSError as e:
            cl.close()
            if srv:
                srv.close()
            QMessageBox.critical(self, 'Ошибка', str(e))
            return

        text = f'Введите имя пользовтеля (максимум символов: {cl.get_username_limit()})'
        username, ok_pressed = QInputDialog.getText(self, 'Имя пользовтеля', text)
        if not ok_pressed:
            cl.close()
            if srv:
                srv.close()
            return

        main = MainWindow(cl)
        main.attach_server(srv)
        try:
            users = cl.authorize(username, main.on_receive, main.on_connection_close)
            main.load_users(users)
            main.show()
            self.close()
        except (OSError, networking.NetworkingError) as e:
            cl.close()
            if srv:
                srv.close()
            main.close()
            QMessageBox.critical(self, 'Ошибка', str(e))
            return

    def on_connect_btn(self):
        self.switch_to_main()

    def on_host_btn(self):
        srv = networking.Server()
        try:
            srv.bind(*self.get_addr())
        except OSError as e:
            srv.close()
            QMessageBox.critical(self, 'Ошибка', str(e))
            return
        self.switch_to_main(srv)

    def on_del_history_older_than_btn(self):
        days, ok_pressed = QInputDialog.getInt(self,
                                               'Количество дней',
                                               'Введите N. Данное действие нельзя будет отменить.',
                                               min=1)
        if ok_pressed:
            sql = SQLHelper()
            sql.delete_older_than_and_commit(days)
            sql.close()

    def on_del_history_all_btn(self):
        res = QMessageBox.question(self,
                                   'Очистить историю',
                                   'Вы действительно хотите очистить историю сообщений? '
                                   'Это дейтсвие нельзя будет отменить.',
                                   QMessageBox.Yes | QMessageBox.No)
        if res == QMessageBox.Yes:
            sql = SQLHelper()
            sql.delete_all_and_commit()
            sql.close()
