# 10k_parser

This is a simple Form 10-K parser with web front end.

Sample Form 10-K's can be found [here](https://app.quotemedia.com/data/downloadFiling?webmasterId=101533&ref=318113828&type=PDF&symbol=RNA&cdn=a21db366a91fc6f6801b95b95dc56cb4&companyName=Avidity+Biosciences+Inc.&formType=10-K&dateFiled=2024-02-28) and [here](https://www.annualreports.com/HostedData/AnnualReportArchive/a/NASDAQ_RNA_2022.pdf)


# Install and Run

Use pip to install this project

```bash
pip install git+https://github.com/dvigh8/10k_parser.git
```

To lanch the webpage locally run

```bash
python -m webview10k
```

You should now have a working website at http://localhost:5555

## Optional Flags

All of these flags must be set before the webview10k is started

### Available on network

To make the webpage available to everyone on network run the command below. When starting flask will print the link that can be used to access the tool http://your-computers-ip:5555

```bash
export FLASK_RUN_HOST="0.0.0.0"
```

### Logging

This application comes with automatic logging to the terminial where it is being run. To enable optianal [logfire](https://logfire.pydantic.dev) logging create a project and get a write token. Add the token with the comand below.

```bash
export LOGFIRE_TOKEN="<your-logfire-token>"
```


# Design Choices

## Flask Application Factory
- Modular design using **Blueprint** pattern
- Configurable through environment variables
- Separation of concerns between views and processing logic

## Asynchronous Processing
- Uses `asyncio` for non-blocking PDF processing
- Async API endpoints for better performance
- Background task handling for long-running operations

## Data Storage
- Processed files stored in structured directories
- Separation between uploads and processed data
- No database required - file-based storage

## Frontend Architecture
- **Bootstrap 5** for responsive design
- Tab-based interface for different sections
- Async JavaScript for dynamic content loading
- Client-side table formatting and rendering

## API Design
- RESTful endpoints for different 10-K sections
- JSON responses for structured data
- Error handling and status codes
- Supports both file uploads and data retrieval

# Key Components

## PDF Processing Pipeline
- Text extraction and section parsing
- Financial table identification
- Document structure analysis
- Metadata extraction

## Financial Data Processing
- Table extraction and formatting
- Data normalization
- Number formatting
- Multi-year comparison support

## Risk Factor Analysis
- Section identification
- Title and description separation

# Project Structure

```
webview10k/
├── __init__.py          # Application factory
├── __main__.py          # Entry point
├── config.py            # Configuration & logging
├── views/               # Route handlers
│   ├── api_bp.py       # API endpoints
│   └── main_bp.py      # Main routes
├── utils/              
│   └── pdf_processor.py # PDF processing logic
├── static/
│   └── js/             # Frontend JavaScript
└── templates/           # HTML templates
```