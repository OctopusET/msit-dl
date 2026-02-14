#!/usr/bin/env python3
"""Download HWP/HWPX/ODT documents from Korean MSIT press releases."""

import argparse
import os
import re
import subprocess
import time

__version__ = "0.1.0"

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# MSIT press release board (공지사항)
LIST_URL = (
    "https://www.msit.go.kr/bbs/list.do"
    "?sCode=user&mId=310&mPid=121&bbsSeqNo=96&pageIndex={page}"
)
VIEW_URL = (
    "https://www.msit.go.kr/bbs/view.do"
    "?sCode=user&mId=310&mPid=121&bbsSeqNo=96&nttSeqNo={ntt}"
)
DOWNLOAD_URL = "https://www.msit.go.kr/ssm/file/fileDown.do"


def curl_get(url):
    """Fetch URL content via curl (bypasses bot protection that blocks urllib)."""
    result = subprocess.run(
        ["curl", "-sL", "-A", UA, url], capture_output=True, timeout=30
    )
    return result.stdout.decode("utf-8", errors="replace")


def curl_download(atch_file_no, file_ord, outpath):
    """Download a file attachment via POST request."""
    result = subprocess.run(
        [
            "curl",
            "-sL",
            "-A",
            UA,
            "-d",
            f"atchFileNo={atch_file_no}&fileOrd={file_ord}&fileBtn=A",
            "-o",
            outpath,
            DOWNLOAD_URL,
        ],
        capture_output=True,
        timeout=60,
    )
    if result.returncode == 0 and os.path.exists(outpath):
        size = os.path.getsize(outpath)
        if size > 100:
            return size
    if os.path.exists(outpath):
        os.remove(outpath)
    return 0


def get_article_ids(page):
    """Extract article IDs from a listing page."""
    html = curl_get(LIST_URL.format(page=page))
    # Listing page uses fn_detail(NNN) JavaScript calls
    pattern = r"fn_detail\((\d+)\)"
    return list(set(re.findall(pattern, html)))


def get_file_info(ntt_seq_no):
    """Get downloadable file info from an article page."""
    html = curl_get(VIEW_URL.format(ntt=ntt_seq_no))
    # File download links use fn_download('atchFileNo', 'fileOrd', 'ext')
    pattern = r"fn_download\('(\d+)',\s*'(\d+)',\s*'(\w+)'\)"
    matches = re.findall(pattern, html)
    seen = set()
    files = []
    for atch, ord_, ext in matches:
        key = (atch, ord_, ext)
        if key not in seen:
            seen.add(key)
            files.append({"atchFileNo": atch, "fileOrd": ord_, "ext": ext})
    return files


def main():
    parser = argparse.ArgumentParser(
        prog="msit-dl",
        description="Download HWP/HWPX/ODT documents from MSIT press releases",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=3,
        help="Number of listing pages to scan (default: 3)",
    )
    parser.add_argument(
        "--outdir", default="msit-docs", help="Output directory (default: msit-docs)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between requests in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    print(f"Scanning {args.pages} pages of MSIT press releases...")

    all_article_ids = []
    for page in range(1, args.pages + 1):
        print(f"  Page {page}...", end=" ", flush=True)
        try:
            ids = get_article_ids(page)
            print(f"{len(ids)} articles")
            all_article_ids.extend(ids)
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(args.delay)

    all_article_ids = list(set(all_article_ids))
    print(f"\nFound {len(all_article_ids)} unique articles. Checking for files...")

    downloaded = {"hwp": 0, "hwpx": 0, "odt": 0}

    for i, ntt_id in enumerate(sorted(all_article_ids)):
        print(
            f"\n[{i + 1}/{len(all_article_ids)}] Article {ntt_id}:", end=" ", flush=True
        )
        try:
            files = get_file_info(ntt_id)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(args.delay)
            continue

        if not files:
            print("no downloadable files")
            time.sleep(args.delay)
            continue

        exts = [f["ext"] for f in files]
        print(f"files: {', '.join(exts)}")

        for finfo in files:
            ext = finfo["ext"]
            if ext not in ("hwp", "hwpx", "odt"):
                continue

            outpath = os.path.join(args.outdir, f"msit-{ntt_id}.{ext}")
            if os.path.exists(outpath):
                print(f"  {ext}: already exists, skipping")
                downloaded[ext] += 1
                continue

            print(f"  Downloading {ext}...", end=" ", flush=True)
            size = curl_download(finfo["atchFileNo"], finfo["fileOrd"], outpath)
            if size:
                print(f"OK ({size:,} bytes)")
                downloaded[ext] += 1
            else:
                print("FAILED")

            time.sleep(args.delay * 0.5)

        time.sleep(args.delay)

    print(
        f"\nDone! Downloaded: {downloaded['hwp']} HWP, "
        f"{downloaded['hwpx']} HWPX, {downloaded['odt']} ODT"
    )
    print(f"Files saved to: {args.outdir}")


if __name__ == "__main__":
    main()
