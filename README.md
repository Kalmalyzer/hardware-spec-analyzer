# Hardware spec analyzer

This program fetches data from three sources:

- [Steam Hardware Survey](https://github.com/jdegene/steamHWsurvey)
- [PassMark's Video Card Benchmark database](https://www.videocardbenchmark.net/)
- [Anteru's GPU architectural information database](https://db.thegpu.guru/)

We have a list of machines and their specs.

This program then computes what % of Steam's userbase is covered by each machine specification.

Currently, this only looks at GPU specs.

# Usage

Run this under Linux.

- Install Python 3.x
- Install `chromium-chromedriver`
- Modify the list of specs at the top of `target_configuration_db.py` if necessary
- `make clean` will remove all cached files
- `make analyze` will recreate cached files if necessary, perform analysis, and write results to `output`
