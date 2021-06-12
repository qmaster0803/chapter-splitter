from vosk import Model, KaldiRecognizer
import argparse
import os
import subprocess
import json
import datetime
from pydub import AudioSegment

arg_parser = argparse.ArgumentParser(description="Generate json listing of audio file (Russian STT)")
arg_parser.add_argument('input', type=str, help="Path to source audio file")

args = arg_parser.parse_args()

if not os.path.exists("model.large"):
    print ("Please download the model from https://alphacephei.com/vosk/models and unpack as 'model' in the current folder.")
    exit (1)

def generate_json_for_audio(path_to_audio, path_to_output):
    audio = AudioSegment.from_file(path_to_audio)
    audio_duration = audio.duration_seconds
    del audio

    sample_rate=16000
    model = Model("model.large")
    rec = KaldiRecognizer(model, sample_rate)
    rec.SetWords(True)

    process = subprocess.Popen(['ffmpeg', '-loglevel', 'quiet', '-i',
                                path_to_audio,
                                '-ar', str(sample_rate) , '-ac', '1', '-f', 's16le', '-'],
                                stdout=subprocess.PIPE)

    WORDS_PER_LINE = 1

    def transcribe():
        results = []
        subs = []
        try:
            while True:
                data = process.stdout.read(4000)
                if len(data) == 0:
                   break
                if rec.AcceptWaveform(data):
                    res = rec.Result()
                    try:
                        for word in json.loads(res)["result"]:
                            results.append(word)
                    except KeyError: pass #no words in this part
                    try: print("Processed", str(datetime.timedelta(seconds=results[-1]["end"])), "from", str(datetime.timedelta(seconds=audio_duration)))
                    except: print("Processed 0:00:00.000000", "from", str(datetime.timedelta(seconds=audio_duration)))
            try:
                for word in json.loads(rec.FinalResult())["result"]:
                    results.append(word)
            except KeyError: pass
        except KeyboardInterrupt: print("Aborted.")
        return results

    res = transcribe()
    with open(path_to_output, "w") as file:
        file.write(json.dumps(res))

if(__name__ == "__main__"):
    if(os.path.isdir(args.input)):
        print("Working in dir mode")
        files = os.listdir(args.input)
        for file in files:
            if(os.path.splitext(file)[1] == ".mp3"):
                print("Working on", file)
                generate_json_for_audio(args.input+"/"+file, args.input+"/"+os.path.splitext(file)[0]+".json")
        print("Done")
    else:
        generate_json_for_audio(args.input, os.path.splitext(args.input)[0]+".json")