#! bin/sh

echo Testing search-only
python src/main.py Frankenstein -s -f txt,epub,ignore

echo 
echo Testing download-only
python src/main.py 84,41445,42324 -d --formats txt,epub

echo 
echo Testing search and download
python src/main.py Frankenstein --formats txt,epub,trash,garbage -r