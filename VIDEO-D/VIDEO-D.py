import subprocess


def check_install_dependency(package):
    try:
        __import__(package)
    except ImportError:
        subprocess.run(
            ["pip", "install", package, "--user"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        
required_packages = [
    "spotdl",
    "yt_dlp",
    "pystray",
    "requests",
    "validators",
]

for package in required_packages:
    check_install_dependency(package)

import os
import re
import gc
import sys
import time
import ctypes
import signal
import yt_dlp
import shutil
import tempfile
import platform
import requests
import threading
import itertools
import subprocess
import validators
from PIL import Image
from pathlib import Path
from pystray import Icon, MenuItem as item

DOWNLOAD_DIRECTORY = os.path.join(os.path.expanduser("~/Downloads"), "DOWNLOAD")

download_directory = os.path.abspath(DOWNLOAD_DIRECTORY)

os.makedirs(download_directory, exist_ok=True)

session = requests.Session()

start_time = time.time()


def on_exit(icon):
    icon.stop()

    # FIND AND DELETE DYNAMICALLY GENERATED TEMPORARY FOLDERS
    temp_folder_pattern = re.compile(r"(_MEI|\_ME|\_M|\_)\d+")
    temp_dir = Path(tempfile.gettempdir())

    for folder in temp_dir.iterdir():
        if folder.is_dir() and temp_folder_pattern.match(folder.name):
            try:
                shutil.rmtree(folder)
            except PermissionError:
                time.sleep(1)
                shutil.rmtree(folder, ignore_errors=True)

    os._exit(0)


def tray_thread(icon):
    icon.run()


def stop_tray_thread():
    icon.stop()


def setup_tray(icon_path):
    image = Image.open(icon_path)
    menu = (item("EXIT", on_exit),)
    icon = Icon("name", image, "SPOTUBE", menu=menu)
    return icon


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def center_console():
    # Get the console window handle
    h_wnd = ctypes.windll.kernel32.GetConsoleWindow()

    # Get the screen size
    screen_width = ctypes.windll.user32.GetSystemMetrics(0)
    screen_height = ctypes.windll.user32.GetSystemMetrics(1)

    # Get the console window rectangle
    rect = ctypes.wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(h_wnd, ctypes.byref(rect))

    # Calculate the new position
    console_width = rect.right - rect.left
    console_height = rect.bottom - rect.top
    x = (screen_width - console_width) // 2
    y = (screen_height - console_height) // 2

    # Move the console window
    ctypes.windll.user32.MoveWindow(h_wnd, x, y, console_width, console_height, True)


def setup_console():
    try:
        ctypes.windll.kernel32.SetConsoleTitleW("SPOTUBE v2.6")

        HWND = ctypes.windll.kernel32.GetConsoleWindow()
        style = ctypes.windll.user32.GetWindowLongW(HWND, -16)  # GWL_STYLE
        style &= ~0x00040000  # WS_SIZEBOX
        style &= ~0x00010000  # WS_MAXIMIZEBOX
        ctypes.windll.user32.SetWindowLongW(HWND, -16, style)

        set_screen_buffer_size(120, 30)
        disable_text_selection()
        set_console_transparency(0.9)

    except Exception as e:
        print(f"ERROR SETTING UP CONSOLE: {e} ⚠️")


def set_screen_buffer_size(width, height):
    try:
        subprocess.call(f"mode con: cols={width} lines={height}", shell=True)
    except Exception as e:
        print(f"ERROR SETTING SCREEN BUFFER SIZE: {e} ⚠️")


def disable_text_selection():
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), 128)
    except Exception as e:
        print(f"ERROR DISABLING TEXT SELECTION: {e} ⚠️")


def set_console_transparency(transparency):
    try:
        HWND = ctypes.windll.kernel32.GetConsoleWindow()
        ctypes.windll.user32.SetLayeredWindowAttributes(
            HWND, 0, int(255 * transparency), 2
        )
    except Exception as e:
        print(f"ERROR SETTING CONSOLE TRANSPARENCY: {e} ⚠️")


if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit(0)
else:
    setup_console()


def signal_handler(_, __):
    clear_console()
    print("\033[91m {}\033[00m".format("-- PROGRAM TERMINATED BY USER."))
    stop_tray_thread()
    time.sleep(2)
    sys.exit(0)


def my_hook(d):
    if d["status"] == "downloading":
        progress = int(
            float(re.sub(r"\x1b\[[0-9;]*m", "", d["_percent_str"]).replace("%", ""))
        )
        progress_bar_length = 20
        filled_length = int(progress_bar_length * progress // 100)

        elapsed_time = int(d["elapsed"]) if "elapsed" in d else 0

        # Convert elapsed time to HH:MM format
        elapsed_minutes, elapsed_seconds = divmod(elapsed_time, 60)
        elapsed_time_formatted = "{:02}:{:02}".format(elapsed_minutes, elapsed_seconds)

        print(
            "\rPROGRESS: [{}{}] -{} -TIME {}".format(
                "=" * filled_length,
                " " * (progress_bar_length - filled_length),
                progress,
                elapsed_time_formatted,
            ),
            end="",
            flush=True,
        )


def clear_cookies(session):
    session.cookies.clear()


def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def clear_console():
    os.system("cls" if os.name == "nt" else "clear")


def choose_audio_codec_spotify(video_number, is_playlist):
    while True:
        clear_console()
        if is_playlist:
            print("DOWNLOAD SPOTIFY PLAYLIST...")
        else:
            print(f"AUDIO NUMBER: [{video_number}]")

        print("CHOOSE AUDIO CODEC:")
        print("1. MP3")
        print("2. OGG")
        print("3. M4A")
        print("4. WAV")
        print("5. OPUS")
        print("6. FLAC")
        audio_codec_choice = input("ENTER THE NUMBER: ")
        clear_console()

        audio_codecs = {
            "1": "mp3",
            "2": "ogg",
            "3": "m4a",
            "4": "wav",
            "5": "opus",
            "6": "flac",
        }

        audio_codec = audio_codecs.get(audio_codec_choice)
        if audio_codec is None:
            print(
                "\033[91m {}\033[00m".format(
                    "INVALID AUDIO CODEC CHOICE ❌ PLEASE ENTER A NUMBER BETWEEN 1 AND 6."
                )
            )
            time.sleep(2)
            continue

        return audio_codec


def choose_audio_bitrate_spotify(video_number, is_playlist):
    while True:
        clear_console()
        if is_playlist:
            print("DOWNLOAD SPOTIFY PLAYLIST...")
        else:
            print(f"AUDIO NUMBER: [{video_number}]")

        print("CHOOSE AUDIO CODEC:")
        print("1. 128K")
        print("2. 192K")
        print("3. 224K")
        print("4. 256K")
        print("5. 320K")

        audio_bitrates = {
            "1": "128k",
            "2": "192k",
            "3": "224k",
            "4": "256k",
            "5": "320k",
        }
        audio_bitrate_choice = input("ENTER THE NUMBER: ")
        clear_console()

        audio_bitrate = audio_bitrates.get(audio_bitrate_choice)
        if audio_bitrate is None:
            print(
                "\033[91m {}\033[00m".format(
                    "INVALID AUDIO BITRATE CHOICE ❌ PLEASE ENTER A NUMBER BETWEEN 1 AND 5. "
                )
            )
            time.sleep(2)
            continue

        return audio_bitrate


def download_from_spotify(url, video_number):
    global DOWNLOAD_DIRECTORY
    start_time = time.time()

    if not validators.url(url) or "spotify" not in url.lower():
        print("\033[91m {}\033[00m".format(f"SKIPPING.. INVALID SPOTIFY URL: [{url}]"))
        return False

    spotify_directory = os.path.join(DOWNLOAD_DIRECTORY, "SPOTIFY")
    create_directory(spotify_directory)

    try:
        clear_console()
        clear_cookies(session)

        # Detect if the URL is a Spotify playlist
        is_playlist = "playlist" in url.lower()

        if is_playlist:
            print("DOWNLOAD SPOTIFY PLAYLIST...")
        else:
            print(f"AUDIO NUMBER: [{video_number}]...")

        audio_codec = choose_audio_codec_spotify(video_number, is_playlist)
        audio_bitrate = choose_audio_bitrate_spotify(video_number, is_playlist)

        print(
            f"SPOTIFY: [{video_number}]  AUDIO CODEC: [{audio_codec.upper()}] | AUDIO BITRATE: [{audio_bitrate.upper()}]"
        )

        command = [
            "spotdl",
            url,
            "--output",
            spotify_directory,
            "--bitrate",
            audio_bitrate,
            "--format",
            audio_codec,
        ]

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        # Detect if the URL is a Spotify playlist
        is_playlist = "playlist" in url.lower()

        if is_playlist:
            print("DOWNLOAD SPOTIFY PLAYLIST...")
        else:
            pass

        def hide_cursor():
            sys.stdout.write("\033[?25l")
            sys.stdout.flush()

        def show_cursor():
            sys.stdout.write("\033[?25h")
            sys.stdout.flush()

        spinner = itertools.cycle(["█■■■■", "■█■■■", "■■█■■", "■■■█■", "■■■■█"])
        hide_cursor()
        while process.poll() is None:
            print(f"\rSPOTIFY DOWNLOAD {next(spinner)}", end="", flush=True)
            time.sleep(0.2)
        show_cursor()

        clear_console()
        print("\rSPOTIFY DOWNLOAD START...")

        while True:
            output = process.stdout.readline()
            error = process.stderr.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                if "SPOTIFY DOWNLOAD:" in output:
                    print(output.strip())
            if error:
                print(f"ERROR: {error}")

        for i in range(101):
            time.sleep(0.02)
            my_hook(
                {
                    "status": "downloading",
                    "_percent_str": f"{i}%",
                    "elapsed": time.time() - start_time,
                }
            )

        print("\nDOWNLOAD FROM SPOTIFY FINISHED ✅")
        time.sleep(3)
        return True

    except subprocess.CalledProcessError as e:
        print(
            "\033[91m {}\033[00m".format(f"ERROR DOWNLOAD FROM SPOTIFY: {e.stderr} ❌")
        )
        return False
    except Exception as e:
        print("\033[91m {}\033[00m".format(f"UNEXPECTED ERROR: {e} ❌"))
        return False


def get_available_resolutions(url):
    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        resolutions = set()
        resolutions_list = []  # List to hold resolutions for indexing

        if "entries" in info:
            # It's a playlist, get resolutions for each video in the playlist
            for video in info["entries"]:
                for stream in video.get("formats", []):
                    if "height" in stream and stream["vcodec"] != "none":
                        resolution = stream["height"]
                        if resolution not in resolutions:  # Ensure uniqueness
                            resolutions.add(resolution)
                            resolutions_list.append(resolution)
        else:
            # It's a single video, get resolutions as usual
            for stream in info.get("formats", []):
                if "height" in stream and stream["vcodec"] != "none":
                    resolution = stream["height"]
                    if resolution not in resolutions:  # Ensure uniqueness
                        resolutions.add(resolution)
                        resolutions_list.append(resolution)

        return resolutions_list

    except yt_dlp.DownloadError as e:
        print(f"ERROR: {e}")
        return []  # Exit the function by returning an empty list on error


def download_video_with_resolution(url, video_number, total_videos):
    try:
        global DOWNLOAD_DIRECTORY

        youtube_directory = os.path.join(DOWNLOAD_DIRECTORY, "YOUTUBE")
        create_directory(youtube_directory)

        resolutions = get_available_resolutions(url)

        if not resolutions:
            print("NO AVAILABLE RESOLUTIONS FOUND ⚠️")
            return

        # Reverse the resolutions list
        resolutions_list = list(reversed(resolutions))

        clear_console()

        if total_videos > 2:
            print(f"-- DOWNLOAD YOUTUBE PLAYLIST VIDEO: [{total_videos}]")
        else:
            print(f"VIDEO NUMBER: [{video_number}]...")

        print("AVAILABLE VIDEO RESOLUTIONS:")

        while True:
            for idx, resolution in enumerate(resolutions_list, 1):
                print(f"{idx}. RESOLUTION {resolution}p")

            resolution_choice = input("ENTER THE NUMBER OF YOUR CHOICE: ")

            try:
                resolution_index = int(resolution_choice) - 1

                if 0 <= resolution_index < len(resolutions_list):
                    selected_resolution = resolutions_list[resolution_index]
                    clear_console()

                    if total_videos > 2:
                        print(f"DOWNLOAD YOUTUBE PLAYLIST..")
                        print(
                            f"SELECTED RESOLUTION: [ {selected_resolution}p ] | YOUTUBE PLAYLIST VIDEO: [{total_videos}]"
                        )

                    else:
                        clear_console()
                        print(f"SELECTED RESOLUTION: [ {selected_resolution}p ]")
                        print(f"YOUTUBE DOWNLOAD...")

                    yt_opts = {
                        "outtmpl": os.path.join(
                            youtube_directory, f"{video_number}_%(title)s.%(ext)s"
                        ),
                        "format": f"bestvideo[height={selected_resolution}]+bestaudio/best",
                        "progress_hooks": [my_hook],
                        "quiet": True,
                        "noprogress": True,
                        "no_warnings": True,
                    }

                    with yt_dlp.YoutubeDL(yt_opts) as ydl:
                        ydl.download([url])

                    print(" ")
                    print("\nDOWNLOAD YOUTUBE VIDEO FINISHED ✅")
                    time.sleep(3)
                    break  # Exit the loop if the resolution choice is valid

                else:
                    clear_console()
                    print(
                        "\033[91m {}\033[00m".format(
                            f"INVALID RESOLUTION CHOICE. PLEASE ENTER A NUMBER BETWEEN 1 AND {len(resolutions_list)} ❌"
                        )
                    )

            except ValueError:
                clear_console()
                print("INVALID INPUT. PLEASE ENTER A VALID NUMBER ❌")

    except Exception as e:
        print(f"ERROR: {str(e)}")


def get_total_playlist_songs(url):
    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if "entries" in info:
            return len(info["entries"])
        else:
            return 1  # It's a single video, not a playlist

    except yt_dlp.DownloadError as e:
        print(f"ERROR: {e}")
        return 0  # Return 0 on error


def get_youtube_playlist_name(url):
    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,  # This option is added to get only the playlist title
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if "title" in info:
            return info["title"]
        else:
            return "UNKNOWN PLAYLIST"

    except yt_dlp.DownloadError as e:
        print(f"ERROR: {e} ❌")
        return "UNKNOWN PLAYLIST"


def print_menu():
    center_console()
    clear_console()
    print("╔════════════════════════════╗")
    print("║      CHOOSE AN OPTION      ║")
    print("╠════════════════════════════╣")
    print("║  1. DOWNLOAD FROM SPOTIFY  ║")
    print("║  2. DOWNLOAD FROM YOUTUBE  ║")
    print("║  3. QUIT                   ║")
    print("╚════════════════════════════╝")


def download_from_youtube(urls):
    url_list = [url.strip() for url in urls.split(",")]
    video_number = 1

    for url in url_list:
        if validators.url(url) and (
            "youtube.com" in url.lower() or "youtu.be" in url.lower()
        ):
            # Display "Please wait" message for playlist links
            is_playlist = "list=" in url.lower()
            if is_playlist:
                clear_console()
                print(f"PROCESSING YOUTUBE PLAYLIST: ", flush=True)
                print("PLEASE WAIT...", end="", flush=True)

                # Add a delay to allow time for fetching playlist information
                time.sleep(1)

                playlist_name = get_youtube_playlist_name(url)
                clear_console()
                print(f"\rPROCESSING YOUTUBE PLAYLIST: [{playlist_name}]", flush=True)
                print("PLEASE WAIT..", end="", flush=True)
                time.sleep(15)
                print("\rPLEASE WAIT. SET FEW THINGS...")

            total_videos = get_total_playlist_songs(url)

            # Download video with resolution
            download_video_with_resolution(url, video_number, total_videos)

            video_number += 1
        else:
            print(
                "\033[91m {}\033[00m".format(
                    f"SKIPPING.. INVALID SPOTIFY URL: [{url}] ❌"
                )
            )
            time.sleep(3)
            main()

    ask_for_more_downloads()


# Modify the download_spotify_songs function
def download_spotify_songs():
    urls = input("ENTER SPOTIFY URLS: ")
    url_list = [url.strip() for url in urls.split(",")]
    video_number = 1

    for url in url_list:
        if validators.url(url) and "spotify" in url.lower():
            if not download_from_spotify(url, video_number):
                # If download fails, skip to the next URL
                continue
            video_number += 1
        else:
            print(
                "\033[91m {}\033[00m".format(
                    f"SKIPPING.. INVALID SPOTIFY URL: [{url}] ❌"
                )
            )
            time.sleep(2)
            main()

    ask_for_more_downloads()


def ask_for_more_downloads():
    while True:
        clear_console()
        input("PRESS ENTER TO MAIN MENU...")
        clear_console()
        print("WAIT...")
        time.sleep(3)
        clear_console()
        main()


def main():
    signal.signal(signal.SIGINT, signal_handler)

    try:
        if platform.system() == "Windows":
            # Windows-specific console setup functions
            setup_console()

        while True:
            print_menu()

            choice = input("ENTER THE NUMBER: ")

            if choice == "1":
                download_spotify_songs()

            elif choice == "2":
                urls = input("ENTER YOUTUBE URLS: ")
                download_from_youtube(urls)

            elif choice == "3":
                clear_console()
                print("EXITING TOOL -THANKS FOR USING..")
                time.sleep(3)
                clear_console()
                icon.stop()

                # FIND AND DELETE DYNAMICALLY GENERATED TEMPORARY FOLDERS
                temp_folder_pattern = re.compile(r"(_MEI|\_ME|\_M|\_)\d+")
                temp_dir = Path(tempfile.gettempdir())

                for folder in temp_dir.iterdir():
                    if folder.is_dir() and temp_folder_pattern.match(folder.name):
                        try:
                            shutil.rmtree(folder)
                        except PermissionError:
                            time.sleep(1)
                            shutil.rmtree(folder, ignore_errors=True)

                os._exit(0)

            else:
                clear_console()
                print(
                    "\033[91m {}\033[00m".format(
                        f"INVALID OPTION ❌ - PLEASE ENTER 1 2 OR 3"
                    )
                )
                continue

    except KeyboardInterrupt:
        clear_console()
        print("\033[91m {}\033[00m".format("-- PROGRAM TERMINATED BY USER"))
        sys.exit(0)
    finally:
        gc.collect()


if __name__ == "__main__":
    script_directory = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(script_directory, r"_ICON\ICON.ico")
    icon = setup_tray(icon_path)

    if icon:
        tray_thread = threading.Thread(target=tray_thread, args=(icon,))
        tray_thread.start()
    else:
        print("TRAY SETUP FAILED ⚠️")
    try:
        main()
    except Exception as e:
        pass
