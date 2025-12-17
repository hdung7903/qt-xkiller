
import sys
import psutil
import datetime
import qtawesome as qta
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTableWidget, QTableWidgetItem, 
                             QPushButton, QLineEdit, QLabel, QHeaderView, 
                             QTimeEdit, QMessageBox, QListWidget, QListWidgetItem, QSplitter,
                             QTabWidget, QSpinBox, QGroupBox, QGridLayout,
                             QSystemTrayIcon, QMenu, QStyle, QPlainTextEdit,
                             QCheckBox, QApplication)
from PyQt6.QtCore import Qt, QTimer, QTime, QDate, QDateTime, QSize, QEvent
from PyQt6.QtGui import QIcon, QAction
from qt_material import apply_stylesheet

from .constants import HARD_WHITELIST

class TaskKillerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Qt-XKiller")
        self.resize(1100, 800)
        self.setWindowIcon(qta.icon('fa5s.robot', color='white'))

        # Data structures
        self.scheduled_tasks = [] 
        self.current_selection = None
        self.current_processes = []
        
        # Whitelist
        self.user_whitelist = set()
        
        # System Tray Setup
        self.setup_system_tray()

        # Scheduler State
        self.scheduler_enabled = True

        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # UI Components
        self.setup_ui(main_layout)

        # Timers
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_scheduled_tasks)
        self.check_timer.start(1000) 

        # Initial Load
        self.refresh_process_list()
        self.refresh_whitelist_ui()
        self.log_message("INFO", "Application started. Scheduler active.")

    def setup_ui(self, main_layout):
        # --- Top Bar ---
        top_bar_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search process by name or PID...")
        self.search_bar.setClearButtonEnabled(True)
        self.search_bar.textChanged.connect(self.filter_processes)
        
        self.refresh_btn = QPushButton("Refresh List")
        self.refresh_btn.setIcon(qta.icon('fa5s.sync-alt', color='white'))
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.refresh_process_list)

        top_bar_layout.addWidget(QLabel("Process Filter:"))
        top_bar_layout.addWidget(self.search_bar)
        top_bar_layout.addWidget(self.refresh_btn)
        main_layout.addLayout(top_bar_layout)

        # --- Splitter ---
        splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(splitter)

        # --- Process Table ---
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(4)
        self.process_table.setHorizontalHeaderLabels(["PID", "Name", "Status", "Memory (MB)"])
        self.process_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.process_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.process_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.process_table.itemSelectionChanged.connect(self.on_process_selected)
        splitter.addWidget(self.process_table)

        # --- Bottom Control Area ---
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        # Action Panel
        action_group = QGroupBox("Action Panel")
        action_layout = QVBoxLayout(action_group)
        
        self.selected_label = QLabel("No process selected")
        self.selected_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #00d0ff;")
        action_layout.addWidget(self.selected_label)

        self.tabs = QTabWidget()
        self.tabs.setEnabled(False)
        
        # Tabs...
        self.setup_tabs()
        
        action_layout.addWidget(self.tabs)
        bottom_layout.addWidget(action_group, 2)

        # Info Panel
        info_group = QGroupBox("System Status")
        info_layout = QVBoxLayout(info_group)
        self.info_tabs = QTabWidget()
        
        self.setup_info_tabs()

        info_layout.addWidget(self.info_tabs)
        bottom_layout.addWidget(info_group, 3)

        splitter.addWidget(bottom_widget)
        splitter.setSizes([450, 300])

    def setup_tabs(self):
        # 1. Instant Kill
        tab_instant = QWidget()
        lay_instant = QVBoxLayout(tab_instant)
        self.btn_kill_now = QPushButton("TERMINATE IMMEDIATELY")
        self.btn_kill_now.setIcon(qta.icon('fa5s.skull-crossbones', color='white'))
        self.btn_kill_now.setIconSize(QSize(24, 24))
        self.btn_kill_now.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold; padding: 15px;")
        self.btn_kill_now.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_kill_now.clicked.connect(self.kill_process_now)
        lay_instant.addWidget(QLabel("Warning: Stops process immediately."))
        lay_instant.addWidget(self.btn_kill_now)
        lay_instant.addStretch()
        self.tabs.addTab(tab_instant, qta.icon('fa5s.bolt', color='white'), "Instant")

        # 2. Timer
        tab_countdown = QWidget()
        lay_countdown = QGridLayout(tab_countdown)
        self.spin_hours = QSpinBox()
        self.spin_hours.setRange(0, 24)
        self.spin_minutes = QSpinBox()
        self.spin_minutes.setRange(0, 59)
        self.spin_minutes.setValue(10)
        lay_countdown.addWidget(QLabel("Hours:"), 0, 0)
        lay_countdown.addWidget(self.spin_hours, 0, 1)
        lay_countdown.addWidget(QLabel("Minutes:"), 1, 0)
        lay_countdown.addWidget(self.spin_minutes, 1, 1)
        self.btn_schedule_timer = QPushButton("Schedule Countdown")
        self.btn_schedule_timer.setIcon(qta.icon('fa5s.hourglass-start', color='white'))
        self.btn_schedule_timer.clicked.connect(self.schedule_timer_kill)
        lay_countdown.addWidget(self.btn_schedule_timer, 2, 0, 1, 2)
        lay_countdown.setRowStretch(3, 1)
        self.tabs.addTab(tab_countdown, qta.icon('fa5s.stopwatch', color='white'), "Timer")

        # 3. Clock
        tab_time = QWidget()
        lay_time = QVBoxLayout(tab_time)
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm:ss")
        self.time_edit.setTime(QTime.currentTime().addSecs(60))
        self.btn_schedule_time = QPushButton("Schedule Time")
        self.btn_schedule_time.setIcon(qta.icon('fa5s.calendar-times', color='white'))
        self.btn_schedule_time.clicked.connect(self.schedule_time_kill)
        lay_time.addWidget(QLabel("Select Time:"))
        lay_time.addWidget(self.time_edit)
        lay_time.addWidget(self.btn_schedule_time)
        lay_time.addStretch()
        self.tabs.addTab(tab_time, qta.icon('fa5s.clock', color='white'), "Clock")

        # 4. Whitelist
        self.tab_whitelist = QWidget()
        lay_whitelist = QVBoxLayout(self.tab_whitelist)
        self.btn_add_whitelist = QPushButton("Add to Whitelist")
        self.btn_add_whitelist.setIcon(qta.icon('fa5s.shield-alt', color='white'))
        self.btn_add_whitelist.clicked.connect(self.add_current_to_whitelist)
        lay_whitelist.addWidget(QLabel("Protect this process from being killed."))
        lay_whitelist.addWidget(self.btn_add_whitelist)
        lay_whitelist.addStretch()
        self.tabs.addTab(self.tab_whitelist, qta.icon('fa5s.shield-alt', color='white'), "Whitelist")

    def setup_info_tabs(self):
        # 1. Queue
        queue_tab = QWidget()
        queue_layout = QVBoxLayout(queue_tab)
        self.tasks_list = QListWidget()
        self.tasks_list.itemDoubleClicked.connect(self.cancel_task)
        queue_layout.addWidget(self.tasks_list)
        btn_cancel = QPushButton("Cancel Selected Task")
        btn_cancel.setIcon(qta.icon('fa5s.ban', color='white'))
        btn_cancel.clicked.connect(self.cancel_selected_task)
        queue_layout.addWidget(btn_cancel)
        self.info_tabs.addTab(queue_tab, "Scheduled Queue")

        # 2. Whitelist View
        whitelist_tab = QWidget()
        wl_layout = QVBoxLayout(whitelist_tab)
        self.whitelist_list = QListWidget()
        wl_layout.addWidget(self.whitelist_list)
        btn_remove_wl = QPushButton("Remove from Whitelist")
        btn_remove_wl.clicked.connect(self.remove_from_whitelist)
        wl_layout.addWidget(btn_remove_wl)
        self.info_tabs.addTab(whitelist_tab, "Whitelist Rules")
        
        # 3. Logs
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        self.log_viewer = QPlainTextEdit()
        self.log_viewer.setReadOnly(True)
        log_layout.addWidget(self.log_viewer)
        self.info_tabs.addTab(log_tab, "Logs")

    def setup_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(qta.icon('fa5s.robot', color='white'))
        
        tray_menu = QMenu()
        
        action_show = QAction("Show", self)
        action_show.triggered.connect(self.show)
        tray_menu.addAction(action_show)
        
        self.action_enable_scheduler = QAction("Enable Scheduler", self)
        self.action_enable_scheduler.setCheckable(True)
        self.action_enable_scheduler.setChecked(True)
        self.action_enable_scheduler.triggered.connect(self.toggle_scheduler)
        tray_menu.addAction(self.action_enable_scheduler)
        
        tray_menu.addSeparator()
        
        action_quit = QAction("Quit", self)
        action_quit.triggered.connect(self.force_quit)
        tray_menu.addAction(action_quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.log_message("INFO", "Minimized to tray.")
        self.tray_icon.showMessage("Qt-XKiller", "Application running in background", QSystemTrayIcon.MessageIcon.Information, 2000)

    def force_quit(self):
        QApplication.quit()

    def toggle_scheduler(self):
        self.scheduler_enabled = self.action_enable_scheduler.isChecked()
        status = "enabled" if self.scheduler_enabled else "disabled"
        self.log_message("INFO", f"Scheduler {status}.")

    def refresh_process_list(self):
        self.process_table.setRowCount(0)
        self.current_processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'status', 'memory_info']):
                try:
                    info = proc.info
                    self.current_processes.append(info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except Exception as e:
            self.log_message("WARNING", f"Error listing processes: {e}")
        self.filter_processes()

    def filter_processes(self):
        query = self.search_bar.text().lower()
        self.process_table.setRowCount(0)
        row = 0
        for p in self.current_processes:
            p_name = p['name'] if p['name'] else ""
            p_pid = str(p['pid'])
            if query in p_name.lower() or query in p_pid:
                self.process_table.insertRow(row)
                self.process_table.setItem(row, 0, QTableWidgetItem(p_pid))
                self.process_table.setItem(row, 1, QTableWidgetItem(p_name))
                self.process_table.setItem(row, 2, QTableWidgetItem(p['status']))
                mem_mb = p['memory_info'].rss / (1024 * 1024) if p['memory_info'] else 0
                self.process_table.setItem(row, 3, QTableWidgetItem(f"{mem_mb:.2f} MB"))
                row += 1

    def on_process_selected(self):
        selected_items = self.process_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            pid = int(self.process_table.item(row, 0).text())
            name = self.process_table.item(row, 1).text()
            self.current_selection = {'pid': pid, 'name': name}
            self.selected_label.setText(f"{name} (PID: {pid})")
            self.tabs.setEnabled(True)
            self.check_if_whitelisted()
        else:
            self.current_selection = None
            self.selected_label.setText("No process selected")
            self.tabs.setEnabled(False)

    def check_if_whitelisted(self):
        if not self.current_selection: return False
        name = self.current_selection['name'].lower()
        if name in HARD_WHITELIST or name in self.user_whitelist:
            self.selected_label.setText(self.selected_label.text() + " [WHITELISTED]")
            self.selected_label.setStyleSheet("color: #00e676; font-weight: bold;")
            return True
        else:
            self.selected_label.setStyleSheet("color: #00d0ff; font-weight: bold;") 
            return False

    def is_protected(self, name):
        name = name.lower()
        return name in HARD_WHITELIST or name in self.user_whitelist

    def add_current_to_whitelist(self):
        if not self.current_selection: return
        name = self.current_selection['name'].lower()
        if name in HARD_WHITELIST:
             QMessageBox.information(self, "Info", "This process is already in the System Hard Whitelist.")
             return
        if name not in self.user_whitelist:
            self.user_whitelist.add(name)
            self.refresh_whitelist_ui()
            self.log_message("INFO", f"Added '{name}' to user whitelist.")
            self.check_if_whitelisted()
        else:
            self.log_message("INFO", f"'{name}' is already whitelisted.")

    def remove_from_whitelist(self):
        row = self.whitelist_list.currentRow()
        if row >= 0:
            item = self.whitelist_list.item(row)
            name = item.text()
            if name in HARD_WHITELIST:
                QMessageBox.warning(self, "Restricted", "Cannot remove System Hard Whitelist items.")
                return
            self.user_whitelist.remove(name)
            self.refresh_whitelist_ui()
            self.log_message("INFO", f"Removed '{name}' from user whitelist.")
            if self.current_selection and self.current_selection['name'].lower() == name:
                self.check_if_whitelisted()

    def refresh_whitelist_ui(self):
        self.whitelist_list.clear()
        for w in sorted(HARD_WHITELIST):
            item = QListWidgetItem(f"[SYSTEM] {w}")
            item.setForeground(Qt.GlobalColor.gray)
            self.whitelist_list.addItem(item)
        for w in sorted(self.user_whitelist):
            self.whitelist_list.addItem(w)

    def kill_process_now(self):
        if not self.current_selection: return
        self.execute_kill({'pid': self.current_selection['pid'], 'name': self.current_selection['name'], 'type': 'instant'})

    def schedule_timer_kill(self):
        if not self.current_selection: return
        hours = self.spin_hours.value()
        minutes = self.spin_minutes.value()
        if hours == 0 and minutes == 0:
            QMessageBox.warning(self, "Invalid Time", "At least 1 minute duration required.")
            return
        target_time = QDateTime.currentDateTime().addSecs(hours * 3600 + minutes * 60)
        self.add_task(target_time, "Timer")

    def schedule_time_kill(self):
        if not self.current_selection: return
        target_qtime = self.time_edit.time()
        now = QDateTime.currentDateTime()
        target_time = QDateTime(now.date(), target_qtime)
        if target_time < now:
             QMessageBox.warning(self, "Time Passed", "Time already passed today.")
             return
        self.add_task(target_time, "Clock")

    def add_task(self, target_datetime, mode_str):
        pid = self.current_selection['pid']
        name = self.current_selection['name']
        if self.is_protected(name):
             reply = QMessageBox.question(self, "Protected Process", 
                                          f"'{name}' is on the whitelist. Are you SUPER sure you want to schedule a kill?",
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
             if reply == QMessageBox.StandardButton.No:
                 return

        time_str = target_datetime.toString("HH:mm:ss")
        display_str = f"[{mode_str}] Kill '{name}' ({pid}) at {time_str}"
        self.tasks_list.addItem(display_str)
        
        task = {
            'pid': pid,
            'name': name,
            'target_time': target_datetime,
            'list_item': self.tasks_list.item(self.tasks_list.count() - 1)
        }
        self.scheduled_tasks.append(task)
        self.process_table.clearSelection()
        self.log_message("INFO", f"Scheduled kill for '{name}' ({pid}) at {time_str}")

    def check_scheduled_tasks(self):
        if not self.scheduler_enabled: return
        now = QDateTime.currentDateTime()
        for task in self.scheduled_tasks[:]:
            if now >= task['target_time']:
                self.execute_kill(task)

    def execute_kill(self, task):
        pid = task['pid']
        name = task['name']
        is_instant = task.get('type') == 'instant'
        if self.is_protected(name):
            msg = f"Prevented kill of whitelisted process: {name} ({pid})"
            self.log_message("WARNING", msg)
            if is_instant:
                 QMessageBox.warning(self, "Blocked", msg)
            else:
                 self.tray_icon.showMessage("Safety Block", msg, QSystemTrayIcon.MessageIcon.Warning, 3000)
            self.cleanup_task(task)
            return

        try:
            if psutil.pid_exists(pid):
                p = psutil.Process(pid)
                p.terminate()
                try:
                   p.wait(timeout=3)
                except psutil.TimeoutExpired:
                   p.kill()
                success_msg = f"Process {name} ({pid}) was killed."
                self.log_message("CRITICAL", success_msg)
                if not is_instant:
                    self.tray_icon.showMessage("Qt-XKiller", success_msg, QSystemTrayIcon.MessageIcon.Critical, 5000)
            else:
                self.log_message("INFO", f"Process {name} ({pid}) not found or already dead.")
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            err_msg = f"Failed to kill {name} ({pid}): {e}"
            self.log_message("WARNING", err_msg)
            if not is_instant:
                 self.tray_icon.showMessage("Qt-XKiller Error", err_msg, QSystemTrayIcon.MessageIcon.Warning, 4000)

        self.cleanup_task(task)
        self.refresh_process_list()

    def cleanup_task(self, task):
        if 'list_item' in task:
            try:
                row = self.tasks_list.row(task['list_item'])
                self.tasks_list.takeItem(row)
            except: pass
            if task in self.scheduled_tasks:
                self.scheduled_tasks.remove(task)

    def cancel_selected_task(self):
        row = self.tasks_list.currentRow()
        if row >= 0:
            item = self.tasks_list.item(row)
            self.cancel_task(item)

    def cancel_task(self, item):
        for task in self.scheduled_tasks:
            if task['list_item'] == item:
                self.scheduled_tasks.remove(task)
                row = self.tasks_list.row(item)
                self.tasks_list.takeItem(row)
                self.log_message("INFO", f"Cancelled task for {task['name']}")
                break
    
    def log_message(self, level, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{level}] {message}"
        self.log_viewer.appendPlainText(formatted)
