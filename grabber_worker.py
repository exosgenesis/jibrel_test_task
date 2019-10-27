import threading

from grabber import RatesGrabber


class GrabberWorker:

    def __init__(self, config):
        self._updates_delay = config['RATES_UPDATES_DELAY']
        self._grabber = RatesGrabber(config)

        self._rates_api_event = threading.Event()
        self._stop_event = threading.Event()
        self._rates_api_event.clear()
        self._stop_event.clear()
        self._thread = None
        self.grabbed_event = threading.Event()

    def notify(self):
        self._rates_api_event.set()

    def grab_in_this_thread(self):
        self._grabber.grab()

    def start(self):
        self._thread = threading.Thread(target=self._routine)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._rates_api_event.set()

    def _routine(self):
        while not self._stop_event.is_set():
            try:
                self.grabbed_event.clear()
                self._grabber.grab()
            except Exception as e:
                print(e)
            self.grabbed_event.set()
            self._rates_api_event.wait(self._updates_delay)
            self._rates_api_event.clear()
