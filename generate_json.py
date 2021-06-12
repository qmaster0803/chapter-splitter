#!/usr/bin/env python3

from vosk import Model, KaldiRecognizer
import argparse
import os
import subprocess
import json

arg_parser = argparse.ArgumentParser(description="Generate json listing of audio file (Russian STT)")
arg_parser.add_argument('input', type=str, help="Path to source audio file")

args = arg_parser.parse_args()

if not os.path.exists("model.large"):
    print ("Please download the model from https://alphacephei.com/vosk/models and unpack as 'model' in the current folder.")
    exit (1)

sample_rate=16000
model = Model("model.large")
rec = KaldiRecognizer(model, sample_rate)
rec.SetWords(True)

process = subprocess.Popen(['ffmpeg', '-loglevel', 'quiet', '-i',
                            args.input,
                            '-ar', str(sample_rate) , '-ac', '1', '-f', 's16le', '-'],
                            stdout=subprocess.PIPE)

WORDS_PER_LINE = 1

def transcribe():
    results = []
    subs = []
    count = 0
    try:
        while True:
            data = process.stdout.read(4000)
            if len(data) == 0:
               break
            if rec.AcceptWaveform(data):
                count += 1
                print("Step", count)
                res = rec.Result()
                try:
                    for word in json.loads(res)["result"]:
                        results.append(word)
                except KeyError: pass #no words in this part
        try:
            for word in json.loads(rec.FinalResult())["result"]:
                results.append(word)
        except KeyError: pass
    except KeyboardInterrupt: print("Aborted.")
    return results

res = transcribe()
with open(os.path.splitext(args.input)[0]+".json", "w") as file:
    file.write(json.dumps(res))