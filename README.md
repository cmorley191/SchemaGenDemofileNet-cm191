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

## Building and Usage

This tool's only prescribed use is updating the schema that [saul/demofile-net](https://github.com/saul/demofile-net) is using (whenever *Deadlock* receives an update). This tool is forked from [neverlosecc/source2gen](https://github.com/neverlosecc/source2gen) which has greater capabilities; see that project's README if you're interested in other use cases.

TODO

