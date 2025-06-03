#!/usr/bin/env python3
import os
import time
import subprocess
import argparse
from pathlib import Path

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

class ClipboardManager:
    def __init__(self):
        self.history_file = Path.home() / ".clipboard_history"
        self.max_entries = 5
        self.separator = "---CLIPBOARD_ENTRY_SEPARATOR---"
        
        # Create history file if it doesn't exist
        self.history_file.touch(exist_ok=True)
    
    def get_clipboard_content(self):
        """Get current clipboard content safely"""
        try:
            result = subprocess.run(
                ["xclip", "-o", "-selection", "clipboard"], 
                capture_output=True, text=True, timeout=2
            )
            return result.stdout if result.returncode == 0 else ""
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            print(f"{RED}Error accessing clipboard{RESET}")
            return ""
    
    def set_clipboard_content(self, content):
        """Set clipboard content"""
        try:
            process = subprocess.Popen(
                ["xclip", "-selection", "clipboard"],
                stdin=subprocess.PIPE, text=True
            )
            process.communicate(input=content)
            return process.returncode == 0
        except subprocess.SubprocessError:
            print(f"{RED}Error setting clipboard{RESET}")
            return False
    
    def add_to_history(self):
        """Add current clipboard content to history"""
        content = self.get_clipboard_content()
        
        # Skip if empty
        if not content:
            return False
            
        # Read current history
        try:
            with open(self.history_file, 'r') as f:
                history = f.read()
        except Exception:
            history = ""
            
        # Check if content is same as most recent entry
        entries = history.split(self.separator)
        if entries and entries[0].strip() == content.strip():
            return False
            
        # Add new entry at beginning
        with open(self.history_file, 'w') as f:
            f.write(content)
            f.write(f"\n{self.separator}\n")
            f.write(history)
            
        # Trim to max entries
        self.trim_history()
        return True
    
    def trim_history(self):
        """Keep only max_entries in history file"""
        try:
            with open(self.history_file, 'r') as f:
                content = f.read()
                
            entries = content.split(self.separator)
            if len(entries) > self.max_entries:
                with open(self.history_file, 'w') as f:
                    f.write(self.separator.join(entries[:self.max_entries]))
        except Exception as e:
            print(f"{RED}Error trimming history: {e}{RESET}")
    
    def clear_history(self):
        """Clear the clipboard history"""
        try:
            open(self.history_file, 'w').close()  # Truncate file to zero length
            print(f"{GREEN}Clipboard history cleared.{RESET}")
            return True
        except Exception as e:
            print(f"{RED}Error clearing history: {e}{RESET}")
            return False
    
    def show_history(self):
        """Show history with a simple numbered menu and copy selection to clipboard"""
        try:
            # Display ASCII art banner
            banner = [
                f"{BOLD}{CYAN}  ____ _ _       _                         _  {RESET}",
                f"{BOLD}{CYAN} / ___| (_)_ __ | |__   ___   __ _ _ __ __| | {RESET}",
                f"{BOLD}{CYAN}| |   | | | '_ \| '_ \ / _ \ / _` | '__/ _` | {RESET}",
                f"{BOLD}{CYAN}| |___| | | |_) | |_) | (_) | (_| | | | (_| | {RESET}",
                f"{BOLD}{CYAN} \____|_|_| .__/|_.__/ \___/ \__,_|_|  \__,_| {RESET}",
                f"{BOLD}{CYAN}          |_|                                 {RESET}",
                f"{BOLD}{GREEN}History Mode{RESET}"
            ]
            
            for line in banner:
                print(line)
                
            with open(self.history_file, 'r') as f:
                content = f.read()
                
            if not content.strip():
                print(f"\n{YELLOW}Clipboard history is empty{RESET}")
                return
                
            # Process the entries
            entries = content.split(self.separator)
            display_entries = []
            full_entries = []
            
            for entry in entries:
                if entry.strip():
                    # Get just the first line for display
                    first_line = entry.strip().split('\n')[0]
                    
                    # Truncate if first line is too long
                    if len(first_line) > 60:
                        first_line = first_line[:57] + "..."
                    
                    # Add indicator if multiline
                    if '\n' in entry.strip():
                        first_line += f" {BLUE}[...]{RESET}"
                        
                    display_entries.append(first_line)
                    full_entries.append(entry.strip())
            
            if not display_entries:
                print(f"{YELLOW}No valid entries in clipboard history{RESET}")
                return
            
            while True:
                print(f"\n{CYAN}=== {BOLD}Clipboard History{RESET} {CYAN}==={RESET}")
                
                # Display numbered menu
                for i, item in enumerate(display_entries, 1):
                    print(f"{YELLOW}{i}{RESET}. {item}")
                
                print(f"\n{CYAN}=== {BOLD}Options{RESET} {CYAN}==={RESET}")
                print(f"{BOLD}Enter a number{RESET} to copy to clipboard")
                print(f"'{BOLD}p{RESET}' to preview an entry")
                print(f"'{BOLD}c{RESET}' to clear history")
                print(f"'{BOLD}q{RESET}' to quit")
                
                choice = input(f"\n{CYAN}>{RESET} ").strip().lower()
                
                if choice == 'q':
                    return
                elif choice == 'c':
                    # Clear history confirmation
                    confirm = input(f"{YELLOW}Are you sure you want to clear clipboard history? (y/n):{RESET} ").strip().lower()
                    if confirm == 'y' or confirm == 'yes':
                        if self.clear_history():
                            return  # Exit after clearing
                elif choice == 'p':
                    # Preview mode
                    preview_num = input(f"{CYAN}Enter number to preview:{RESET} ").strip()
                    try:
                        preview_index = int(preview_num) - 1
                        if 0 <= preview_index < len(full_entries):
                            print(f"\n{CYAN}=== {BOLD}Preview{RESET} {CYAN}==={RESET}")
                            preview_lines = full_entries[preview_index].split('\n')[:10]  # Limit to 10 lines
                            for line in preview_lines:
                                print(line)
                                
                            if len(preview_lines) < full_entries[preview_index].count('\n') + 1:
                                print(f"\n{YELLOW}(Content truncated...){RESET}")
                                
                            input(f"\n{BLUE}Press Enter to continue{RESET}")
                        else:
                            print(f"{RED}Invalid number{RESET}")
                            input(f"{BLUE}Press Enter to continue{RESET}")
                    except ValueError:
                        print(f"{RED}Please enter a valid number{RESET}")
                        input(f"{BLUE}Press Enter to continue{RESET}")
                else:
                    # Selection mode
                    try:
                        index = int(choice) - 1
                        if 0 <= index < len(full_entries):
                            selected = full_entries[index]
                            if self.set_clipboard_content(selected):
                                print(f"{GREEN}Copied to clipboard!{RESET}")
                                return
                        else:
                            print(f"{RED}Invalid number{RESET}")
                    except ValueError:
                        print(f"{RED}Please enter a valid number, 'p', 'c', or 'q'{RESET}")
                
        except Exception as e:
            print(f"{RED}Error showing history: {e}{RESET}")
            import traceback
            traceback.print_exc()
    
    def monitor(self):
        """Monitor clipboard for changes and add to history"""
        last_content = ""
        
        # Draw ASCII art banner
        banner = [
            f"{BOLD}{CYAN}  ____ _ _       _                         _  {RESET}",
            f"{BOLD}{CYAN} / ___| (_)_ __ | |__   ___   __ _ _ __ __| | {RESET}",
            f"{BOLD}{CYAN}| |   | | | '_ \| '_ \ / _ \ / _` | '__/ _` | {RESET}",
            f"{BOLD}{CYAN}| |___| | | |_) | |_) | (_) | (_| | | | (_| | {RESET}",
            f"{BOLD}{CYAN} \____|_|_| .__/|_.__/ \___/ \__,_|_|  \__,_| {RESET}",
            f"{BOLD}{CYAN}          |_|                                 {RESET}",
            f"{BOLD}{GREEN}Monitor Mode{RESET}"
        ]
        
        for line in banner:
            print(line)
        
        print(f"\n{YELLOW}Starting clipboard monitor...{RESET}")
        
        # Log to file for debugging
        log_file = Path.home() / ".clipboard_monitor.log"
        with open(log_file, 'a') as log:
            log.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Monitor started\n")
            
            # Test clipboard access at startup
            try:
                test_content = self.get_clipboard_content()
                log.write(f"Initial clipboard test: {'Success' if test_content is not None else 'Failed'}\n")
                log.flush()
            except Exception as e:
                log.write(f"Error testing clipboard: {str(e)}\n")
                log.flush()
        
        retry_count = 0
        max_retries = 5
        
        # Spinner animation for monitoring
        spinner = ['-', '\\', '|', '/']
        spin_idx = 0
        
        try:
            while True:
                try:
                    # Show spinner animation
                    print(f"\r{CYAN}Monitoring clipboard {spinner[spin_idx]}{RESET}", end='')
                    spin_idx = (spin_idx + 1) % len(spinner)
                    
                    current_content = self.get_clipboard_content()
                    
                    # Reset retry count on successful clipboard access
                    retry_count = 0
                    
                    if current_content and current_content != last_content:
                        if self.add_to_history():
                            timestamp = time.strftime('%H:%M:%S')
                            print(f"\r{GREEN}Clipboard updated at {timestamp}{RESET}        ")
                            with open(log_file, 'a') as log:
                                log.write(f"[{timestamp}] Clipboard updated\n")
                        last_content = current_content
                except Exception as e:
                    retry_count += 1
                    with open(log_file, 'a') as log:
                        log.write(f"[{time.strftime('%H:%M:%S')}] Error: {str(e)}\n")
                    
                    if retry_count >= max_retries:
                        print(f"\n{RED}Too many errors ({retry_count}), exiting{RESET}")
                        with open(log_file, 'a') as log:
                            log.write(f"Too many errors ({retry_count}), exiting\n")
                        break
                        
                    # Wait longer between retries
                    time.sleep(5)
                    continue
                    
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Stopping clipboard monitor.{RESET}")
            with open(log_file, 'a') as log:
                log.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Monitor stopped by user\n")


def main():
    parser = argparse.ArgumentParser(description="Clipboard Manager")
    parser.add_argument('action', choices=['add', 'show', 'monitor', 'clear'],
                        help='Action to perform')
    
    args = parser.parse_args()
    manager = ClipboardManager()
    
    if args.action == 'add':
        manager.add_to_history()
    elif args.action == 'show':
        manager.show_history()
    elif args.action == 'monitor':
        manager.monitor()
    elif args.action == 'clear':
        manager.clear_history()

if __name__ == "__main__":
    main()
