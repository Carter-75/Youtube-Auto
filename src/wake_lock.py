"""
Windows Wake Lock - Prevents system sleep during video generation
Uses Windows SetThreadExecutionState API for independent wake lock control
"""
import ctypes
import logging
import platform

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Windows constants for SetThreadExecutionState
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002
ES_AWAYMODE_REQUIRED = 0x00000040


class WakeLock:
    """
    Windows wake lock manager - prevents system sleep during active work
    Each instance maintains its own independent lock state
    """
    
    def __init__(self, lock_name="LoFiAutomation"):
        self.lock_name = lock_name
        self.is_locked = False
        self.is_windows = platform.system() == "Windows"
        
        if not self.is_windows:
            logger.warning("Wake lock only supported on Windows. Skipping wake lock functionality.")
    
    def acquire(self):
        """
        Acquire wake lock - prevents system from sleeping
        System stays awake until release() is called
        """
        if not self.is_windows:
            return
        
        if self.is_locked:
            logger.debug(f"Wake lock '{self.lock_name}' already acquired")
            return
        
        try:
            # Prevent system sleep and screen sleep
            # ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
            result = ctypes.windll.kernel32.SetThreadExecutionState(
                ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
            )
            
            if result:
                self.is_locked = True
                logger.info(f"[LOCK] Wake lock '{self.lock_name}' ACQUIRED - System will stay awake")
            else:
                logger.error(f"Failed to acquire wake lock '{self.lock_name}'")
                
        except Exception as e:
            logger.error(f"Error acquiring wake lock: {e}")
    
    def release(self):
        """
        Release wake lock - allows system to sleep normally
        Other applications' wake locks are not affected
        """
        if not self.is_windows:
            return
        
        if not self.is_locked:
            logger.debug(f"Wake lock '{self.lock_name}' not acquired, nothing to release")
            return
        
        try:
            # Restore normal power management
            result = ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            
            if result or True:  # Always mark as released even if API call seems to fail
                self.is_locked = False
                logger.info(f"[UNLOCK] Wake lock '{self.lock_name}' RELEASED - System can sleep normally")
            else:
                logger.warning(f"Wake lock release may have failed for '{self.lock_name}'")
                self.is_locked = False  # Mark as released anyway
                
        except Exception as e:
            logger.error(f"Error releasing wake lock: {e}")
            self.is_locked = False
    
    def __enter__(self):
        """Context manager entry - auto acquire lock"""
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - auto release lock"""
        self.release()
        return False
    
    def is_active(self):
        """Check if wake lock is currently active"""
        return self.is_locked


# Convenience functions for quick use
def keep_awake():
    """Quick function to prevent system sleep (must call allow_sleep to release)"""
    lock = WakeLock("LoFi-QuickLock")
    lock.acquire()
    return lock


def allow_sleep(lock):
    """Release a previously acquired wake lock"""
    if lock:
        lock.release()

