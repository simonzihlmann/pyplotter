# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore, QtTest
from typing import Callable
import sys

from ..config import config

# def trap_exc_during_debug(*args) -> None:
#     # when app raises uncaught exception, print info
#     print(' -- loadDataBase -- ')
#     print(int(QtCore.QThread.currentThreadId()))
#     print(args)
#     print(' --              -- ')


# install exception hook: without this, uncaught exception would cause application to exit
# sys.excepthook = trap_exc_during_debug

class loadDataBaseSignal(QtCore.QObject):
    """
    Class containing the signal of the loadDataBaseThread, see below
    """


    # When the run method is done
    updateDatabase = QtCore.pyqtSignal(str, bool, int)
    # Signal used to update the status bar
    setStatusBarMessage = QtCore.pyqtSignal(str, bool)
    # Signal used to add n rows in the database table
    addRows = QtCore.pyqtSignal(list, list, list, list, list, list, list, list, int, str)
    # Signal used to update the progress bar
    updateProgressBar = QtCore.pyqtSignal(str, int)




class loadDataBaseThread(QtCore.QRunnable):


    def __init__(self, getRunInfos: Callable[[int], dict], progressBarKey: str):
        """
        Thread used to get all the run info of a database.
        !! Do not import data !!

        Parameters
        ----------
        getRunInfos : func
            Function which returns all infos of a database in a nice python dict.
        progressBarKey : str
            Key to the progress bar in the dict progressBars
        """

        super(loadDataBaseThread, self).__init__()

        self.getRunInfos    = getRunInfos
        self.progressBarKey = progressBarKey

        self.signals = loadDataBaseSignal()



    @QtCore.pyqtSlot()
    def run(self):
        """
        Method launched by the worker.
        Go through the runs and send a signal for each new entry.
        Each signal is catch by the main thread to add a line in the database
        table displaying all the info of each run.
        """

        self.signals.setStatusBarMessage.emit('Gathered runs infos database', False)
        runInfos = self.getRunInfos(self.signals.updateProgressBar, self.progressBarKey)

        # If database is empty
        if runInfos is None:
            self.signals.setStatusBarMessage.emit('Database empty', True)
            QtTest.QTest.qWait(1000) # To let user see the error message
            self.signals.updateDatabase.emit(self.progressBarKey, False, 0)
            return

        # Going through the database here
        self.signals.setStatusBarMessage.emit('Loading database', False)
        nbTotalRun = len(runInfos)


        # We go through the runs info and build list to be transferred to the main
        # thread. Every config['NbRunEmit'] a signal is emitted and the list are
        # empty and the process starts again until all info have been stransferred.
        runId           = []
        dim             = []
        experimentName  = []
        sampleName      = []
        runName         = []
        started         = []
        completed       = []
        runRecords      = []
        for key, val in runInfos.items():

            runId.append(key)
            dim.append('-'.join(str(i) for i in val['nb_independent_parameter'])+'d')
            experimentName.append(val['experiment_name'])
            sampleName.append(val['sample_name'])
            runName.append(val['run_name'])
            started.append(val['started'])
            completed.append(val['completed'])
            runRecords.append(str(val['records']))

            # If we reach enough data, we emit the signal.
            if key%config['NbRunEmit']==0:
                self.signals.addRows.emit(runId,
                                         dim,
                                         experimentName,
                                         sampleName,
                                         runName,
                                         started,
                                         completed,
                                         runRecords,
                                         nbTotalRun,
                                         self.progressBarKey)

                runId           = []
                dim             = []
                experimentName  = []
                sampleName      = []
                runName         = []
                started         = []
                completed       = []
                runRecords      = []

        # If there is still information to be transferred, we do so
        if len(runId)!=0:
            self.signals.addRows.emit(runId,
                                      dim,
                                      experimentName,
                                      sampleName,
                                      runName,
                                      started,
                                      completed,
                                      runRecords,
                                      nbTotalRun,
                                      self.progressBarKey)

        # Signal that the whole database has been looked at
        self.signals.updateDatabase.emit(self.progressBarKey, False, nbTotalRun)


