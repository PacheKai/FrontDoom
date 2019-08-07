# ================================================================
# Imports
# ================================================================
import sys, os, subprocess, configparser, json, getpass, zipfile, hashlib#, time, urllib.request
from functools import partial
from timeit import default_timer as timer

import PyQt5
from PyQt5 import QtWidgets, QtCore, QtGui

import form
# ================================================================
# Constants
# ================================================================
EXTS = ['.wad', '.pk3', '.pk7', '.ipk3', '.zip']
LUMPS = ['acs', 'colormaps', 'filter', 'flats', 'graphics', 'hires', 'maps', 'music', 'patches', 'sounds', 'sprites', 'textures', 'voices', 'voxels']
LOGOS = {'doom.wad': "images/doom.png",
            'doom2.wad':"images/doom2.png",
            'heretic.wad':"images/heretic.png",
            'hexen.wad':"images/hexen.png",
            'strife1.wad':"images/strife.png",
            'chex.wad':"images/chexquest.png",
            'def':"images/no_logo.png"}

if sys.platform.startswith('win32'):
    PLATFORM = 'WIN'
elif sys.platform.startswith('linux'):
    PLATFORM = 'LIN'
else:
    print('Unsupported OS.')
    sys.exit()
    
# ================================================================
# Classes
# ================================================================        
class WADListItem(PyQt5.QtGui.QStandardItem):
    """List item class.
    
    Links to relevant item from list of WADs.
    """
    
    def __init__(self, wad):
        super().__init__()
        self.wad = wad
        self.setText(wad.name())        
        
    def __lt__(a, b):
        """ "Less than" function.
        
        Required by Qt to do sorting in lists.    
        """
        if a.text() < b.text():
            return True
        else:
            return False
            
class WADItem:
    def __init__(self, path, cat = "Unsorted"):
        super().__init__()
        self.path = path
        self.cat = cat
        
    def name(self):
        return os.path.basename(self.path)
        

# ================================================================
# Functions
# ================================================================
def saveWADList(filename, dictionary):
    """ Saves list of WADItem objects.
    
    Function writes JSON file with list of WAD files which consists of:
    hash - hash of file
    item.path - file path
    item.cat - assigned category
    
    Args:
    filename - where to save
    dictionary - what to save
    
    """
    temp = []
    for hash, item in dictionary.items():
        temp.append([hash, item.path, item.cat])
    try:
        with open(filename, 'w') as file:
            json.dump(temp, file)
    except OSError:
        print('Couldn\'t write WAD list to file {0}.'.format(filename))

def loadWADList(filename, dictionary):
    """ Loads list of "installed" WADs.
    
    Function reads JSON file with list of WAD files which consists of:
    l[0] - hash of file
    l[1] - file path
    l[2] - assigned category
    
    Args:
    filename - from where to load
    dictionary - what to load
    """
    try:
        with open(filename, 'r') as file:
            temp_list = json.load(file)
        for item in temp_list:
            if os.path.exists(item[1]):
                if item[0] == fileToHash(item[1]):
                    dictionary[item[0]] = WADItem(item[1], item[2])
                else:
                    print("{0} - incorrect checksum.")
            else:
                print("{0} - file does not exist.".format(item[1]))
    except OSError:
        print('Couldn\'t load WAD list from file {0}.'.format(filename))
    return
        
def loadCats():
    """ Everything is better with cats.
    
    """
    global cats
    try:
        with open('CatsList.dat', 'r') as file:
            cats = json.load(file)
    except OSError:
        print('Couldn\'t load cat list file.')
    except json.decoder.JSONDecodeError:
        print('CatsList.dat malformed. Please delete file and restart application.')
        
def saveCats():
    """ Saves your cats for better times.
    
    """
    try:
        with open('CatsList.dat', 'w') as file:
            json.dump(cats, file)
    except OSError:
        print('Couldn\'t write cats list file.')

def checkCats(item):
    """ Checks breed cat belongs to.
    
    """
    global cats
    item.cat = cats.setdefault(item.text(), 'All WADs')
    if item.cat in cat_model_contents:
        cat_model_contents[item.cat].appendRow(item.copy())
        #print('CATS - Added {0} to listing'.format(item.text()))
    else:
        temp = WADListItem(item.cat, '', 0, 'Dog')
        cat_model_contents[item.cat] = temp
        temp.appendRow(item.copy())
        cat_model.appendRow(temp)
        #print('CATS - Added {0} to listing'.format(item.text()))

def checkWAD(path, name, root):
    """ Check supplied WAD to see what kind of beast it is.

    WAD files can be of two main types - IWAD (Internal WAD), which is
    game itself and requires nothing else to be played, or PWAD
    (Patch WAD), which "patches" some IWAD with it's own data.
    Function makes sure PWADs are separated from IWADs, process is
    different for various formats.
    
    .wad files has 4-byte header which plainly states if it's I or P.
    .pk3, .ipk3, .zip files must contain 'iwadinfo' file
    .pk7 - not yet implemented, considered PWAD by default
    .ipk7 - not yet implemented, considered IWAD by default
    
    Args:
    path - path to WAD file
    name - name of WAD file
    root - item to append to for data model
    
    Return:
    New WADListItem object in either item list.
    WADs with malformed headers are dropped.
    """
    iwadStatus = False
    temp_ext = os.path.splitext(name)[1].lower()
    # Testing .wad file for status of stand-alone game
    if temp_ext == '.wad':
        with open(path, 'rb') as wad:
            header = wad.read(4)
            if header == b'IWAD':
                iwadStatus = True
            elif header == b'PWAD':
                pass
            else:
                print('{0}{1}: WAD header not found'.format(path, name))
                return
    # Testing .ipk3 and .zip for status of stand-alone game
    elif temp_ext in ['.ipk3', '.zip', '.pk3']:
        pwadStatus = False
        with zipfile.ZipFile(path, 'r') as wad:
            for thing in wad.infolist():
                #print('1 - {0}, 2 - {1}, 3 - {2}'.format(pwadStatus, thing.is_dir(), thing.filename.lower()))
                if thing.filename.lower() == 'iwadinfo':
                    iwadStatus = True
                    break
                elif not pwadStatus and thing.filename.partition('/')[0].lower() in LUMPS:
                    pwadStatus = True
        if not (pwadStatus or iwadStatus):
            print('{0}{1}: not compatible with GZDoom'.format(path, name))
            return    
    # "Testing" .ipk7 for status of stand-alone game
    if temp_ext == '.ipk7':
        iwadStatus = True
                
    temp = WADListItem(name, path, 1)            
    if iwadStatus:
        iwad_model.appendRow(temp)
        if name == config_current['-iwad']:
            config_current['-iwad_index'] = iwad_model.rowCount()-1
        #print('IWAD - Added {0} to listing'.format(temp.text()))
    else:
        if name in config_current['-file']:
            temp.setCheckState(QtCore.Qt.Checked)
        root.appendRow(temp)
        #print('PWAD - Added {0} to listing'.format(temp.text()))
        checkCats(temp)
    return

def scanFolders(path, recursive, parent):
    """ Scan folder used for mods.

    Runs through files, drops everything that's not a WAD on the first
    glance, then checks if WADs are actually WADs, and of what type.
    See checkWAD for more.

    Args:
    path - filesystem path to folder containing WADs
    recursive - if True, also recursively scans all folders found
    during procedure's run
    parent - item model or previous root found during recursive folder
    scanning
    
    Return:
    Two item models filled with info about WADs - for PWADs and IWADs
    """
    temp = os.path.basename(path)
    #print("Found folder {}...".format(temp))
    root = WADListItem(temp, '', 0)
    parent.appendRow(root)
    with os.scandir(path) as stuff:
        for thing in stuff:
            if not thing.name.startswith('.'):
                if thing.is_file():
                    if os.path.splitext(thing.name)[1].lower() in EXTS:
                        checkWAD(thing.path, thing.name, root)
                elif thing.is_dir() and recursive:
                    scanFolders(thing.path, recursive, root)
    if not root.hasChildren():
        parent.takeRow(root.row())
    return
    
def refreshFolders():
    """ Initiates full rescan of all WAD folders program uses.
    
    Cleans item models, measures time taken for refresh.
    
    Args:
    None
    
    Returns:
    See scanFolders()
    """
    wad_model.clear()
    iwad_model.clear()
    start = timer()
    for line in prefs['WADPaths']['path'].split('\n'):
        if not os.path.exists(line):
            print('Path {} does not exist.'.format(line))
            continue
        #wad_model.appendRow(WADListItem(line, '', 0))
        scanFolders(line, True, wad_model)
    end = timer()
    print('Folder scan complete in {} seconds'.format(end - start))
    
def attachToPort(path):
    """ Acquire relevant settings from selected source port.
    
    Most notably, we need folders source port looks up files at,
    since those will form bulk of WAD folders to scan later.
    
    Args:
    path - path to source port's folder
    
    Returns:
    None
    """
    configFile = 'gzdoom-' + getpass.getuser() + '.ini'
    if configFile in [x.name for x in os.scandir(path)]:
        reading = False
        with open(prefs['General']['gz_path'] + configFile, 'r') as file:
            for line in file:
                temp = line.strip()
                if any(section in temp for section in ('[IWADSearch.Directories]', '[FileSearch.Directories]')):
                    reading = True
                    continue
                if reading and temp.startswith('Path='):
                    temp = temp[5:]
                    for key in gzShortcuts.keys():
                        temp = os.path.normpath(temp.replace(key, gzShortcuts[key]))
                    temp = os.path.normpath(temp)
                    if temp in gzShortcuts:
                        temp = temp.replace(temp, gzShortcuts[temp])
                    if not temp in prefs['WADPaths']['path']:
                        prefs['WADPaths']['path'] += '\n' + temp 
                        #print(prefs['WADPaths']['path'])
                else:
                    reading = False
    else:
        print("Couldn\'t find source port's config file.")
        return
        
def fileToHash(filename):
    md5 = hashlib.md5()
    md5.update(open(filename, 'rb').read())
    return md5.hexdigest()    
    
def saveConfig(filename):
    """ Writes game-specific configuration into JSON.
    
    Game-specific config is one that will be given directly to source
    port of choice, includes IWAD to load, PWADs to add on top of it, skill
    level, map, whatever else. Basically, storage for command line arguments.
    
    Args:
    filename - specifies filename of written file.
    
    Returns:
    File "filename" in frontend's config folder.
    """
    try:
        with open(filename, 'w') as file:
            json.dump(config_current, file)
    except OSError:
        print('Couldn\'t save currently used game config to file.')
    
def loadConfig(filename):
    """ Loads game-specific configuration from JSON.
    
    See saveConfig for more.
    
    Args:
    filename - specifies filename of read file.
    
    Returns:
    config_current rewritten with info from file "filename".
    """
    global config_current
    try:
        with open(filename, 'r') as file:
            config_current = json.load(file)
            #print(config_current)
    except OSError:
        print('Couldn\'t load last used game config from file.')
        
# ================================================================
# Initializing
# ================================================================

# Qt-specifics
#icons = {'dir': QtGui.QIcon('dir.png'),
#            'wad': QtGui.QIcon('file.png')}

# Preferences file
print('Initializing...')
prefs = configparser.ConfigParser()
prefs['General'] = {'gz_path': '', 'executable': ''}
prefs['WADPaths'] = {'path': ''}
if not prefs.read('prefs.ini'):
    print('Couldn\'t read preferences file, using default settings.')


gzShortcuts = {'$PROGDIR': prefs['General']['gz_path'],
                '$DOOMWADDIR': os.environ['DOOMWADDIR'] if 'DOOMWADDIR' in os.environ else '',
                '$HOME': os.environ['HOME'] if 'HOME' in os.environ else '',
                '.': prefs['General']['gz_path']}
                
# Saved mod list
wad_list = {}
loadWADList('WADList.dat', wad_list)
iwad_list = {}
loadWADList('IWADList.dat', iwad_list)
print(iwad_list, "ping")

# Last game config file
config_current = {'-iwad': None, '-file': []}
loadConfig('lastconfig.dat')

# Filesystem stuff
# List of IWADs known by application
iwad_model = PyQt5.QtGui.QStandardItemModel()
for item in iwad_list.values():
    temp = WADListItem(item)
    iwad_model.appendRow(temp)

wad_model = PyQt5.QtGui.QStandardItemModel()
for item in wad_list.values():
    temp = WADListItem(item)
    temp.setCheckable(True)
    if temp.wad.path in config_current['-file']:
        temp.setCheckState(QtCore.Qt.Checked)
    wad_model.appendRow(temp)
#cat_model = PyQt5.QtGui.QStandardItemModel()


# Categories
#cats = {}
#dtemp = WADListItem('All WADs', '', 0, 'Dog')
#cat_model.appendRow(dtemp)
#cat_model_contents = {'All WADs': dtemp}
#loadCats()

#for line in prefs['WADCats']['cats'].split('\n'):
#    Cats[line] = WADListItem(line, '', 0)

#refreshFolders()
        
# Quick exit
#sys.exit()

print('Initializing done.')
            
# ================================================================
# Main window class, clean up later
class MyWindowClass(QtWidgets.QMainWindow, form.Ui_MainWindow):
    global config_current
    global wad_list
    global iwad_list
    def __init__(self, parent = None):
        print('Initializing main window...')
        print(config_current)
        QtWidgets.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.last_error_msg = None
        actPrefs = QtWidgets.QAction('Preferences...', self)
        actPrefs.triggered.connect(self.prefDialog)
        actRefresh = QtWidgets.QAction('Refresh WAD list', self)
        actRefresh.triggered.connect(refreshFolders)
        actAdd = QtWidgets.QAction('Add new WAD file...', self)
        actAdd.triggered.connect(self.addDialog)
        actAddI = QtWidgets.QAction('Add new IWAD file...', self)
        actAddI.triggered.connect(self.addIDialog)
        #actLogin = QtWidgets.QAction(QIcon('icon_login.png'), 'Log in', self)
        #actLogin.triggered.connect(self.loginDialog)
        #actLogout = QtWidgets.QAction(QIcon('icon_logout.png'), 'Log out', self)
        #actLogout.triggered.connect(self.logoutDialog)
        actQuit = QtWidgets.QAction('Quit', self)
        actQuit.triggered.connect(self.clExit)
        #self.actUsername = QtWidgets.QAction(self.Username, self)
        #self.actCart = QtWidgets.QAction(QIcon('icon_cart.png'), 'Cart', self)
        #self.actCart.setEnabled(False)
        #self.actCart.triggered.connect(self.cartPrepare)

        #self.toolbar = self.addToolBar('Tools')
        #self.toolbar.addAction(actRefresh)
        #self.toolbar.addAction(actLogin)
        #self.toolbar.addAction(self.actUsername)
        #self.toolbar.addAction(self.actCart)

        self.menuFile.addAction(actAdd)
        self.menuFile.addAction(actAddI)
        self.menuFile.addAction(actRefresh)
        self.menuFile.addSeparator()
        self.menuFile.addAction(actPrefs)
        #self.menuUser.addAction(self.actCart)
        #self.menuUser.addAction(actLogout)
        #self.menuQuit.addAction(actRegister)
        #self.menuQuit.addSeparator()
        self.menuQuit.addAction(actQuit)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuQuit.menuAction())
        
        self.launch_button.clicked.connect(self.launchGame)
        
        # Setup models here
        #self.iwad_model = PyQt5.QtGui.QStandardItemModel(self)
        #self.wad_model = PyQt5.QtGui.QStandardItemModel(self)
        #self.iwad_model = dummyI
        #self.wad_model = dummyP
        wad_model.itemChanged.connect(self.checkingItems)
        self.iwad_select.activated.connect(self.iwadChanged)
        #self.load_wad_model = PyQt5.QtGui.QStandardItemModel(self)
        
        #self.loadSettings()
        
        #self.scanFolders()
        #self.load_list.setModel(self.load_wad_model)
        #self.load_list.setSelectionMode(0)
        self.iwad_select.setModel(iwad_model)
        #self.iwad_select.setCurrentIndex()
        for i in range(0, iwad_model.rowCount()):
            if iwad_model.item(i).wad.path == config_current['-iwad']:
                self.iwad_select.setCurrentIndex(iwad_model.item(i).row())
                try:
                    self.iwad_label.setPixmap(QtGui.QPixmap(LOGOS[iwad_model.item(i).text().lower()]))
                except KeyError:
                    self.iwad_label.setPixmap(QtGui.QPixmap(LOGOS['def']))
        
        self.wad_list.setModel(wad_model)
        #self.cat_list.setModel(cat_model)
        #self.cat_list.customContextMenuRequested.connect(self.wadMenu)

        
        
        self.statusBar().showMessage('Ready.')
        
    def wadMenu(self, position):
        item = cat_model.itemFromIndex(self.cat_list.indexAt(position))
        # If nothing is selected, default to root
        if isinstance(item, type(None)):
            item = cat_model.item(0)
            print(item.text())
        menu = QtWidgets.QMenu()
        
        openItem = menu.addAction('View in Explorer')
        sortItems = menu.addAction('Sort list')
        
        addCat = menu.addAction('Add new category...')
        setItem = menu.addAction('Set category...')
        delCat = menu.addAction('Remove category')
        if item.type:
            delCat.setVisible(False)
        else:
            setItem.setVisible(False)
            openItem.setVisible(False)
        
        action = menu.exec_(self.cat_list.mapToGlobal(position))
        if action == addCat:
            self.catDialog()
        elif action == setItem:
            self.setDialog(item)
        elif action == delCat:
            self.delCatDialog(item)
        elif action == openItem:
            self.openItem(item)
        elif action == sortItems:
            self.cat_list.model().sort(0)

    def addDialog(self):
        # getOpenFileName returns tuple (filename, filter)
        temp = QtWidgets.QFileDialog.getOpenFileName(self, "Select WAD file", prefs['WADPaths']['path'].split('\n')[0], 'WAD files (*.wad *.pk3 *.pk7 *.zip)')[0]
        if not temp:
            return
        temp = os.path.normpath(temp)
        hash = fileToHash(temp)
        wad_list[hash] = WADItem(temp)
        item = WADListItem(wad_list[hash])
        item.setCheckable(True)
        wad_model.appendRow(item)
        
    def addIDialog(self):
        # getOpenFileName returns tuple (filename, filter)
        temp = QtWidgets.QFileDialog.getOpenFileName(self, "Select IWAD file", prefs['WADPaths']['path'].split('\n')[0], 'IWAD files (*.wad *.pk3 *.ipk3 *.pk7 *.ipk7 *.zip)')[0]
        if not temp:
            return
        temp = os.path.normpath(temp)
        hash = fileToHash(temp)
        iwad_list[hash] = WADItem(temp)
        iwad_model.appendRow(WADListItem(iwad_list[hash]))
        if len(iwad_list) == 1:
            config_current['-iwad'] = iwad_list[hash].path
            
    def catDialog(self):
        dc = QtWidgets.QDialog(parent = self)
        dc.setWindowTitle('Add new category...')
        dc.setWindowModality(QtCore.Qt.ApplicationModal)
        
        dc_layoutV = QtWidgets.QVBoxLayout()
        dc.text_name = QtWidgets.QLineEdit()
        dc.text_name.setPlaceholderText('Name your new category...')
        dc_layoutV.addWidget(dc.text_name)
        
        dc_layoutH = QtWidgets.QHBoxLayout()
        apply = QtWidgets.QPushButton("OK")
        dc_layoutH.addWidget(apply)
        cancel = QtWidgets.QPushButton("Cancel")
        dc_layoutH.addWidget(cancel)
        
        dc_layoutV.addLayout(dc_layoutH)
        
        apply.clicked.connect(partial(self.addNewCat, dc))
        cancel.clicked.connect(dc.reject)
        
        dc.setLayout(dc_layoutV)
        dc.exec_()
        
    def addNewCat(self, dialog):
        cat = dialog.text_name.text()
        if cat not in cat_model_contents:
            temp = WADListItem(cat, '', 0, 'Dog')
            cat_model_contents[cat] = temp
            cat_model.appendRow(temp)
            dialog.accept()
        else:
            msg = QtWidgets.QMessageBox.warning(self, 'Error!', 'Such category already exists!', QtWidgets.QMessageBox.Ok)
        return
        
    def setDialog(self, item):
        di = QtWidgets.QDialog(parent = self)
        di.setWindowTitle('Choose category...')
        di.setWindowModality(QtCore.Qt.ApplicationModal)
        
        di_layoutV = QtWidgets.QVBoxLayout()
              
        di.list_cats = QtWidgets.QListWidget()
        for cat in cat_model_contents.keys():
            di.list_cats.addItem(cat)
                
        di_layoutV.addWidget(di.list_cats)
        
        di_layoutH = QtWidgets.QHBoxLayout()
        apply = QtWidgets.QPushButton("OK")
        di_layoutH.addWidget(apply)
        cancel = QtWidgets.QPushButton("Cancel")
        di_layoutH.addWidget(cancel)
        
        di_layoutV.addLayout(di_layoutH)
        
        apply.clicked.connect(partial(self.setItem, item, di))
        cancel.clicked.connect(di.reject)
        
        di.setLayout(di_layoutV)
        di.exec_()
        
    def setItem(self, item, dialog):
        new_cat = dialog.list_cats.selectedItems()[0].text()
        old_cat = item.cat
        item.cat = new_cat
        cats[item.text()] = new_cat
        cat_model_contents[new_cat].appendRow(cat_model_contents[old_cat].takeRow(item.row()))
        dialog.accept()
        return
        
    def delCatDialog(self, item):
        print('Deleting a category')
        if item.text() == 'All WADs':
            msg = QtWidgets.QMessageBox.warning(self, 'Error!', 'This is default category, you can\'t remove it!', QtWidgets.QMessageBox.Ok)
            return
        msg = QtWidgets.QMessageBox.question(self, 'Confirmation', 'Are you sure you want to delete this category?\nAll items in it will be moved to default one!', QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if msg == QtWidgets.QMessageBox.Yes:
            while item.hasChildren():
                cat_model_contents['All WADs'].appendRow(item.takeRow(0))
            cat_model.takeRow(cat_model_contents.pop(item.text()).row())
        
    def openItem(self, item):
        os.startfile(os.path.dirname(item.path))
        return
    
    def prefDialog(self):
        # Dialog stuff
        dp = QtWidgets.QDialog(parent = self)
        dp.setWindowTitle("Preferences")
        dp.setWindowModality(QtCore.Qt.ApplicationModal)
        
        # Main widget setup
        dp_layoutV = QtWidgets.QVBoxLayout()
        tabs = QtWidgets.QTabWidget(dp)
        
        # First tab goes here
        tab_general = QtWidgets.QWidget()
        generalG = QtWidgets.QGridLayout()
        
        label_gzpath = QtWidgets.QLabel('GZDoom folder path: ')
        generalG.addWidget(label_gzpath, 0, 0)
        
        dp.text_gzpath = QtWidgets.QLineEdit()
        dp.text_gzpath.setText(prefs['General']['gz_path'])
        generalG.addWidget(dp.text_gzpath, 0, 1)
        
        button_gzpath = QtWidgets.QPushButton("Browse...")
        button_gzpath.clicked.connect(partial(self.setEnginePath, dp.text_gzpath))
        generalG.addWidget(button_gzpath, 0, 2)
        
        label_port = QtWidgets.QLabel('Save config in application\'s folder: ')
        generalG.addWidget(label_port, 1, 0)
        
        check_port = QtWidgets.QCheckBox()
        generalG.addWidget(check_port, 1, 1)
        
        tab_general.setLayout(generalG)
        tabs.addTab(tab_general, 'General')
        
        # Second tab
        tab_paths = QtWidgets.QWidget()
        pathsV = QtWidgets.QVBoxLayout()
        
        label_pwads = QtWidgets.QLabel('PWAD folder paths: ')
        pathsV.addWidget(label_pwads)
        
        dp.list_pwads = QtWidgets.QListWidget()
        for line in prefs['WADPaths']['path'].split('\n'):
        # Conditional makes sure list won't have stray blank lines
            if line:
                dp.list_pwads.addItem(line)
        pathsV.addWidget(dp.list_pwads)
        
        pathButtonsH = QtWidgets.QHBoxLayout()
        buttonAddPath = QtWidgets.QPushButton('Add folder...')
        buttonAddPath.clicked.connect(partial(self.addPWADPath, dp.list_pwads))
        pathButtonsH.addWidget(buttonAddPath)
        buttonAddPortPath = QtWidgets.QPushButton('Add source port\'s WAD\nfolders to list')
        buttonAddPortPath.clicked.connect(partial(self.addPortPWADPaths, dp.list_pwads))
        pathButtonsH.addWidget(buttonAddPortPath)
        buttonRemovePath = QtWidgets.QPushButton('Remove folder')
        buttonRemovePath.clicked.connect(partial(self.removePWADPath, dp.list_pwads))
        pathButtonsH.addWidget(buttonRemovePath)
        
        pathsV.addLayout(pathButtonsH)
        pathsV.setAlignment(pathButtonsH, PyQt5.QtCore.Qt.AlignRight)
        
        tab_paths.setLayout(pathsV)
        tabs.addTab(tab_paths, 'Paths')
        dp_layoutV.addWidget(tabs)
        
        # Apply Cancel buttons go here
        dp_layoutH = QtWidgets.QHBoxLayout()
        apply = QtWidgets.QPushButton("Apply")
        dp_layoutH.addWidget(apply)
        cancel = QtWidgets.QPushButton("Cancel")
        dp_layoutH.addWidget(cancel)
        dp_layoutV.addLayout(dp_layoutH)
        dp_layoutV.setAlignment(dp_layoutH, PyQt5.QtCore.Qt.AlignRight)
        
        apply.clicked.connect(partial(self.saveSettings, dp))
        cancel.clicked.connect(dp.reject)
        
        dp.setLayout(dp_layoutV)
        dp.exec_()

    def setEnginePath(self, caller):
        temp = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self, "Select GZDoom executable"))
        caller.setText(temp)
        
    def addPWADPath(self, caller):
        caller.addItem(os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self, "Select new PWAD folder")))
        
    def removePWADPath(self, caller):
    # Headscratcher - Qt's docs state this simply takes item out of list, but doesn't delete it, and user shoulda do it
    # themselves. On the other hand, Python's deleting works such as when object is not referenced by anything else, it's
    # destroyed. This thing should NOT be referenced by anything else, so, will it be destroyed?
        caller.takeItem(caller.currentRow())
        
    def addPortPWADPaths(self, caller):
        print(prefs['WADPaths']['path'])
        attachToPort(prefs['General']['gz_path'])
        print(prefs['WADPaths']['path'])
        caller.clear()
        for line in prefs['WADPaths']['path'].split('\n'):
            caller.addItem(line)
        
    def saveSettings(self, dialog):
        # General tab
        prefs['General']['gz_path'] = dialog.text_gzpath.text()
        # Paths tab
        prefs['WADPaths']['path'] = ''
        temp = []
        for num in range(dialog.list_pwads.count()):
            temp.append(dialog.list_pwads.item(num).text())
        prefs['WADPaths']['path'] = '\n'.join(temp)
        dialog.accept()
    
    def launchGame(self):
        """ Start GZDoom with selected parametres.
    
        This will be collecting info from all over the programm and assemble it in one
        long, thick string that's then is sent to subprocess module, which launches game.
        There will be selectable behaviour - to lay hidden in wait for game to terminate,
        or exit after launching it.
        """
        #print(self.iwad_list.selectedIndexes()[0].data())
        #print(self.iwad_model.item(self.iwad_select.currentIndex()).wad)
        #print(self.wad_list.selectedIndexes()[0].row())
        command_string = [prefs['General']['gz_path'] + prefs['General']['executable'], '-iwad', config_current['-iwad']]
        for item in config_current['-file']:
            command_string.append('-file')
            command_string.append(item)
        gzprocess = subprocess.Popen(command_string)
        self.hide()
        gzprocess.wait()
        self.show()
        
    def checkingItems(self, item):
        if item.checkState():
            print('Added ', item)
            config_current['-file'].append(item.wad.path)
        if not item.checkState():
            print('Removed ', item)
            config_current['-file'].remove(item.wad.path)
            
    def iwadChanged(self, what):
        config_current['-iwad'] = iwad_model.item(what).wad.path
        self.iwad_label.setPixmap(QtGui.QPixmap(LOGOS[iwad_model.item(what).text().lower()]))
        
    def closeEvent(self, event):
        print('Exiting...')
        saveConfig('lastconfig.dat')
        #saveCats()
        with open('prefs.ini', 'w') as file:
            prefs.write(file)
        saveWADList('WADList.dat', wad_list)
        saveWADList('IWADList.dat', iwad_list)
        event.accept()

    def clExit(self):
        self.close()
        
# ================================================================
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    myWindow = MyWindowClass(None)
    myWindow.show()
    app.exec_()
