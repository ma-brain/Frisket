
English only: there's no language setting or Romanian anywhere in the UI.
Opening screen: the app opens on a card board, like the old New document screen (01). Blank A4 is the selected default; the template cards and "Start from a file" options sit beside it. "Create", Return or a double-click opens it.
One window: every document, and Settings, opens as a tab in the same window (tab strip at the top of every screen). Export and the file dialogs appear inside the current tab, not as new windows.
Mouse zoom:
⌘ + scroll wheel or trackpad pinch zooms toward the mouse pointer.
Space + drag pans the page.
A zoom slider with Fit page and 100% sits in the bottom-right corner.
The zoom level also shows in the status bar (02, 03).
Built-in fonts (02, 10): five font families ship with the app. I chose ones with the same letter widths as the fonts most documents use, so imported Word and PowerPoint files keep their line breaks:
Liberation Sans (matches Arial and Helvetica)
Liberation Serif (matches Times New Roman)
Carlito (matches Calibri)
Caladea (matches Cambria)
Lora (for headings)
Their licences allow bundling them in a paid app.
Commercial licence: everything planned so far uses Apache, MIT, BSD or OFL licences, which all allow closed-source commercial use. The earlier AGPL citation component is out.
Page layout and PDF output run in Rust (using the Typst engine) rather than in the web view.
File format (screen 11): this shows how compatibility works in practice:
an older file opens normally and a backup is kept when it's upgraded;
a newer file opens read-only;
after a crash, autosaved work can be restored;
moved figures can be relinked automatically.

Screen list: 01 Home, 02 Blank A4 with the font menu, 03 Poster workspace, 04 Preflight, 05 Export, 06 Linked files, 07 Data merge, 08 References, 09 Theme and brand kit, 10 Settings › Fonts, 11 File version dialogs, 12 Booklet.