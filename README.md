A simple patcher using python designed to edit code/data contained in Wii modules (REL or RSO files). [The patch format is identical to gecko codetypes](https://wiigeckocodes.github.io/codetypedocumentation.html), but your affected address has to be in terms of an offset into the Module.
***
## Supported Codetypes
- `00` (8 bit write)
- `02` (16 bit write)
- `04` (32 bit write)
- `06` (patch/string write)
- `C2` (Insert ASM)
- `FILE PATH` (Directly appends data from a file located at PATH to the end of the module)

Comments are also supported by beginning a line with #.

***
## Usage
`modpatch.py` loads patches from a .txt file or a folder of .txt files. So a path to a folder or just one txt file can be specificed.
> `python modpatch.py INPUT_MODULE OUTPUT_FILE PATH_TO_PATCHES`
In addition, the following should be considered:
- It is not recommended to patch the same file more than once because patches cannot be undone and patches are meant to be modular.
- In most cases, modules will have to be decompressed to be edited then compressed in the same fashion to work in-game.
- The patcher makes the assumption that the game loads the entire module into memory at once. This is true for most games.
