import argparse
from re import search
import sys
import os.path
import enum
import gutengreb as greb

class Interactive_Modes(enum.IntEnum):
	MODE_SELECT = 0
	SEARCH = enum.auto()
	REMOVE = enum.auto()
	VIEW = enum.auto()
	FINISH = enum.auto()

def comma_separated_list(list_str):
	return list_str.split(",")

def validate_args(args):
	formats = []
	for val in args.formats:
		if val in greb.FILE_EXTENSIONS:
			formats.append(val)
		else:
			print(f"Invalid file format \"{val}\" ignored.", file=sys.stderr)
	if not len(formats):
		print("No valid file formats found. Exiting.", file=sys.stderr)
		return False

	fields = []
	for val in args.fields:
		if val in greb.SEARCH_FIELDS:
			fields.append(val)
		else:
			print(f"Invalid search field \"{val}\" ignored.", file=sys.stderr)
	if not len(fields):
		print("No valid search fields found. Exiting.", file=sys.stderr)
		return False

	args.formats = formats
	args.fields = fields

	return True

def interactive_mode(args):
	search_results = []
	state = Interactive_Modes.MODE_SELECT
	running = True

	while running:
		if state == Interactive_Modes.MODE_SELECT:
			prompt_input = input("(s)earch, (r)emove from results, (v)iew results, (f)inish\n")	
			if prompt_input == "s":
				state = Interactive_Modes.SEARCH
			elif prompt_input == "r":
				state = Interactive_Modes.REMOVE
			elif prompt_input == "v":
				state = Interactive_Modes.VIEW
			elif prompt_input == "f":
				state = Interactive_Modes.FINISH
			else:
				print("Invalid command")

		elif state == Interactive_Modes.SEARCH:
			prompt_input = input("Search keywords (comma-separated): ")
			keywords = prompt_input.split(",")
			prompt_input = input("Search fields (comma-separated): ")
			fields = prompt_input.split(",")

			print(f"Searching for {keywords} in {fields}")
			new_results = greb.search_catalog(keywords, fields)
			
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

		elif state == Interactive_Modes.REMOVE:
			prompt_input = input("Title number to remove: ")
			if prompt_input.isnumeric():
				for result in search_results:
					if result["Text#"] == prompt_input:
						search_results.remove(result)
						print(f"Text#{prompt_input} removed")
			else: 
				print("Invalid Text#")
			state = Interactive_Modes.MODE_SELECT

		elif state == Interactive_Modes.VIEW:
			# TO-DO: Re-use args.report behavior
			prompt_input = input("View (s)imple or (d)etailed summary? ")
			if prompt_input == "s":
				for result in search_results:
					print(result.description())
				state = Interactive_Modes.MODE_SELECT
			elif prompt_input == "d":
				for result in search_results:
					print(result)
				state = Interactive_Modes.MODE_SELECT
			else:
				print("Invalid command")

		elif state == Interactive_Modes.FINISH:
			print("Finishing...")
			running = False
	return search_results

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
	group.add_argument("-i", "--interactive", action="store_true", help="Run in interactive mode")
	group.add_argument("-d", "--download", action="store_true", help="Download ebooks, given list of Project Gutenbook book text #s")
	group.add_argument("-s", "--search", action="store_true", help="Search catalog and print as list of text #s")
	
	args = parser.parse_args()
	if not validate_args(args):
		exit()

#	if args.out: greb.book_dir = args.out

	if not args.noupdate:
		update, response = greb.check_for_catalog_updates()	
		if update:
			update = greb.download_catalog(response)

	search_results = []
	if greb.catalog_exists():
		if args.interactive:
			search_results = interactive_mode(args)
		elif args.download:
			for word in args.keywords:
				if word.isnumeric():
					result = greb.search_catalog([word], ["Text#"])
					if len(result):	search_results.append( result[0] )	
					else:			print(f"Text number {word} not found.", file=sys.stderr)
				else:
					print(f"Invalid Text#: {word}", file=sys.stderr)	
		else:
			search_results = greb.search_catalog(args.keywords, args.fields)
	else: # not catalog_exists()
		print("Failed to open catalog.", file=sys.stderr)

	if not args.search:
		for result in search_results:
			for format in args.formats:
				book_path = greb.book_dir+greb.format_file_name(result["Text#"], result["Title"], format)
				if os.path.isfile(book_path):
					success = True
				else:
					success = greb.download_title(result["Text#"], result["Title"], format)

				if success:
					print(book_path)
	else: # search-only mode
		output = ""
		for result in search_results:
			output += result["Text#"]+","
		print(output[:-1])

	if args.report:
		width = os.get_terminal_size()[0]
		divider = "\n" + "-" * (width//1) + "\n"
		print(divider)
		for result in search_results:
			for key in result:
				print(f"{key}: {result[key]}")
			print(divider)