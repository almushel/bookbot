import time
import os
import os.path
from tkinter import W
import urllib.error
import urllib.request
import gzip
import csv

DEFAULT_BOOK_DIR = "books/"
DEFAULT_CATALOG_DIR = DEFAULT_BOOK_DIR
GB_HOST = "https://www.gutenberg.org"
GB_CACHE_PATH = "/cache/epub/"
GB_CATALOG_PATH = GB_CACHE_PATH+"feeds/pg_catalog.csv.gz"


FILE_EXTENSIONS = {
	"html"					: "-images.html",
	"epub3"					: "-images-3.epub",
	"epub"					: "-images.epub",
	"epub-no-images"		: ".epub",
	"kindle"				: "-images-kf8.mobi",
	"kindle-old"			: "-images.mobi",
	"kindle-old-no-images"	: ".mobi",
	"txt"					: ".txt",
	"txt-utf8"				: ".txt.utf8"
}

SEARCH_FIELDS = {
	"Title", "Authors", "Subjects", "Bookshelves"
}

book_dir = DEFAULT_BOOK_DIR
catalog_dir = DEFAULT_CATALOG_DIR

class Greb_Result:
	def __init__(self, relevance = 0, row = {}):
		# type: (int, dict) -> None
		self.relevance = relevance
		self.row = row

	def description(self):
		return "{}: {}".format(self.row["Text#"], self.row["Title"])

	def __iter__(self):
		return iter(self.row.keys())

	def __getitem__(self, key):
		return self.row[key]
	
	def __eq__(self, other):
		result = isinstance(other, Greb_Result)
		result = (other.row == self.row)	
		return result

	def __str__(self):
		result = ""
		for key in self.row:
			result += "{}: {}\n".format(key, self.row[key])
		return result[:-1] # exclude trailing newline

# Expected date format: "Mon, 00 Jan 2023 00:00:00 GMT"
def __parse_date_header(date):
	# type: (str) -> tuple[int, int, int, int, int, int]
	month_values = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12 }

	date_words = date.split(" ")
	if len(date_words) >= 5:
		day, month, year, clock = date_words[1: 5]

		clock_words = clock.split(":")
		if len(clock_words) == 3:
			hours, minutes, seconds = clock.split(":")
			return (int(year), month_values[month], int(day), int(hours), int(minutes), int(seconds))

	return (0,0,0,0,0,0)

def get_local_catalog_path():
	# type: () -> str
	return catalog_dir+"catalog.csv.gz"

def catalog_exists():
	# type: () -> bool
	return os.path.isfile( get_local_catalog_path() )

def format_file_name(title_number, title, file_format):
	# type (str, str, str) -> str
	result = f"{title_number}"
	if title:
		result = f"{title_number} - {title}"
	return result+FILE_EXTENSIONS[file_format]
	
def check_for_catalog_updates():
	# type: () -> tuple[bool, urllib.request._UrlopenRet]
	
	try:
		response = urllib.request.urlopen(GB_HOST+GB_CATALOG_PATH)
	except urllib.error.URLError as e:
		print(e)	
		return False, None
	else:
		if catalog_exists():
			local_modified = time.gmtime( os.path.getmtime( get_local_catalog_path() ) )
			remote_modified = __parse_date_header( response.getheader("last-modified") )

			for i in range(len(remote_modified)):
				if local_modified[i] >= remote_modified[i]:
					response.close()
					return False, response
	
	return True, response
			
def download_catalog(response=None):
	# type: (urllib.request._UrlopenRet) -> bool
	try:
		if response is None:
			response = urllib.request.urlopen(f"{GB_HOST}{GB_CATALOG_PATH}")
	except urllib.error.URLError as e:
		print(e)	
		return False
	else:
		os.makedirs(catalog_dir, exist_ok=True)

		temp_buf = response.read()
		response.close()

		with open(get_local_catalog_path(), "wb") as save_stream:
			save_stream.seek(0)
			save_stream.write(temp_buf)

	return True

def search_catalog(keywords, fields=["Title"], languages=["en"]):
	# type: (list[str], list[str], list[str]) -> list[Greb_Result]
	result = []
	with gzip.open(get_local_catalog_path(), "rt") as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			if row["Language"] not in languages: continue
			if row["Type"] == "Sound": continue

			new_result = Greb_Result(row=row)
			for key in row:
				if key not in fields: continue

				r = row[key].lower()
				for word in keywords:
					found = True
					for w in word.lower().split(" "):
						if w not in r:
							found = False
					if found:
						new_result.relevance += 1
						if new_result not in result:
							result.append(new_result)
	return result

def download_title(title_number, title=None, format="txt"):
	# type: (str, str|None, str) -> bool
	url = GB_HOST+GB_CACHE_PATH+f"/{title_number}/pg{title_number}"+FILE_EXTENSIONS[format]

	try:
		response = urllib.request.urlopen(url)
	except urllib.error.URLError as e:
		print(e)
		return False
	else:
		os.makedirs(book_dir, exist_ok=True)
		file_path = book_dir+format_file_name(title_number, title, format)
		buf = response.read() 
		with open(file_path, "wb") as save_file:
			save_file.seek(0)
			save_file.write(buf) 
		response.close()

	return True