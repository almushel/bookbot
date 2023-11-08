import urllib.request
import gzip
# import csv

BOOK_DIR = "books/"
GB_HOST = "https://www.gutenberg.org"
GB_CATALOG = "/cache/epub/feeds/pg_catalog.csv.gz"

# Fetch Project Gutenberg catalog from GB_CATALOG 
def get_catalog():
	catalog_archive_path = f"{BOOK_DIR}{GB_CATALOG.split('/')[-1]}"

	temp_file, headers = urllib.request.urlretrieve(f"{GB_HOST}{GB_CATALOG}")
	temp_stream = open(temp_file, "rb")
	temp_buf = temp_stream.read()

	save_stream = open(catalog_archive_path, "wb")
	save_stream.seek(0)
	save_stream.write(temp_buf)	

	temp_stream.close()
	save_stream.close()

	save_stream = open(catalog_archive_path[:-3], "wb")
	gz_file = gzip.open(catalog_archive_path)
	gz_buffer = gz_file.read()
	save_stream.write(gz_buffer)

	save_stream.close()
	gz_file.close()

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

if __name__ == "__main__":
	if False:	
		get_catalog()
	else:
		book_dir = f"{BOOK_DIR}frankenstein.txt"
		contents = ""
		
		with open(book_dir) as f:
			contents = f.read()
		
		print(f"--- Begin report of {book_dir} ---\n")
		print(f"{count_words(contents)} words found in the document\n")

		letters = count_letters(contents)
		def get_count(e):
			return letters[e]

		letter_list = list(letters)
		letter_list.sort(reverse=True, key=get_count)

		for l in letter_list:
			print(f"The {l} character was found {letters[l]} times")
		
		print("\n--- End report ---")