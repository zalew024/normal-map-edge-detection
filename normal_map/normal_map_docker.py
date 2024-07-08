import sys
from click import Path
from krita import *
from PyQt5 import QtCore, QtGui, QtWidgets
from os import path
from .normal_map_filter import *

from pathlib import Path


DOCKER_TITLE = "Normal Map (Edge Detection)"


class NormalMapDocker(DockWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(DOCKER_TITLE)
        mainWidget = QWidget(self)

        self.groupBox1 = QGroupBox("Filter Type", mainWidget)
        self.ComboBox1 = QComboBox(self.groupBox1)
        self.ComboBox1.addItems(["Simple", "Sobel", "Prewitt"])
        layout1 = QVBoxLayout()
        layout1.addWidget(self.ComboBox1)
        self.groupBox1.setLayout(layout1)

        self.groupBox2 = QGroupBox("Normal Map Format", mainWidget)
        self.ComboBox2 = QComboBox(self.groupBox2)
        self.ComboBox2.addItems(["OpenGL", "DirectX"])
        layout2 = QVBoxLayout()
        layout2.addWidget(self.ComboBox2)
        self.groupBox2.setLayout(layout2)

        self.groupBox3 = QGroupBox("Width", mainWidget)
        self.horizontalSlider = QSlider(self.groupBox3)
        self.horizontalSlider.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider.setValue(1)
        self.horizontalSlider.valueChanged.connect(self.changeWidthValueSpinBox)
        self.doubleSpinBox = QDoubleSpinBox(self.groupBox3)
        self.doubleSpinBox.setValue(1.00)
        self.doubleSpinBox.setRange(0, 100.00)
        self.doubleSpinBox.setSingleStep(0.01)
        self.doubleSpinBox.valueChanged.connect(self.changeWidthValueSlider)
        layout3 = QHBoxLayout()
        layout3.addWidget(self.horizontalSlider)
        layout3.addWidget(self.doubleSpinBox)
        self.groupBox3.setLayout(layout3)

        self.groupBox4 = QGroupBox("Shape", mainWidget)
        self.radioButton1 = QRadioButton("bump", self.groupBox4)
        self.radioButton2 = QRadioButton("hole", self.groupBox4)
        self.radioButton2.setChecked(True)
        layout4 = QHBoxLayout()
        layout4.addWidget(self.radioButton1)
        layout4.addWidget(self.radioButton2)
        self.groupBox4.setLayout(layout4)

        self.groupBox5 = QGroupBox("Slope", mainWidget)
        self.spinBox = QSpinBox(self.groupBox5)
        self.spinBox.setValue(45)
        self.spinBox.setRange(0, 90)
        self.label = QLabel(self.groupBox5)
        self.label.setText("\u00B0")
        self.dir = str(path.dirname(path.realpath(__file__)))
        self.path = str(self.dir + "/images/slope.png")
        self.label2 = QLabel(self.groupBox5)
        self.pixmap = QPixmap(self.path)
        self.label2.setPixmap(self.pixmap)
        self.label2.resize(self.pixmap.width(), self.pixmap.height())
        layout5 = QHBoxLayout()
        layout5.addWidget(self.spinBox)
        layout5.addWidget(self.label)
        layout5.addWidget(self.label2)
        self.groupBox5.setLayout(layout5)

        self.pushButton1 = QPushButton("Export", mainWidget)
        self.pushButton1.clicked.connect(self.export)
        self.pushButton2 = QPushButton("New Normal Map", mainWidget)
        self.pushButton2.clicked.connect(self.newNormalMap)

        mainLayout = QGridLayout()
        mainLayout.addWidget(self.groupBox1, 0, 0, 2, 4)
        mainLayout.addWidget(self.groupBox2, 0, 4, 2, 4)
        mainLayout.addWidget(self.groupBox3, 2, 0, 2, 8)
        mainLayout.addWidget(self.groupBox4, 4, 0, 2, 5)
        mainLayout.addWidget(self.groupBox5, 4, 5, 2, 3)
        mainLayout.addWidget(self.pushButton1, 6, 0, 1, 3)
        mainLayout.addWidget(self.pushButton2, 6, 3, 1, 5)
        mainWidget.setLayout(mainLayout)

        self.setWidget(mainWidget)

        self.num = 0

    def export(self):

        Krita.instance().action("file_export_file").trigger()

    def newNormalMap(self):

        self.doc = Krita.instance().activeDocument()
        self.num += 1
        if self.doc is not None:
            self.layer = self.doc.activeNode()
            self.newLayer = self.layer.duplicate()
            self.newLayer.setName("normal_map_{}".format(self.num))
            root_node = self.doc.rootNode()
            prevLayer = self.doc.nodeByName("normal_map_{}".format(self.num - 1))
            root_node.addChildNode(self.newLayer, prevLayer)
            self.doc.setActiveNode(self.newLayer)
            if self.newLayer.colorModel() != "RGBA":
                self.doc.setColorSpace("RGBA", "U8", "sRGB-elle-V2-srgbtrc.icc")
            self.readProps()
            self.applyFilter(self.newLayer)

    def readProps(self):

        self.normalMapProps = {
            "type": self.ComboBox1.currentText().lower(),
            "format": self.ComboBox2.currentText(),
            "width": self.doubleSpinBox.value(),
            "shape": ("bump" if (self.radioButton1.isChecked()) else "hole"),
            "slope": self.spinBox.value(),
        }

    def applyFilter(self, filterLayer):

        filter = Filter(self.normalMapProps)
        filter.setFilterProps()
        filter.heightToNormalFilter.apply(
            filterLayer, 0, 0, self.doc.width(), self.doc.height()
        )

        pixelBytes = filterLayer.projectionPixelData(
            0, 0, self.doc.width(), self.doc.height()
        )
        imageFormat = QImage.Format_RGBA8888  # U8
        imageData = QImage(
            pixelBytes, self.doc.width(), self.doc.height(), imageFormat
        ).rgbSwapped()
        filter.changeSlope(imageData, filterLayer)
        self.doc.refreshProjection()

    def changeWidthValueSpinBox(self):
        self.width_value_slider = self.horizontalSlider.value()
        self.doubleSpinBox.setValue(self.width_value_slider)

    def changeWidthValueSlider(self):
        self.width_value_spinbox = self.doubleSpinBox.value()
        self.horizontalSlider.setValue(int(self.width_value_spinbox))

    def canvasChanged(self, canvas):
        pass
