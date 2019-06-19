from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(640, 480)
        MainWindow.setMinimumSize(QtCore.QSize(640, 480))
        
        # Main window stuff. Central layout is vertical
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.vertical_main = QtWidgets.QVBoxLayout(self.centralwidget)
        self.vertical_main.setObjectName("central_vertical")
        
        # Middle section starts here. Horizontal row of blocks
        self.horizontal_lists = QtWidgets.QHBoxLayout()
        self.vertical_main.addLayout(self.horizontal_lists)
        
        # Third block is list of all detected PWADs in folders we scan
        self.tabs = QtWidgets.QTabWidget(self.centralwidget)
        self.tab_folders = QtWidgets.QWidget()
        self.tab_folders_horizontal = QtWidgets.QHBoxLayout()
        
        self.wad_list = QtWidgets.QTreeView(self.centralwidget)
        self.wad_list.setUniformRowHeights(True)
        #self.wad_list.setHeaderHidden(True)
        self.tab_folders_horizontal.addWidget(self.wad_list)
        
        self.tab_folders.setLayout(self.tab_folders_horizontal)
        self.tabs.addTab(self.tab_folders, 'Folder view')
        
        self.tab_cats = QtWidgets.QWidget()
        self.tab_cats_horizontal = QtWidgets.QHBoxLayout()
        
        self.cat_list = QtWidgets.QTreeView(self.centralwidget)
        self.cat_list.setUniformRowHeights(True)
        self.cat_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        #self.wad_list.setHeaderHidden(True)
        self.tab_cats_horizontal.addWidget(self.cat_list)
        
        self.tab_cats.setLayout(self.tab_cats_horizontal)
        self.tabs.addTab(self.tab_cats, 'Category view')
        
        self.horizontal_lists.addWidget(self.tabs)
        
        # First block is IWAD choice and related things
        self.vertical_iwad = QtWidgets.QVBoxLayout()
        self.horizontal_lists.addLayout(self.vertical_iwad)
        self.iwad_label = QtWidgets.QLabel("Game", self.centralwidget)
        self.vertical_iwad.addWidget(self.iwad_label)
        self.iwad_select = QtWidgets.QComboBox(self.centralwidget)
        self.vertical_iwad.addWidget(self.iwad_select)
        #self.map_label = QtWidgets.QLabel("Map:", self.centralwidget)
        
        # Second block is list of PWADs of user's choice.
        #self.load_list = QtWidgets.QListView(self.centralwidget)
        #self.horizontal_lists.addWidget(self.load_list)

        # Lower-most section is delegated to launch-game button
        self.horizontal_buttons = QtWidgets.QHBoxLayout()
        self.vertical_main.addLayout(self.horizontal_buttons)        
        self.launch_button = QtWidgets.QPushButton("Launch game", self.centralwidget)
        self.horizontal_buttons.addWidget(self.launch_button)

        # Once all UI stuff is created, attach central widget to main window
        MainWindow.setCentralWidget(self.centralwidget)
        
        # Setting up menu bar
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 640, 21))
        self.menubar.setObjectName("menubar")
        
        # "File" submenu goes here
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        
        # "Quit" submenu goes here
        self.menuQuit = QtWidgets.QMenu(self.menubar)
        self.menuQuit.setObjectName("menuQuit")
        
        # Once menu is set, attach to main window
        MainWindow.setMenuBar(self.menubar)
        
        # Setting up status bar (Do I even need this?..)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        
        # This is something related to translations. I'll have to work with it later on
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "GZDoom Frontend"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuQuit.setTitle(_translate("MainWindow", "Quit"))

