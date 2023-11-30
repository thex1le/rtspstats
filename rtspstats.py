from threading import Thread, Lock
from json import dumps
from time import sleep
from datetime import datetime
import argparse
import sys
import base64

#3rd party imports
import cv2


class StreamStats():
    pass


class StreamStats(Thread):
    def __init__(self, stream: str, statsTime: float = 1) -> None:
        """
        Init Function
        stream: the RTSP URI as a string
        statsTime: Seconds to wait between loop of stats as an float to allow for sub second
        return: None
        """
        Thread.__init__(self)
        Thread.deamon = True
        self.statsTime = statsTime
        self.stream_ip = stream
        self.camera_frame_rate = 0
        self.camera_resolution = (1920, 1080)
        self.camera_format = cv2.CAP_PROP_FOURCC
        self.camera_focus = cv2.CAP_PROP_FOCUS
        self.camera_exposure = cv2.CAP_PROP_EXPOSURE
        #self.camera_white_balance = cv2.CAP_PROP_WHITE_BALANCE
        #self.camera_histogram = cv2.CAP_PROP_HISTOGRAM
        #self.camera_noise = cv2.CAP_PROP_GAIN
        #self.camera_distortion = cv2.CAP_PROP_DISTORTION
        self.camera_artifacts = cv2.CAP_PROP_SHARPNESS
        self.cap = cv2.VideoCapture(self.stream_ip)
        if not self.cap.isOpened():
            raise StreamStats(f"Error: Could not open self.camera stream {self.stream_ip}")
        self.stats = dict()
        self.stopthread = False
        self.rawFrame = False
        self.lock = Lock()
    
    def set_raw(self, rawFrame: bool = False) -> None:
        """
        Set collection of raw frames in the stats to true or false
        """
        self.rawFrame = rawFrame

    def stop(self) -> None:
        """
        Stop the loop thread
        return = None
        """
        self.stopthread = True

    def get_stats(self, jsonb: bool = False) -> (dict, str): 
        """
        get current stats as either a dict object or json string
        jsonb: True false, default False to return json string
        return: dict or str object of stats results, if a json string is required
        raw frame if it exists will be base64 encoded
        """
        self.lock.acquire()
        stats = self.stats
        if stats != dict():
            if jsonb is True:
                if stats['rawframe'] is not None:
                    stats['rawframe'] = base64.b64encode(stats['rawframe']).decode('ASCII')
                print(stats)
                stats = dumps(stats)
        self.lock.release()
        return stats

    def generate_stats(self) -> None: 
        self.lock.acquire()
        frame = None
        if self.rawFrame is True:
            ret, frame = self.cap.read()
        self.stats['rawframe'] = frame
        self.stats['frame_rate'] = self.cap.get(cv2.CAP_PROP_FPS)
        self.stats['resolution'] = (int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        self.stats['cformat'] = self.cap.get(self.camera_format)
        self.stats['focus'] = self.cap.get(self.camera_focus)
        self.stats['exposure'] = self.cap.get(self.camera_exposure)
        #self.stats['white_balance'] = self.cap.get(self.camera_white_balance)
        #self.stats['histogram'] = self.cap.get(self.camera_histogram)
        #self.stats['noise'] = self.cap.get(self.camera_noise)
        #self.stats['distortion'] = self.cap.get(self.camera_distortion)
        self.stats['artifacts'] = self.cap.get(self.camera_artifacts)
        #self.stats['quality'] = self.cap.get(self.camera_quality)
        now = datetime.now()
        self.stats['timestamp'] = now.strftime("%m/%d/%Y, %H:%M:%S")
        self.stats['rawframe'] = frame
        self.lock.release()

    def run(self) -> None:
        while self.stop is False:
            self.generate_stats()
            sleep(self.statsTime)
        self.cap.release()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='RTSP Stats Tracker')
    parser.add_argument('--rtsp', type=str, default=1, dest='rtsp', nargs=1, help='RTSP Stream URI')
    try: 
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(0)
    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1) 
    vidstats = StreamStats(args.rtsp[0])
    vidstats.generate_stats()
    vidstats.set_raw(True)
    vidstats.start()
    # give a few seconds to load the feed
    sleep(2)
    print(vidstats.get_stats())
    print(vidstats.get_stats(jsonb=True))
    try:
        while True:
            print(vidstats.get_stats())
            print(vidstats.get_stats(jsonb=True))
            sleep(2)
    except KeyboardInterrupt:
        vidstats.stop()
        vidstats.join()
