import os


def lista_file_progetto(directory_base="."):
    escludi = {".venv", ".env", "__pycache__", ".git"}
    for root, dirs, files in os.walk(directory_base):
        dirs[:] = [d for d in dirs if d not in escludi]
        for file in files:
            print(os.path.join(root, file))


if __name__ == "__main__":
    lista_file_progetto()
