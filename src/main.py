import argparse
import os.path
import gutengreb as greb

def comma_separated_list(list_str):
	return list_str.split(",")

def validate_args(args):
	formats = []
	for val in args.formats:
		if val in greb.FILE_EXTENSIONS:
			formats.append(val)
		else:
			print(f"Invalid file format \"{val}\" ignored.")
	if not len(formats):
		print("No valid file formats found. Exiting.")
		return False

	fields = []
	for val in args.fields:
		if val in greb.SEARCH_FIELDS:
			fields.append(val)
		else:
			print(f"Invalid search field \"{val}\" ignored.")
	if not len(fields):
		print("No valid search fields found. Exiting.")
		return False

	args.formats = formats
	args.fields = fields

	return True

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		prog="gutengreb",
		description="A command-line utility for downloading public domain ebooks from Project Gutenberg"
	)
	
	# TO-DO: keywords behavior differs based on program mode:
	# 	"search" & "both": search keywords
	# 	"download": book download title#s
	parser.add_argument("keywords", type=comma_separated_list)
	parser.add_argument("-m", "--mode", type=str, choices=["search", "download", "both"], default="both")
	parser.add_argument("-f", "--formats", type=comma_separated_list, default=["txt"])
	parser.add_argument("-s", "--fields", type=comma_separated_list, default=["Title"])
	
	args = parser.parse_args()
	if not validate_args(args):
		exit()

	print("Checking for catalog updates...")
	update, response = greb.check_for_catalog_updates()	
	if update:
		print("Updating catalog...")
		update = greb.download_catalog(response)
		print("Catalog updated.")
	else:
		print("No updates found.")	

	if greb.catalog_exists():
		print(f"Searching for keywords {args.keywords} in fields {args.fields}...") 
		search_results = greb.search_catalog(args.keywords, args.fields)

		for result in search_results:
			for format in args.formats:
				book_path = greb.book_dir+greb.format_file_name(result["Text#"], result["Title"], format)
				if os.path.isfile(book_path):
					print(f"Local copy exists for {format} for {result['Text#']}: {result['Title']}.")
					continue

				print(f"Attempting to download {format} for {result['Text#']}: {result['Title']}.")

				success = greb.download_title(result["Text#"], result["Title"], format)

				if success:
					print(f"Downloaded {result['Text#']}: {result['Title']} ({format}).")

	else: # not catalog_exists()
		print("Failed to open catalog")