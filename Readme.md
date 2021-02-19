# SnipTools DataProvider

Project directly linked to the [SnipTools](https://github.com/jaqxues/SnipTools) repository. This handles the releases
for the app (and its packs) using an SQL database. Any network requests are generated and hosted statically so SnipTools
can operate backend-less and serverless to some extent.

The `main.py` script handles adding release notes and known bugs to Packs and APKs. The network requests that are
currently supported and generated include:
* Available Packs ([ServerPacks.json](Packs/Info/ServerPacks.json))
* Pack History ([History](Packs/Info/History))
* Known Pack Bugs ([KnownBugs](Packs/Info/KnownBugs))
* Pack Updates ([Updates](Packs/Info/Updates))

