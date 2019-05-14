# Start Xampp, start sql server, start apache server

import re
import sys

import mysql.connector
import qtmodern.styles
import qtmodern.windows
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from mysql.connector import errorcode, errors
from qtpy.QtCore import Slot

from employees import Employee

my_signal = pyqtSignal


class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.ui = uic.loadUi('employee_database_ui.ui', self)
        self.setWindowIcon(QIcon('emp_icon.ico'))
        self.setWindowTitle('Employee Database')
        self.ui.widget.hide()
        self.ui.confirm_button_2.hide()
        self.center()
        # Since we're using one confirmation button to look up, update or delete, I'm going to use the boolean
        # variables to see which button the user clicked
        self.update = False
        self.look_up = False
        self.delete = False
        self.add = False
        self.found = False

        self.sql = mysql.connector

        try:

            self.my_db = self.sql.connect(
                host='localhost',
                user='root',
                password='',
                database='employee_database'
            )
            self.my_cursor = self.my_db.cursor(buffered=True)
        except errorcode.ER_BAD_DB_ERROR:
            self.my_db = mysql.connector.connect(
                host='localhost',
                user='root',
                password='',
            )
            self.my_cursor = self.my_db.cursor(buffered=True)
            self.my_cursor.execute("CREATE DATABASE IF NOT EXISTS employee_database")

        # my_cursor.execute("SHOW DATABASES")
        self.my_cursor.execute(
            "CREATE TABLE IF NOT EXISTS employees (emp_id int PRIMARY KEY, emp_name varchar(255), emp_department varchar(255), emp_title varchar(255))")

    # Function to show an error message box
    def error_msg(self, error_string):
        QMessageBox.about(self, 'Errors in your form!', error_string)

    # Function to show a confirmation message box
    def confirmation_msg(self, good_string):
        QMessageBox.about(self, 'Confirmation!', good_string)

    # Function to center our application instead of putting it in the top left
    # It opens in the center of whichever screen it's on in case of dual monitors
    def center(self):
        frame_gm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        center_point = QApplication.desktop().screenGeometry(screen).center()
        frame_gm.moveCenter(center_point)
        self.move(frame_gm.topLeft())

    # When look up, update or delete is clicked, we want the id only, to look up the employee first
    def show_look_up(self):
        self.ui.label_3.hide()
        self.ui.label_4.hide()
        self.ui.label_5.hide()
        self.ui.name_input.hide()
        self.ui.department_input.hide()
        self.ui.title_input.hide()
        self.ui.confirm_button.hide()
        self.ui.confirm_button_2.show()

    # After looking up an employee if they exist, show text boxes and labels for further input
    def hide_look_up(self):
        self.ui.label_2.show()
        self.ui.label_3.show()
        self.ui.label_4.show()
        self.ui.label_5.show()
        self.ui.id_input.show()
        self.ui.name_input.show()
        self.ui.department_input.show()
        self.ui.title_input.show()
        self.ui.line.move(140, 180)
        self.ui.clear_button.move(160, 180)
        self.ui.confirm_button_2.hide()
        self.ui.confirm_button.show()

    # Check if ID format is correct. This method is not static because it initialized the id, name, dept, and title
    def check_id(self):
        global id_number, name, department, title
        id_number = self.ui.id_input.text()
        name = self.ui.name_input.text()
        department = self.ui.department_input.text()
        title = self.ui.title_input.text()
        return bool(re.match(r'^([\s\d]+)$', id_number))

    # Check if name format is correct
    @staticmethod
    def check_name():
        global id_number, name, department, title
        return bool(re.match("[a-zA-Z]+", name))

    # Check if department format is correct
    @staticmethod
    def check_department():
        return bool(re.match("[a-zA-Z]+", department))

    # check if the title format is correct
    @staticmethod
    def check_title():
        return bool(re.match("[a-zA-Z]+", title))

    # Check to see if ID input is correct, and that every textbox is filled
    def add_or_update(self):
        things_to_check = {
            'id': self.check_id(),
            'name': self.check_name(),
            'department': self.check_department(),
            'title': self.check_title()
        }

        # Check for valid inputs and display the appropriate error message
        try:
            global msg
            if all(things_to_check.values()):
                employee_object = Employee(name, id_number, department, title)
                if self.update:
                    self.update_info(id_number, name, department, title)
                    if self.found and self.confirm_selection(id_number):
                        self.confirmation_msg(f'Employee {id_number} has been updated!')

                    else:
                        pass
                elif self.add:
                    self.add_info(id_number, employee_object)
                    if not self.found:
                        self.confirmation_msg(f'Employee {id_number} has been added!')
                    else:
                        pass
                        self.found = False
            else:
                msg = ''
                if not things_to_check['id']:
                    msg += 'Invalid ID format!\n'
                if not things_to_check['name']:
                    msg += 'Invalid Name format!\n'
                if not things_to_check['department']:
                    msg += 'Invalid Department format!\n'
                if not things_to_check['title']:
                    msg += 'Invalid Title format!\n'
                self.error_msg(msg)
                msg = ''
        except TypeError:
            msg += 'One or more columns requires an input!\n'
            self.error_msg(msg)
            msg = ''

    # Function for confirming if you want to update, delete, or purge the employee list
    def confirm_selection(self, id_=None):
        global reply
        if id_ is not None:
            if self.update:
                place_holder = 'update'
            else:
                place_holder = 'delete'

            # noinspection PyCallByClass
            reply = QMessageBox.question(self, 'Confirmation!', f'Are you sure you want to {place_holder} {id_}?\n\n')

        else:
            place_holder = 'Employees'

            reply = QMessageBox.question(self, 'Confirmation!', f'Employee data is saved even after you close the '
            f'application.\nThis option clears that saved data.\nAre you sure you want to purge all {place_holder}?')
        # if they reply yes, exit window
        if reply == QMessageBox.Yes:
            return True
        # if they reply no, stay where you are
        else:
            self.ui.widget.update()
            return False

    # Add info to the database
    def add_info(self, id_, object_):
        try:
            command = "INSERT INTO employees (emp_id, emp_name, emp_department, emp_title) VALUES (%s, %s, %s, %s)"
            values = (f'{int(id_)}', f'{object_.get_name()}', f'{object_.get_department()}', f'{object_.get_title()}')
            self.my_cursor.execute(command, values)
            self.my_db.commit()
            self.found = False
        except errors.IntegrityError:
            self.error_msg('User already exists!')
            self.found = True

    # Remove info from the database
    def remove_info(self, id_):
        check_query = "SELECT * from employees WHERE emp_id=%s"
        self.my_cursor.execute(check_query, (id_,))

        if self.my_cursor.rowcount == 1:
            command = "DELETE from employees WHERE emp_id=%s"
            self.my_cursor.execute(command, (id_,))
            self.my_db.commit()
            self.confirmation_msg(f'Employee {id_} deleted!')
        else:
            self.error_msg(f'Employee {id_} doesn\'t exist!')

    # Update info in database
    def update_info(self, id_, name_, department_, title_):
        check_query = "SELECT * from employees WHERE emp_id=%s"
        self.my_cursor.execute(check_query, (id_,))

        if self.my_cursor.rowcount == 1:
            self.found = True
            command = 'UPDATE employees SET emp_name=%s, emp_department=%s, emp_title=%s WHERE emp_id=%s'
            values = (f'{name_}', f'{department_}', f'{title_}', f'{int(id_)}')
            self.my_cursor.execute(command, values)
            self.my_db.commit()
        else:
            self.found = False
            self.error_msg('Employee doesn\'t exist!')

    # Return info about employee given employee id
    def get_info(self, id_):
        check_query = "SELECT * from employees WHERE emp_id=%s"
        self.my_cursor.execute(check_query, (id_,))

        if self.my_cursor.rowcount == 1:
            new_cursor = self.my_db.cursor(dictionary=True)
            command = "SELECT * FROM employees WHERE emp_id=%s"
            value = (id_,)
            new_cursor.execute(command, value)
            results = new_cursor.fetchall()

            def get_value(val):
                for row in results:
                    return row[val]

            id_ = get_value('emp_id')
            name_ = get_value('emp_name')
            department_ = get_value('emp_department')
            title_ = get_value('emp_title')

            self.confirmation_msg(f'ID: {id_}\nName: {name_}\nDepartment: {department_}\nTitle: {title_}\n\n')
        else:
            self.error_msg(f'There exists no such user {id_}!')

    @Slot()
    def on_add_button_clicked(self):
        self.add = True
        self.update = False
        self.look_up = False
        self.delete = False
        self.ui.widget.show()
        self.hide_look_up()
        self.ui.confirm_button.setText('Add')
        self.ui.widget.update()

    @Slot()
    def on_look_up_button_clicked(self):
        self.look_up = True
        self.add = False
        self.update = False
        self.delete = False
        self.ui.widget.show()
        self.show_look_up()
        self.ui.clear_button.move(180, 50)
        self.ui.line.move(160, 50)
        self.ui.confirm_button_2.setText('Look up')
        self.ui.widget.update()

    @Slot()
    def on_update_button_clicked(self):
        self.update = True
        self.add = False
        self.delete = False
        self.look_up = False
        self.ui.widget.show()
        self.hide_look_up()
        self.ui.confirm_button.setText('Update')
        self.ui.widget.update()

    @Slot()
    def on_delete_button_clicked(self):
        self.delete = True
        self.add = False
        self.update = False
        self.look_up = False
        self.ui.widget.show()
        self.show_look_up()
        self.ui.clear_button.move(180, 50)
        self.ui.line.move(160, 50)
        self.ui.confirm_button_2.setText('Delete')
        self.ui.widget.update()

    @Slot()
    def on_clear_button_clicked(self):
        self.ui.id_input.clear()
        self.ui.name_input.clear()
        self.ui.department_input.clear()
        self.ui.title_input.clear()
        self.ui.widget.update()

    @Slot()
    def on_purge_button_clicked(self):
        if self.confirm_selection():
            self.my_cursor.execute("TRUNCATE TABLE employees")
        self.ui.widget.update()

    @Slot()
    def on_quit_button_clicked(self):
        self.close()

    @Slot()
    def on_confirm_button_clicked(self):
        self.add_or_update()

    @Slot()
    def on_confirm_button_2_clicked(self):
        _id_ = self.ui.id_input.text()
        if self.look_up:
            self.get_info(_id_)
        elif self.delete:
            if self.confirm_selection(id_=_id_):
                self.remove_info(_id_)

    @Slot()
    def closeEvent(self, event):
        # noinspection PyCallByClass
        reply = QMessageBox.question(self, 'Leaving so soon?', 'Do you want to exit?\n\n')

        # if they reply yes, exit window
        if reply == QMessageBox.Yes:
            event.accept()
            self.my_db.close()
        # if they reply no, stay where you are
        else:
            event.ignore()
            self.ui.widget.update()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    qtmodern.styles.dark(app)

    window = qtmodern.windows.ModernWindow(MyWindow())
    window.show()
    sys.exit(app.exec_())
