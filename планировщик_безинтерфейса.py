# в тз я писала, что при нажатии на дату будет появляться выбор для пользователя (добавить, удалить, изменить)
# но я решила, что лучше сделать так, как представлено у меня в коде

import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QCalendarWidget, QLabel, QSplitter, QFrame, QPushButton,
                             QLineEdit, QMessageBox, QTextEdit, QDialog, QComboBox,
                             QSpinBox, QGroupBox, QCheckBox)
from PyQt6.QtCore import QDate, Qt, QTimer, QDateTime
from PyQt6.QtGui import QColor, QTextCharFormat, QFont, QPainter, QBrush


class CalendarApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PlanUp")
        self.tasks = {}  # словарь для хранения задач: {дата: [список задач]}
        self.notes = {}  # словарь для хранения заметок: {дата: {индекс_задачи: текст_заметки}}
        self.notifications = {}  # словарь для хранения уведомлений: {дата: {индекс_задачи: настройки}}
        self.goals = {}  # отдельный словарь для целей с длительным периодом
        self.completed_tasks = {}  # словарь для выполненных задач: {дата: {индекс: bool}}

        self.notification_timer = QTimer()
        self.notification_timer.timeout.connect(self.check_notifications)
        self.notification_timer.start(60000)  # проверка каждую минуту

        self.showMaximized()
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        splitter = QSplitter(Qt.Orientation.Vertical)

        # создаем основной контейнер для календаря с заголовком
        calendar_main_frame = QFrame()
        calendar_main_layout = QVBoxLayout(calendar_main_frame)

        # верхняя часть - календарь
        self.calendar = CustomCalendarWidget(self)
        self.calendar.setSelectedDate(QDate.currentDate())
        self.calendar.selectionChanged.connect(self.on_date_selected)

        # настраиваем формат для сегодняшней даты
        today_fmt = QTextCharFormat()
        today_fmt.setBackground(QColor(0, 184, 217))  # зелёный фон с прозрачностью
        today_fmt.setForeground(QColor(255, 255, 255))  # белый текст
        today_fmt.setFontWeight(QFont.Weight.Bold)  # толщина начертания шрифта
        self.calendar.setDateTextFormat(QDate.currentDate(), today_fmt)  # изменение формата даты

        # изменяем формат заголовка
        header_fmt = QTextCharFormat()
        header_fmt.setBackground(QColor(0, 0, 255))
        header_fmt.setForeground(Qt.GlobalColor.white)
        self.calendar.setHeaderTextFormat(header_fmt)

        # отображение задач
        self.tasks_frame = QFrame()
        tasks_layout = QVBoxLayout()

        # создаем кнопки
        self.btn_add = QPushButton('Добавить')
        self.btn_add.clicked.connect(self.add_task)

        # текст с информацией о задачах
        self.tasks_label = QLabel("Задач пока нет")
        self.tasks_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # контейнер для отображения задач
        self.tasks_container = QVBoxLayout()

        # добавляем кнопку и метку в layout задач
        tasks_layout.addWidget(self.btn_add)
        tasks_layout.addWidget(self.tasks_label)
        tasks_layout.addLayout(self.tasks_container)

        self.tasks_label.setStyleSheet("padding: 20px;")
        self.tasks_frame.setLayout(tasks_layout)

        # добавляем виджеты в сплиттер
        splitter.addWidget(self.calendar)
        splitter.addWidget(self.tasks_frame)
        splitter.setSizes([int(self.height() / 2), int(self.height() / 2)])

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        self.on_date_selected()

    def on_date_selected(self):
        selected_date = self.calendar.selectedDate()
        # используем ISO формат для ключа в словаре задач
        self.current_date = selected_date.toString(Qt.DateFormat.ISODate)

        # обновляем отображение задач для выбранной даты
        self.display_tasks()

    def display_tasks(self):
        # очищаем контейнер с задачами
        for i in reversed(range(self.tasks_container.count())):
            self.tasks_container.itemAt(i).widget().setParent(None)

        # получаем задачи для текущей даты
        tasks = self.tasks.get(self.current_date, [])

        # проверяем активные цели
        active_goals = self.get_active_goals_for_date(self.current_date)

        if not tasks and not active_goals:
            # отображаем дату в читаемом формате
            selected_date = QDate.fromString(self.current_date, Qt.DateFormat.ISODate)
            self.tasks_label.setText(f"Задач на {selected_date.toString('dd.MM.yyyy')} пока нет")
            self.tasks_label.show()
        else:
            self.tasks_label.hide()

            # сначала отображаем цели
            for goal_data in active_goals:
                self.create_goal_widget(goal_data)

            # затем обычные задачи
            for i, task in enumerate(tasks):
                self.create_task_widget(task, i)

    def get_active_goals_for_date(self, date_str):
        #  возвращает активные цели для указанной даты
        active_goals = []
        current_date = QDate.fromString(date_str, Qt.DateFormat.ISODate)

        for goal_id, goal_data in self.goals.items():
            start_date = QDate.fromString(goal_data['start_date'], Qt.DateFormat.ISODate)
            end_date = QDate.fromString(goal_data['end_date'], Qt.DateFormat.ISODate)

            if start_date <= current_date <= end_date:
                active_goals.append(goal_data)

        return active_goals

    def create_goal_widget(self, goal_data):
        #  создаёт виджет для отображения цели
        goal_widget = QWidget()
        goal_widget.setStyleSheet("""
            QWidget {
                background-color: rgb(0, 0, 255);
                border: 2px solid #ffeaa7;
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            }
        """)

        goal_layout = QVBoxLayout()

        # заголовок цели
        goal_header = QLabel("🎯 АКТИВНАЯ ЦЕЛЬ")

        # текст цели
        goal_text = QLabel(goal_data['goal_text'])
        goal_text.setWordWrap(True)

        # причина
        reason_text = QLabel(f"💡 Почему важно: {goal_data['reason_text']}")
        reason_text.setWordWrap(True)

        # период
        start_date = QDate.fromString(goal_data['start_date'], Qt.DateFormat.ISODate)
        end_date = QDate.fromString(goal_data['end_date'], Qt.DateFormat.ISODate)
        period_text = QLabel(f"📅 Период: {start_date.toString('dd.MM.yy')} - {end_date.toString('dd.MM.yy')}")

        # кнопки
        buttons_layout = QHBoxLayout()
        note_btn = QPushButton('Заметка')
        stop_btn = QPushButton('Остановить')
        edit_notifications_btn = QPushButton('Напоминания')

        note_btn.clicked.connect(lambda: self.show_goal_note_dialog(goal_data['id']))
        stop_btn.clicked.connect(lambda: self.stop_goal(goal_data['id']))
        edit_notifications_btn.clicked.connect(lambda: self.edit_goal_notifications(goal_data['id']))

        buttons_layout.addWidget(note_btn)
        buttons_layout.addWidget(edit_notifications_btn)
        buttons_layout.addWidget(stop_btn)

        goal_layout.addWidget(goal_header)
        goal_layout.addWidget(goal_text)
        goal_layout.addWidget(reason_text)
        goal_layout.addWidget(period_text)
        goal_layout.addLayout(buttons_layout)

        goal_widget.setLayout(goal_layout)
        self.tasks_container.addWidget(goal_widget)

    def create_task_widget(self, task_text, task_index):
        task_widget = QWidget()
        task_layout = QHBoxLayout()

        # Проверяем выполнена ли задача
        is_completed = self.is_task_completed(task_index)

        # Создаем кликабельную метку для отметки выполнения
        task_label = QLabel(task_text)
        task_label.setWordWrap(True)
        task_label.mousePressEvent = lambda event: self.toggle_task_completion(task_index)

        # Стиль для выполненных задач
        if is_completed:
            task_label.setStyleSheet("""
                QLabel {
                    text-decoration: line-through;
                    color: gray;
                    background-color: #e8f5e8;
                    padding: 5px;
                    border-radius: 3px;
                }
            """)
        else:
            task_label.setStyleSheet("""
                QLabel {
                    padding: 5px;
                    border-radius: 3px;
                }
                QLabel:hover {
                    background-color: #f0f0f0;
                }
            """)

        # Проверяем есть ли заметка для этой задачи
        has_note = self.has_note_for_task(task_index)
        note_indicator = " 📌" if has_note else ""

        note_btn = QPushButton('Заметка' + note_indicator)
        delete_btn = QPushButton('Удалить')
        modify_btn = QPushButton('Изменить')
        notifications_btn = QPushButton('🔔')

        # подключаем кнопки к функциям
        note_btn.clicked.connect(lambda: self.show_note_dialog(task_index))
        delete_btn.clicked.connect(lambda: self.delete_task(task_index))
        modify_btn.clicked.connect(lambda: self.modify_task(task_index))
        notifications_btn.clicked.connect(lambda: self.set_task_notifications(task_index))

        task_layout.addWidget(task_label)
        task_layout.addWidget(note_btn)
        task_layout.addWidget(notifications_btn)
        task_layout.addWidget(modify_btn)
        task_layout.addWidget(delete_btn)

        task_widget.setLayout(task_layout)
        self.tasks_container.addWidget(task_widget)

    def is_task_completed(self, task_index):
        """Проверяет, выполнена ли задача"""
        if self.current_date in self.completed_tasks:
            return self.completed_tasks[self.current_date].get(str(task_index), False)
        return False

    def toggle_task_completion(self, task_index):
        """Отмечает задачу как выполненную/невыполненную"""
        if self.current_date not in self.completed_tasks:
            self.completed_tasks[self.current_date] = {}

        current_state = self.is_task_completed(task_index)
        self.completed_tasks[self.current_date][str(task_index)] = not current_state
        self.display_tasks()

    def has_note_for_task(self, task_index):
        # проверяет, есть ли заметка для задачи
        if self.current_date in self.notes:
            return task_index in self.notes[self.current_date]
        return False

    def show_note_dialog(self, task_index):
        # показывает диалог для редактирования заметки
        # получаем текущую заметку если есть
        current_note = ""
        if self.current_date in self.notes and task_index in self.notes[self.current_date]:
            current_note = self.notes[self.current_date][task_index]

        # получаем текст задачи для отображения в заголовке
        task_text = self.tasks[self.current_date][task_index]
        if task_text.startswith("🎯 "):
            task_display = task_text.split(" | ")[0]
        else:
            task_display = task_text

        dialog = NoteDialog(self, task_display, current_note, task_index)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            note_text = dialog.get_note_text()
            if note_text.strip():
                # сохраняем заметку
                if self.current_date not in self.notes:
                    self.notes[self.current_date] = {}
                self.notes[self.current_date][task_index] = note_text.strip()
            else:
                # удаляем заметку если текст пустой
                if self.current_date in self.notes and task_index in self.notes[self.current_date]:
                    del self.notes[self.current_date][task_index]

            # обновляем отображение чтобы показать/скрыть индикатор заметки
            self.display_tasks()

    def show_goal_note_dialog(self, goal_id):
        # показывает диалог для заметки цели
        current_note = self.goals[goal_id].get('note', '')
        goal_text = self.goals[goal_id]['goal_text']

        dialog = NoteDialog(self, f"Цель: {goal_text}", current_note, goal_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            note_text = dialog.get_note_text()
            self.goals[goal_id]['note'] = note_text.strip()

    def stop_goal(self, goal_id):
        # останавливает цель
        reply = QMessageBox.question(self, 'Остановить цель',
                                     'Вы уверены, что хотите остановить эту цель?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            # устанавливаем дату окончания на сегодня
            self.goals[goal_id]['end_date'] = QDate.currentDate().toString(Qt.DateFormat.ISODate)
            self.display_tasks()

    def edit_goal_notifications(self, goal_id):
        # редактирует настройки уведомлений для цели
        dialog = GoalNotificationDialog(self, self.goals[goal_id])
        if dialog.exec() == QDialog.DialogCode.Accepted:
            settings = dialog.get_notification_settings()
            self.goals[goal_id]['notifications'] = settings

    def set_task_notifications(self, task_index):  # ЗАДАЧА-БАЗА
        # устанавливает уведомления для обычной задачи
        dialog = TaskNotificationDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            settings = dialog.get_notification_settings()
            if self.current_date not in self.notifications:
                self.notifications[self.current_date] = {}
            self.notifications[self.current_date][task_index] = settings

    def add_task(self):
        # сначала показывает выбор типа задачи
        self.task_type_window = TaskTypeDialog(self)
        self.task_type_window.show()

    def delete_task(self, task_index):  # удаление чего-то
        if self.current_date in self.tasks:
            tasks = self.tasks[self.current_date]
            if 0 <= task_index < len(tasks):
                # удаляем также связанную заметку
                if self.current_date in self.notes and task_index in self.notes[self.current_date]:
                    del self.notes[self.current_date][task_index]

                # удаляем уведомления
                if self.current_date in self.notifications and task_index in self.notifications[self.current_date]:
                    del self.notifications[self.current_date][task_index]

                # удаляем информацию о выполнении
                if self.current_date in self.completed_tasks and str(task_index) in self.completed_tasks[
                    self.current_date]:
                    del self.completed_tasks[self.current_date][str(task_index)]

                tasks.pop(task_index)
                if not tasks:
                    del self.tasks[self.current_date]
                self.display_tasks()
                self.calendar.update()  # обновляем календарь, чтобы убрать маркер если задач не осталось

    def modify_task(self, task_index):  # редактирование чего-то
        if self.current_date in self.tasks:
            tasks = self.tasks[self.current_date]
            if 0 <= task_index < len(tasks):
                old_task = tasks[task_index]
                # определяем тип задачи для редактирования
                if old_task.startswith("🎯 "):
                    # цель - используем диалог для целей
                    self.child_window = GoalTaskDialog(self, old_task, task_index)
                else:
                    # обычная задача - используем обычный диалог
                    self.child_window = CalendarApp_2(self, old_task, task_index)
                self.child_window.show()

    def save_task(self, task_text, task_index=None):
        if self.current_date not in self.tasks:
            self.tasks[self.current_date] = []

        if task_index is None:
            # добавление новой задачи
            self.tasks[self.current_date].append(task_text)
        else:
            # изменение существующей задачи
            if 0 <= task_index < len(self.tasks[self.current_date]):
                self.tasks[self.current_date][task_index] = task_text

        self.display_tasks()
        self.calendar.update()  # обновляем календарь, чтобы показать маркер

    def save_goal(self, goal_data):
        # сохраняет цель с длительным периодом
        goal_id = str(len(self.goals) + 1)
        goal_data['id'] = goal_id
        self.goals[goal_id] = goal_data
        self.display_tasks()

    def check_notifications(self):
        # проверяет и показывает уведомления
        current_time = QDateTime.currentDateTime()

        # проверяет уведомления для целей
        for goal_id, goal_data in self.goals.items():
            if self.should_show_goal_notification(goal_data, current_time):
                self.show_goal_notification(goal_data)

        # проверяет уведомления для обычных задач
        for date_str, tasks_notifications in self.notifications.items():
            for task_index, settings in tasks_notifications.items():
                if self.should_show_task_notification(date_str, task_index, settings, current_time):
                    self.show_task_notification(date_str, task_index)

    def should_show_goal_notification(self, goal_data, current_time):
        # проверяет, нужно ли показать уведомление для цели
        if 'notifications' not in goal_data:
            return False

        settings = goal_data['notifications']
        if not settings.get('enabled', False):
            return False

        # проверяем период цели
        end_date = QDate.fromString(goal_data['end_date'], Qt.DateFormat.ISODate)
        if QDate.currentDate() > end_date:
            return False

        # здесь можно добавить логику для разных интервалов уведомлений
        # пока просто показываем раз в день
        last_notification = goal_data.get('last_notification')
        if last_notification:
            last_time = QDateTime.fromString(last_notification, Qt.DateFormat.ISODate)
            if last_time.daysTo(current_time) < 1:
                return False

        goal_data['last_notification'] = current_time.toString(Qt.DateFormat.ISODate)
        return True

    def should_show_task_notification(self, date_str, task_index, settings, current_time):
        # проверяет, нужно ли показать уведомление для задачи
        if not settings.get('enabled', False):
            return False

        # проверяем, не истекла ли дата задачи
        task_date = QDate.fromString(date_str, Qt.DateFormat.ISODate)
        if QDate.currentDate() > task_date:
            return False

        # проверяем частоту уведомлений (раз в день)
        last_notification = settings.get('last_notification')
        if last_notification:
            last_time = QDateTime.fromString(last_notification, Qt.DateFormat.ISODate)
            if last_time.daysTo(current_time) < 1:
                return False

        # сохраняем время последнего уведомления
        settings['last_notification'] = current_time.toString(Qt.DateFormat.ISODate)
        return True

    def show_goal_notification(self, goal_data):
        # показывает уведомление для цели
        message = f"🎯 Напоминание о цели:\n\n{goal_data['goal_text']}\n\n💡 Почему это важно:\n{goal_data['reason_text']}"
        QMessageBox.information(self, "Напоминание о цели", message)

    def show_task_notification(self, date_str, task_index):
        # показывает уведомление для задачи
        task_text = self.tasks[date_str][task_index]
        message = f"📝 Напоминание о задаче:\n\n{task_text}"
        QMessageBox.information(self, "Напоминание о задаче", message)

    def get_dates_with_tasks(self):
        # возвращает список дат, на которых есть задачи
        return list(self.tasks.keys())


class CustomCalendarWidget(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent

    def paintCell(self, painter, rect, date):
        super().paintCell(painter, rect, date)

        # проверяем, есть ли задачи на эту дату
        date_str = date.toString(Qt.DateFormat.ISODate)
        if date_str in self.parent_app.tasks and self.parent_app.tasks[date_str]:
            # рисуем маленький кружок в правом нижнем углу
            dot_size = 6
            dot_rect = rect.adjusted(
                rect.width() - dot_size - 2,
                rect.height() - dot_size - 2,
                -2, -2
            )

            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QBrush(QColor(255, 0, 0)))  # красный кружок
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(dot_rect)
            painter.restore()


class NoteDialog(QDialog):
    def __init__(self, parent, task_text, current_note, item_id):
        super().__init__(parent)
        self.item_id = item_id
        self.initUI(task_text, current_note)

    def initUI(self, task_text, current_note):
        self.setWindowTitle(f"Заметка: {task_text}")
        self.resize(500, 400)

        layout = QVBoxLayout()

        # поле для заметки
        self.note_label = QLabel("Заметка:")
        self.note_input = QTextEdit()
        self.note_input.setPlainText(current_note)
        self.note_input.setPlaceholderText("Введите ваши заметки здесь...")

        # создаём кнопки 2
        buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отмена")
        self.clear_btn = QPushButton("Очистить")

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.clear_btn.clicked.connect(self.clear_note)

        buttons_layout.addWidget(self.clear_btn)
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.save_btn)

        layout.addWidget(self.note_label)
        layout.addWidget(self.note_input)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def clear_note(self):
        self.note_input.clear()

    def get_note_text(self):
        return self.note_input.toPlainText()


class GoalNotificationDialog(QDialog):
    def __init__(self, parent, goal_data):
        super().__init__(parent)
        self.goal_data = goal_data
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Настройка уведомлений для цели")
        self.resize(400, 300)

        layout = QVBoxLayout()

        # группа настроек уведомлений
        notification_group = QGroupBox("Настройки уведомлений")
        notification_layout = QVBoxLayout()

        # включение уведомлений
        self.enable_checkbox = QCheckBox("Включить уведомления")
        self.enable_checkbox.setChecked(self.goal_data.get('notifications', {}).get('enabled', False))

        # интервал уведомлений
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Интервал:"))
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["Ежедневно", "Каждые 2 дня", "Еженедельно"])
        interval_layout.addWidget(self.interval_combo)
        interval_layout.addStretch()

        # время уведомления
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Время:"))
        self.time_combo = QComboBox()
        for hour in range(8, 22):
            self.time_combo.addItem(f"{hour:02d}:00")
        time_layout.addWidget(self.time_combo)
        time_layout.addStretch()

        notification_layout.addWidget(self.enable_checkbox)
        notification_layout.addLayout(interval_layout)
        notification_layout.addLayout(time_layout)
        notification_group.setLayout(notification_layout)

        # создаём кнопки 3
        buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отмена")

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.save_btn)

        layout.addWidget(notification_group)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def get_notification_settings(self):
        return {
            'enabled': self.enable_checkbox.isChecked(),
            'interval': self.interval_combo.currentText(),
            'time': self.time_combo.currentText()
        }


class TaskNotificationDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Настройка уведомлений для задачи")
        self.resize(400, 250)

        layout = QVBoxLayout()

        # группа настроек уведомлений
        notification_group = QGroupBox("Настройки уведомлений")
        notification_layout = QVBoxLayout()

        # включение уведомлений
        self.enable_checkbox = QCheckBox("Включить уведомления")
        self.enable_checkbox.setChecked(True)

        # количество напоминаний в день
        reminders_layout = QHBoxLayout()
        reminders_layout.addWidget(QLabel("Напоминаний в день:"))
        self.reminders_spin = QSpinBox()
        self.reminders_spin.setRange(1, 5)
        self.reminders_spin.setValue(1)
        reminders_layout.addWidget(self.reminders_spin)
        reminders_layout.addStretch()

        # период напоминаний
        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel("Период:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["1 день", "3 дня", "Неделя", "Месяц"])
        period_layout.addWidget(self.period_combo)
        period_layout.addStretch()

        notification_layout.addWidget(self.enable_checkbox)
        notification_layout.addLayout(reminders_layout)
        notification_layout.addLayout(period_layout)
        notification_group.setLayout(notification_layout)

        # создаём кнопки 4
        buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отмена")

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.save_btn)

        layout.addWidget(notification_group)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def get_notification_settings(self):
        return {
            'enabled': self.enable_checkbox.isChecked(),
            'reminders_per_day': self.reminders_spin.value(),
            'period': self.period_combo.currentText()
        }


class TaskTypeDialog(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Выбор типа задачи")
        self.resize(300, 200)
        layout = QVBoxLayout()

        # заголовок
        title_label = QLabel("Какую задачу вы хотите создать?")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 20px;")

        # кнопки выбора типа задачи 5
        self.btn_basic = QPushButton('📝 Задача-база')
        self.btn_goal = QPushButton('🎯 Задача-цель')

        # настраиваем кнопки
        self.btn_basic.setMinimumHeight(50)
        self.btn_goal.setMinimumHeight(50)

        self.btn_basic.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                padding: 10px;
                background-color: rgb(0, 0, 255);
                border: 2px solid #90caf9;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #bbdefb;
            }
        """)

        self.btn_goal.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                padding: 10px;
                background-color: rgb(0, 0, 255);
                border: 2px solid #ce93d8;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e1bee7;
            }
        """)

        # подключаем кнопки
        self.btn_basic.clicked.connect(self.create_basic_task)
        self.btn_goal.clicked.connect(self.create_goal_task)

        layout.addWidget(title_label)
        layout.addWidget(self.btn_basic)
        layout.addWidget(self.btn_goal)
        layout.addStretch()

        self.setLayout(layout)
        self.center()

    def center(self):
        fg = self.frameGeometry()
        sc = self.screen().availableGeometry().center()
        fg.moveCenter(sc)
        self.move(fg.topLeft())

    def create_basic_task(self):
        self.close()
        self.parent.child_window = CalendarApp_2(self.parent)
        self.parent.child_window.show()

    def create_goal_task(self):
        self.close()
        self.parent.child_window = GoalTaskDialog(self.parent)
        self.parent.child_window.show()


class CalendarApp_2(QWidget):
    def __init__(self, parent, old_task="", task_index=None):
        super().__init__()
        self.parent = parent
        self.old_task = old_task
        self.task_index = task_index
        self.initUI()

    def initUI(self):
        if self.old_task:
            self.setWindowTitle("Изменение задачи-базы")
        else:
            self.setWindowTitle("Создание задачи-базы")

        self.resize(400, 200)
        layout = QVBoxLayout()

        # ввод задачи
        self.name_label = QLabel("Введите название задачи:")
        self.name_input = QLineEdit()
        self.name_input.setText(self.old_task)

        # кнопки 6
        buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отмена")

        self.save_btn.clicked.connect(self.save_task)
        self.cancel_btn.clicked.connect(self.close)

        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.cancel_btn)

        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        self.center()

    def center(self):
        fg = self.frameGeometry()
        sc = self.screen().availableGeometry().center()
        fg.moveCenter(sc)
        self.move(fg.topLeft())

    def save_task(self):
        task_text = self.name_input.text().strip()
        if task_text:
            self.parent.save_task(task_text, self.task_index)
            self.close()
        else:
            QMessageBox.warning(self, "Ошибка", "Введите название задачи!")


class GoalTaskDialog(QWidget):
    def __init__(self, parent, old_task="", task_index=None):
        super().__init__()
        self.parent = parent
        self.old_task = old_task
        self.task_index = task_index
        self.initUI()

    def initUI(self):
        if self.old_task:
            self.setWindowTitle("Изменение задачи-цели")
            # извлекаем цель и причину из старой задачи
            if " | Почему важно: " in self.old_task:
                parts = self.old_task.split(" | Почему важно: ")
                goal_text = parts[0].replace("🎯 ", "")
                reason_text = parts[1]
            else:
                goal_text = self.old_task.replace("🎯 ", "")
                reason_text = ""
        else:
            self.setWindowTitle("Создание задачи-цели")
            goal_text = ""
            reason_text = ""

        self.resize(500, 550)
        layout = QVBoxLayout()

        # ввод цели
        self.goal_label = QLabel("Сформулируйте вашу цель одним предложением:")
        self.goal_input = QTextEdit()
        self.goal_input.setPlainText(goal_text)
        self.goal_input.setPlaceholderText("Например: Я хочу выучить английский язык на уровне B1 к концу этого года")
        self.goal_input.setMaximumHeight(80)

        # ввод причины
        self.reason_label = QLabel("Почему это важно для вас? (сформулируйте одним предложением) *")
        self.reason_input = QTextEdit()
        self.reason_input.setPlainText(reason_text)
        self.reason_input.setPlaceholderText(
            "Например: Это поможет мне получить повышение на работе и свободно общаться в путешествиях")
        self.reason_input.setMaximumHeight(80)

        # период цели
        period_group = QGroupBox("Период цели")
        period_layout = QVBoxLayout()

        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Длительность:"))
        self.duration_combo = QComboBox()
        self.duration_combo.addItems(["2 месяца", "3 месяца", "6 месяцев", "1 год"])
        duration_layout.addWidget(self.duration_combo)
        duration_layout.addStretch()

        period_layout.addLayout(duration_layout)
        period_group.setLayout(period_layout)

        # настройки уведомлений
        notification_group = QGroupBox("Настройки уведомлений")
        notification_layout = QVBoxLayout()

        self.notification_checkbox = QCheckBox("Включить ежедневные напоминания")
        self.notification_checkbox.setChecked(True)

        notification_hint = QLabel("Вы будете получать напоминания о цели и причине её важности")
        notification_hint.setStyleSheet("color: #666; font-size: 10px;")

        notification_layout.addWidget(self.notification_checkbox)
        notification_layout.addWidget(notification_hint)
        notification_group.setLayout(notification_layout)

        # подсказки (для правильной формулировки)
        goal_hint = QLabel(
            "* Цель должна быть сформулирована одним полным предложением (не словом или словосочетанием)")
        goal_hint.setStyleSheet("color: #666; font-size: 10px;")

        reason_hint = QLabel("* Причина должна быть сформулирована одним полным предложением")
        reason_hint.setStyleSheet("color: #666; font-size: 10px;")

        # кнопки 7
        buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить цель")
        self.cancel_btn = QPushButton("Отмена")

        self.save_btn.clicked.connect(self.save_goal_task)
        self.cancel_btn.clicked.connect(self.close)

        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.cancel_btn)

        layout.addWidget(self.goal_label)  # добавление элементов цели
        layout.addWidget(self.goal_input)
        layout.addWidget(goal_hint)
        layout.addSpacing(10)  # отступ

        layout.addWidget(self.reason_label)  # добавление элементов причины
        layout.addWidget(self.reason_input)
        layout.addWidget(reason_hint)
        layout.addSpacing(10)  # отступ

        layout.addWidget(period_group)  # добавление групп настроек
        layout.addSpacing(10)
        layout.addWidget(notification_group)
        layout.addSpacing(20)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        self.center()

    def center(self):
        fg = self.frameGeometry()
        sc = self.screen().availableGeometry().center()
        fg.moveCenter(sc)
        self.move(fg.topLeft())

    def save_goal_task(self):
        goal_text = self.goal_input.toPlainText().strip()
        reason_text = self.reason_input.toPlainText().strip()

        if not goal_text:
            QMessageBox.warning(self, "Ошибка", "Введите цель!")
            return

        if not reason_text:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, ответьте на вопрос 'Почему это важно для вас?'")
            return

        # определяем период цели
        duration_map = {
            "2 месяца": 60,
            "3 месяца": 90,
            "6 месяцев": 180,
            "1 год": 365
        }
        duration_days = duration_map[self.duration_combo.currentText()]

        start_date = QDate.currentDate()
        end_date = start_date.addDays(duration_days)

        # создаём данные цели
        goal_data = {
            'goal_text': goal_text,
            'reason_text': reason_text,
            'start_date': start_date.toString(Qt.DateFormat.ISODate),
            'end_date': end_date.toString(Qt.DateFormat.ISODate),
            'notifications': {
                'enabled': self.notification_checkbox.isChecked(),
                'interval': 'daily'
            }
        }

        self.parent.save_goal(goal_data)
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CalendarApp()
    window.show()
    sys.exit(app.exec())