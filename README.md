# Game Development Toolset

This is a series of tools geared towards assisting Houdini users with a variety of tasks for game development. The older version of this repository focused on just the shelf. Now this is an all-inclusive toolset that spans the shelf, digital assets, custom desktops and scripts.

If you'd like more information, please check out [Game Development Toolset Overview](https://www.sidefx.com/tutorials/game-development-toolset-overview/), which contains tutorials for several of the provided tools. 

NOTE: This is in-progress. Please file an [Issue](https://github.com/sideeffects/GameDevelopmentToolset/issues) if something doesn't seem quite right!

Also, if you forked the respository and suddenly it stopped pulling, that's due to the repository name changing from [GameDevelopmentShelf](https://github.com/sideeffects/GameDevelopmentShelf/) to [GameDevelopmentToolset](https://github.com/sideeffects/GameDevelopmentToolset/). Github appears to forward traffic to the new link, but here's a little FYI just in case.

# Installation

You can install the Game Development Toolset from the updater built in to Houdini 16.5+ or you can manually download the sources from github.

## Method 1 (Recommended): Built in Updater

Use the built in Updater in Houdini 16.5+ to download the latest releases from Github. You can find more information [here](https://www.sidefx.com/tutorials/game-dev-toolset-installation/)

## Method 2 (Cutting Edge): Manually Download from Github

1. Download the repository using the green Clone or Download Button and unzip contents into the folder of your choosing.

2. Edit [houdini.env](https://www.sidefx.com/docs/houdini/basics/config_env#setting-environment-variables) and set `HOUDINI_PATH` and `PATH` into something like:

    ```
    HOUDINI_PATH = C:\Users\Luiz\Documents\GameDevelopmentToolset;&
    PATH = C:\Users\Luiz\Documents\GameDevelopmentToolset\bin;$PATH
    ```

# What's Changed?
Hi, my name is Luiz Kruel and I have taken over the github from Steven B. who is now working in production. A few of the SideFX TAs (TDs) will also be contributing example files and tools.

We haven't done a lot in this Github in a while, but we are changing that. The original thought was that new tools would go straight into the build and the Github would eventually be phased out.
But we saw a lot of value in having this experimental testbed for tools, so we will continue to develop our tools live and as they mature they will move into the main Houdini Build.

## Live Development
We're actively developing the tools in this Repository. The [Releases](https://github.com/sideeffects/GameDevelopmentToolset/releases) provide safe checkpoints in the code for you to download. The internal Houdini Updater uses the releases to install the tools.  

## Expanded HDAs
All of the HDAs are now using the new expanded format that was introduced in H16. This allows better diffing of the tools so you can see what our changes are doing and choose to integrate them back into your production.

## Example Files
Instead of tying the examples as HDAs, we will be generating separate hip files that show how the tools should work in context

## Branched Development
The [Development](https://github.com/sideeffects/GameDevelopmentToolset/tree/Development) branch is where we'll be working from. This is where the latest and greatest will live. The HoudiniXX branches are for archival purposes and we'll keep working on the latest release and will branch off when we make HDAs that use new functionality. 

The [Stable](https://github.com/sideeffects/GameDevelopmentToolset/tree/Stable) branch will be soon deprecated as the [Releases](https://github.com/sideeffects/GameDevelopmentToolset/releases) workflow provides the same gating functionality. 

