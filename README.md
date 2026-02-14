# msit-dl

Download HWP/HWPX/ODT documents from Korean MSIT (Ministry of Science and ICT) press releases.

The MSIT website publishes government notices with file attachments in HWP 5.0,
HWPX, and ODT formats simultaneously, making them useful for testing document
format import filters.

**Note:** This is slop-coded for quick bulk downloading. Don't expect clean code.

## Install

```
pip install msit-dl
```

## Usage

```
msit-dl
```

Downloads documents from recent press releases. Files are saved as
`msit-{articleId}.{hwp,hwpx,odt}` in the output directory.

### Options

```
msit-dl [--pages N] [--outdir DIR] [--delay SECONDS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--pages` | 3 | Number of listing pages to scan |
| `--outdir` | msit-docs | Output directory |
| `--delay` | 1.0 | Delay between requests in seconds |

### Resume

Already-downloaded files are skipped automatically. Re-run the same command
to download only new files.

## Requirements

- `curl` must be installed (used for HTTP requests to bypass bot protection)

## How it works

1. Scrapes the MSIT press release listing pages for article IDs
2. Fetches each article page to find file attachment metadata
3. Downloads HWP, HWPX, and ODT attachments via POST requests
4. Skips files that already exist in the output directory

