import argparse
import os
import pathlib
from typing import List

import requests


def get_all_dependents(pkg_name: str) -> List[str]:
    """Get all PyPI packages that depend on a given package.

    Uses https://libraries.io/.

    Parameters
    ----------
    pkg_name : str
        The package to inspect.

    Environment variables
    ---------------------
    LIBRARIES_API_KEY
        Your user's API key for libraries.io

    Returns
    -------
    List[str]
        A list of package names, sorted by descending number of Github stars.
    """
    PER_PAGE = 100
    BASE_URL = "https://libraries.io/api"

    api_key = os.getenv("LIBRARIES_API_KEY")
    if not api_key:
        raise ValueError("LIBRARIES_API_KEY environment variable not found")

    pkg_info = requests.get(f"{BASE_URL}/pypi/{pkg_name}?api_key={api_key}").json()
    num_pages = pkg_info["dependents_count"] // PER_PAGE + 1

    results = []
    for page in range(1, num_pages + 1):
        print(f"Getting page {page} of {num_pages}")
        x = requests.get(
            f"{BASE_URL}"
            f"/pypi/{pkg_name}/dependents"
            f"?api_key={api_key}"
            f"&per_page={PER_PAGE}"
            f"&page={page}"
        )
        results += x.json()

    # deduplicate
    num_stars = {pkg["name"]: pkg["stars"] for pkg in results}

    return [
        pkg_name for pkg_name, _ in sorted(num_stars.items(), key=lambda pkg: -pkg[1])
    ]


def get_downloads_in_last_month(pkg_name: str) -> int:
    """Find the number of PyPI downloads in the last month for a given package.

    Uses https://pypistats.org/.

    Parameters
    ----------
    pkg_name : str
        The package to inspect.

    Returns
    -------
    int
        The number of downloads in the last month.
    """
    res = requests.get(f"https://pypistats.org/api/packages/{pkg_name}/recent")
    res.raise_for_status()
    return res.json()["data"]["last_month"]


def main(pkg_name: str, output_file: pathlib.Path):
    """Create/update a CSV of all packages that depend on your package. The CSV contains
    each package's number of downloads in the last month.

    Parameters
    ----------
    pkg_name : str
        The package to inspect.
    output_file : pathlib.Path
        A path to the output CSV file. Intermediate results are cached here in case of
        API failures like 429 Too Many Requests.
    """
    if not output_file.exists():
        # cache packages in the CSV in case of later API failure
        dependents = get_all_dependents(pkg_name)
        with open(output_file, "w") as f:
            f.write("pkg_name,downloads\n")
            for pkg_name in dependents:
                f.write(f"{pkg_name},\n")

    with open(output_file, "r") as f:
        next(f)  # pop off the header
        all_downloads = dict(line.strip().split(",") for line in f)

    try:
        for row_ix, (pkg_name, downloads) in enumerate(all_downloads.items()):
            if not downloads:
                try:
                    all_downloads[pkg_name] = get_downloads_in_last_month(pkg_name)
                    print(
                        f"({row_ix + 1}/{len(all_downloads)}) "
                        f"{pkg_name} has {all_downloads[pkg_name]} downloads"
                    )
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 404:
                        all_downloads[pkg_name] = "NA"
                        print(
                            f"({row_ix + 1}/{len(all_downloads)}) "
                            f"Could not find {pkg_name}, continuing..."
                        )
                    else:
                        raise
    except Exception:
        raise
    else:
        print("All done!")
    finally:
        with open(output_file, "w") as f:
            f.write("pkg_name,downloads\n")
            for pkg_name, downloads in all_downloads.items():
                f.write(f"{pkg_name},{downloads}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Find the most downloaded dependents of your package. "
        "If you get a TOO_MANY_REQUESTS error, wait a bit and try again. "
        "Intermediate results are cached in the output file."
    )
    parser.add_argument("--pkg-name", "-p", help="Package name", type=str)
    parser.add_argument(
        "--output-file", "-o", help="Output CSV file", type=pathlib.Path
    )
    args = parser.parse_args()

    main(pkg_name=args.pkg_name, output_file=args.output_file)
