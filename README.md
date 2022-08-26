# dependent_downloads
A script to find out the most popular packages depending on your package.

This script will hit https://libraries.io/ and https://pypistats.org/ to find your
package's reverse dependencies, and figure out how many downloads each has in the last
month. It requires an API key for https://libraries.io/ which you can set in the
`LIBRARIES_API_KEY` environment variable.

```
usage: python dependent_downloads.py [-h] [--pkg-name PKG_NAME] [--output-file OUTPUT_FILE]

Find the most downloaded dependents of your package. If you get a TOO_MANY_REQUESTS
error, wait a bit and try again. Intermediate results are cached in the output file.

optional arguments:
  -h, --help            show this help message and exit
  --pkg-name PKG_NAME, -p PKG_NAME
                        Package name
  --output-file OUTPUT_FILE, -o OUTPUT_FILE
                        Output CSV file
```
