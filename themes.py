from PyQt5 import QtGui, QtWidgets, QtCore

class Theme:
    current_theme = "DARK"

    colors = {
        "DARK":{
            "DEFAULT":"#202124",
            "RED":"#5c2b29",
            "ORANGE":"#614a19",
            "YELLOW":"#635d19",
            "GREEN":"#345920",
            "TEAL":"#16504b",
            "BLUE":"#2d555e",
            "CERULEAN":"#1e3a5f",
            "PURPLE":"#42275e",
            "PINK":"#5b2245",
            "BROWN":"#442f19",
            "GRAY":"#3c3f43",
            "text":"white",
            None:None,
        },
        "LIGHT":{
            "DEFAULT":"#ffffff",
            "RED":"#f28b82",
            "ORANGE":"#fbbc04",
            "YELLOW":"#fff475",
            "GREEN":"#ccff90",
            "TEAL":"#a7ffeb",
            "BLUE":"#cbf0f8",
            "CERULEAN":"#aecbfa",
            "PURPLE":"#d7aefb",
            "PINK":"#fdcfe8",
            "BROWN":"#e6c9a8",
            "GRAY":"#e8eaed",
            "text":"black",
            None:None,
        }
    }

    stylesheet = """
QFrame {
    border:/*QFrame_border_width*/px solid #636466;
    border-radius: /*QFrame_border_radius*/px;
}
/*QFrame:hover*/
QWidget {
    background: /*note_color*/;
    font-size: 15px;
}
QLabel {
    border: 1px solid green;
    color: /*text_color*/;
}
QLabel:hover {
    border: 0px solid green;
}
QScrollArea {
    border: 0px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::vertical {              
    border: none;
    background: /*note_color*/;
    width:10px;
}
QScrollBar::handle:vertical {
    background: #636466;
    min-height: 20px;
    border: none;
    width: 5px;
    border-radius: 5px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
/*# add-line & sub-line w/ height 0 hides arrows */
QScrollBar::add-line:vertical {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
    stop: 0 rgb(0, 0, 255), stop: 0.5 rgb(0, 0, 255),  stop:1 rgb(32, 47, 130));
    height: 0px;
    subcontrol-position: bottom;
    subcontrol-origin: margin;
}
QScrollBar::sub-line:vertical {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
    stop: 0  rgb(255, 0, 0), stop: 0.5 rgb(255, 0, 0),  stop:1 rgb(255, 0, 0));
    height: 0 px;
    subcontrol-position: top;
    subcontrol-origin: margin;
}
QPushButton{
    border: 0px solid white;
    border-radius: 16px;
}
QPushButton:hover  {
    background: rgba(95,99,104,0.157);
}"""

    def __getitem__(self, key):
        return self.colors[self.current_theme][key]

    def get_stylesheet(
        self,
        class_name: str,
        color: str = "DEFAULT",
        ):
        
        class_replacement = {
            "TitleBar":{
                "/*QFrame_border_width*/":"0",
                "/*QFrame_border_radius*/":"0",
                "/*note_color*/":self[color],
                "/*text_color*/":self["text"],
            },
            "NotesListWindow":{
                "/*QFrame_border_width*/":"2",
                "/*QFrame_border_radius*/":"0",
                "/*note_color*/":self["DEFAULT"],
                "/*text_color*/":self["text"],
            },
            "NoteListPreview":{
                "/*QFrame_border_width*/": str(int(color == "DEFAULT")),
                "/*QFrame_border_radius*/":"15",
                "/*QFrame:hover*/": r"QFrame:hover {border: 2px solid /*text_color*/;}",
                "/*note_color*/":self[color],
                "/*text_color*/":self["text"],
            },
            "NoteWindow":{
                "/*QFrame_border_width*/": "2",
                "/*QFrame_border_radius*/":"0",
                "/*note_color*/":self[color],
                "/*text_color*/":self["text"],
            }
        }[class_name]

        class_stylesheet = self.stylesheet

        for key, value in class_replacement.items():
            class_stylesheet = class_stylesheet.replace(key, value)
        
        return class_stylesheet

    def get_icon(self, icon_type):
        toggle_icons = {
            "pin":{QtGui.QIcon.On:"pin_filled", QtGui.QIcon.Off:"pin_outlined"}
        }

        if icon_type in toggle_icons:
            states = toggle_icons.get(icon_type)
            icon = QtGui.QIcon()
            for state, file in states.items():
                path = f"assets/icons/{self.current_theme}/{file}.svg"
                icon.addPixmap(QtGui.QPixmap(path), QtGui.QIcon.Normal, state)
        else:
            icon = QtGui.QIcon(f"assets/icons/{self.current_theme}/{icon_type}.svg")
        return icon
    
    def get_button(self, button_icon):
        button = QtWidgets.QPushButton()
        button.setIcon(self.get_icon(button_icon))
        button.setIconSize(QtCore.QSize(30,34))
        button.setCheckable(True)
        return button

theme = Theme()