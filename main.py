import subprocess

from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
from datasets import load_dataset
import time
import torch
import soundfile as sf
import os
from argparse import ArgumentParser
import glob
import re

import logging

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S')

# import the inflect library
import inflect

p = inflect.engine()

device = "cuda" if torch.cuda.is_available() else "cpu"
# load the processor
processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
# load the model
model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts").to(device)
# load the vocoder, that is the voice encoder
vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan").to(device)
# we load this dataset to get the speaker embeddings
embeddings_dataset = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")

speaker_embeddings = torch.tensor(embeddings_dataset[6799]["xvector"]).unsqueeze(0).to(device)

# argument parser
parser = ArgumentParser()
parser.add_argument("-f", "--file", dest="filename",
                    help="read text from FILE", metavar="FILE", default='example.txt')


# parser.add_argument("-q", "--quiet",
#                    action="store_false", dest="verbose", default=True,
#                    help="don't print status messages to stdout")

def save_text_to_speech(text, speaker_embeddings, output_filename):
    # preprocess text
    inputs = processor(text=text, return_tensors="pt").to(device)

    # generate speech with the models
    speech = model.generate_speech(inputs["input_ids"], speaker_embeddings, vocoder=vocoder)

    # save the generated speech to a file with 16KHz sampling rate
    start = time.process_time()
    sf.write(output_filename, speech.cpu().numpy(), samplerate=16000)
    # return the filename for reference
    return [output_filename, time.process_time() - start, text]

def prepare_case(match_obj):
    if match_obj.group(1) is not None:
        ch_list = ([char for char in match_obj.group(1)])
        return " ".join(ch_list)

def convert_number(text):
    # split string into list of words
    temp_str = text.split()
    # initialise empty list
    new_string = []

    for word in temp_str:
        # if word is a digit, convert the digit
        # to numbers and append into the new_string list
        clear_word = word.strip('.,;')
        if clear_word.isdigit():
            temp = p.number_to_words(clear_word)
            new_string.append(temp)

        # append the word as it is
        else:
            temp = re.sub(r"((^|\s|\()[A-Z]{2,5}(\b|\)))", prepare_case, word)
            new_string.append(temp)

    # join the words of new_string to form a string
    temp_str = ' '.join(new_string)
    return temp_str.replace('-', ' ').rstrip('.') + '.'


def render_audio(res_dir, file, text):
    # Use a breakpoint in the code line below to debug your script.
    target = res_dir + '/' + file + '.mp3'
    if not os.path.exists(target):
        name = 'Mike, the Gods creature.'
        res = save_text_to_speech(text, speaker_embeddings, target)
        print(res)
    else:
        print('File ' + target + ' exists. Skipping')

def build_final_file(parts_path, file_name):
    # Default options
    dir_path = os.getcwd()
    out_file = 'results/' + file_name + '.mp3'

    # Find and sort mp3 files.
    file_paths = sorted(glob.glob(parts_path + '/*.mp3'))

    # Count the number of files.
    num_files = len(file_paths)

    file_list_filename = 'file.list'
    if os.path.isfile(file_list_filename):
        os.remove(file_list_filename)

    with open(file_list_filename, 'a') as file_list:
        for file in file_paths:
            file_list.write('file \'' + file + '\'\n')

    print("Found %d MP3 files in '%s'" % (num_files, dir_path))

    print("Concatenating files...")
    ffmpeg_cmd = ['ffmpeg', '-f', 'concat', '-safe', '0',  '-i', 'file.list', '-acodec', 'copy', out_file]
    command_string = ' '.join(ffmpeg_cmd)
    print('FFMPEG command ' + command_string)

    if os.path.isfile(out_file):
        os.remove(out_file)

    subprocess.run(command_string, shell=True)

    os.remove(file_list_filename)
    print("Wrote '%s' in '%s'" % (out_file, dir_path))



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    args = parser.parse_args()

    if not args.filename:
        parser.print_help()
        exit(0)

    file_name = args.filename

    run: float = time.process_time()
    source_file = 'source/' + file_name
    if not os.path.isfile(source_file):
        print('File ' + source_file + ' not found')
        exit(0)

    print('Reading file ' + source_file + ' start. ML loading time: ' + str(run))

    results_dir = 'results/' + file_name + '.parts'

    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    i = 0
    with open(source_file, 'r', encoding='UTF-8') as source_file:
        while raw_line := source_file.readline():
            lines = raw_line.split('.')

            for line in lines:
                if len(line) < 2:
                    continue
                i = i + 1
                str_data = convert_number(line.rstrip())
                render_audio(results_dir, 'r_' + str(i), str_data)
                logging.info(str_data)
                # print(str_data)

    if i > 0:
        build_final_file(results_dir, file_name)


