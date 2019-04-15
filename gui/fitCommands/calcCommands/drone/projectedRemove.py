import wx
from logbook import Logger

import eos.db
from gui.fitCommands.helpers import DroneInfo
from service.fit import Fit


pyfalog = Logger(__name__)


class CalcRemoveProjectedDroneCommand(wx.Command):

    def __init__(self, fitID, droneInfo):
        wx.Command.__init__(self, True, 'Remove Projected Drone')
        self.fitID = fitID
        self.droneInfo = droneInfo
        self.savedDroneInfo = None

    def Do(self):
        pyfalog.debug('Doing removal of projected drone {} from fit {}'.format(self.droneInfo, self.fitID))
        fit = Fit.getInstance().getFit(self.fitID)
        drone = next((pd for pd in fit.projectedDrones if pd.itemID == self.droneInfo.itemID), None)
        if drone is None:
            pyfalog.warning('Unable to find projected drone')
            return False
        self.savedDroneInfo = DroneInfo.fromDrone(drone)
        drone.amount = max(drone.amount - self.droneInfo.amount, 0)
        # Remove stack if we have no items remaining
        if drone.amount == 0:
            fit.projectedDrones.remove(drone)
        else:
            if drone.amountActive > 0:
                drone.amountActive = min(drone.amountActive, drone.amount)
        eos.db.commit()
        return True

    def Undo(self):
        pyfalog.debug('Undoing removal of projected drone {} from fit {}'.format(self.droneInfo, self.fitID))
        fit = Fit.getInstance().getFit(self.fitID)
        # Change stack if we still have it
        drone = next((pd for pd in fit.projectedDrones if pd.itemID == self.savedDroneInfo.itemID), None)
        if drone is not None:
            drone.amount = self.savedDroneInfo.amount
            drone.amountActive = self.savedDroneInfo.amountActive
            return True
        # Make new stack
        from .projectedAdd import CalcAddProjectedDroneCommand
        cmd = CalcAddProjectedDroneCommand(fitID=self.fitID, droneInfo=self.savedDroneInfo)
        return cmd.Do()