from PyQt5.QtCore import Qt, QObject, QEvent
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, \
    QGridLayout, QButtonGroup, QHBoxLayout, QLineEdit, QCheckBox, QRadioButton, QMessageBox, QFormLayout, QDialog

from utils.utils import Logger
import warnings


class AssignmentFramePHP(Logger, QWidget):
    name = "AssignmentFramePHP"

    def __init__(self, parent, param):

        # noinspection PyArgumentList
        super().__init__(parent=parent)
        
        self.param = param

        self.layout = QVBoxLayout()

        self.next_button = QPushButton("Next")
        self.previous_button = QPushButton("Previous")
        self.scan_button = QPushButton("Look for new participants...")
        self.erase_sql_tables_button = QPushButton("Erase tables...")

        # Window popping to erase sql tables
        self.erase_sql_tables_window = QDialog(self)
        self.erase_sql_tables_window.setLayout(QVBoxLayout())
        self.erase_sql_tables_window.setWindowTitle("Erase tables")
        self.cancel_button = QPushButton("Cancel")
        self.ok_button = QPushButton("Ok")
        self.tables_check_boxes = {}
        self.form_layout = QFormLayout()

        self.group = QButtonGroup()

        self.group.addButton(self.previous_button)
        self.group.addButton(self.next_button)
        self.group.addButton(self.scan_button)
        self.group.addButton(self.erase_sql_tables_button)


        self.parameters = dict()

        self.error = None

        self.setup_done = False

        self.setup()

    def setup(self):

        # noinspection PyUnusedLocal
        roles = \
            ["firm" for i in range(self.param["game"]["n_firms"])] \
            + ["customer" for i in range(self.param["game"]["n_customers"])]

        n_agents = len(roles)

        labels = ("Name", "Firm " + " Customer", "Bot")

        # noinspection PyUnusedLocal
        self.parameters["assign"] = [[] for i in range(n_agents)]

        self.new_setup(n_agents=n_agents, roles=roles)
        
        # --------- fill layout ----------------------------------- #

        self.fill_layout(labels, n_agents)

        self.fill_erase_sql_tables_window(self.param["sql_tables"]["table_names"])

        # noinspection PyUnresolvedReferences
        self.next_button.clicked.connect(self.push_next_button)
        # noinspection PyUnresolvedReferences
        self.previous_button.clicked.connect(self.push_previous_button)
        # noinspection PyUnresolvedReferences
        self.scan_button.clicked.connect(self.push_scan_button)
        # noinspection PyUnresolvedReferences
        self.erase_sql_tables_button.clicked.connect(self.push_erase_sql_tables_button)
        # noinspection PyUnresolvedReferences
        self.ok_button.clicked.connect(self.push_ok_button)
        # noinspection PyUnresolvedReferences
        self.cancel_button.clicked.connect(self.push_cancel_button)

        self.setup_done = True

    def fill_layout(self, labels, n_agents):

        # prepare layout
        grid_layout = QGridLayout()

        # add labels
        for y, label in enumerate(labels):
            grid_layout.addWidget(QLabel(label), 0, y)

        # grid layout coordinates
        coordinates = [(x, y) for x in range(1, n_agents + 1) for y in range(len(labels))]

        # parameters index
        index = [(i, j) for i in range(n_agents) for j in range(len(labels))]

        for (i, j), (x, y) in zip(index, coordinates):
            self.parameters["assign"][i][j].add_to_grid_layout(grid_layout, x, y)

        horizontal_layout = QHBoxLayout()
        horizontal_layout.addWidget(self.previous_button, alignment=Qt.AlignCenter)
        horizontal_layout.addWidget(self.next_button, alignment=Qt.AlignCenter)
        
        self.layout.addLayout(grid_layout)
        self.layout.addLayout(horizontal_layout)
        
        self.layout.addWidget(self.scan_button, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.erase_sql_tables_button, alignment=Qt.AlignCenter)

        self.setLayout(self.layout)

    def prepare(self):

        self.next_button.setEnabled(True)
        self.next_button.setFocus()
        self.setFocus()

    def new_setup(self, n_agents, roles):

        for i in range(n_agents):
            self.parameters["assign"][i].append(IntParameter(parent=self, value="Bot", idx=i))

            self.parameters["assign"][i].append(RadioParameter(checked=roles[i]))

            self.parameters["assign"][i].append(CheckParameter(parent=self, checked=True, idx=i))

    # ---------------------- PUSH BUTTONS --------------------------------- #

    def push_next_button(self):

        warning = self.check_assignment_validity()

        if warning:
            self.show_warning(msg=warning)

        else:
            self.log("Push 'next' button.")
                  
            self.param["assignment_php"] = self.get_parameters()
            self.parent().save_parameters("assignment_php", self.param["assignment_php"])
            self.parent().set_assignment(assignment=self.param["assignment_php"])
            self.parent().show_frame_parametrization()

    def push_previous_button(self):

        if self.error:

            self.show_warning(msg=self.error)

        else:
            self.log("Push 'previous' button.")
            self.parent().show_frame_load_game_new_game_php()

    def push_scan_button(self):

        self.scan_button.setEnabled(False)

        self.parent().php_scan_button()

    # ------------------------------------------------------------------------------- #

    def update_participants(self, participants):

        for i, name in enumerate(participants):
            line_edit = self.parameters["assign"][i][0].edit  # line edit widget
            check_box = self.parameters["assign"][i][2].check_box  # check box widget

            self.enable_line_edit(line_edit=line_edit, check_box=check_box, name=name)

        self.scan_button.setEnabled(True)

    # ------------------------------------------------------------------------------- #

    def check_assignment_validity(self):

        assignment = list(enumerate(self.get_parameters()))

        for i, (server_id, role, bot) in assignment:

            for j, (other_id, other_role, other_bot) in assignment:

                if other_id == server_id and other_id != "Bot" and i != j:
                    return "Two identical ids: '{}'.".format(server_id)

    def get_parameters(self):
        return [[i.get_value(), j.get_value(), k.get_value()] for i, j, k in self.parameters["assign"]]
    
    def show_warning(self, **instructions):

        QMessageBox().warning(
            self, "", instructions["msg"],
            QMessageBox.Ok
        )

    def switch_line_edit(self, idx, from_line):

        if self.setup_done:

            # get desired widgets
            line_edit = self.parameters["assign"][idx][0].edit  # line edit widget
            check_box = self.parameters["assign"][idx][2].check_box  # check box widget
            warnings.warn("Hard variables without clear meaning here!")

            # if line edit (containing server ids) is not enabled
            if not line_edit.isEnabled():
                self.enable_line_edit(line_edit, check_box)

            # if line edit is enabled and signal comes from check box
            elif line_edit.isEnabled() and not from_line:
                self.disable_line_edit(line_edit)

    @staticmethod
    def disable_line_edit(line_edit):

        line_edit.setText("Bot")
        line_edit.setEnabled(False)
        line_edit.setStyleSheet(line_edit.greyed_style)

    @staticmethod
    def enable_line_edit(line_edit, check_box, name=""):

        check_box.setChecked(False)
        line_edit.setEnabled(True)
        line_edit.setText(name)
        line_edit.setStyleSheet("")
        line_edit.setFocus(True)

        # --------------------------------- Erase Tables Window  --------------------------------- #

    def fill_erase_sql_tables_window(self, tables):
        
        for label in tables:
            self.tables_check_boxes[label] = QCheckBox()
            self.form_layout.addRow(QLabel(label), self.tables_check_boxes[label])

        self.form_layout.setFormAlignment(Qt.AlignHCenter)

        horizontal_layout = QHBoxLayout()

        horizontal_layout.addWidget(self.ok_button, alignment=Qt.AlignRight)
        horizontal_layout.addWidget(self.cancel_button, alignment=Qt.AlignRight)

        self.erase_sql_tables_window.layout().addLayout(self.form_layout)
        self.erase_sql_tables_window.layout().addLayout(horizontal_layout)

    def push_erase_sql_tables_button(self):

        self.erase_sql_tables_button.setEnabled(False)
        
        self.erase_sql_tables_window.show()

        self.erase_sql_tables_button.setEnabled(True)

    def push_cancel_button(self):

        self.cancel_button.setEnabled(False)

        self.erase_sql_tables_window.hide()

        self.cancel_button.setEnabled(True)

    def push_ok_button(self):

        self.ok_button.setEnabled(False)

        checked_tables = [k for k, v in self.tables_check_boxes.items() if v.isChecked()]

        if len(checked_tables):
            self.parent().php_erase_sql_tables(checked_tables)

        self.erase_sql_tables_window.hide()
        self.ok_button.setEnabled(True)

        # --------------------------------- Widgets used in assignment menu --------------------------------- #


class RadioParameter(object):
    """role (firm/customer)"""

    def __init__(self, checked):

        self.layout = QHBoxLayout()

        self.group = QButtonGroup()

        self.firm = QRadioButton()
        self.customer = QRadioButton()

        self.setup(checked)

    def setup(self, checked):

        if checked == "customer":
            self.customer.setChecked(True)
        else:
            self.firm.setChecked(True)

        self.group.addButton(self.firm)
        self.group.addButton(self.customer)

        self.layout.addWidget(self.firm)
        self.layout.addWidget(self.customer)

    def get_value(self):

        return ("customer", "firm")[self.firm.isChecked()]

    def add_to_grid_layout(self, layout, x, y):

        layout.addLayout(self.layout, x, y)


class IntParameter(object):
    """server_id"""

    def __init__(self, parent, value, idx):

        self.idx = idx
        self.edit = QLineEdit(str(value))
        self.edit.greyed_style = '''color: #808080;
                              background-color: #F0F0F0;
                              border: 1px solid #B0B0B0;
                              border-radius: 2px;'''

        self.filter = MouseClick(parent=parent, idx=idx)
        self.setup(value)

    def setup(self, value):

        if value == "Bot":
            self.edit.setEnabled(False)
            self.edit.setStyleSheet(self.edit.greyed_style)
        else:
            self.edit.setEnabled(True)

        self.edit.installEventFilter(self.filter)

    def get_value(self):

        return self.edit.text()

    def add_to_grid_layout(self, layout, x, y):

        layout.addWidget(self.edit, x, y, alignment=Qt.AlignCenter)


class CheckParameter(object):
    """bot or not"""

    def __init__(self, parent, checked, idx):
        self.parent = parent
        self.idx = idx
        self.check_box = QCheckBox()
        self.setup(checked)

    def setup(self, checked):
        # noinspection PyUnresolvedReferences
        self.check_box.stateChanged.connect(
            lambda: self.parent.switch_line_edit(idx=self.idx, from_line=False))

        self.check_box.setChecked(checked)

    def get_value(self):
        return self.check_box.isChecked()

    def add_to_grid_layout(self, layout, x, y):
        layout.addWidget(self.check_box, x, y)


class MouseClick(QObject):
    """class used in order
    to detect if QLineEdit widget
    has been clicked"""

    def __init__(self, parent, idx):
        super().__init__()
        self.idx = idx
        self.parent = parent

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            self.parent.switch_line_edit(idx=self.idx, from_line=True)
            return True

        return False
