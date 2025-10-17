import os
import sys

# Simple file-based lock that works on all platforms
class BotLock:
    def __init__(self, lock_file="bot.lock"):
        self.lock_file = lock_file
        self.lock_handle = None
        
    def acquire(self):
        """Try to acquire the lock"""
        try:
            # Check if lock file already exists
            if os.path.exists(self.lock_file):
                # Try to read the PID from the lock file
                try:
                    with open(self.lock_file, 'r') as f:
                        pid_str = f.read().strip()
                        if pid_str.isdigit():
                            pid = int(pid_str)
                            # Check if the process is still running
                            if self._is_process_running(pid):
                                print(f"Another bot instance is already running! (PID: {pid})")
                                return False
                            else:
                                print(f"Found stale lock file from PID {pid}, removing...")
                                os.remove(self.lock_file)
                except:
                    # If we can't read the lock file, remove it
                    os.remove(self.lock_file)
            
            # Create lock file
            self.lock_handle = open(self.lock_file, 'w')
            self.lock_handle.write(str(os.getpid()))
            self.lock_handle.flush()
            
            print(f"Bot lock acquired. PID: {os.getpid()}")
            return True
            
        except Exception as e:
            if self.lock_handle:
                self.lock_handle.close()
                self.lock_handle = None
            
            print(f"Error acquiring lock: {e}")
            return False
    
    def release(self):
        """Release the lock"""
        if self.lock_handle:
            try:
                self.lock_handle.close()
                
                # Remove lock file
                if os.path.exists(self.lock_file):
                    os.remove(self.lock_file)
                    
                print("Bot lock released.")
            except Exception as e:
                print(f"Error releasing lock: {e}")
            finally:
                self.lock_handle = None
    
    def _is_process_running(self, pid):
        """Check if a process with given PID is running"""
        try:
            if os.name == 'nt':  # Windows
                import subprocess
                result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], 
                                      capture_output=True, text=True)
                return str(pid) in result.stdout
            else:  # Unix/Linux/Mac
                os.kill(pid, 0)  # This will raise an exception if process doesn't exist
                return True
        except:
            return False 