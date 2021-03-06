import json
import argparse
import Levenshtein
import sys
import signal
import ffmpeg
import subprocess
import os

def signal_handler(sig, frame):
    print()
    print('Aborted.')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def queryYN(text):
    result = True
    while(True):
        inp = input(text+" [Y/n]")
        if(inp.lower() == 'y' or inp == ""): break
        if(inp == 'n'):
            result = False
            break
    return result

def queryNum(text):
    result = 0
    while(True):
        inp = input(text)
        try: result = int(inp)
        except ValueError: print("Please enter correct number")
        else: break
    return result

arg_parser = argparse.ArgumentParser(description="Split mp3 to chapters using search entry")
arg_parser.add_argument('input_audio', type=str, help="Path to source audio file")
arg_parser.add_argument('search_mask', type=str, help="Phrase to search (every entry would used as start of new chapter)")
arg_parser.add_argument('-name_length', type=int, help="Words added after search_mask in chapter name")
arg_parser.add_argument('-d', action="store_true", help="Delete source files after completing action")

args = arg_parser.parse_args()

if(args.name_length): add_words_after_search = args.name_length
else: add_words_after_search = 1

if(not os.path.splitext(args.input_audio)[0]+".json"):
    print("JSON file with markup should have same name as audio file")
    sys.exit(1)

with open(os.path.splitext(args.input_audio)[0]+".json") as file:
    markup = json.loads(file.read())

parsed_phrase = args.search_mask.split(" ")
levenshtein_thresold = int(round(len(parsed_phrase)+len(parsed_phrase)/2))
chapters = []
scan_complete = False

while(not scan_complete):
    chapters = []
    for offset in range(len(markup)-len(parsed_phrase)+1):
        offsetted_part = [i["word"] for i in markup[offset:offset+len(parsed_phrase)]]
        now_phrase = " ".join(offsetted_part)
        if(Levenshtein.distance(now_phrase, " ".join(parsed_phrase)) <= levenshtein_thresold):
            chapters.append([offset, " ".join([i["word"] for i in markup[offset:offset+len(parsed_phrase)+add_words_after_search]])])

    print("File contains", len(chapters), "chapter(s); Chapters start with:")
    for i, chapter in enumerate(chapters):
        print(i+1, "-", chapter[1])

    if(not queryYN("Is it correct?")):
        print("Increasing thresold.")
        levenshtein_thresold += 1
        continue
    else: scan_complete = True

input_file = ffmpeg.input(args.input_audio)

start_num_from = 0
while(True):
    start_num_from = queryNum("Which chapter is first in this audio? ")
    exists = False
    for i in range(start_num_from, start_num_from+len(chapters)):
        if(os.path.exists("output/chapter_"+str(i)+".mp3")): exists = True
    if(exists):
        print("Can't create output numeration: file(s) exists!")
    else: break

os.makedirs("output", exist_ok=True)
for i in range(len(chapters)):
    print("Processing", i+1, "from", len(chapters))
    start_time = markup[chapters[i][0]]["start"]-1
    if(i == len(chapters)-1):
        end_time = None #end of file
    else:
        end_time = markup[chapters[i+1][0]-1]["start"]+1
    #print("Start time:", start_time, " end time:", end_time)
    if(end_time): proc = subprocess.Popen(['ffmpeg', '-loglevel', 'quiet', '-i', args.input_audio, '-c:a', 'copy', '-ss', str(start_time), '-t', str(end_time-start_time), 'output/chapter_'+str(start_num_from+i)+'.mp3'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else: proc = subprocess.Popen(['ffmpeg', '-loglevel', 'quiet', '-i', args.input_audio, '-c:a', 'copy', '-ss', str(start_time), 'output/chapter_'+str(start_num_from+i)+'.mp3'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    proc.wait()

if(args.d):
    os.remove(args.input_audio)
    os.remove(os.path.splitext(args.input_audio)[0]+".json")