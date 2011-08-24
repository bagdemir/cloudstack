'''
Created on Jun 6, 2011

@author: frank
'''
from OvmCommonModule import *
try:
    from multiprocessing import Process, Manager
except ImportError:
    from processing import Process, Manager
import signal

logger = OvmLogger("OvmHaHeartBeat")

class OvmHaHeartBeat(object):
    '''
    classdocs
    '''
    def __init__(self, mountPoint, ip):
        self.mountPoint = mountPoint
        self.ip = ip
    
    def mark(self, file):
        timestamp = HEARTBEAT_TIMESTAMP_FORMAT % time.time()
        try:
            fd = open(file, 'w')
            fd.write(timestamp)
            fd.close()
        except Exception, e:
            errmsg = fmt_err_msg(e)
            logger.error(OvmHaHeartBeat.mark, errmsg)
        
    def run(self):
        '''
        Constructor
        '''
        heartBeatDir = join(self.mountPoint, HEARTBEAT_DIR)
        if not exists(heartBeatDir):
            os.makedirs(heartBeatDir)
        hearBeatFile = join(heartBeatDir, ipToHeartBeatFileName(self.ip))
        while True:
            self.mark(hearBeatFile)
            time.sleep(120)
    
    @staticmethod
    def start(poolPath, ip):
        pidFile = join(PID_DIR, "heartbeat.pid")
        
        def isLive():
            if exists(pidFile):
                f = open(pidFile)
                pid = f.read().strip()
                f.close()
                if isdir("/proc/%s" % pid):
                    return long(pid)
            return None
        
        def stopOldHeartBeat(pid):
            os.kill(pid, signal.SIGTERM)
            time.sleep(5)
            pid = isLive()
            if pid != None:
                logger.debug(OvmHaHeartBeat.start, "SIGTERM cannot stop heartbeat process %s, will try SIGKILL"%pid)
                os.kill(pid, signal.SIGKILL)
                time.sleep(5)
                pid = isLive()
                if pid != None:
                    raise Exception("Cannot stop old heartbeat process %s, setup heart beat failed"%pid)
        
        def heartBeat(hb):
            hb.run()
           
        def setupHeartBeat():
            hb = OvmHaHeartBeat(poolPath, ip)
            p = Process(target=heartBeat, args=(hb,))
            p.start()
            pid = p.pid
            if not isdir(PID_DIR):
                os.makedirs(PID_DIR)
            pidFd = open(pidFile, 'w')
            pidFd.write(str(pid))
            pidFd.close()
            logger.info(OvmHaHeartBeat.start, "Set up heart beat successfully, pid is %s" % pid)
             
        pid = isLive()
        if pid != None:
            stopOldHeartBeat(pid)
            
        setupHeartBeat()
            
