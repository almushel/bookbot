import time
import os
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

def search_row(row, keywords, fields):
	# type: (dict, list[str], list[str]) -> Greb_Result
	result = Greb_Result(row=row)

	for key in row:
		if key not in fields: continue

		r = row[key].lower()
		for word in keywords:
			found = True
			for w in word.lower().split(" "):
				if w not in r:
					found = False
					break
			if found:
				result.relevance += 1

	return result

def search_catalog(keywords, fields=["Title"], languages=["en"]):
	# type: (list[str], list[str], list[str]) -> list[Greb_Result]
	search_results = []
	with gzip.open(get_local_catalog_path(), "rt") as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			if row["Language"] not in languages: continue
			if row["Type"] == "Sound": continue

			result = search_row(row, keywords, fields)
			if result.relevance:
				search_results.append(result)

	return sorted(search_results, key=lambda r: r.relevance, reverse=True)

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

if __name__ == "__main__":
	import argparse
	import sys
	import enum

	class Interactive_Modes(enum.IntEnum):
		MODE_SELECT = 0
		SEARCH = enum.auto()
		VIEW = enum.auto()
		FILTER = enum.auto()
		QUIT = enum.auto()

	def comma_separated_list(list_str):
		# type: (str) -> list[str]
		if len(list_str) == 0:
			return []
		return list_str.split(",")

	def validate_args(args):
		# type: (argparse.Namespace) -> bool
		formats = []
		for val in args.formats:
			if val in FILE_EXTENSIONS:
				formats.append(val)
			else:
				print(f"Invalid file format \"{val}\" ignored.", file=sys.stderr)
		if not len(formats):
			print("No valid file formats found. Exiting.", file=sys.stderr)
			return False

		fields = []
		for val in args.fields:
			if val in SEARCH_FIELDS:
				fields.append(val)
			else:
				print(f"Invalid search field \"{val}\" ignored.", file=sys.stderr)
		if not len(fields):
			print("No valid search fields found. Exiting.", file=sys.stderr)
			return False

		args.formats = formats
		args.fields = fields

		return True

	def report_greb_results(results):
		# type: (list[Greb_Result]) -> None
		width = os.get_terminal_size()[0]
		divider = "-"*width
		print(divider)
		for result in results:
			print(result)
			print(divider)

	def interactive_mode(args):
		# type: (argparse.Namespace) -> list[Greb_Result]
		search_results = []
		keywords = args.keywords
		fields = args.fields	
		if keywords:
			state = Interactive_Modes.SEARCH
			initial_search = True
		else:
			state = Interactive_Modes.MODE_SELECT
			initial_search = False
		running = True

		print("Starting Gutengreb in Interactive Mode")
		while running:
			if state == Interactive_Modes.MODE_SELECT:
				prompt_input = input("(s)earch, (v)iew results, (f)ilter results, (q)uit and execute\n")	
				if prompt_input == "s":
					state = Interactive_Modes.SEARCH
				elif prompt_input == "v":
					state = Interactive_Modes.VIEW
				elif prompt_input == "f":
					state = Interactive_Modes.FILTER
				elif prompt_input == "q":
					state = Interactive_Modes.QUIT
				else:
					print("Invalid command")

			elif state == Interactive_Modes.SEARCH:
				if not initial_search:
					prompt_input = input("Search keywords (comma-separated): ")
					keywords = prompt_input.split(",")
					prompt_input = input("Search fields (comma-separated): ")
					fields = prompt_input.split(",")
				else:
					initial_search = False

				print(f"Searching for {keywords} in {fields}")
				new_results = search_catalog(keywords, fields)
				
				print("Search results: ")
				for r in new_results:
					print(r.description())
				prompt_input = input("Add to final results? (y) or (n) ")
				if prompt_input == "y":
					for r in new_results:
						if r not in search_results:
							search_results.append(r)
				else:
					print("Results discarded")
				state = Interactive_Modes.MODE_SELECT

			elif state == Interactive_Modes.FILTER:
				prompt_input = input("Filter keywords (comma-separated): ")
				keywords = prompt_input.split(",")
				prompt_input = input("Filter fields (comma-separated): ")
				fields = prompt_input.split(",")

				new_results = []
				while True:
					prompt_input = input("(i)nclusive or (e)xclusive: ")
					if prompt_input != "i" and prompt_input != "e":
						print("Invalid response: (i)nclusive or (e)xclusive: ")
					else: break

				for result in search_results:
					found = search_row(result.row, keywords, fields).relevance > 0
					if found:
						if prompt_input == "i":
							new_results.append(result)
					elif prompt_input == "e":
						new_results.append(result)
				
				print("Filtered results: ")
				for r in new_results:
					print(r.description())
				prompt_input = input("Update final results? (y) or (n) ")
				if prompt_input == "y":
					search_results = new_results
				else:
					print("Filtered results discarded")
				state = Interactive_Modes.MODE_SELECT

			elif state == Interactive_Modes.VIEW:
				prompt_input = input("View (s)imple or (d)etailed summary? ")
				if prompt_input == "s":
					for result in search_results:
						print(result.description())
					state = Interactive_Modes.MODE_SELECT
				elif prompt_input == "d":
					report_greb_results(search_results)
					state = Interactive_Modes.MODE_SELECT
				else:
					print("Invalid command")

			elif state == Interactive_Modes.QUIT:
				print("Quitting and processing results...")
				running = False
		return search_results

	parser = argparse.ArgumentParser(
		prog="gutengreb",
		description="A command-line utility for downloading public domain ebooks from Project Gutenberg"
	)
	
	parser.add_argument("keywords", type=comma_separated_list, help="Search keywords. In (-d)ownload mode, list of ebook text #s")
	parser.add_argument("-f", "--formats", type=comma_separated_list, default=["txt"], help="ebook formats to download")
	parser.add_argument("-f2", "--fields", type=comma_separated_list, default=["Title"], help="Metadata fields to search for keywords")
	parser.add_argument("-o", "--out", type=str, help="Output directory for book downloads") 
	parser.add_argument("-c", "--catalog", type=str, help="Set catalog file location (defaults to book directory)")
	parser.add_argument("--noupdate", action="store_true", help="Skip catalog update check")
	parser.add_argument("-r", "--report", action="store_true", help="Print metadata for all search and download results.")

	group = parser.add_mutually_exclusive_group()
	group.add_argument("-i", "--interactive", action="store_true", help="Run in interactive mode")
	group.add_argument("-d", "--download", action="store_true", help="Download ebooks, given list of Project Gutenbook book text #s")
	group.add_argument("-s", "--search", action="store_true", help="Search catalog and print as list of text #s")
	
	args = parser.parse_args()
	if not validate_args(args):
		exit()

	if args.out: 
		book_dir = args.out
		if not args.catalog:
			catalog_dir = args.out

	if args.catalog:
		catalog_dir = args.catalog

	if not args.noupdate:
		update, response = check_for_catalog_updates()	
		if update:
			update = download_catalog(response)

	search_results = []
	if catalog_exists():
		if args.interactive:
			search_results = interactive_mode(args)
		elif args.download:
			for word in args.keywords:
				if word.isnumeric():
					result = search_catalog([word], ["Text#"])
					if len(result):	search_results.append( result[0] )	
					else:			print(f"Text number {word} not found.", file=sys.stderr)
				else:
					print(f"Invalid Text#: {word}", file=sys.stderr)	
		else:
			search_results = search_catalog(args.keywords, args.fields)
	else: # not catalog_exists()
		print("Failed to open catalog.", file=sys.stderr)

	if args.search:
		output = ""
		for result in search_results:
			output += result["Text#"]+","
		print(output[:-1])
	else:
		for result in search_results:
			for format in args.formats:
				book_path = book_dir+format_file_name(result["Text#"], result["Title"], format)
				if os.path.isfile(book_path):
					success = True
				else:
					success = download_title(result["Text#"], result["Title"], format)

				if success:
					print(book_path)

	if args.report:
		report_greb_results(search_results)