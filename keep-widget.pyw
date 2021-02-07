from PyQt5 import QtWidgets, QtCore, QtGui
import configparser, gkeepapi, sys, urllib.request, time, re, pickle
from themes import theme # theme object


class Manager:
    """
    This class
    - Keep track of open windows and their position
    - Saves geometry of windows
    """
    open_windows = {}
    geometries = {}

    @classmethod
    def open_list(cls, geometry = None):
        notes = [note for note in keep.all() if not note.trashed and not note.archived][:2]
        if "NotesListWindow" not in cls.open_windows:
            if "NotesListWindow" in cls.geometries:
                geometry = cls.geometries.get("NotesListWindow")
            cls.open_windows["NotesListWindow"] = NotesListWindow(notes, geometry)
        cls.save_open_windows()

    @classmethod
    def open_note(cls, note, geometry = None):
        if type(note) == str: # if note is an id
            note = keep.get(note)
        if note.id not in cls.open_windows:
            if note.id in cls.geometries:
                geometry = cls.geometries.get(note.id)
            cls.open_windows[note.id] = NoteWindow(note, geometry)
        cls.save_open_windows()

    @classmethod
    def close_window(cls, obj):
        cls.save_open_windows()
        try:
            cls.open_windows.pop(obj.id)
            obj.close()
        except KeyError:
            pass
        
    @classmethod
    def save_open_windows(cls):
        dump = list(cls.open_windows.keys())
        pickle.dump(dump, open("open_windows.p", "wb"))

    @classmethod
    def save_geometry(cls, obj):
        cls.geometries[obj.id] = obj.geometry().getRect()
        pickle.dump(cls.geometries, open("geometries.p", "wb"))

    @classmethod
    def startup(cls):
        try:
            open_windows_ids = pickle.load(open("open_windows.p", "rb"))
            cls.geometries = pickle.load(open("geometries.p", "rb"))
        except:
            open_windows_ids = []
            cls.geometries = {}
        
        if open_windows_ids == []:
            open_windows_ids = ["NotesListWindow"]

        
        for id_ in open_windows_ids:
            geometry = cls.geometries.get(id_)
            if id_ == "NotesListWindow":
                cls.open_list(geometry)
            else:
                note = keep.get(id_)
                cls.open_note(note, geometry)


class TitleBar(QtWidgets.QFrame):
    def __init__(self, parent, color: str, actions: [str]):
        """

        """
        super().__init__()

        self.setStyleSheet(theme.get_stylesheet("TitleBar", color))
        self.setMinimumHeight(30)

        layout = QtWidgets.QHBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignRight)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self.parent = parent
        self.mousePressEvent = self.pressed
        self.mouseReleaseEvent = self.released
        self.can_move = False

        self.parent.closeEvent = lambda _: Manager.close_window(self.parent)

        if "pin" in actions:
            self.pin_button = theme.get_button("pin")
            self.pin_button.setChecked(self.parent.note.pinned)
            self.pin_button.clicked.connect(self.toggle_pin)
            layout.addWidget(self.pin_button)

        if "list" in actions:
            list_button = theme.get_button("list")
            layout.addWidget(list_button)
            list_button.clicked.connect(lambda: Manager.open_list())
        
        if "minimize" in actions:
            minimize_button = theme.get_button("minimize")
            layout.addWidget(minimize_button)
            minimize_button.clicked.connect(lambda: self.parent.showMinimized())
        
        if "close" in actions:
            close_button = theme.get_button("close")
            layout.addWidget(close_button)
            close_button.clicked.connect(lambda: Manager.close_window(self.parent))

    def toggle_pin(self, event):
        self.parent.note.pinned = not self.parent.note.pinned
        self.pin_button.setChecked(self.parent.note.pinned)
        keep.sync()

    """
    Below methods are for moving the window
    """
    def mouseMoveEvent(self, event):
        if self.can_move:
            x = event.globalX()
            y = event.globalY()
            x_w = self.offset.x()
            y_w = self.offset.y()
            self.parent.move(x-x_w, y-y_w)

    def pressed(self, event):
        self.offset = event.pos()
        self.can_move = True

    def released(self, *_):
        self.can_move = False
        Manager.save_geometry(self.parent)


class NotesListWindow(QtWidgets.QFrame):
    def __init__(self, notes, geometry = None):
        super().__init__()
        self.id = "NotesListWindow"

        if geometry is None:
            geometry = (100,100,350,550)
        self.setGeometry(*geometry)

        self.setStyleSheet(theme.get_stylesheet("NotesListWindow"))
        self.setMinimumSize(300,200)
        self.setWindowTitle("Keep")
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.title_bar = TitleBar(self, "DEFAULT", ["minimize", "close"])
        self.layout.addWidget(self.title_bar)

        self.note_previews = [NoteListPreview(note, self) for note in notes]
        self.scroll = Scroll(self, *self.note_previews)
        self.layout.addWidget(self.scroll)

        self.grip = Grip(self)
        self.layout.addWidget(self.grip, 0, QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight)


        self.show()


    def resizeEvent(self, event):
        """
        We have to show and hide the scroll bar ourselves because if we let PyQt do it with
        QtCore.Qt.ScrollBarAsNeeded it causes crashes when scrollbar visibility changes.
        """
        if self.scroll.verticalScrollBar().maximum() == 0:
            self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        else:
            self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

class NoteListPreview(QtWidgets.QFrame):
    def __init__(self, note, parent):
        super().__init__()
        self.note = note

        # setup layout
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(10,10,10,10) #
        self.layout.setAlignment(QtCore.Qt.AlignTop) #
        self.setLayout(self.layout)

        self.setMinimumSize(1,1)
        self.mouseReleaseEvent = lambda x: Manager.open_note(self.note) #
        self.setStyleSheet(theme.get_stylesheet("NoteListPreview", note.color.value)) #

        # setup widgets
        self.images_widget = NoteImages(self, note)
        self.title_widget = NoteTitle(self, note)
        self.text_widget = NoteText(
            self,
            note = note,
            interaction = False
        )
        self.labels_widget = NoteLabels(self, note)

        for widget in self.images_widget, self.title_widget, self.text_widget, self.labels_widget:
            if widget.has_content:
                self.layout.addWidget(widget)

class NoteWindow(QtWidgets.QFrame):
    def __init__(self, note, geometry = None):
        super().__init__()
        self.id = note.id
        self.note = note
        
        # setup layout
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(10,10,10,10)
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(self.layout)

        self.setMinimumSize(1,1)
        self.setStyleSheet(theme.get_stylesheet("NoteWindow", self.note.color.value))
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setMinimumSize(250, 150)
        if geometry is not None:
            self.setGeometry(*geometry)
        self.layout.setContentsMargins(10, 1, 10, 0) # Left, Top, Right, Bottom
        if self.note.title:
            self.setWindowTitle(f"Keep - {self.note.title}")
        else:
            self.setWindowTitle(f"Keep - Note")

        # setup widgets
        self.title_bar = TitleBar(self, self.note.color.value, ["list","pin","minimize", "close"])
        self.layout.addWidget(self.title_bar)

        sections = []

        sections.append(NoteImages(self, self.note))
        sections.append(NoteTitle(self, self.note))
        text_widget = NoteText(
            self,
            note = self.note,
            interaction = False
        )
        text_widget.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.MinimumExpanding,
        )
        if text_widget.has_content:
            sections.append(Scroll(self, text_widget))
        sections.append(NoteLabels(self, self.note))

        for widget in [section for section in sections if section.has_content]:
            self.layout.addWidget(widget)

        grip = Grip(self)
        self.layout.addWidget(grip, 0, QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight)

        self.show()

class Scroll(QtWidgets.QScrollArea):
    def __init__(self, parent, *widgets):
        super().__init__(parent)
        self.has_content = bool(widgets)

        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setAlignment(QtCore.Qt.AlignTop)

        frame = QtWidgets.QWidget(self)
        frame.setLayout(self.layout)
        
        self.setWidget(frame)

        self.addWidgets(*widgets)

    def addWidgets(self, *widgets):
        for widget in widgets:
            self.layout.addWidget(widget)


class NoteImages(QtWidgets.QLabel):
    def __init__(self, parent, note):
        self.has_content = bool(note.blobs)
        if not self.has_content:
            # disable resize
            return

        super().__init__(parent = parent)

        image_url = keep.getMediaLink(note.blobs[0])
        data = urllib.request.urlopen(image_url).read()

        self.image = QtGui.QPixmap()
        self.image.loadFromData(data)

    def resizeEvent(self, event):
        width = self.width()
        try:
            self.setPixmap(
                self.image.scaledToWidth(
                    width,
                    QtCore.Qt.FastTransformation,
                )
            )
        except AttributeError:
            pass

class NoteTitle(QtWidgets.QLabel):
    def __init__(self, parent, note):
        self.has_content = bool(note.title)
        if not self.has_content:
            return

        super().__init__(parent = parent)

        self.setText(note.title)
        self.setWordWrap(True)
        self.setTextFormat(QtCore.Qt.RichText)
        self.setFont(QtGui.QFont("Helvetica", 32, weight=QtGui.QFont.ExtraBold))

class NoteText(QtWidgets.QLabel):
    def __init__(
        self,
        parent,
        note,
        interaction: bool,
        ):
        self.has_content = bool(note.text)
        if not self.has_content:
            return

        super().__init__(parent = parent)
        
        self.setMinimumSize(1,1)
        self.setTextFormat(QtCore.Qt.RichText)
        self.setOpenExternalLinks(True)
        self.setWordWrap(True)
        self.setAlignment(QtCore.Qt.AlignTop)
        # https://doc.qt.io/qt-5/qt.html#TextInteractionFlag-enum
        if interaction:
            self.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse | QtCore.Qt.TextSelectableByMouse)
        else:
            self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)

        text = note.text.replace("\n", "<br>")
        text = self.add_hyperlinks(text)
    
        self.setText(text)

    def add_hyperlinks(self, text):
        return re.sub(
            r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&\/\/=]*)",
            f'<a style="color: {theme["text"]}" href = "\\g<0>">\\g<0></a>',
            text,
            re.MULTILINE
        )

class NoteLabels(QtWidgets.QLabel): 
    def __init__(self, parent, note):
        labels = [label.name for label in note.labels.all()]
        self.has_content = bool(labels)
        if not self.has_content:
            return

        super().__init__()

        self.setText("🏷"+" ".join(labels))

class Grip(QtWidgets.QSizeGrip):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setFixedSize(75, 4)
        self.mouseReleaseEvent = lambda x: Manager.save_geometry(self.parent)

def get_keep():
    config = configparser.ConfigParser()
    config.read("credentials.ini")
    username = config["Credentials"]["username"]
    password = config["Credentials"]["password"]


    keep = gkeepapi.Keep()
    try:
        keep.resume(username, config["Credentials"]["token"])
        print("used token")
    except:
        keep.login(username, password)
        config["Credentials"]["token"] = keep.getMasterToken()
        with open("credentials.ini","w") as f:
            config.write(f)
    return keep

if __name__ in '__main__':
    app = QtWidgets.QApplication(sys.argv)
    keep = get_keep()
    Manager.startup()
    app.exec_()