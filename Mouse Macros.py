import tkinter as tk
from tkinter import filedialog, simpledialog
import subprocess
import os
import sys
from pynput.mouse import Controller as MouseController
from pynput.keyboard import Controller as KeyboardController, Key
import time
from pynput import mouse
from pynput.keyboard import Listener
import keyboard
import threading



recorded_inputs = []
replay_count = 0
status_label = None
recording_in_progress = False
thread_stop_event = threading.Event()
replay_count = 1




def on_click(x, y, button, pressed):
    if recording_in_progress and pressed:
        recorded_inputs.append((time.time(), f"Mouse Click: {x}, {y}"))

def on_move(x, y):
    if recording_in_progress:
        recorded_inputs.append((time.time(), f"Mouse Move: {x}, {y}"))

def get_replay_count():
    global replay_count
    replay_count = simpledialog.askinteger("Replay Count", "Enter the number of replays:")


def on_press(key):
    global recording_in_progress, recorded_inputs, stop_flag, thread_stop_event, replay_count

    if key == Key.f8:
        if not recording_in_progress:
            print("Recording Started")
            recorded_inputs.clear()
            recording_in_progress = True
            update_status_label("Recording Started")

    elif key == Key.f9:
        if recording_in_progress:
            print("Recording Stopped")
            recording_in_progress = False
            update_status_label("Recording Stopped")
            save_inputs_to_file()

    elif key == Key.f10:
        if not recording_in_progress:
            file_path = filedialog.askopenfilename(title="Select Recorded Inputs File", filetypes=[("Text files", "*.txt")])
            if not file_path:
                print("No file selected. Exiting.")
                return
        recorded_inputs = read_recorded_inputs(file_path)
        if replay_count > 0:
            play_macro_repeatedly(recorded_inputs, replay_count)
            print("Playing Recorded Inputs")
        else:
            print("Replay count not set. Defaulting to 1.")
            replay_count = 1
            play_macro_repeatedly(recorded_inputs, replay_count)
            print("Playing Recorded Inputs")
    elif key == Key.esc:
        print("Escape Key pressed")
        thread_stop_event.set()

def update_status_label(text):
    # Function to update the status label on the GUI
    status_label.config(text=text)

def save_inputs_to_file():
    filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if filename:
        with open(filename, "w") as file:
            for timestamp, input_event in recorded_inputs:
                file.write(f"{timestamp}: {input_event}\n")
def mouse_listener_thread():
    # Function to start the mouse listener
    with mouse.Listener(on_click=on_click, on_move=on_move) as mouse_listener:
        mouse_listener.join()
def start_keyboard_listener():
    # Function to start the keyboard listener
    with Listener(on_press=on_press) as keyboard_listener:
        keyboard_listener.join()
        


def read_recorded_inputs(file_path):
    # Function to read recorded inputs from the text file
    recorded_inputs = []
    with open(file_path, "r") as file:
        for line in file:
            line = line.strip()
            if ": " in line:
                timestamp_str, event_data = line.split(": ", 1)
                try:
                    timestamp = float(timestamp_str)
                    recorded_inputs.append((timestamp, event_data))
                except ValueError:
                    print(f"Invalid timestamp format: {timestamp_str}. Skipping line.")
            else:
                print(f"Invalid line format: {line}. Skipping line.")
    return recorded_inputs

def play_macro_repeatedly(recorded_inputs, repeat_count):
    global thread_stop_event 
    mouse_controller = MouseController()
    keyboard_controller = KeyboardController()

    for _ in range(repeat_count):
        if thread_stop_event.is_set():
            print("Stop Function Activated. Stopping..")
            break
        
        for i in range(len(recorded_inputs)):
            timestamp, event_data = recorded_inputs[i]
            # Get the timestamp of the next event (if it exists) to calculate the delay
            next_timestamp = recorded_inputs[i + 1][0] if i + 1 < len(recorded_inputs) else None

            # Calculate the delay until the next event (if available)
            delay = next_timestamp - timestamp if next_timestamp else 0

            # Wait for the appropriate time delay between actions
            time.sleep(max(0, delay))

            if thread_stop_event.is_set():
                print("Stop Function Activated. Stopping..")
                break

            if "Mouse Click" in event_data:
                x, y = map(int, event_data.split(": ")[1].split(", "))
                mouse_controller.position = (x, y)
                mouse_controller.click(mouse.Button.left)

            elif "Mouse Move" in event_data:
                # Skip the event if it doesn't contain valid x, y values
                if len(event_data.split(": ")) < 2:
                    continue
                
                x, y = map(int, event_data.split(": ")[1].split(", "))
                mouse_controller.position = (x, y)

            elif "Keyboard Press" in event_data:
                # Extract the key from the event string
                key = event_data.split(": ")[1]
                # Perform the keyboard press
                keyboard_controller.press(key)
                keyboard_controller.release(key)

def start_keyboard_listener():
    # Function to start the keyboard listener
    keyboard_listener = threading.Thread(target=keyboard_listener_thread)
    keyboard_listener.start()

def keyboard_listener_thread():
    # Function to start the keyboard listener
    with Listener(on_press=on_press) as keyboard_listener:
        keyboard_listener.join()



def main():
    global status_label, recorded_inputs
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    status_window = tk.Toplevel()
    status_window.title("Recording Status")
    status_window.attributes("-topmost", True)  # Set the window to always be on top
    status_label = tk.Label(status_window, text="Not Recording")
    status_label.pack()

    get_replay_count()

    # Start the mouse listener in a separate thread
    mouse_thread = threading.Thread(target=mouse_listener_thread)
    mouse_thread.start()

    # Start the keyboard listener in a separate thread
    keyboard_listener = threading.Thread(target=start_keyboard_listener)
    keyboard_listener.start()

    # Start the main event loop
    root.mainloop()
    

    # Stop the keyboard listener when the main event loop exits
    keyboard.unhook_all()

if __name__ == "__main__":
    main()
