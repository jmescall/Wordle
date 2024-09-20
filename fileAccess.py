import os.path

def sameDirFilePath(file_name: str) -> str:
    '''
    Returns the file path to `file_name` in the current file's directory

    :param file_name: The file to access from the current file's directory
    '''
    return os.path.dirname(__file__) + "/" + file_name