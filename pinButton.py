
from sys     import exc_info
from machine import Pin
from utime   import ticks_ms
from _thread import allocate_lock, start_new_thread

class PinButton :
    
    # ============================================================================
    # ===( Constructor )==========================================================
    # ============================================================================

    def __init__( self,
                  pinNum,
                  strPull,
                  btnChangeCallback,
                  btnReversed       = False,
                  btnThreaded       = False,
                  Id                = 0 ) :

        pinId   = self._getPinIdFromPinNum(pinNum)
        pinPull = self._getPinPullFromStrPull(strPull)
        if not pinId or not pinPull :
            raise Exception('Incorrects arguments in PinButton constructor.')

        self._Id          = Id
        self._btnChangeCB = btnChangeCallback
        self._btnReversed = btnReversed
        self._btnThreaded = btnThreaded
        self._lockProcess = allocate_lock()
        self._process     = False
        self._pin         = Pin(pinId, mode=Pin.IN, pull=pinPull)
        self._btnIsOn     = self._isLogicalBtnOnFromPin()
        self._saveTicksMS = ticks_ms() if self._btnIsOn else 0
        
        print("BUTTON ON PIN [%s] INITIALIZED FROM [%s]" % (self._pin.id(), "ON" if self._btnIsOn else "OFF"))

        self._pin.callback(Pin.IRQ_FALLING | Pin.IRQ_RISING, self._pinInterrupt)
    
    # ============================================================================
    # ===( Functions )============================================================
    # ============================================================================

    def GetId(self) :
        return self._Id
    
    # ----------------------------------------------------------------------------

    def IsOn(self) :
        return self._btnIsOn
    
    # ----------------------------------------------------------------------------

    def IsOff(self) :
        return not self._btnIsOn
    
    # ============================================================================
    # ===( Utils )================================================================
    # ============================================================================

    def _getPinIdFromPinNum(self, pinNum) :
        return ("P" + str(pinNum)) if isinstance(pinNum, int) else None

    # ----------------------------------------------------------------------------

    def _getPinPullFromStrPull(self, strPull) :
        if hasattr(strPull, 'upper') :
            strPull = strPull.upper()
            if strPull == "UP" :
                return Pin.PULL_UP
            if strPull == "DOWN" :
                return Pin.PULL_DOWN
        return None

    # ----------------------------------------------------------------------------

    def _isLogicalBtnOnFromPin(self) :
        if self._pin.pull() == Pin.PULL_DOWN :
            isOn = self._pin.value()
        else :
            isOn = not self._pin.value()
        return (isOn if not self._btnReversed else not isOn)

    # ============================================================================
    # ===( Events )===============================================================
    # ============================================================================

    def _pinInterrupt(self, pin) :
        isOn = self._isLogicalBtnOnFromPin()
        if (isOn != self._btnIsOn) :
            if (isOn and not self._process) or not isOn :
                self._btnIsOn = isOn
                self._process = True
                if isOn :
                    msPressed         = 0
                    self._saveTicksMS = ticks_ms()
                else :
                    msPressed = ticks_ms() - self._saveTicksMS
                if self._btnThreaded :
                    start_new_thread(self._processBtnChange, (isOn, msPressed))
                else :
                    self._processBtnChange(isOn, msPressed)

    # ----------------------------------------------------------------------------

    def _processBtnChange(self, isOn, msPressed) :
        with self._lockProcess :
            print("BUTTON ON PIN [%s] CHANGED TO [%s]" % (self._pin.id(), "ON" if isOn else "OFF"))
            if self._btnChangeCB :
                try :
                    self._btnChangeCB(self, isOn, msPressed)
                except :
                    print('Error on callback process of PinButton change (%s).' % exc_info()[1])
            if not isOn :
                self._process = False

    # ============================================================================
    # ============================================================================
    # ============================================================================
