# Pyper

A common interface for interacting with VFX applications, shipped with a collection of widgets built on that common interface.

[Features](#features)  
[Getting started](#getting-started)  
[Build your own widget](#build-your-own-widget)  
[Package description](#package-description)  
[Authors](#authors)  
[Acknowledgments](#acknowledgments)  
[License](#license)  

## Features
- A common interface, `pyper.wrappers`, for interacting with VFX applications.
- A common `__init__.py` with cross application `run()` function to launch the widget.
- A logging system built on python's logging module with configuration file ready to used.

## Getting Started
#### Quick start 
- clone the repository to a folder in your python path
  ```
  cd /path/to/your/tool/folder
  git clone https://gitlab.com/brunoebe/pyper.git
  ```
- create a shelf tool with the following code:
  ```
  from pyper.widgets import simplelist
  simplelist.run()
  ```

## Build your own widget
- Copy paste one of the widgets found in `pyper/widgets` to your folder:
  ```
  cd /path/to/your/tool/folder
  cp -R pyper/widgets/simplelist .
  ```
- Rename it to your liking, e.g. `myWidget`
  ```
  mv simplelist myWidget
  ```
- Edit  the `myWidget/ui/widget.ui` file in QtDesigner, or design a new one to overwrite it.
- create a shelf tool with the following code:
  ```
  import myWidget
  myWidget.run()
  ```
- Now go to `myWidget/ui.py` and change the logic to fit your needs. Use other widgets in `pyper/widgets` as examples.  

## Package description
### Wrappers
This package defines different models sharing a common interface to interact with corresponding DCC.  
*Note: currently only wrappers for Side Fx Houdini and Autodesk Maya have been written.*

Let's say you want to get the selected objects
in Autodesk Maya you would run `maya.cmds.ls(sl=True)`
and in Side Fx Houdini `hou.selectedNodes()`

This is a problem when you want to develop a tool that needs to be used in both applications (or more).  
To get around this, we wrapped those functions to provide a common interface.  

- In wrappers.maya we define:
  ```
  def selection(self):
      return self._mayamodule.ls(sl=True, long=True)
  ```

- In wrappers.houdini we define:
  ```
  def selection(self):
      return [node.path() for node in hou.selectedNodes()]
  ```

- And in the widget we use:
  ```
  from wrappers import houdini as wrapper
  ```
  or 
  ```
  from wrappers import maya as wrapper
  ```
  and then
  ```
  selectedNodes = wrapper.Model().selection()
  ```

<!-- ## Contributing

Please read CONTRIBUTING.md for details on our code of conduct, and the process for submitting pull requests to us. -->

## Authors

* **Bruno Ébé** | contact@brunoebe.com | https://gitlab.com/brunoebe

<!-- See also the list of [contributors](https://gitlab.com/your/project/contributors) who participated in this project. -->

## Acknowledgments

* The [Qt.py](https://github.com/mottosso/Qt.py) project

## License

Copyright: (C) 2014 Bruno Ébé | contact@brunoebe.com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

See the [LICENSE.md](LICENSE.md) file for details

