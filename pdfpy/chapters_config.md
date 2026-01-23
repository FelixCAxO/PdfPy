<!-- PDF Chapter Finder Configuration
INSTRUCTIONS:
- Do not change the text to the left of the colon (e.g., CHAPTER_REGEX).
- Only edit the value to the right of the colon.
- The script will use these settings if the PDF has no bookmarks.
A regular expression (regex) to identify chapter title lines.
The default value looks for lines starting with "Chapter" followed by a number.
EXAMPLES:
- To find "Section 1.1" or "Section 3": ^Section\s+[\d.]+
- To find "Part III": ^Part\s+[IVXLCDM]+ -->
CHAPTER_REGEX: ^Chapter\s+\d+

<!-- The minimum font size for a line to be considered a chapter title.
You may need to experiment to find the right value for your document. -->
MIN_FONT_SIZE: 16

<!-- Set to "true" if the chapter title must be bold.
Set to "false" if boldness is not a requirement. -->
MUST_BE_BOLD: true