import config
import threading
import time
import logging

from agent.handle_turn import HandleTurn


logger = logging.getLogger(__name__)

class SessionStore:
    def __init__(self, ttl=1800):
        self.ttl = ttl
        self._sessions = {}
        self._lock = threading.Lock()

    def get(self, sid):      # -> HandleTurn
        now = time.time()
        with self._lock:
            self._sweep(now)
            item = self._sessions.get(sid)
            if item is None:
                session = HandleTurn()
                self._sessions[sid] = (session,now)
                return session
            session,_ = item
            self._sessions[sid] = (session, now)
            return session


    def drop(self, sid):     # -> None
        with self._lock:
            self._sessions.pop(sid,None)

    def _sweep(self,now):
        expired = [f for f,(_,t) in self._sessions.items() if now-t > self.ttl]
        for f in expired:
            del self._sessions[f]