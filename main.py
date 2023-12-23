from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
from datasets import load_dataset
import time
import torch
import random
import soundfile as sf
import os



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

def save_text_to_speech(text, speaker_embeddings, output_filename):
    # preprocess text
    inputs = processor(text=text, return_tensors="pt").to(device)

    # generate speech with the models
    speech = model.generate_speech(inputs["input_ids"], speaker_embeddings, vocoder=vocoder)

    # save the generated speech to a file with 16KHz sampling rate
    start = time.process_time()
    sf.write(output_filename, speech.cpu().numpy(), samplerate=16000)
    # return the filename for reference
    return [output_filename, time.process_time() - start]


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
            new_string.append(word)

    # join the words of new_string to form a string
    temp_str = ' '.join(new_string)
    return temp_str.replace('-', ' ').rstrip('.') + '.'


def print_hi(res_dir, file, text):
    # Use a breakpoint in the code line below to debug your script.
    target = res_dir + '/' + file + '.mp3'
    if not os.path.exists(target):
        name = 'Mike, the Gods creature.'
        res = save_text_to_speech(text, speaker_embeddings, target)
        print(res)
    else:
        print('File ' + target + ' exists. Skipping')


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    run: float = time.process_time()
    res_dir = 'book'
    print('Res dir ' + res_dir + ' start load time ' + str(run))

    file = 'source/book.txt'
    res_dir = 'results' + file

    if not os.path.exists(res_dir):
        os.makedirs(res_dir)

    i = 0
    with open(file, 'r', encoding='UTF-8') as file:
        while line := file.readline():
            if len(line) < 2:
                continue
            i = i + 1
            str_data = convert_number(line.rstrip())
            print_hi(res_dir, 'r_' + str(i), str_data)
            print(str_data)




# See PyCharm help at https://www.jetbrains.com/help/pycharm/
