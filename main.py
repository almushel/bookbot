import os.path
import gutengreb as greb

if __name__ == "__main__":
	keywords = ["Frankenstein"]
	fields = ["Title"]
	formats = ["txt", "epub"]

	print("Checking for catalog updates...")
	update, response = greb.check_for_catalog_updates()	
	if update:
		print("Updating catalog...")
		update = greb.download_catalog(response)
		print("Catalog updated.")
	else:
		print("No updates found.")	

	if greb.catalog_exists():
		print(f"Searching for keywords {keywords} in fields {fields}...") 
		search_results = greb.search_catalog(keywords, fields)

		for result in search_results:
			for format in formats:
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