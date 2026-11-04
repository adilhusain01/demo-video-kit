#!/bin/zsh
# Park the mouse pointer in the bottom-right corner so it is not in the shot. The recorder already hides
# the cursor (-capture_cursor 0) but an I-beam over a terminal can still be drawn by the app.
osascript -l JavaScript -e 'ObjC.import("CoreGraphics"); ObjC.import("AppKit"); var f = $.NSScreen.mainScreen.frame; $.CGWarpMouseCursorPosition({x: f.size.width - 4, y: f.size.height - 4}); "pointer parked"'
