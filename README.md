![SideFXLabs logo](https://github.com/sideeffects/SideFXLabs/blob/Development/help/icons/sidefxlabs_full.png)
# SideFX Labs - Houdini 18.5

SideFX Labs is a completely free, open-source toolset geared towards assisting Houdini users with a variety of tasks commonly used for digital content creation. It is an all-inclusive toolset that spans the shelf, digital assets, custom desktops and scripts and more. The toolset is currently maintained by Paul Ambrosiussen and Mai Ao. It also receives a lot of contributions from the always-active Houdini community. The toolset originates from the GameDevelopmentToolset, which got a re-launch in the Houdini 18.0 release. To get automatic bi-weekly updates, subscribe to the following thread: [Update Thread](https://www.sidefx.com/forum/topic/70854/)

# Installation

You can install the SideFX Labs Toolset directly from inside Houdini, (Requires Houdini 18.0 or newer) or install it manually using the packages system.

## Method 1 (Recommended): Built-in Updater

Use the built-in Updater in Houdini 18.0 or newer to install a version of the toolset. The updater can be found in the SideFX Labs shelf.

The updater provides several options of installation depending on your needs / limitations.
1. If you do not have internet access, the updater allows you to install a local version of the toolset. This local version is tied to which version of Houdini you are running the updater from. (Ex Houdini 18.0.274 would install 274 of the toolset) To obtain a newer version, you would need a more recent version of Houdini.
2. REQUIRES INTERNET ACCESS. Download a production build from Github. A production build is released every four weeks. This type of build will not contain the cutting edge additions to the toolset, but will have had more production testing prior to release than a development build. (These builds can be found in the releases section of this repository and are marked as "Release")
3. REQUIRES INTERNET ACCESS. Download a development build from SideFX.com. A development build gets released every 24 hours. These builds will contain bugfixes that have been implemented in the day prior. To get access to these type of builds, untick the "Production Builds Only" checkbox in the updater. 

## Method 2: Command Line
Houdini now also allows you to install SideFXLabs through python in case you wish to do so. This is especially useful for deploying the toolset in large environments. The updating can be done through the `sidefxlabs` module. Launch Houdini, on the menu bar, choose Windows > Python Shell. Then you can type in the following commands:

```python
import sidefxlabs

updater = sidefxlabs.SideFXLabsUpdater() # This is the updater object.

updater.production_releases # Lists containing the available production releases
updater.development_releases # Lists containing the available development releases

updater.install_latest_production_toolset() # Installs latest production build from sidefx.com
updater.install_latest_development_toolset() # Installs latest development build from sidefx.com
updater.install_embedded_toolset() # Installs embedded version of the toolset. No internet required.

# Tip: Check the contents of updater.production_releases or updater.development_releases
# to see which most recent versions are available.
updater.update_toolset_version(VERSION_NUMBER) # Installs a specific version, e.g., '18.5.533'

updater.uninstall_toolset() # Uninstalls the toolset from Houdini. Did we do something wrong? :(
```

In addition to the above examples, you can also run a headless session of Hython using simple script arguments.
You can for example do this in Command Prompt:

```
set HFS=C:/Program Files/Side Effects Software/Houdini 18.5.532
"%HFS%/bin/hython2.7.exe" "%HFS%/houdini/python2.7libs/sidefxlabs.py" -p

The available arguments are:
-p/--installs latest production release 
-d/--installs latest development release
-e/--installs embedded version
-v/--version NUM 
-u/--uninstalls
```

You can also search for and run Houdini's own Command Line Tools 18.5.533 (or whatever Houdini version you have; this is a separate program on your system that comes with Houdini). In Command Line Tools, you do not have to set the variable HFS since it will already be set for you. You may also skip the double quotes in the second line:

```
%HFS%/bin/hython2.7.exe %HFS%/houdini/python2.7libs/sidefxlabs.py -p
```

## Method 3: Manually Download from Github

1. Download the repository using the green Clone or Download Button and unzip contents into the folder of your choosing.

2. Copy the SideFXLabs.json file from the location used in step 1 to `$HOME/Houdini18.0/packages`, and change the contained paths to match the location chosen in step 1. [Information on Packages](https://www.sidefx.com/docs/houdini/ref/plugins.html)


# Additional Information

## Live Development
We're actively developing the tools in this Repository. The [Releases](https://github.com/sideeffects/SideFXLabs/releases) provide safe checkpoints in the code for you to download. The internal Houdini Updater uses the releases to install the tools.  

## Expanded HDAs
All of the HDAs are using the expanded format that was introduced in H16. This allows better diffing of the tools so you can see what our changes are doing and choose to integrate them back into your production.

## Example Files
Instead of tying the examples as HDAs, we will be generating separate hip files that show how the tools should work in context. These can be found [Here](https://github.com/sideeffects/SideFXLabs/tree/Development/hip)

## Data Analytics
SideFX Labs *optionally* collects data about what tools are used through Google Analytics. We do this in order to focus our resources on the more active tools and therefore be able to help more people. This does *not* track any personal user data such as IP, Name, License use etc. To opt-out of this tracking, you can disable the "Send Anonymous Usage Statistics" toggle under preferences. Additionally, you can bypass this behavior entirely by setting the environment variable "HOUDINI_ANONYMOUS_STATISTICS = 0".

## Other Environment Variables
SideFX Labs has a few other environment variables that can be set to modify the behavior of the toolset and its installation process:
1. "SIDEFXLABS_NOINSTALL_MESSAGE = Your message here" - Disables the installing of the toolset on the machine, and shows the text stored in the environment variable.
2. "SIDEFXLABS_ADMIN_UPDATES = 1" - This prevents users from updating the already installed toolset on their machine. Useful for studios where one version of the toolset is enforced.

