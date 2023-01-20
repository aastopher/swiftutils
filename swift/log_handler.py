import logging, os, datetime
from types import SimpleNamespace

class Logger:
    def __init__(self, module_name, logger_names, file_fmt='%Y-%m-%d_%H-%M-%S', log_fmt='%H:%M:%S', log_lvl=logging.INFO):
        self.module_name = module_name
        self.loggers = {}
        self.log_lvl = log_lvl
        self.root_logger = logging.getLogger()
        for name in logger_names:
            logger = logging.getLogger(name)
            self.loggers[name] = logger
            self.root_logger.addHandler(logger)

        now = datetime.datetime.now()
        now = now.strftime(file_fmt)
        self.root_logger.setLevel(log_lvl)
        if not os.path.exists('logs'):
            os.mkdir('logs')
        if not os.path.exists(f'logs/{self.module_name}'):
            os.mkdir(f'logs/{self.module_name}')
        fh = logging.FileHandler(f'logs/{self.module_name}/{now}.log','w')
        # fh = logging.TimedRotatingFileHandler(f'logs/{self.module_name}/{now}.log','w', when='midnight')
        fh.setLevel(self.log_lvl)
        formatter = logging.Formatter('%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s', datefmt=log_fmt)
        fh.setFormatter(formatter)
        for log in self.loggers.keys():
            logger = logging.getLogger(log)
            logger.addHandler(fh)
            logger.propagate = False
        self.loggers = SimpleNamespace(**self.loggers)