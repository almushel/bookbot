#!/bin/sh

echo Testing search-only
python src/main.py Frankenstein -s -f txt,epub,ignore -o books/

echo 
echo Testing download-only
python src/main.py 84,41445,42324 -d --formats txt,epub -o books/ -c books2/

echo 
echo Testing search and download
python src/main.py Frankenstein --formats txt,epub,trash,garbage -o books2/ -c books/ -r --noupdate