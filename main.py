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

def main():
	book_dir = "books/frankenstein.txt"
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

main()