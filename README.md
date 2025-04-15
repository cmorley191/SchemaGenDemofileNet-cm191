# SchemaGenDemofileNet-cm191

An easy-to-use tool that generates a schema model for [*Deadlock*](what_is_deadlock.md) - a computer game built on Valve's Source 2 engine.
This tool reads your installed game executables and outputs a set of json files describing the game's data structures.

SchemaGenDemofileNet-cm191 is for educational purposes only.

### demofile-net and CS2SchemaGen

This tool's output is designed for use in [saul/demofile-net](https://github.com/saul/demofile-net) -- a library for parsing *Deadlock*'s publicly-available match replay files (called "demos").

saul already has a tool for generating schema models: [saul/CS2SchemaGen](https://github.com/saul/CS2SchemaGen). 
This new tool (SchemaGenDemofileNet-cm191) exists because:
1. CS2SchemaGen "injects" itself into your game *while the game is running*. SchemaGenDemofileNet-cm191 does not use this method, which feels less invasive.
2. SchemaGenDemofileNet-cm191's author couldn't get CS2SchemaGen working at the time this was made. Please create a issue on github if you have any trouble building/using SchemaGenDemofileNet-cm191.

### source2gen

SchemaGenDemofileNet-cm191 is essentially just a fork of c++ schema generator [neverlosecc/source2gen](https://github.com/neverlosecc/source2gen), combined with the json logic of CS2SchemaGen. source2gen and CS2SchemaGen work with other Source 2 games besides *Deadlock*.

### Acknowledgements

A few changes have been added, but the credit for the bulk of this tool goes to saul and NEVERLOSE for their amazing projects. See their projects' READMEs (linked above) for further acknowledgements to other projects and authors in the community.

---

# Building and Usage

This tool's only prescribed use is updating the schema that [saul/demofile-net](https://github.com/saul/demofile-net) is using (whenever *Deadlock* receives an update). This tool is forked from [neverlosecc/source2gen](https://github.com/neverlosecc/source2gen) which has greater capabilities; see that project's README if you're interested in other use cases.

- Prerequisites:
  - Windows
  - Visual Studio 2019 or newer
  - CMake
  - Python 3 (recommended 3.13+)
  - A recent *Deadlock* match replay file (.dem)
    - More details in the steps below
- Clone the repository with submodules:
```
git clone --recurse-submodules <url>
```
- Create the project files (only need to do this once):
```
cmake -B build -DCMAKE_BUILD_TYPE=Release -DSOURCE2GEN_GAME=DEADLOCK
```
- You may open `build\source2gen.sln` in Visual Studio to make any code changes to the tool.
- Build the tool:
```
cmake --build build
```
- Run the loader binary, which is the most automated form of the tool:
```
cd build\bin\Debug
.\source2gen-loader.exe
```
- The tool will generate an output directory called `sdk` next to the binary.
- Apply various post-processing to the output files:
  - (Note: this step has a variation (#2) explained later in this document)
```
cd schema-gen-helpers
py postprocess.py ..\build\bin\Debug\sdk
```
> If you're curious, this is what the post-processing does:
> (it tries to imitate the CS2SchemaGen output format as closely as possible)
> - Removes illegal trailing commas
> - Sorts the schema types in "dependency order": independent types first, followed by types that depend on those types
> - Adds a json field stating the "outer" type of generic types
> - Enforces a json field ordering
> - Removes unnecessary metadata values
> - Minor whitespace changes
- Copy the output files that seem relevant to `demofile-net\src\DemoFile.Game.Deadlock\Schema`
  - (Note: this step has a variation (#3) explained later in this document)
- List all the file names that you copied over in the `schemaFiles` variable of `demofile-net\src\DemoFile.SdkGen\Program.cs`
- Build and run the demofile-net "DemoFile.SdkGen" project. It expects two command line arguments:
  - First argument: the path to the match replay file (.dem) of a recently-played game of *Deadlock*. (i.e. a match played on the most recent game version)
    - Two ways to get a .dem file:
      - Get one of your own game's demos:
        - Play a game
        - On the main menu, click your profile
        - Click the recently played match
        - Click "Download Replay"
      - Get someone else's game (e.g. a streamer):
        - Get the match id (shown during gameplay)
        - On the main menu, click "Watch"
        - Click "Enter Match Id"
        - Click "Download Replay"
      - Downloaded replay files are stored in `...\steamapps\common\Deadlock\game\citadel\replays`
  - Second argument: the path to `demofile-net\src\DemoFile.Game.Deadlock`
  - Full example:
```
cd demofile-net\src\DemoFile.SdkGen\bin\Debug\net7.0
.\DemoFile.SdkGen.exe C:\path\to\steamapps\common\Deadlock\game\citadel\replays\123456789.dem C:\path\to\demofile-net\src\DemoFile.Game.Deadlock
```
- `demofile-net` will now be using the updated schema! Test it out to see if *Deadlock* has been updated with any breaking schema changes.

## Diff-Friendly Usage Variations

The output of the above steps doesn't generate great git diffs.

There are 4 variations to the Usage steps above that each help simplify the git diff. You can use as many or as few of these variations as you want (they can be combined).

### Variation 1: Create a Diff-Friendly Baseline

SchemaGenDemofileNet-cm191 tries its best to match the CS2SchemaGen format exactly, but there are some elements of it that can't be replicated from the side of SchemaGenDemofileNet-cm191.

If your git history is starting from json files that were generated by CS2SchemaGen rather than by SchemaGenDemofileNet-cm191, then you'll want to apply post-processing to the existing CS2SchemaGen files *before* you copy over the new ones, to eliminate these minor unreproducible elements.

```
cd schema-gen-helpers
py postprocess_cs2schemagen.py C:\path\to\demofile-net\src\DemoFile.Game.Deadlock\Schema
```
The automated post-processing here is pretty gentle. It consists of:
- Removing escaped forward-slashes (this is an optional feature of json, and python prefers not to have it)
- Adding "outer" fields to types that are missing it ("outer" describes the outer type of generic types, and CS2SchemaGen seems to include this field intermittently)

Commit these changes as your new baseline, and you'll have a simpler diff when you update the schema with  SchemaGenDemofileNet-cm191.

### Variation 2: Maintain Type Ordering

The output format of both CS2SchemaGen and this tool are intended to be in "dependency order" - where independent types are listed first in the file, and types that depend on those types come later.

Where there's some flexibility in that order, the `postprocess.py` script can try to match the existing json files' ordering as closely as possible, to simplify the diff. When you use the script, give it the path to the existing schemas as a second argument:

```
cd schema-gen-helpers
py postprocess.py ..\build\bin\Debug\sdk C:\path\to\demofile-net\src\DemoFile.Game.Deadlock\Schema
```

### Variation 3: Only Copy Necessary Files

Each json file is for a different "Type Scope" or "Module". demofile-net only needs a couple of the *Deadlock* modules, so adding *all* of them to its git tracking might be excessive.

However, you also can't just assume that you only need the modules that are currently listed in demofile-net (e.g. "!GlobalTypes" and "server"), because types can move around between modules when *Deadlock* receives updates -- new modules might suddenly be needed even though they weren't needed before.

To solve this, instead of *manually* copying over files to `demofile-net\src\DemoFile.Game.Deadlock\Schema`, use this script that reads what types are in the existing modules, and only copies over the new modules that contain those existing types:
```
cd schema-gen-helpers
py install_necessary.py ..\build\bin\Debug\sdk ..\..\src\DemoFile.Game.Deadlock\Schema
```

### Variation 4: Split Details

Git diff will always have trouble with the "monolithic" json files output format.

The `split_into_detailed.py` script splits each module file into *many* files (one file per type), which is a much more natural format for git to track.

Creating these split copies are only aesthetic purposes; demofile-net still requires the monolithic versions.

- Choose an empty directory to store the split files. (e.g. `C:\split-schema-details`)
- You'll want to generate the baseline, first. Checkout the existing main branch, and generate the split files for that version:
```
cd schema-gen-helpers
py split_into_detailed.py C:\path\to\demofile-net\src\DemoFile.Game.Deadlock\Schema C:\split-schema-details
```
- Commit the split files directory to a git repo.
- Generate the new schemas, and post-process / install them as usual.
- Generate the split files for the new version (the above `split_into_detailed.py` command again).
- Now when you go to commit the split files directory again, the schema changes/additions/deletions will be very obvious in the diff.

