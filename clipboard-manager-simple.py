#!/usr/bin/env python3
import os
import time
import subprocess
import argparse
from pathlib import Path

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
            print("Error accessing clipboard")
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
            print("Error setting clipboard")
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
            print(f"Error trimming history: {e}")
    
    def clear_history(self):
        """Clear the clipboard history"""
        try:
            open(self.history_file, 'w').close()  # Truncate file to zero length
            print("Clipboard history cleared.")
            return True
        except Exception as e:
            print(f"Error clearing history: {e}")
            return False
    
    def show_history(self):
        """Show history with a simple numbered menu and copy selection to clipboard"""
        try:
            with open(self.history_file, 'r') as f:
                content = f.read()
                
            if not content.strip():
                print("Clipboard history is empty")
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
                        first_line += " [...]"
                        
                    display_entries.append(first_line)
                    full_entries.append(entry.strip())
            
            if not display_entries:
                print("No valid entries in clipboard history")
                return
            
            while True:
                print("\n=== Clipboard History ===")
                
                # Display numbered menu
                for i, item in enumerate(display_entries, 1):
                    print(f"{i}. {item}")
                
                print("\nEnter number to copy to clipboard, 'p' to preview an entry, 'c' to clear history, or 'q' to quit")
                choice = input("> ").strip().lower()
                
                if choice == 'q':
                    return
                elif choice == 'c':
                    # Clear history confirmation
                    confirm = input("Are you sure you want to clear clipboard history? (y/n): ").strip().lower()
                    if confirm == 'y' or confirm == 'yes':
                        if self.clear_history():
                            return  # Exit after clearing
                elif choice == 'p':
                    # Preview mode
                    preview_num = input("Enter number to preview: ").strip()
                    try:
                        preview_index = int(preview_num) - 1
                        if 0 <= preview_index < len(full_entries):
                            print("\n=== Preview ===")
                            preview_lines = full_entries[preview_index].split('\n')[:5]  # Limit to 5 lines
                            for line in preview_lines:
                                print(line)
                            if len(preview_lines) < full_entries[preview_index].count('\n') + 1:
                                print("...")
                            input("\nPress Enter to continue")
                        else:
                            print("Invalid number")
                            input("Press Enter to continue")
                    except ValueError:
                        print("Please enter a valid number")
                        input("Press Enter to continue")
                else:
                    # Selection mode
                    try:
                        index = int(choice) - 1
                        if 0 <= index < len(full_entries):
                            selected = full_entries[index]
                            if self.set_clipboard_content(selected):
                                print("Copied to clipboard!")
                                return
                        else:
                            print("Invalid number")
                    except ValueError:
                        print("Please enter a valid number, 'p', 'c', or 'q'")
                
        except Exception as e:
            print(f"Error showing history: {e}")
            import traceback
            traceback.print_exc()
    
    def monitor(self):
        """Monitor clipboard for changes and add to history"""
        last_content = ""
        print("Starting clipboard monitor...")
        
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
        
        try:
            while True:
                try:
                    current_content = self.get_clipboard_content()
                    
                    # Reset retry count on successful clipboard access
                    retry_count = 0
                    
                    if current_content and current_content != last_content:
                        if self.add_to_history():
                            print(f"Clipboard updated at {time.strftime('%H:%M:%S')}")
                            with open(log_file, 'a') as log:
                                log.write(f"[{time.strftime('%H:%M:%S')}] Clipboard updated\n")
                        last_content = current_content
                except Exception as e:
                    retry_count += 1
                    with open(log_file, 'a') as log:
                        log.write(f"[{time.strftime('%H:%M:%S')}] Error: {str(e)}\n")
                    
                    if retry_count >= max_retries:
                        with open(log_file, 'a') as log:
                            log.write(f"Too many errors ({retry_count}), exiting\n")
                        break
                        
                    # Wait longer between retries
                    time.sleep(5)
                    continue
                    
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping clipboard monitor.")
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
