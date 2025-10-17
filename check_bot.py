#!/usr/bin/env python3
"""
Script to check if the bot is running and show running processes
"""

import os
import sys
import psutil

def check_bot_processes():
    """Check for running bot processes"""
    bot_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check if this is a Python process running our bot
            if proc.info['name'] == 'python.exe' or proc.info['name'] == 'python':
                cmdline = proc.info['cmdline']
                if cmdline and any('main.py' in arg for arg in cmdline):
                    bot_processes.append({
                        'pid': proc.info['pid'],
                        'cmdline': ' '.join(cmdline)
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    return bot_processes

def check_lock_file():
    """Check if lock file exists"""
    lock_file = "bot.lock"
    if os.path.exists(lock_file):
        try:
            with open(lock_file, 'r') as f:
                pid = f.read().strip()
            return pid
        except:
            return None
    return None

def main():
    print("🔍 Checking for running bot instances...")
    print("=" * 50)
    
    # Check for lock file
    lock_pid = check_lock_file()
    if lock_pid:
        print(f"🔒 Lock file found with PID: {lock_pid}")
    else:
        print("🔓 No lock file found")
    
    # Check for running processes
    bot_processes = check_bot_processes()
    
    if bot_processes:
        print(f"\n🤖 Found {len(bot_processes)} bot process(es):")
        for proc in bot_processes:
            print(f"  PID: {proc['pid']}")
            print(f"  Command: {proc['cmdline']}")
            print()
    else:
        print("\n❌ No bot processes found")
    
    # Check if lock PID matches any running process
    if lock_pid and bot_processes:
        lock_pid = int(lock_pid)
        matching_proc = [p for p in bot_processes if p['pid'] == lock_pid]
        if matching_proc:
            print(f"✅ Lock file PID {lock_pid} matches running process")
        else:
            print(f"⚠️  Lock file PID {lock_pid} doesn't match any running process")
            print("   (This might indicate a stale lock file)")
    
    print("=" * 50)

if __name__ == "__main__":
    main() 