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
	
def check_for_catalog_updates():
	try:
		response = urllib.request.urlopen(f"{GB_HOST}{GB_CATALOG}")
	except urllib.error.URLError as e:
		print(e)	
		return False, None
	else:
		if catalog_exists():
			local_modified = time.gmtime( os.path.getmtime(ARCHIVE_PATH) )
			remote_modified = parse_date_header( response.getheader("last-modified") )

			for i in range(len(remote_modified)):
				if local_modified[i] >= remote_modified[i]:
					response.close()
					return False, response
	
	return True, response
			
def download_catalog(response=None):
	try:
		if response is None:
			response = urllib.request.urlopen(f"{GB_HOST}{GB_CATALOG}")
	except urllib.error.URLError as e:
		print(e)	
		return False
	else:
		if not os.path.isdir(BOOK_DIR): os.makedirs(BOOK_DIR)

		temp_buf = response.read()
		response.close()

		with open(ARCHIVE_PATH, "wb") as save_stream:
			save_stream.seek(0)
			save_stream.write(temp_buf)

	return True

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

def download_title(title_number, title=None):
	if title is None:
		file_name = f"{title_number}"
	else:
		file_name = f"{title_number} - {title}"
	url = f"{GB_HOST}/files/{title_number}/{title_number}-0.txt"

	try:
		response = urllib.request.urlopen(url)
	except urllib.error.URLError as e:
		print(e)
	else:
		buf = response.read() 
		with open(f"{BOOK_DIR}{file_name}.txt", "wb") as save_file:
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

	print("Checking for catalog updates...")
	update, response = check_for_catalog_updates()	
	if update:
		print("Updating catalog...")
		update = download_catalog(response)
		print("Catalog updated.")
	else:
		print("No updates found.")	

	if catalog_exists():
		print(f"Searching for keywords {keywords}...") 
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
