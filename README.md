# gutengreb

Gutengreb is a python module and command-line utility for downloading specific public domain ebooks from the Project Gutenberg library, while following their access [rules for robots](https://www.gutenberg.org/policy/robot_access.html). 
As these rules aren't particularly explicit about what constitutes "the Project Gutenberg website," which is "intended for human users only," there is still some risk of tempory or permanent IP block.
See their official recommendations for bulk downloading and mirroring large numbers of their files.

Gutengreb can check and download the latest catalog (updated once per week), search it for books given a list of keywords, and download ebooks in a variety of formats based on those results.

**Note:** *The CLI is currently hardcoded to grab English language `.txt`/`.epub` Frankenstein books for testing purpose.*