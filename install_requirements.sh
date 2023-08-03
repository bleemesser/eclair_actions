python -m pip install -r requirements.txt
python -m pip uninstall googlesearch-python
python -m pip install googlesearch-python
# linux: 
# CMAKE_ARGS="-DLLAMA_CUBLAS=on" FORCE_CMAKE=1 python -m pip install llama-cpp-python
# macos:
# CMAKE_ARGS="-DLLAMA_METAL=on" FORCE_CMAKE=1 python -m pip install llama-cpp-python
