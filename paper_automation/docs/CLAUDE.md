# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a RISS (Research Information Sharing Service) academic paper automation system that scrapes, collects, and summarizes Korean academic papers using Playwright for web scraping and Google Gemini API for AI summarization.

## Essential Commands

### Running the Application

```bash
# Using uv (preferred - manages dependencies automatically)
uv run run.py                    # GUI mode
uv run run.py --cli -k "AI,머신러닝" -c 10  # CLI mode

# First-time setup with uv
uv sync                          # Install dependencies
uv run playwright install chromium  # Install browser
```

### Alternative with pip

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Run application
python run.py                    # GUI mode
python run.py --cli -k "keywords" -c 10  # CLI mode
```

## Architecture

### Core Components

1. **Entry Points**
   - `run.py`: Main entry point, handles CLI/GUI mode selection
   - `gui.py`: PySide6-based GUI application

2. **Backend Engine**
   - `backend.py`: Orchestrates the entire workflow via `PaperCollectionEngine`
   - Coordinates between scraper, extractor, storage, summarizer, and exporter

3. **Data Flow Pipeline**
   - `scraper.py`: Web scraping using Playwright (`RISSScraper`)
   - `extractor.py`: Extracts paper metadata from HTML (`DataExtractor`)
   - `storage.py`: JSON storage management (`DataStorage`)
   - `summarizer.py`: AI summarization using Gemini API (`PaperSummarizer`)
   - `exporter.py`: Excel export functionality (`ExcelExporter`)

### Key Dependencies

- **Web Automation**: playwright for browser automation
- **GUI**: PySide6 for desktop interface
- **AI**: google-generativeai for paper summarization
- **Data**: pandas, openpyxl for Excel export
- **Parsing**: beautifulsoup4, lxml for HTML parsing

### Important Configuration

- Gemini API key required for AI summarization (set via GUI or `--api-key` flag)
- Default output directory: `./results`
- Logs stored in: `./logs/`

## Common Issues and Solutions

### Playwright Browser Not Installed
```bash
# Install with uv
uv run playwright install chromium

# Or with pip
playwright install chromium
```

### Module Import Errors
```bash
# Ensure all dependencies are installed
uv sync  # or pip install -r requirements.txt
```

### API Key Configuration
- Set via GUI in the API key field
- Or use `--api-key YOUR_KEY` in CLI mode
- Or set `GEMINI_API_KEY` environment variable