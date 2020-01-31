# graph-unar
Assumptions: 
- The script in its current form does not actually crop/extract the photos from the PDF
- There are places where I would want to make it as general as possible.

Approaches I didn't take:
- For task2 I was initially thinking of extracting the straight line equation. However
that would not be generic enough for all kinds of curves which we can find in high school
textbooks. The script would work for any curve, but it is a bit thick.


Usage:
1. Task1 `python3 task1.py <filename of photo>`
2. Task2 `python3 task2.py <filename of photo>`

TODOs:
1. Make the curve extracted in task2 less thick
2. Automatically print braille characters on the image
3. Remove number hardcodings.
