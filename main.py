import sqlite3
import sys
import random
from math import ceil
from collections import defaultdict
from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

COLORS = [
    "rgb(183, 173, 168)",  # серый
    "rgb(177, 247, 161)",  # зелёный
    "rgb(95, 255, 59)",  # зелёный тёмный
    "rgb(96, 97, 96)"  # светло-серый
    "rgb(89, 152, 247)",  # синий
    "rgb(3, 2, 2)",  # Чёрный
    "rgb(183, 0, 255)",  # фиолетовый
    "rgb(235, 49, 0)",  # Розовый
    "rgb(0, 171, 201)",  # голубой
    "rgb(255, 132, 0)",  # оранжевый
    "rgb(153, 75, 8)",  # коричневый
    "rgb(166, 91, 116)",  # типо розовый
    "rgb(255, 112, 112)",  # красный

]
DB_NAME = "sapper.db"
LOSE_IMG = "lose2.png"
LOSE_TEXT = "Вы проиграли"
WIN_IMG = "cup.jpg"
WIN_TEXT = "Вы выиграли"
FONT_SIZE = "14pt"
DEFAULT_NAME = "default_name"
PERCENT_BOMBS = 0.15
# PERCENT_BOMBS = 0
CREATE_TABLE_HISTORY = """CREATE TABLE IF NOT EXISTS history 
                                        (id integer PRIMARY KEY,
                                        user_id,
                                        is_win boolean,
                                        time_close int,
                                        map_size int
                                        );"""
CREATE_TABLE_USERS = """CREATE TABLE IF NOT EXISTS users 
                                        (id integer PRIMARY KEY,
                                        username TEXT
                                        );"""
INSERT_USERNAME = """INSERT INTO users (username)  VALUES  (?)"""
INSERT_TO_HISTORY = """INSERT INTO history (user_id, is_win, time_close, map_size )  
                                        VALUES  (?, ?, ? , ?)"""
GET_WIN_GAMES = """SELECT * FROM history WHERE is_win=1 AND map_size = (?);"""
GET_ALL_GAMES = """SELECT * FROM history;"""
GET_USERNAME_ID = """SELECT * FROM users WHERE username=?;"""
GET_USERNAME_BY_ID = """SELECT username FROM users WHERE id=?;"""
GET_ALL_USERNAMES = """SELECT username FROM users;"""

StyleSheet = """
QComboBox {
    border: 0px;
    border-radius: 3px;
    padding: 1px 18px 1px 3px;
    min-width: 6em;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 0px;
}


QComboBox QAbstractItemView {
    border: 2px solid darkgray;
    selection-background-color: lightgray;
}
"""


def find_color(bombs):
    if bombs == 0:
        return COLORS[8]
    if bombs == 1:
        return COLORS[4]
    if bombs == 2:
        return COLORS[5]
    if bombs == 3:
        return COLORS[6]
    if bombs == 4:
        return COLORS[7]
    if bombs == 5:
        return COLORS[9]
    if bombs == 6:
        return COLORS[10]
    if bombs == 7:
        return COLORS[11]
    if bombs == 8:
        return COLORS[12]


class Finish(QWidget):
    def __init__(self, file_name, set_text):
        super(Finish, self).__init__()
        pixmap = QPixmap(file_name)
        text = QLabel(self)
        text.setText(set_text)
        text.setStyleSheet("font-size: 30pt;")
        text.setAlignment(Qt.AlignCenter)
        text.setGeometry(0, 0, pixmap.width() + 50, 60)
        text.show()
        self.load_image(file_name)

    def load_image(self, file_name):
        pixmap = QPixmap(file_name)
        picture = QLabel(self)
        picture.setPixmap(pixmap)
        picture.setGeometry(25, 60, pixmap.width(), pixmap.height())
        self.setFixedSize(QSize(pixmap.width() + 50, pixmap.height() + 60))
        picture.show()

    def mousePressEvent(self, event):
        self.mainwindow = MainWindow()
        self.mainwindow.show()
        self.close()


class Game(QWidget):
    def __init__(self, amount, userid, size=25, start_pos=60):
        super().__init__()
        self.user_id = userid
        self.is_win = False
        self.start_pos = start_pos
        self.amount = amount
        self.list_QWidget_cells = []
        self.is_near_cell_with_zero_bombs = [[-1 for _ in range(self.amount)] for _ in range(self.amount)]
        self.list_cells = [[0 for j in range(self.amount)] for i in range(self.amount)]
        self.size = size
        self.near_bombs = defaultdict(int)
        self.setFixedSize(QSize(amount * size, amount * size + self.start_pos))
        self.map_generator()
        self.setWindowTitle('Сапёр')
        self.timer = QtCore.QTimer()
        self.time = QtCore.QTime(0, 0, 0)
        self.timer.timeout.connect(self.timerEvent)
        self.timer.start(1000)
        self.time_output = QLCDNumber(self)
        self.time_output.setGeometry(0, 0, amount * size, start_pos)
        self.time_output.setDigitCount(8)
        self.time_output.display(self.time.toString())

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            return None
        if event.y() < 60:
            return None
        interaction = self.find_pos_by_coord_click(event.x(), event.y())
        is_lose = self.change_status_cell(interaction)
        if is_lose:
            self.save_result_play(False)
            self.loose_window = Finish(LOSE_IMG, LOSE_TEXT)
            self.loose_window.show()
            self.close()
            return None

        for cell in self.list_QWidget_cells:
            cell.deleteLater()
        self.update()
        self.list_QWidget_cells = []
        self.is_win = self.is_win_func()
        if self.is_win:
            self.save_result_play(True)
            self.timer.disconnect()
            self.won_window = Finish(WIN_IMG, WIN_TEXT)
            self.won_window.show()
            self.close()
            return None

    def is_win_func(self):
        for row in self.list_cells:
            for cell in row:
                if cell == 0:
                    return False

        return True

    def save_result_play(self, is_win):
        sqlite_connection = sqlite3.connect(DB_NAME)
        cursor = sqlite_connection.cursor()
        time_count = self.time.second() + self.time.minute() * 60 + self.time.hour() * 3600
        cursor.execute(INSERT_TO_HISTORY, [self.user_id, is_win, time_count, self.amount])
        sqlite_connection.commit()
        cursor.close()

    def map_generator(self):
        for i in range(self.amount):
            for j in range(self.amount):
                cell = QLabel(self)
                if random.random() < PERCENT_BOMBS:
                    self.list_cells[i][j] = 2
                cell.setGeometry(i * self.size, j * self.size + self.start_pos, self.size, self.size)
                cell.setStyleSheet(f"background-color:{COLORS[1]}; border: 0.5px solid {COLORS[3]};")
                self.list_QWidget_cells.append(cell)

        for i in range(self.amount):
            for j in range(self.amount):
                if self.list_cells[i][j] == 2:
                    self.near_bombs[f"{i}:{j}"] = -1
                    continue
                bombs = 0
                if i != 0:
                    if self.list_cells[i - 1][j] == 2:
                        bombs += 1
                    if self.list_cells[i - 1][j - 1] == 2 and j != 0:
                        bombs += 1
                    if j != self.amount - 1:
                        if self.list_cells[i - 1][j + 1] == 2:
                            bombs += 1

                if i != self.amount - 1:
                    if self.list_cells[i + 1][j] == 2:
                        bombs += 1
                    if self.list_cells[i + 1][j - 1] == 2 and j != 0:
                        bombs += 1
                    if j != self.amount - 1:
                        if self.list_cells[i + 1][j + 1] == 2:
                            bombs += 1

                if j != 0:
                    if self.list_cells[i][j - 1] == 2:
                        bombs += 1
                if j != self.amount - 1:
                    if self.list_cells[i][j + 1] == 2:
                        bombs += 1
                self.near_bombs[f"{i}:{j}"] = bombs
                if bombs == 0:
                    self.is_near_cell_with_zero_bombs[i][j] = 1

        for i in range(self.amount):
            for j in range(self.amount):
                if self.list_cells[i][j] > 0 or self.is_near_cell_with_zero_bombs[i][j] == 1:
                    continue
                if i != 0:
                    if self.is_near_cell_with_zero_bombs[i - 1][j] == 1:
                        self.is_near_cell_with_zero_bombs[i][j] = 0
                    if self.is_near_cell_with_zero_bombs[i - 1][j - 1] == 1 and j != 0:
                        self.is_near_cell_with_zero_bombs[i][j] = 0
                    if j != self.amount - 1:
                        if self.is_near_cell_with_zero_bombs[i - 1][j + 1] == 1:
                            self.is_near_cell_with_zero_bombs[i][j] = 0

                if i != self.amount - 1:
                    if self.is_near_cell_with_zero_bombs[i + 1][j] == 1:
                        self.is_near_cell_with_zero_bombs[i][j] = 0
                    if self.is_near_cell_with_zero_bombs[i + 1][j - 1] == 1 and j != 0:
                        self.is_near_cell_with_zero_bombs[i][j] = 0
                    if j != self.amount - 1:
                        if self.is_near_cell_with_zero_bombs[i + 1][j + 1] == 1:
                            self.is_near_cell_with_zero_bombs[i][j] = 0

                if j != 0:
                    if self.is_near_cell_with_zero_bombs[i][j - 1] == 1:
                        self.is_near_cell_with_zero_bombs[i][j] = 0
                if j != self.amount - 1:
                    if self.is_near_cell_with_zero_bombs[i][j + 1] == 1:
                        self.is_near_cell_with_zero_bombs[i][j] = 0

    def update(self):
        for rounds in range(int(self.amount / 2 + 0.5)):
            self.func_by_some_criteria(1, self.open_cell, self.examination_nearest, lambda x, y: True)
            self.func_by_some_criteria(1, self.open_cell, self.examination_near_cell_with_zero, self.is_zero_cell)
        for i in range(self.amount):
            for j in range(self.amount):
                cell = QLabel(self)
                cell.setGeometry(i * self.size, j * self.size + self.start_pos, self.size, self.size)
                cell.setAlignment(Qt.AlignCenter)
                if self.list_cells[i][j] == 1:
                    text_color = find_color(self.near_bombs[f"{i}:{j}"])
                    if self.near_bombs[f"{i}:{j}"] != 0:
                        cell.setText(str(self.near_bombs[f"{i}:{j}"]))
                    cell.setStyleSheet(
                        f"background-color:rgb(255,255,255); border: 0.5px solid {COLORS[3]}; font-size: {FONT_SIZE}; color:{text_color}")
                else:
                    cell.setStyleSheet(
                        f"background-color:{COLORS[1]}; border: 0.5px solid {COLORS[3]}; "
                        f"font-size: {FONT_SIZE};")
                self.list_QWidget_cells.append(cell)
        for widget in self.list_QWidget_cells:
            widget.show()

    def is_zero_cell(self, i, j):
        return self.near_bombs[f"{i}:{j}"] == 0

    def find_pos_by_coord_click(self, x, y):
        pos_i = ceil(x / self.size)
        pos_j = ceil((y - self.start_pos) / self.size)
        return pos_i - 1, pos_j - 1

    def change_status_cell(self, interaction):
        cell = self.list_cells[interaction[0]][interaction[1]]
        if cell == 0:
            self.list_cells[interaction[0]][interaction[1]] = 1
        elif cell == 2:
            self.list_cells[interaction[0]][interaction[1]] = 3
            return True
        return False

    def open_cell(self, i, j):
        self.list_cells[i][j] = 1

    def examination_nearest(self, i, j):
        if self.list_cells[i][j] == 0 and self.near_bombs[f"{i}:{j}"] == 0:
            return True
        return False

    def examination_near_cell_with_zero(self, i, j):
        return self.is_near_cell_with_zero_bombs[i][j] != -1

    def func_by_some_criteria(self, criteria, func, examination, addit_examination):
        for i in range(self.amount):
            for j in range(self.amount):
                if examination(i, j):
                    if i != 0:
                        if self.list_cells[i - 1][j] == criteria and addit_examination(i - 1, j):
                            func(i, j)
                        if self.list_cells[i - 1][j - 1] == criteria and j != 0 and addit_examination(i - 1, j - 1):
                            func(i, j)
                        if j != self.amount - 1:
                            if self.list_cells[i - 1][j + 1] == criteria and addit_examination(i - 1, j + 1):
                                func(i, j)

                    if i != self.amount - 1:
                        if self.list_cells[i + 1][j] == criteria and addit_examination(i + 1, j):
                            func(i, j)
                        if self.list_cells[i + 1][j - 1] == 1 and j != 0 and addit_examination(i + 1, j - 1):
                            func(i, j)
                        if j != self.amount - 1:
                            if self.list_cells[i + 1][j + 1] == criteria and addit_examination(i + 1, j + 1):
                                func(i, j)

                    if j != 0:
                        if self.list_cells[i][j - 1] == criteria and addit_examination(i, j - 1):
                            func(i, j)
                    if j != self.amount - 1:
                        if self.list_cells[i][j + 1] == criteria and addit_examination(i, j + 1):
                            func(i, j)

    def timerEvent(self, **kwargs):
        self.time = self.time.addSecs(1)
        self.time_output.display(self.time.toString())
        self.time_output.show()


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle('Сапёр')
        all_length = 1000
        all_height = 500
        indentation = 10
        length_buttons = 40
        length_plaques = 170
        height_plaques = 30
        self.setMinimumWidth(all_length)
        self.setMinimumHeight(all_height)
        self.setStyleSheet("background-color:white")
        x = 25
        y = 5
        self.user_name = QLabel(self)
        self.user_name.setText("Ваш ник")
        self.user_name.setGeometry(x, y, length_plaques, height_plaques)
        self.user_name.setStyleSheet("font-size:20px;")
        self.user_name.setAlignment(Qt.AlignCenter)
        y += height_plaques
        self.username_box = QComboBox(self)
        self.username_box.setStyleSheet("font-size:17px; text-align:center;")
        self.all_usernames = select_usernames()
        self.username_box.addItems(self.all_usernames)
        self.username_box.setGeometry(x, y + indentation, length_plaques, height_plaques)

        self.user_name.setStyleSheet("font-size:20px;")
        y += height_plaques + indentation

        self.create_name_label = QLabel(self)
        self.create_name_label.setText("Создать ник")
        self.create_name_label.setGeometry(x, y + indentation * 2, length_plaques, height_plaques)
        self.create_name_label.setStyleSheet("font-size:20px;")
        self.create_name_label.setAlignment(Qt.AlignCenter)

        y += indentation * 3 + height_plaques
        self.input_username = QLineEdit(self)
        self.input_username.setGeometry(x, y, length_plaques - indentation - length_buttons, height_plaques)
        self.input_username.setStyleSheet("font-size:15px")

        self.create_name_button = QPushButton(self)
        self.create_name_button.clicked.connect(self.add_username_to_box)
        self.create_name_button.setGeometry(x + (length_plaques - length_buttons), y, length_buttons, height_plaques)
        self.create_name_button.setStyleSheet(
            f"border:1px solid black; border-radius:2px; background-color:{COLORS[0]};")

        x += length_plaques + indentation
        self.start_game = QPushButton(self)
        self.start_game.clicked.connect(self.show_map)
        self.start_game.clicked.connect(self.close)
        self.start_game.setGeometry(x + 30, 5, 120, 50)
        self.start_game.setText("Начать игру")
        self.start_game.setStyleSheet(
            f"border:1px solid black; border-radius:2px; background-color:white; font-size:20px;")

        self.history_button = QPushButton(self)
        self.history_button.clicked.connect(self.show_history)
        self.history_button.setGeometry(x + 30 + 120 + 16, 5, 120, 50)
        self.history_button.setText("История")
        self.history_button.setStyleSheet(
            f"border:1px solid black; border-radius:2px; background-color:white; font-size:20px;")

        self.mapsize_label = QLabel(self)
        self.mapsize_label.setText("Размер поля (от 8 до 30)")
        self.mapsize_label.setGeometry(x + 50, y - indentation - height_plaques, length_plaques + 60,
                                       height_plaques)
        self.mapsize_label.setStyleSheet("font-size:18px;")
        self.mapsize_label.setAlignment(Qt.AlignCenter)

        self.input_amount = QLineEdit(self)
        self.input_amount.setGeometry(x + 50 + (length_plaques + 60 - length_buttons) // 2, y, length_buttons,
                                      length_buttons)
        self.input_amount.setText("8")
        self.input_amount.setStyleSheet("font-size:18px;")
        x += 50 + (length_plaques + 60 - length_buttons) // 2
        x += length_plaques + 60

        self.change_rating = QLineEdit(self)
        self.change_rating.setGeometry(x, 5, length_buttons, height_plaques)
        self.change_rating.setStyleSheet("font-size:15px")
        self.change_rating.setText("8")

        self.change_rating_button = QPushButton(self)
        self.change_rating_button.clicked.connect(self.create_rating)
        self.change_rating_button.setGeometry(x + length_buttons + indentation, 5,
                                              length_plaques - indentation - length_buttons, height_plaques)
        self.change_rating_button.setStyleSheet(
            f"font-size:15px; border:1px solid black; border-radius:2px;")
        self.change_rating_button.setText("Обновить")

        self.rating = QTableWidget(self)
        self.rating.setColumnCount(2)
        self.rating.setHorizontalHeaderLabels(["Username", "Время"])
        self.rating.horizontalHeaderItem(0).setTextAlignment(Qt.AlignHCenter)
        self.rating.horizontalHeaderItem(1).setTextAlignment(Qt.AlignHCenter)
        self.rating.setStyleSheet("font-size:17px")
        self.start_x = x
        self.start_y = 5 + height_plaques + indentation
        self.create_rating()

    def get_map_size(self):
        amount = 8
        try:
            amount = int(self.change_rating.text())
            if amount < 8:
                amount = 8
            if amount > 41:
                amount = 30
        except ValueError:
            pass
        return amount

    def add_username_to_box(self):
        username = self.input_username.text()
        if username in self.all_usernames:
            return 0
        self.all_usernames.append(username)
        if username == '':
            username = 'default_name'
        create_or_select_username(username)
        self.username_box.addItem(username)

    def show_history(self):
        self.history = History()
        self.history.show()

    def show_map(self):
        amount = 16
        try:
            amount = int(self.input_amount.text())
            if amount < 8:
                amount = 8
            if amount > 41:
                amount = 30
        except ValueError:
            pass
        userid = create_or_select_username(self.username_box.currentText())
        self.game_board = Game(amount, userid)
        self.game_board.show()

    def create_rating(self):
        sqlite_connection = sqlite3.connect(DB_NAME)
        cursor = sqlite_connection.cursor()
        win_plays = cursor.execute(GET_WIN_GAMES, [self.get_map_size()]).fetchall()
        map_best_result = defaultdict(lambda: 10 ** 4)
        for win_play in win_plays:
            if map_best_result[win_play[1]] > win_play[3]:
                map_best_result[win_play[1]] = win_play[3]
        list_sort_best_result = list(map_best_result.items())
        list_sort_best_result.sort(key=lambda x: x[1])
        self.rating.setRowCount(len(list_sort_best_result))

        max_len = len("UsernameВремя") + len(str((len(list_sort_best_result)))) + 2
        for index, play in enumerate(list_sort_best_result):
            username = get_name_by_id(play[0])
            username_widget = QTableWidgetItem(username)
            max_len = max(max_len, len(username) + max(len("Время"), len(str(play[1]))) + len(str(index)))
            time = QTableWidgetItem(str(play[1]))
            time.setTextAlignment(Qt.AlignCenter)
            username_widget.setTextAlignment(Qt.AlignCenter)
            self.rating.setItem(index, 0, username_widget)
            self.rating.setItem(index, 1, time)
        self.rating.resizeColumnsToContents()
        self.rating.setVerticalHeaderLabels([])
        if max_len > 25:
            max_len -= max_len // 6
        self.rating.setGeometry(self.start_x, self.start_y, min(1000, int(max_len * 10)),
                                55 + 40 * (len(list_sort_best_result) - 1))


class History(QWidget):
    def __init__(self):
        super().__init__()
        sqlite_connection = sqlite3.connect(DB_NAME)
        cursor = sqlite_connection.cursor()
        self.history = cursor.execute(GET_ALL_GAMES).fetchall()
        cursor.close()
        self.history_table = QTableWidget(self)
        self.history_table.setColumnCount(4)
        self.history_table.setRowCount(len(self.history))
        self.history_table.setHorizontalHeaderLabels(["username", "Победа", "Время", "Размер"])
        self.create_history_table()
        self.history_table.setMinimumHeight(len(self.history) * 33)
        self.history_table.setStyleSheet("font-size:17px")
        self.history_table.resizeColumnsToContents()

        self.history_table.setMinimumWidth(700)
        self.history_table.setMinimumHeight(600)
        self.history_table.show()

    def create_history_table(self):
        for index, play in enumerate(self.history[::-1]):
            username = get_name_by_id(play[1])
            username_widget = QTableWidgetItem(username)
            is_win = "YES" if play[2] else "NO"
            is_win_widget = QTableWidgetItem(is_win)
            time = QTableWidgetItem(str(play[3]))
            map_size = QTableWidgetItem(str(play[4] * play[4]))

            username_widget.setTextAlignment(Qt.AlignCenter)
            is_win_widget.setTextAlignment(Qt.AlignCenter)
            time.setTextAlignment(Qt.AlignCenter)
            map_size.setTextAlignment(Qt.AlignCenter)

            self.history_table.setItem(index, 0, username_widget)
            self.history_table.setItem(index, 1, is_win_widget)
            self.history_table.setItem(index, 2, time)
            self.history_table.setItem(index, 3, map_size)


def create_sql_table():
    sqlite_connection = sqlite3.connect(DB_NAME)
    cursor = sqlite_connection.cursor()
    cursor.execute(CREATE_TABLE_HISTORY)
    cursor.execute(CREATE_TABLE_USERS)
    default_username = cursor.execute(GET_USERNAME_ID, [DEFAULT_NAME]).fetchone()
    if default_username is None:
        cursor.execute(INSERT_USERNAME, [DEFAULT_NAME])
        sqlite_connection.commit()
    cursor.close()
    if sqlite_connection:
        sqlite_connection.close()


def create_or_select_username(user_name):
    sqlite_connection = sqlite3.connect(DB_NAME)
    cursor = sqlite_connection.cursor()
    data = cursor.execute(GET_USERNAME_ID, [user_name]).fetchone()
    if data is None:
        cursor.execute(INSERT_USERNAME, [user_name])
        sqlite_connection.commit()
        return cursor.execute(GET_USERNAME_ID, [user_name]).fetchone()[0]
    cursor.close()
    return data[0]


def get_name_by_id(user_id):
    sqlite_connection = sqlite3.connect(DB_NAME)
    cursor = sqlite_connection.cursor()
    return cursor.execute(GET_USERNAME_BY_ID, [user_id]).fetchone()[0]


def select_usernames():
    sqlite_connection = sqlite3.connect(DB_NAME)
    cursor = sqlite_connection.cursor()
    all_usernames = cursor.execute(GET_ALL_USERNAMES).fetchall()
    list_usernames = []
    for index, username in enumerate(all_usernames):
        list_usernames.append(username[0])
    return list_usernames[::-1]


if __name__ == '__main__':
    create_sql_table()
    app = QApplication(sys.argv)
    app.setStyleSheet(StyleSheet)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec())
