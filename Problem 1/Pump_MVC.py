import numpy as np
import PyQt5.QtWidgets as qtw
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from LeastSquares import LeastSquaresFit_Class

class Pump_Model():
    """
    This is the pump model. It just stores data.
    """
    def __init__(self):
        self.PumpName   = ""
        self.FlowUnits  = ""
        self.HeadUnits  = ""
        self.FlowData   = np.array([])
        self.HeadData   = np.array([])
        self.EffData    = np.array([])
        self.LSFitHead  = LeastSquaresFit_Class()
        self.LSFitEff   = LeastSquaresFit_Class()

class Pump_Controller():
    def __init__(self):
        self.Model = Pump_Model()
        self.View  = Pump_View()

    def setViewWidgets(self, w):
        self.View.setViewWidgets(w)

    def ImportFromFile(self, data):
        """
        Processes the lines in 'data' to build the pump model
        :param data: list of strings, where each string is a line from the pump data file.
                        - data[0] should contain the pump name.
                        - data[2] should contain unit definitions ('gpm ft %').
                        - data[3] should contain the numeric data for the pump.
        :return: None
        """
        self.Model.PumpName = data[0].strip()
        #data[2] is the units line
        L = data[2].split()
        self.Model.FlowUnits = L[0]
        self.Model.HeadUnits = L[1]

        # extracts flow, head and efficiency data and calculates coefficients
        self.SetData(data[3:])
        self.updateView()

    def SetData(self, dataLines):
        """
        Expects lines with three columns: Flow, Head, Efficiency
        :param data:
        :return:
        """
        #clear existing arrays data
        self.Model.FlowData = np.array([])
        self.Model.HeadData = np.array([])
        self.Model.EffData  = np.array([])

        #parse new data
        for line in dataLines:
            cells = line.strip().split() #parses line into an array of strings
            self.Model.FlowData = np.append(self.Model.FlowData, float(cells[0])) #removes any spaces and convert string to a float
            self.Model.HeadData = np.append(self.Model.HeadData, float(cells[1])) #removes any spaces and convert string to a float
            self.Model.EffData  = np.append(self.Model.EffData,  float(cells[2])) #removes any spaces and convert string to a float

        #calls least square fit for head and efficiency
        self.LSFit()

    def LSFit(self):
        """
        Use a 2nd-degree polynomial for Head, 3rd-degree for Efficiency
        """
        # Head => Quadratic
        self.Model.LSFitHead.x = self.Model.FlowData
        self.Model.LSFitHead.y = self.Model.HeadData
        self.Model.LSFitHead.LeastSquares(2)

        # Efficiency => Cubic
        self.Model.LSFitEff.x = self.Model.FlowData
        self.Model.LSFitEff.y = self.Model.EffData
        self.Model.LSFitEff.LeastSquares(3)

    def updateView(self):
        self.View.updateView(self.Model)


class Pump_View():
    def __init__(self):
        """
        Widgets are simply placeholders until they are set by setViewWidgets.
        """
        self.LE_PumpName  = qtw.QLineEdit()
        self.LE_FlowUnits = qtw.QLineEdit()
        self.LE_HeadUnits = qtw.QLineEdit()
        self.LE_HeadCoefs = qtw.QLineEdit()
        self.LE_EffCoefs  = qtw.QLineEdit()
        self.ax           = None
        self.canvas       = None

    def setViewWidgets(self, w):
        """
        Unpack the 7 widgets passed from pump_app.py
        """
        (self.LE_PumpName,
         self.LE_FlowUnits,
         self.LE_HeadUnits,
         self.LE_HeadCoefs,
         self.LE_EffCoefs,
         self.ax,
         self.canvas) = w

    def updateView(self, Model):
        """
        Push Model data into the view widgets, then create the plot.
        """
        self.LE_PumpName.setText(Model.PumpName)
        self.LE_FlowUnits.setText(Model.FlowUnits)
        self.LE_HeadUnits.setText(Model.HeadUnits)
        self.LE_HeadCoefs.setText(Model.LSFitHead.GetCoeffsString())
        self.LE_EffCoefs.setText(Model.LSFitEff.GetCoeffsString())

        self.DoPlot(Model)

    def DoPlot(self, Model):
        """
        Creates a black-and-white plot with distinct line/marker styles
        for Head (left y-axis) and Efficiency (right y-axis).
        """
        # 2nd-degree fit for head, 3rd-degree for efficiency
        headx, heady, headRSq = Model.LSFitHead.GetPlotInfo(2)
        effx, effy, effRSq     = Model.LSFitEff.GetPlotInfo(3)

        # clear previous axes, create a twin y-axis for efficiency
        self.ax.clear()
        ax1 = self.ax
        ax2 = ax1.twinx()

        # --- HEAD data & fit (left axis) ---
        # open circles for data, dashed line for fit
        hd_data = ax1.plot(
            Model.FlowData, Model.HeadData,
            linestyle='None', marker='o', markerfacecolor='None', 
            markeredgecolor='k', markersize=8,
            label='Head'
        )
        hd_fit = ax1.plot(
            headx, heady,
            color='k', linestyle='--',
            label=f'Head (R²={headRSq:.3f})'
        )

        # --- EFFICIENCY data & fit (right axis) ---
        # open triangles for data, dotted line for fit
        ef_data = ax2.plot(
            Model.FlowData, Model.EffData,
            linestyle='None', marker='^', markerfacecolor='None',
            markeredgecolor='k', markersize=8,
            label='Efficiency'
        )
        ef_fit = ax2.plot(
            effx, effy,
            color='k', linestyle=':',
            label=f'Efficiency (R²={effRSq:.3f})'
        )

        # Labels & Title
        ax1.set_xlabel(f'Flow Rate ({Model.FlowUnits})')
        ax1.set_ylabel(f'Head ({Model.HeadUnits})')
        ax2.set_ylabel('Efficiency (%)')
        ax1.set_title(f'Pump Curve: {Model.PumpName}')

        # Combine legend entries from both axes
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='best')

        # Grid on the left axis (this will show across the figure)
        ax1.grid(True)
        # Redraw
        self.canvas.draw()