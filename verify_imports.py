import sys
import os
from unittest.mock import MagicMock
import types

def mock_package(name):
    m = types.ModuleType(name)
    m.__path__ = []
    sys.modules[name] = m
    return m

# Helper to link submodules to parent
def link_module(parent, child_name, child_module):
    setattr(parent, child_name, child_module)

# Mock pymongo
mock_pymongo = mock_package('pymongo')
mock_pymongo.MongoClient = MagicMock()
mock_pymongo.ASCENDING = 1

mock_pymongo_errors = mock_package('pymongo.errors')
mock_pymongo_errors.PyMongoError = Exception
mock_pymongo_errors.ConnectionFailure = Exception
link_module(mock_pymongo, 'errors', mock_pymongo_errors)

# Mock mysql
mock_mysql = mock_package('mysql')
mock_mysql_connector = mock_package('mysql.connector')
mock_mysql_connector.connect = MagicMock()
link_module(mock_mysql, 'connector', mock_mysql_connector)

# Mock requests
mock_requests = mock_package('requests')
mock_requests.get = MagicMock()
mock_requests.post = MagicMock()

# Mock selenium
mock_selenium = mock_package('selenium')
mock_webdriver = mock_package('selenium.webdriver')
link_module(mock_selenium, 'webdriver', mock_webdriver)

mock_webdriver.Edge = MagicMock()
mock_webdriver.EdgeOptions = MagicMock()

mock_support = mock_package('selenium.webdriver.support')
link_module(mock_webdriver, 'support', mock_support)

mock_ui = mock_package('selenium.webdriver.support.ui')
link_module(mock_support, 'ui', mock_ui)
mock_ui.WebDriverWait = MagicMock()

mock_ec = mock_package('selenium.webdriver.support.expected_conditions')
mock_common = mock_package('selenium.webdriver.common')
link_module(mock_webdriver, 'common', mock_common)

mock_by = mock_package('selenium.webdriver.common.by')
link_module(mock_common, 'by', mock_by)
mock_by.By = MagicMock()

mock_edge = mock_package('selenium.webdriver.edge')
link_module(mock_webdriver, 'edge', mock_edge)

mock_service = mock_package('selenium.webdriver.edge.service')
link_module(mock_edge, 'service', mock_service)
mock_service.Service = MagicMock()

# Mock PySide6
mock_pyside6 = mock_package('PySide6')
mock_widgets = mock_package('PySide6.QtWidgets')

widgets = [
    'QMainWindow', 'QVBoxLayout', 'QHBoxLayout', 'QWidget', 'QLabel', 
    'QPushButton', 'QComboBox', 'QStackedWidget', 'QApplication', 'QFrame',
    'QTableWidget', 'QTableWidgetItem', 'QHeaderView', 'QScrollArea', 
    'QGridLayout', 'QLineEdit', 'QTextEdit', 'QCheckBox', 'QRadioButton',
    'QGroupBox', 'QFormLayout', 'QDialog', 'QMessageBox', 'QFileDialog',
    'QStyle', 'QSizePolicy', 'QMenu', 'QMenuBar', 'QAction', 'QToolBar',
    'QSpinBox', 'QDoubleSpinBox', 'QSlider', 'QProgressBar', 'QTabWidget',
    'QSplitter', 'QStackedLayout', 'QListWidget', 'QListWidgetItem', 
    'QTreeWidget', 'QTreeWidgetItem', 'QAbstractItemView', 'QDialogButtonBox',
    'QInputDialog', 'QErrorMessage', 'QDockWidget', 'QCompleter', 'QToolTip'
]
for w in widgets:
    setattr(mock_widgets, w, MagicMock())

# Handle common enums or nested classes often accessed
mock_widgets.QStyle.StandardPixmap = MagicMock()

mock_core = mock_package('PySide6.QtCore')
mock_core.Signal = MagicMock
mock_core.Slot = MagicMock
mock_core.Qt = MagicMock
mock_core.QTimer = MagicMock
mock_core.QThread = MagicMock
mock_core.QObject = MagicMock
mock_core.QSize = MagicMock
mock_core.QRect = MagicMock
mock_core.QPoint = MagicMock
mock_core.QUrl = MagicMock
mock_core.QByteArray = MagicMock
mock_core.QMimeData = MagicMock
mock_core.QEvent = MagicMock

mock_gui = mock_package('PySide6.QtGui')
mock_gui.QIcon = MagicMock
mock_gui.QFont = MagicMock
mock_gui.QPixmap = MagicMock
mock_gui.QImage = MagicMock
mock_gui.QColor = MagicMock
mock_gui.QPainter = MagicMock
mock_gui.QPen = MagicMock
mock_gui.QBrush = MagicMock
mock_gui.QAction = MagicMock
mock_gui.QDesktopServices = MagicMock()
mock_gui.QDrag = MagicMock
mock_gui.QCursor = MagicMock
mock_gui.QLinearGradient = MagicMock
mock_gui.QRadialGradient = MagicMock
mock_gui.QConicalGradient = MagicMock
mock_gui.QPainterPath = MagicMock
mock_gui.QRegion = MagicMock
mock_gui.QPolygon = MagicMock
mock_gui.QTransform = MagicMock

mock_network = mock_package('PySide6.QtNetwork')
mock_network.QNetworkAccessManager = MagicMock
mock_network.QNetworkRequest = MagicMock
mock_network.QNetworkReply = MagicMock

mock_charts = mock_package('PySide6.QtCharts')
mock_charts.QChart = MagicMock
mock_charts.QChartView = MagicMock
mock_charts.QBarSeries = MagicMock
mock_charts.QBarSet = MagicMock
mock_charts.QBarCategoryAxis = MagicMock
mock_charts.QValueAxis = MagicMock
mock_charts.QPieSeries = MagicMock
mock_charts.QPieSlice = MagicMock
mock_charts.QLineSeries = MagicMock
mock_charts.QSplineSeries = MagicMock
mock_charts.QScatterSeries = MagicMock

# Mock trio
mock_trio = mock_package('trio')

# Mock paramiko
mock_paramiko = mock_package('paramiko')

sys.path.append(os.getcwd())

try:
    print("Importing main...")
    from main import sim_init
    print("Initializing simulation...")
    # Mocking QApplication to avoid GUI startup issues if sim_init creates one
    with MagicMock(): 
        sim_init()
    print("Simulation initialized successfully.")
except Exception as e:
    print(f"Error during verification: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
