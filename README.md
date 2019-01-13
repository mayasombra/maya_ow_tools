# Maya importer tools for Overwatch

## INSTALLATION

This repository is configured to be easily imported as a Maya module.
http://techartsurvival.blogspot.com/2014/01/mayas-mildy-magical-modules.html
is a good overview on the topic.

Create a .mod file in the appropriate location, with contents something like

`+ owtools 1.0 /Users/mayasombra/code/maya_ow_tools`

or 

`+ owtools 1.0 C:\Users\mayasombra\code\maya_ow_tools`

Then in Maya's plugin manager, select the plugin and configure it to be loaded or
auto-loaded as desired. It will create a menu item 'OW Tools' that contains the
importer functions.

