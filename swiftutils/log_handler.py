import logging, os, datetime, warnings, atexit, argparse
from types import SimpleNamespace
from pathlib import Path

class Logger:
    '''object designed for swift granular logging configuration'''
    def __init__(self, name, loggers, loglvl, filename, filepath, filefmt, fhandler, filecap, filetimeout, file, streamfmt, shandler, stream, warn, cli):

        logging.captureWarnings(warn)

        self.name = name
        self.loggers = {}
        self.filename = filename
        self.filepath = filepath
        self.loglvl = loglvl
        self.rootlogger = logging.getLogger()
        self.filefmt = filefmt
        self.fhandler = fhandler

        self.streamfmt = streamfmt
        self.shandler = shandler

        for log in loggers:
            logger = logging.getLogger(log)
            self.loggers[log] = logger
            self.rootlogger.addHandler(logger)

        self.loggers = SimpleNamespace(**self.loggers)
        # print(self.loggers) # debug
        self.rootlogger.setLevel(loglvl)
        if file:
            self.fhandler.setLevel(self.loglvl)
            self.fhandler.setFormatter(self.filefmt)
            for log in vars(self.loggers).keys():
                logger = logging.getLogger(log)
                logger.addHandler(self.fhandler)
                logger.propagate = False
        if stream:
            self.shandler.setLevel(self.loglvl)
            self.shandler.setFormatter(self.streamfmt)
            for log in vars(self.loggers).keys():
                logger = logging.getLogger(log)
                logger.addHandler(self.shandler)
                logger.propagate = False

        if filecap and isinstance(filecap, int):
            self.cap(filecap)
        if filetimeout and isinstance(filetimeout, str):
            self.timeout(filetimeout)

        atexit.register(self.out)

        if cli:
            self.create_cli()
    
    def create_cli(self):
        print('cli made')
        parser = argparse.ArgumentParser(description='Logger command line interface')
        parser.add_argument('--debug', type=str, choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'], help='Define the log level')
        args = parser.parse_args()
        log_level = args.debug
        if log_level:
            self.rootlogger.setLevel(log_level)

    # currently not in use
    def setLoglvl(self, lvl):
        self.loglvl = lvl
        self.rootlogger.setLevel(lvl)
        self.fhandler.setLevel(lvl)

    def cap(self, filecap):
        '''delete any file outside of range based on file age'''
        parent_folder = Path(self.filepath).parent
        logs = [(os.path.join(parent_folder, f), os.path.getctime(os.path.join(parent_folder, f))) for f in os.listdir(parent_folder) if f.endswith('.log')]
        logs.sort(key=lambda x: x[1], reverse=True) # sort the logs by their creation time in descending order
        if len(logs) > filecap:
            logs_to_remove = len(logs) - filecap # calculate the number of logs to remove
            for log in logs[filecap:]:
                os.remove(log[0])
            if logs_to_remove > 1:
                print(f'filecap removed {logs_to_remove} logs')
            else:
                print("filecap reached")

    def timeout(self, filetimeout):
        '''delete any file outside given time range'''
        try:
            parent_folder = Path(self.filepath).parent
            logs = [os.path.join(parent_folder, f) for f in os.listdir(parent_folder) if f.endswith('.log')]
            time_units = {'m': 'minutes', 'h': 'hours', 'd': 'days', 'o':'months', 'y': 'years'}
            time_unit = time_units[filetimeout[-1]]
            time_amount = int(filetimeout[:-1])
            now = datetime.datetime.now()
            if time_unit == 'years':
                time_threshold = now - datetime.timedelta(days=time_amount*365)
            elif time_unit == "minutes":
                time_threshold = now - datetime.timedelta(minutes=time_amount)
            elif time_unit == 'months':
                time_threshold = now - datetime.timedelta(days=time_amount*30)
            else:
                time_threshold = now - datetime.timedelta(**{time_unit: time_amount})
            logs_removed = 0
            for log in logs:
                if os.path.getctime(log) < time_threshold.timestamp():
                    os.remove(log)
                    logs_removed += 1
            if logs_removed > 0:
                print(f'timeout removed {logs_removed} logs')
        except KeyError:
            warnings.warn(f"Invalid time unit: {filetimeout[-1]}", Warning)
    
    def out(self):
        """
        Check all loggers in the loggers namespace object for existing logs.
        If none exist, close the file fhandlers and remove the empty file
        """
        for log in vars(self.loggers).values():
            if log.hasHandlers():
                for fhandler in log.handlers:
                    fhandler.close()
                log.handlers = []
        try:
            file_size = os.path.getsize(self.filepath)
            if file_size == 0:
                os.remove(self.filepath)
        except Exception as e:
            print(f"Failed to remove file: {e}")