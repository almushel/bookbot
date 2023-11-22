# gutengreb

Gutengreb is a python module and command-line utility for downloading specific public domain ebooks from the Project Gutenberg library, while following their access [rules for robots](https://www.gutenberg.org/policy/robot_access.html). 
As these rules aren't particularly explicit about what constitutes "the Project Gutenberg website," which is "intended for human users only," there is still some risk of temporary or permanent IP block.
See their official recommendations for bulk downloading and mirroring large numbers of their files.

Gutengreb can check and download the latest catalog (updated once per week), search it for books given a list of keywords, and download ebooks in a variety of formats based on those results.

# Using the CLI

The command-line interface takes one positional argument, a comma-separate list of keywords, and multiple optional arguments.
It currently downloads the catalog and ebooks to `books/` in the current working directory.

| Argument 				| Default	| 							Description									|
| --------------------- | --------- | --------------------------------------------------------------------- |
| `keywords`			|   N/A   	| A comma-separated list of keywords used for searching and downloading |
| `-f`/`--formats`		| `"txt"`	| A comma-separated list of file formats to be downloaded |
| `-f2`/`--fields`		| `"Title"`	| A comma=separated list of metadata fields to search |
| `--noupdate` 			| `False` 	| Disable the default catalog update check and download |
| `-o`/`--out`			| `books/`	| Set the output directory for book/catalog downloads. |
| `-c`/`--catalog`		| `books/`	| Set the download directory for the catalog (takes prioritity over `-o` value) |
| `-r`/`--report`		| `False` 	| Print a verbose report of the search results |
| `-i`/`--interactive`	| `False` 	| Enter interactive mode to search and filter results in real-time |
| `-d`/`--download`		| `False` 	| Download a set of books, given a list of Title#s passed as keywords |
| `-s`/`--search`		| `False` 	| Search and output a list of Title#s |