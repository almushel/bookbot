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
	
	parser.add_argument("keywords", type=comma_separated_list, help="Search keywords. In (-d)ownload mode, list of ebook text #s")
	parser.add_argument("-f", "--formats", type=comma_separated_list, default=["txt"], help="ebook formats to download")
	parser.add_argument("-f2", "--fields", type=comma_separated_list, default=["Title"], help="Metadata fields to search for keywords")
#	parser.add_argument("-o", "--out", type=str, help="Output directory for downloaded files") 
	parser.add_argument("--noupdate", action="store_true", help="Skip catalog update check")
	parser.add_argument("-r", "--report", action="store_true", help="Print metadata for all search and download results.")

	group = parser.add_mutually_exclusive_group()
	group.add_argument("-d", "--download", action="store_true", help="Download ebooks, given list of Project Gutenbook book text #s")
	group.add_argument("-s", "--search", action="store_true", help="Search catalog and print as list of text #s")
	
	args = parser.parse_args()
	if not validate_args(args):
		exit()

#	if args.out: greb.book_dir = args.out

	if not args.noupdate:
		print("Checking for catalog updates...")
		update, response = greb.check_for_catalog_updates()	
		if update:
			print("Updating catalog...")
			update = greb.download_catalog(response)
			print("Catalog updated.")
		else:
			print("No updates found.")	

	search_results = []
	if greb.catalog_exists():
		if not args.download:
				print(f"Searching for keywords {args.keywords} in fields {args.fields}...") 
				search_results = greb.search_catalog(args.keywords, args.fields)
		else: # Download-only mode
			for word in args.keywords:
				if word.isnumeric():
					result = greb.search_catalog([word], ["Text#"])
					if len(result):	search_results.append( result[0] )	
					else:			print(f"Text number {word} not found.")
				else:
					print(f"Invalid Text#: {word}")	
	else: # not catalog_exists()
		print("Failed to open catalog")

	if not args.search:
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
	else: # search-only mode
		output = ""
		for result in search_results:
			output += result["Text#"]+","
		print(output[:-1])

	if args.report:
		width = os.get_terminal_size()[0]
		divider = "\n" + "-" * (width//1) + "\n"
		print("\nGREB RESULTS:")
		print(divider)
		for result in search_results:
			for key in result:
				print(f"{key}: {result[key]}")
			print(divider)