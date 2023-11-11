import time
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
	return os.path.isfile(ARCHIVE_PATH)

def parse_date_header(date):
	# Mon, 00 Jan 2023 00:00:00 GMT
	month_values = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12 }
	date_length = len(date)

	start = 5	
	day = date[start:-date_length+(start+2)]
	
	start += 3
	month = date[start:-date_length+(start+3)]

	start += 4
	year = date[start:-date_length+(start+4)]

	start += 5
	hours = date[start:-date_length+(start+2)]

	start += 3
	minutes = date[start:-date_length+(start+2)]

	start += 3
	seconds = date[start:-date_length+(start+2)]

	return (int(year), month_values[month], int(day), int(hours), int(minutes), int(seconds))
	
def update_catalog():
	update = True
	print("Checking for catalog updates...")
	try:
		if os.path.isdir(BOOK_DIR) == False:
			os.makedirs(BOOK_DIR)
		
		response = urllib.request.urlopen(f"{GB_HOST}{GB_CATALOG}")

		if catalog_exists():
			local_modified = time.gmtime( os.path.getmtime(ARCHIVE_PATH) )
			remote_modified = parse_date_header( response.getheader("last-modified") )

			for i in range(len(remote_modified)):
				if local_modified[i] >= remote_modified[i]:
					update = False
					break
	except:
		# TO-DO: Some actual error handling
		pass
	else:
		if update:
			print("Updating catalog...")
			temp_buf = response.read()
			with open(ARCHIVE_PATH, "wb") as save_stream:
				save_stream.seek(0)
				save_stream.write(temp_buf)

def search_catalog(keywords, fields=["Title"], language="en"):
	result = []
	with gzip.open(ARCHIVE_PATH, "rt") as csvfile:
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
	keywords = ["frankenstein"]
	update_catalog()

	if catalog_exists():
		print(f"Searching for keywords {keywords}") 
		search_results = search_catalog(keywords)
		for result in search_results:
			book_path = f"{BOOK_DIR}{result['Text#']}-{result['Title']}.txt"
			if os.path.isfile(book_path):
				print(f"Local TXT file for {result['Text#']}: {result['Title']}" )
			else:
				print(f"Attempting to download .txt format for {result['Text#']}: {result['Title']}")
				download_title(result["Text#"], result["Title"])

			if os.path.isfile(book_path):
				print(f"Downloaded {result['Text#']}: {result['Title']}")
#				print_report(book_path)
	else:
		print("Failed to open catalog")
