Error extracting file: not a 7z file
Bad7zFile: not a 7z file
Traceback:

File "/home/vscode/.local/lib/python3.11/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 565, in _run_script
    exec(code, module.__dict__)
File "/workspaces/Flash-/app.py", line 78, in <module>
    main()
File "/workspaces/Flash-/app.py", line 71, in main
    extract_exe(file_path, extract_dir)
File "/workspaces/Flash-/app.py", line 34, in extract_exe
    with py7zr.SevenZipFile(file_path, mode='r') as archive:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/vscode/.local/lib/python3.11/site-packages/py7zr/py7zr.py", line 415, in __init__
    raise e
File "/home/vscode/.local/lib/python3.11/site-packages/py7zr/py7zr.py", line 396, in __init__
    self._real_get_contents(password)
File "/home/vscode/.local/lib/python3.11/site-packages/py7zr/py7zr.py", line 432, in _real_get_contents
    raise Bad7zFile("not a 7z file")
