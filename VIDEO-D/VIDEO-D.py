import os
import sys
import time
import datetime
import requests
import validators
import subprocess
from pytube import YouTube

DOWNLOAD_DIRECTORY = os.path.join(os.path.expanduser("~"), "Downloads")

download_directory = os.path.abspath(DOWNLOAD_DIRECTORY)

os.makedirs(download_directory, exist_ok=True)

session = requests.Session()

start_time = time.time()

def progress_bar(
    iteration, total, start_time=None, prefix="", suffix="", decimals=1, length=20
):
    if start_time is None:
        start_time = time.time()

    percent = 100 * (iteration / float(total))
    percent = min(percent, 100.0)
    iteration = min(iteration, total)

    filled_length = int(length * iteration // total)
    elapsed_time = time.time() - start_time

    if elapsed_time < 60:
        time_format = f"{elapsed_time:.1f} sec"
    else:
        minutes = elapsed_time // 60
        seconds = elapsed_time % 60
        time_format = f"{minutes:.0f}:{seconds:.1f} SEC"

    formatted_text = (
        f"\r{prefix}|{'=' * filled_length}{'-' * (length - filled_length)}| "
        f"-{percent:.{decimals}f} -TIME {time_format} {suffix}"
    )

    print(formatted_text, end="", flush=True)

    if iteration == total:
        print()

def clear_cookies(session):
    session.cookies.clear()

def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def clear_console():
    if os.name == "nt":
        _ = os.system("cls")
    else:
        _ = os.system("clear")

def download_from_spotify(url, video_number):
    global DOWNLOAD_DIRECTORY
    start_time = time.time()

    if not validators.url(url):
        print("INVALID SPOTIFY URL.")
        return

    spotify_directory = os.path.join(DOWNLOAD_DIRECTORY, "SPOTIFY")
    create_directory(spotify_directory)

    try:
        clear_console()
        clear_cookies(session)
        print(f"VIDEO NUMBER: [{video_number}]...")
        print("CHOOSE AUDIO CODEC :")
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
            print("INVALID AUDIO CODEC CHOOSE")
            return

        print("CHOOSE AUDIO BITRATE:")
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
            print("INVALID AUDIO BITRATE CHOOSE.")
            return

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

        print("DOWNLOAD FROM SPOTIFY...", end="", flush=True)
        time.sleep(15)
        print("\rPLEASE WAIT. SET FEW THINGS...")

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
            time.sleep(0.1)
            progress_bar(
                i,
                100,
                start_time,
                prefix="SPOTIFY DOWNLOAD: ",
                suffix=" ",
                length=20,
            )

        print("\nDOWNLOAD FROM SPOTIFY COMPLETED.")

    except subprocess.CalledProcessError as e:
        print(f"ERROR DOWNLOAD FROM SPOTIFY: {e.stderr}")
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")

def validate_youtube_url(url):
    if not validators.url(url):
        print("\033[1m" + "\033[38;2;255;165;0m" + "INVALID YOUTUBE URL." + "\033[0m")
        return False
    return True

def sanitize_filename(filename):
    # Replace special characters with an underscore
    filename = "".join(c if c.isalnum() or c in [" ", "."] else "_" for c in filename)
    # Replace multiple spaces with a single space
    filename = " ".join(filename.split())
    return filename

def download_from_youtube(url, download_directory, video_number):
    start_time = time.time()
    if not validate_youtube_url(url):
        return

    youtube_directory = os.path.join(download_directory, "YOUTUBE")
    create_directory(youtube_directory)

    try:
        clear_console()
        clear_cookies(session)

        print(f"VIDEO NUMBER: [{video_number}]...")
        print("CHOOSE VIDEO CODEC")
        print("1. VP9")
        print("2. AV1")
        print("3. H.264")
        print("4. H.265")
        print("5. NVENC H.264")
        video_codec_choice = input("ENTER THE NUMBER: ")
        clear_console()

        video_codecs = {
            "1": "libvpx-vp9",
            "2": "libaom-av1",
            "3": "libx264",
            "4": "libx265",
            "5": "h264_nvenc",  # NVIDIA NVENC H.264 codec
        }
        video_codec = video_codecs.get(video_codec_choice)
        if video_codec is None:
            print("INVALID CHOICE")
            return

        print("CHOOSE AUDIO CODEC:")
        print("1. AAC")
        print("2. MP3")
        print("3. FLAC")
        print("4. Opus")  # Adding Opus as an option
        print("5. DOLBY-PLUS")
        audio_codec_choice = input("ENTER THE NUMBER: ")
        clear_console()

        audio_codecs = {
            "1": "aac",
            "2": "mp3",
            "3": "flac",
            "4": "opus",  # Adding Opus to the dictionary
            "5": "eac3",
            # You can continue adding more codec options here
        }

        audio_codec = audio_codecs.get(audio_codec_choice)
        if audio_codec is None:
            print("INVALID CHOICE")
            return

        yt = YouTube(url)
        video_streams = yt.streams.filter(type="video").order_by("resolution").desc()

        print("AVAILABLE VIDEO STREAMS")
        resolutions = {}
        count = 1
        for stream in video_streams:
            if stream.resolution not in resolutions:
                resolutions[stream.resolution] = stream
                print(f"{count}. RESOLUTION {stream.resolution}")
                count += 1

        video_resolution_choice = input("ENTER THE NUMBER: ")
        clear_console()

        try:
            selected_stream = resolutions.get(
                list(resolutions.keys())[int(video_resolution_choice) - 1]
            )
            if selected_stream:
                print(
                    f"SELECTED: [{selected_stream.resolution}] | VIDEO CODEC: [{video_codec}] | "
                    f"AUDIO CODEC: [{audio_codec}]"
                )

                audio_stream = yt.streams.filter(only_audio=True).first()

                if not selected_stream or not audio_stream:
                    print("VIDEO OR AUDIO NOT AVAILABLE")
                    return

                print("YOUTUBE VIDEO DOWNLOAD...", end="", flush=True)
                time.sleep(30)
                print("\rPLEASE WAIT. SET FEW THINGS...")

                sanitized_title = sanitize_filename(yt.title)
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

                video_filename = (
                    f"{sanitized_title}_video_{timestamp}.{selected_stream.subtype}"
                )
                audio_filename = (
                    f"{sanitized_title}_audio_{timestamp}.{audio_stream.subtype}"
                )

                video_path = os.path.join(youtube_directory, video_filename)
                audio_path = os.path.join(youtube_directory, audio_filename)

                selected_stream.download(
                    output_path=youtube_directory, filename=video_filename
                )
                audio_stream.download(
                    output_path=youtube_directory, filename=audio_filename
                )

                merged_filename = f"{sanitized_title}_merged_{timestamp}.mp4"
                merged_path = os.path.join(youtube_directory, merged_filename)

                # https://youtu.be/rSxTumD4kew?si=LxYiRxfRSS76Zrr4

                command = [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "panic",
                    "-hwaccel",
                    "cuda",
                    "-i",
                    video_path,
                    "-i",
                    audio_path,
                    "-c:v",
                    video_codec,
                    "-c:a",
                    audio_codec,
                    "-b:a",
                    "1411k",
                    "-ar",
                    "48000",
                    merged_path,
                ]

                subprocess.run(command, check=True)

                merged_filesize = 100  # Replace with actual file size or duration
                for i in range(merged_filesize + 1):
                    progress_bar(
                        i,
                        merged_filesize,
                        start_time,
                        prefix="YOUTUBE: ",
                        suffix=" ",
                        length=20,
                    )
                    time.sleep(0.1)

                os.remove(video_path)
                os.remove(audio_path)
                print(f"\nDOWNLOAD YOUTUBE VIDEO COMPLETED...")

            else:
                print("INVALID CHOICE.")
                return
        except (ValueError, IndexError):
            print("INVALID CHOICE.")
            return

    except Exception as e:
        print(f"ERROR: {e}")

def print_menu():
    clear_console()
    print("╔════════════════════════════╗")
    print("║      CHOOSE AN OPTION      ║")
    print("╠════════════════════════════╣")
    print("║  1. DOWNLOAD FROM SPOTIFY  ║")
    print("║  2. DOWNLOAD FROM YOUTUBE  ║")
    print("║  3. QUIT                   ║")
    print("╚════════════════════════════╝")

def main():
    while True:
        print_menu()

        choice = input("ENTER THE NUMBER: ")

        if choice == "1":
            urls = input("ENTER SPOTIFY URLS SEPARATED BY COMMA: ")
            url_list = [url.strip() for url in urls.split(",")]
            video_number = 1

            for url in url_list:
                if validators.url(url) and "spotify" in url.lower():
                    download_from_spotify(url, video_number)
                    video_number += 1
                else:
                    print("SKIPPING.. INVALID SPOTIFY URL:", [url])

        elif choice == "2":
            urls = input("ENTER YOUTUBE URLS SEPARATED BY COMMA: ")
            url_list = [url.strip() for url in urls.split(",")]
            video_number = 1

            for url in url_list:
                if validators.url(url) and (
                    "youtube.com" in url.lower() or "youtu.be" in url.lower()
                ):
                    download_from_youtube(url, DOWNLOAD_DIRECTORY, video_number)
                    video_number += 1
                else:
                    print("SKIPPING.. INVALID YOUTUBE URL: ", [url])

        elif choice == "3":
            clear_console()
            print("TOOL EXITING...")
            time.sleep(5)
            sys.exit()
        else:
            print("INVALID CHOICE. PLEASE ENTER 1, 2, OR 3.")
            time.sleep(2)
            continue

        time.sleep(3)
        input("PRESS ENTER TO CONTINUE...")

        clear_console()
        more_songs = input("DO YOU WANT TO DOWNLOAD MORE SONGS (Y/N): ").lower()
        if more_songs == "n":
            print("EXITING THE TOOL. GOODBYE...")
            time.sleep(5)
            sys.exit()

if __name__ == "__main__":
    main()
