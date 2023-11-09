import os
import os.path
import urllib.error
import urllib.request
import gzip
import csv

BOOK_DIR = "books/"
GB_HOST = "https://www.gutenberg.org"
GB_CATALOG = "/cache/epub/feeds/pg_catalog.csv.gz"
ARCHIVE_PATH = f"{BOOK_DIR}{GB_CATALOG.split('/')[-1]}"

def catalog_exists():
	return os.path.isfile(ARCHIVE_PATH[:-3])
# Fetch Project Gutenberg catalog from GB_CATALOG 
def get_catalog():
	try:
		if os.path.isdir(BOOK_DIR) == False:
			os.makedirs(BOOK_DIR)
		temp_file, headers = urllib.request.urlretrieve(f"{GB_HOST}{GB_CATALOG}")
	except:
		pass
	else:
		with open(temp_file, "rb") as temp_stream:
			temp_buf = temp_stream.read()
			with open(ARCHIVE_PATH, "wb") as save_stream:
				save_stream.seek(0)
				save_stream.write(temp_buf)	

			with open(ARCHIVE_PATH[:-3], "wb") as save_stream:
				with gzip.open(ARCHIVE_PATH) as gz_file:
					gz_buffer = gz_file.read()
					save_stream.write(gz_buffer)

def search_catalog(keywords, fields=["Title"], language="en"):
	result = []
	with open(ARCHIVE_PATH[:-3]) as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			if row["Language"] != language: continue
			for key in row:
				if key not in fields: continue
				for word in keywords:
					if word.lower() in row[key].lower():
						result.append(row)
	return result

def download_title(title_number, filename=None):
	if filename is None:
		filename = title_number
	url = f"{GB_HOST}/files/{title_number}/{title_number}-0.txt"
	try:
		file_name, headers = urllib.request.urlretrieve(url)
	except:
		pass
	else:
		print(url)
		with open(file_name, "rb") as temp_file:
			buf = temp_file.read() 
			with open(f"{BOOK_DIR}{title_number}-{filename}.txt", "wb") as save_file:
				save_file.seek(0)
				save_file.write(buf) 



def count_words(words):
	return len(words.split())

def count_letters(words):
	result = {}
	for l in words.lower():
		if not l.isalpha(): continue

		if (l in result):
			result[l] += 1
		else:
			result[l] = 0
	
	return result

def print_report(book_path):
	contents = ""
	
	with open(book_path) as f:
		contents = f.read()
	
	print(f"--- Begin report of {book_path} ---\n")
	print(f"{count_words(contents)} words found in the document\n")

	letters = count_letters(contents)
	def get_count(e):
		return letters[e]

	letter_list = list(letters)
	letter_list.sort(reverse=True, key=get_count)

	for l in letter_list:
		print(f"The {l} character was found {letters[l]} times")
	
	print("\n--- End report ---")

if __name__ == "__main__":
	print("Downloading and printing word report for all EN/.TXT ebooks for 'Frankenstein' on Project Gutenberg")
	if not catalog_exists():
		get_catalog()

	if catalog_exists():
		search_results = search_catalog(["frankenstein"])
		for result in search_results:
			download_title(result["Text#"], result["Title"])
			book_path = f"{BOOK_DIR}{result['Text#']}-{result['Title']}.txt"
			if os.path.isfile(book_path):
				print(f"{result['Text#']}: {result['Title']}")
				print_report(book_path)
	else:
		print("Failed to download catalog")
