![SideFXLabs logo](https://github.com/sideeffects/SideFXLabs/blob/Development/help/icons/sidefxlabs_full.png)
# SideFX Labs - Houdini 19.5

SideFX Labs is a completely free, open-source toolset geared towards assisting Houdini users with a variety of tasks commonly used for digital content creation. It is an all-inclusive toolset that spans the shelf, digital assets, custom desktops and scripts and more. The toolset is currently maintained by Mai Ao, Danicka Oglesby, Alan Gordie, and Christos Stavridis. It also receives a lot of contributions from the always-active Houdini community. The toolset originates from the GameDevelopmentToolset, which got a re-launch in the Houdini 18.0 release. To get automatic bi-weekly updates, subscribe to the following thread: [Update Thread](https://www.sidefx.com/forum/topic/70854/)

# Installation

## Method 1 (Personal): Houdini Launcher

Open **Houdini Launcher** and navigate to the **Labs/Packages** section to install a version of SideFX Labs.

The SideFX Labs package will be installed to `C:\Program Files\Side Effects Software\sidefx_packages`.

Please note that if you have (perhaps accidentally) installed multiple copies of the same version of SideFX Labs (e.g. SideFXLabs19.5), the copy located in `sidefx_packages` will typically take precedence.

## Method 2 (Deployment): Command Line
You can also install the SideFX Labs package through command line, for example, using Windows Command Prompt or Houdini Command Line Tools (C:\Program Files\Side Effects Software\Houdini 19.5.100\bin\hcmd.exe). This is especially useful for deploying the toolset in a studio environment.

To install the latest production build, the latest daily build, or to uninstall (listed below in this order), the commands are:
```
"C:\Program Files\Side Effects Software\Launcher\bin\houdini_installer.exe" install-package --package-name "SideFX Labs 19.5 Production Build" --installdir "D:\studio\sidefxlabs"

"C:\Program Files\Side Effects Software\Launcher\bin\houdini_installer.exe" install-package --package-name "SideFX Labs 19.5 Daily Build" --installdir "D:\studio\sidefxlabs"

"C:\Program Files\Side Effects Software\Launcher\bin\houdini_installer.exe" uninstall-package "D:\studio\sidefxlabs\SideFXLabs19.5.json"
```
Please note that "D:\studio\sidefxlabs" is just an example path.

To replace part of a hard-coded path with an environment variable, you need to first define that environment variable on the machine which executes the commands.

On Windows, search for **Edit environment variables for your account** and then click **New...** on the **Environment Variables** window to add the variable name (e.g. MY_SIDEFXLABS) and the value (the desired directory).

Please note that Houdini-specific environment variables, such as `HSITE`, `HOME`, etc., are not automatically recognized in Windows Command Prompt or Houdini Command Line Tools when you type in the installation commands. For command line installation purposes, adding environment variables to `houdini.env` or a Houdini package definition file is not enough. You have to define them in the system.

Once the environment variable is set, e.g., MY_SIDEFXLABS = D:\studio\sidefxlabs, then the commands become (on Windows):

```
"C:\Program Files\Side Effects Software\Launcher\bin\houdini_installer.exe" install-package --package-name "SideFX Labs 19.5 Production Build" --installdir "%MY_SIDEFXLABS%"

"C:\Program Files\Side Effects Software\Launcher\bin\houdini_installer.exe" install-package --package-name "SideFX Labs 19.5 Daily Build" --installdir "%MY_SIDEFXLABS%"

"C:\Program Files\Side Effects Software\Launcher\bin\houdini_installer.exe" uninstall-package "%MY_SIDEFXLABS%\SideFXLabs19.5.json"
```

For more on how to download, install, upgrade, and uninstall Houdini and its components, please visit [here](https://www.sidefx.com/docs/houdini/ref/utils/launcher.html).

## Method 3 (More Versions): Download from GitHub
While Method 1 and Method 2 allow you download the latest builds, sometimes you may need to access an earlier release or to get the same-day updates before the next day's release is downloadable. In those cases, you can get the SideFX Labs package directly from this GitHub repository.

Step 1. [Option A] Download one of the releases from [here](https://github.com/sideeffects/SideFXLabs/releases). Choose a release, expand **Assets** and select either one of the **Source code** zip files. This step can be automated with a script that downloads the zip files from either one of the following URLs (just replace 19.5.100 with the desired version number).

```
https://github.com/sideeffects/SideFXLabs/archive/refs/tags/19.5.100.zip
https://github.com/sideeffects/SideFXLabs/archive/refs/tags/19.5.100.tar.gz
```

Step 1. [Option B] Click on the top right green **Code** button on the main page of this repository and select "Download ZIP". This allows you to get the same-day updates before the next day's release is downloadable.

Step 1. [Option C] (Advanced) Clone the this repository.

Step 2. If you have downloaded a zipped version of the package in Step 1, unzip it into a custom SideFXLabs directory of your choosing.

Step 3. Go to your custom SideFXLabs directory, copy the package definition template file `SideFXLabs.json` to `C:\Users\...\Documents\houdini19.5\packages` (on Windows). Rename the destination copy to `SideFXLabs19.5.json`. Open this file and replace `"$HOUDINI_PACKAGE_PATH/SideFXLabs19.5"` (line 8) with the path to your custom SideFXLabs directory. (When Houdini launches, it relies on this file to discover the location of your SideFX Labs package.)

For more on how to install and manage Houdini packages, please visit [here](https://www.sidefx.com/docs/houdini/ref/plugins.html).


# Additional Information

## Live Development
We're actively developing the tools in this Repository. The [releases](https://github.com/sideeffects/SideFXLabs/releases) provide safe checkpoints in the code for you to download. The internal Houdini Updater uses the releases to install the tools.  

## Expanded HDAs
All of the HDAs are using the expanded format that was introduced in H16. This allows better diffing of the tools so you can see what our changes are doing and choose to integrate them back into your production.

## Example Files
Instead of tying the examples as HDAs, we will be generating separate hip files that show how the tools should work in context. These can be found [here](https://github.com/sideeffects/SideFXLabs/tree/Development/hip).

## Data Analytics
SideFX Labs *optionally* collects data about what tools are used through Google Analytics. We do this in order to focus our resources on the more active tools and therefore be able to help more people. This does *not* track any personal user data such as IP, Name, License use etc. To opt-out of this tracking, you can disable the "Send Anonymous Usage Statistics" toggle under preferences. Additionally, you can bypass this behavior entirely by setting the environment variable "HOUDINI_ANONYMOUS_STATISTICS = 0".

## Other Environment Variables
SideFX Labs has a few other environment variables that can be set to modify the behavior of the toolset and its installation process:
1. "SIDEFXLABS_NOINSTALL_MESSAGE = Your message here" - Disables the installing of the toolset on the machine, and shows the text stored in the environment variable.
2. "SIDEFXLABS_ADMIN_UPDATES = 1" - This prevents users from updating the already installed toolset on their machine. Useful for studios where one version of the toolset is enforced.

## Contributor Credits
### SideFX Labs Team
- Luiz Kruel
- Mike Lyndon
- Paul Ambrosiussen
- Mai Ao
- Danicka Oglesby
- Alan Gordie
- Christos Stavridis

### SideFX Staff
- Bruno Ebe
- Jeff Lait
- Michael Buckley
- Jeffy Mathew Philip
- Attila Torok
- Simon Verstraete
- Steven Burrichter

### SideFX Interns
- Roahith Raj
- Ryan Gold
- Ciara Cipponeri

### Community Contributors
- Magnus Larsson
- Jake Rice
- Richard C Thomas
- Matt Estela
- Guillaume Jobst
- Baku Hashimoto
- Shari Solo
- Erwin Heyms
- Andrea Di Nardo
