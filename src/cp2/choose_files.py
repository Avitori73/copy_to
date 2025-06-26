import os
from cp2.load_files import load_files_to_cache


def choose_file_to_copy():
    """
    Choose a file to copy from the current directory.
    """

    cache = load_files_to_cache()

    if not cache:
        print("No files available to copy.")
        return None

    print("Available files:")
    for i, (file, path) in enumerate(cache.items(), start=1):
        print(f"{i}: {file} ({path})")

    choice = input("Enter the number of the file you want to copy: ")

    try:
        choice_index = int(choice) - 1
        if 0 <= choice_index < len(cache):
            selected_file = list(cache.keys())[choice_index]
            return selected_file
        else:
            print("Invalid choice. Please try again.")
            return None
    except ValueError:
        print("Invalid input. Please enter a number.")
        return None
