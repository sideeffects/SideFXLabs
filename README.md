![SideFXLabs logo](https://github.com/sideeffects/SideFXLabs/blob/Development/Help/icons/sidefxlabs_full.png)
# SideFX Labs

SideFX Labs is a completely free, open-source toolset geared towards assisting Houdini users with a variety of tasks commonly used for digital content creation. It is an all-inclusive toolset that spans the shelf, digital assets, custom desktops and scripts and more. The toolset is currently maintained by Luiz Kruel, Mike Lyndon and Paul Ambrosiussen, and receives a lot of contributions from the always-active Houdini community. The toolset originates from the GameDevelopmentToolset, which got a re-launch in the Houdini 18.0 release.

# Installation

You can install the SideFX Labs Toolset directly from inside Houdini, (Requires Houdini 18.0 or newer) or install it manually using the packages system.

## Method 1 (Recommended): Built in Updater

Use the built in Updater in Houdini 18.0 or newer to install a version of the toolset. The updater can be found in the SideFX Labs shelf.

The updater provides several options of installation depending on your needs / limitations.
1. If you do not have internet access, the updater allows you to install a local version of the toolset. This local version is tied to which version of Houdini you are running the updater from. (Ex Houdini 18.0.274 would install 274 of the toolset) To obtain a newer version, you would need a more recent version of Houdini.
2. REQUIRES INTERNET ACCESS. Download a production build from Github. A production build is released every four weeks. This type of build will not contain the cutting edge additions to the toolset, but will have had more production testing prior to release than a development build. (These builds can be found in the releases section of this repository and are marked as "Release")
3. REQUIRES INTERNET ACCESS. Download a development build from Github. A development build gets released every 24 hours. These builds will contain bugfixes that have been implemented in the day prior. To get access to these type of builds, untick the "Production Builds Only" checkbox in the updater.


## Method 2: Manually Download from Github

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
SideFX Labs *optionally* collects data about what tools are used through Google Analytics. We do this in order to focus our resources on the more active tools and therefore be able to help more people. This does *not* track any personal user data such as IP, Name, License use etc. To opt-out of this tracking, you can disable the "Send Anonymous Usage Statistics" toggle under preferences. Additionally, you can bypass this behavior entirely by setting the environment variable "HOUDINI_ANONYMOUS_STATISTICS = 1".
