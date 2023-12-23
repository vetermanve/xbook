#!/usr/bin/env bash
# Concatenate mp3 files in a directory into a single mp3.

# Default options
DIR=$(pwd)
OUT_FILE="output.mp3"

help () {
  self=$(basename $0)
  echo "Concatenate mp3 files in a directory into a single mp3."
  echo "Usage: $self -i /path/to/mp3s -o output_name.mp3"
  echo "  -i, --input-dir    Path to directory with mp3s in it."
  echo "                     Defaults to current directory."
  echo "  -o, --output-file  Name of concatenated mp3 file."
  echo "                     Must have .mp3 extension."
  echo "                     Defaults to 'output.mp3'."
}

# Parse command line options.
while [[ $# -gt 0 ]]  # While there are more than 0 arguments to parse
do
  OPTION="$1"
  VALUE="$2"

  case $OPTION in
    -h|--help)
      help; exit 1
    ;;
    -i|--input-dir)
      DIR=$VALUE; shift; shift
    ;;
    -o|--output-file)
      OUT_FILE=$VALUE; shift; shift
    ;;
    *)
      echo "Unrecognized option '$OPTION'"; help; exit 1
    ;;
  esac
done

# Check output file has proper extension.
if [[ "${OUT_FILE: -4}" != ".mp3" ]]
then
  echo "Output filename '$OUT_FILE' must have extension '.mp3'"
  exit 2
fi

# Find and sort mp3 files.
find "$DIR" -maxdepth 1 -iname '*.mp3' | sort -t _ -k 2 -g | sed "s/.*/file \'&\'/" > file.list

NUM_FILES=$(echo $FILES | tr '|' '\n' | wc -l)

echo "Found $NUM_FILES MP3 files in '$DIR'"
#echo "They will be concatenated in this order:"
#echo "########################################"
#echo $FILES | tr '|' '\n' | xargs -I% basename %
#echo $FILES
#return ;
#
## Confirm before concatenating.
#read -p "Is this order OK? (y/n) " -n 1 -r
#echo
#if [[ $REPLY =~ ^[Yy]$ ]]
#then
  echo "Concatenating files..."
  (ffmpeg -f concat -safe 0 -i file.list -acodec copy "$OUT_FILE" )
  echo "Wrote '$OUT_FILE' in '$DIR'"
#fi