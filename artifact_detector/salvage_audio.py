# The code reads a csv file row by row and creates an updated audio (or none) file for each row

import os
import argparse
import pandas as pd
import shutil
from pydub import AudioSegment


def make_dir(dirName):
    # create target directory & all intermediate directories if don't exist
    if not os.path.exists(dirName):
        os.makedirs(dirName)
        print("[INFO] Directory ", dirName, " created")
    else:
        print("[INFO] Directory ", dirName, " already exists")


def get_input_filepath(input_name, dataset_path, mic_id):
    raw_name_list = input_name.split("_")
    sub_id = int(raw_name_list[0])
    trial_id = raw_name_list[1]
    if sub_id in range(121, 143):
        data_folder = 'test_data'
    elif sub_id in range(101, 121):
        data_folder = 'valid_data'
    else:
        data_folder = 'train_data'
    input_filepath = '{}/{}/sub_{}/trial_{}/mic{}_audio_cmd_trim/{}.wav'.format(dataset_path, data_folder, sub_id, trial_id, mic_id, input_name)
    return input_filepath


def get_output_filepath(df, input_name, dataset_path, mic_id):
    raw_name_list = input_name.split("_")
    sub_id = int(raw_name_list[0])
    trial_id = raw_name_list[1]
    if sub_id in range(121, 143):
        data_folder = 'test_data'
    elif sub_id in range(101, 121):
        data_folder = 'valid_data'
    else:
        data_folder = 'train_data'
    output_data_path = '{}/salvaged_files/{}/sub_{}/trial_{}/mic{}_audio_cmd_trim'.format(dataset_path, data_folder, sub_id, trial_id, mic_id)
    make_dir(output_data_path)

    # rename an audio file if needed
    if pd.notna(df.new_name[i]):
        old_name = input_name
        name_list = input_name.split("_")
        name_list[4] = str(int(df.new_name[i]))
        input_name = "_".join(name_list)
        print('[INFO] {}.wav renamed as {}.wav'.format(old_name, input_name))
    output_filepath = '{}/{}.wav'.format(output_data_path, input_name)
    return output_filepath


def copy_audio(input_filepath, output_filepath):
    shutil.copy(input_filepath, output_filepath)


def trim_audio(input_name, input_audio, begin_time, end_time, output_audio_filepath, audio_duration=-100):
    # use audio duration for end timestamp, if NaN
    if pd.isna(end_time):
        end_time = audio_duration
        print('[INFO] done updating end timestamp for {}.wav'.format(input_name))

    # trim an audio file based on timestamps and save it
    output_audio = input_audio[begin_time:end_time]
    output_audio.export(output_audio_filepath, format='wav')


def merge_and_trim_audio(input_name, input_audio, input_audio_2, begin_time, end_time, output_audio_filepath, audio_duration):
    # update end_timestamp
    end_time = end_time + audio_duration
    print('[INFO] done updating end timestamp for {}.wav'.format(input_name))

    # merge two audio files (audio file i with audio file i+1)
    input_audio_2 = AudioSegment.from_wav(input_audio_2)
    merge_output = input_audio + input_audio_2

    # trim and save an audio file
    trim_audio(input_name, merge_output, begin_time, end_time, output_audio_filepath)


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-d", "--dataset", required=True, help="path to dataset")

args = vars(ap.parse_args())

dataset_path = args["dataset"]
print(dataset_path)

# read a csv file without the last column
df = pd.read_csv(dataset_path + '/csvs/salvage_mission_train_data.csv')
df = df.iloc[:, :-1]
print(df)

#salvaged_num = 0

for mic_id in range(2):
    for i in range(len(df)):
        input_name = df.raw_audio_name[i]
        input_audio_filepath = get_input_filepath(input_name, dataset_path, mic_id)
        # check if a file exists
        if os.path.isfile(input_audio_filepath):
            # read an audio file and timestamps
            input_audio = AudioSegment.from_wav(input_audio_filepath)
            audio_duration = 1000 * input_audio.duration_seconds

            # convert seconds to milliseconds
            begin_time = 1000 * int(df.begin_timestamp[i])
            end_time = 1000 * int(df.end_timestamp[i])

            # output path and output file name
            output_audio_filepath = get_output_filepath(df, input_name, dataset_path, mic_id)

            # 4 categories: copy, trim, merge and trim, skip
            if df.comment[i] == 'copy':
                copy_audio(input_audio_filepath, output_audio_filepath)
                print('[INFO] done copying {}.wav'.format(input_name))

            elif df.comment[i] == 'trim':
                trim_audio(input_name, input_audio, begin_time, end_time, output_audio_filepath, audio_duration)
                print('[INFO] done trimming {}.wav'.format(input_name))

            elif df.comment[i] == 'merge and trim':
                # read an audio file on the next row
                input_name_2 = df.raw_audio_name[i+1]
                input_audio_filepath_2 = get_input_filepath(input_name_2, dataset_path, mic_id)
                input_audio_2 = AudioSegment.from_wav(input_audio_filepath_2)

                merge_and_trim_audio(input_name, input_audio, input_audio_2, begin_time, end_time, output_audio_filepath, audio_duration)
                print('[INFO] done merging and trimming {}.wav'.format(input_name))

            elif 'skip' in df.comment[i]:
                # salvaged_num -= 1
                print('[INFO] skipping {}.wav'.format(input_name))

            else:
                # salvaged_num -= 1
                print('[ERROR] comment not provided for {}.wav'.format(input_name))


        else:
            print("[ERROR] {}.wav doesn't exist".format(input_name))

    # salvaged_num += 1
    # print(salvaged_num)
    # salvaged_num = 0