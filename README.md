# 🧬 PhosphoSite Site Table Scraper

A comprehensive web scraping tool for extracting phosphorylation site data from PhosphoSitePlus, with both command-line and Streamlit web interface options.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Data Structure](#data-structure)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [File Structure](#file-structure)
- [Contributing](#contributing)

## 🎯 Overview

This project provides automated web scraping capabilities for PhosphoSitePlus, a comprehensive database of protein phosphorylation sites. The scraper extracts detailed information about phosphorylation sites, including upstream/downstream kinase relationships, LTP/HTP data, and sequence information.

### Key Capabilities

- **Single Protein Scraping**: Extract data for individual proteins by ID
- **Batch Processing**: Process multiple proteins simultaneously
- **Upstream/Downstream Detection**: Automatically detects and extracts kinase-substrate relationships
- **Data Cleaning**: Removes unwanted text and filters data
- **Multiple Output Formats**: CSV, ZIP, and combined datasets
- **Web Interface**: User-friendly Streamlit app for interactive scraping

## ✨ Features

### 🔍 Web Scraping Features
- **Anti-Detection Measures**: Uses Playwright with stealth techniques
- **Cloudflare Bypass**: Handles Cloudflare challenges automatically
- **Cookie Management**: Saves and reuses cookies for better performance
- **Random Delays**: Implements human-like browsing behavior
- **Error Recovery**: Automatic retry mechanisms for failed requests

### 📊 Data Extraction
- **Site Information**: Phosphorylation site identifiers and sequences
- **Upstream/Downstream Data**: Kinase-substrate relationships
- **LTP/HTP Counts**: Low and High Throughput data
- **Protein Information**: Names, organisms, and metadata
- **Data Validation**: Automatic filtering of invalid entries

### 🎨 User Interface
- **Streamlit Web App**: Interactive web interface
- **Progress Tracking**: Real-time progress indicators
- **Data Visualization**: Built-in data preview and analysis
- **Download Options**: Multiple export formats
- **Error Handling**: User-friendly error messages

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Quick Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd phosphosite-scraper
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Install Playwright browsers**:
```bash
playwright install chromium
```

### Manual Installation

If you prefer manual installation:

```bash
pip install playwright pandas streamlit cloudscraper
playwright install chromium
```

## 📖 Usage

### Command Line Usage

#### Single Protein Scraping
```bash
cd streamlit_site_table
python phosphosite_site_table_scraper.py
```

#### Configuration
Edit the configuration in `phosphosite_site_table_scraper.py`:
```python
CONFIG = {
    'headless': True,  # Set to False for debugging
    'start_protein_id': 583,  # Starting protein ID
    'end_protein_id': 583,  # Ending protein ID
    'max_retries': 3,  # Maximum retries per protein
}
```

### Streamlit Web Interface

#### Launch the Web App
```bash
cd streamlit_site_table
streamlit run streamlit_phosphosite_app.py
```

#### Web App Features

1. **Single Protein Mode**:
   - Enter a protein ID (e.g., 583)
   - Click "Scrape Protein"
   - View results and download CSV

2. **Batch Processing Mode**:
   - **Range**: Specify start and end protein IDs
   - **List**: Enter comma-separated protein IDs
   - **Upload CSV**: Upload a file with protein IDs
   - Download individual files or combined dataset

3. **Data Analysis**:
   - Upload existing CSV files
   - View data overview and statistics
   - Generate visualizations

## 📊 Data Structure

### Main DataFrame Columns

| Column | Description | Type |
|--------|-------------|------|
| `Protein` | Protein name | String |
| `Site` | Phosphorylation site identifier | String |
| `Sequence` | Amino acid sequence | String |
| `Upstream` | Whether upstream data is available | Boolean |
| `Downstream` | Whether downstream data is available | Boolean |
| `LTP` | Low-throughput count | Integer |
| `HTP` | High-throughput count | Integer |
| `Organism` | Organism information | String |

### Detailed Data (Optional)
- `Upstream_Data`: Detailed kinase-substrate relationships
- `Downstream_Data`: Detailed kinase-substrate relationships

### Data Cleaning Features
- **Automatic filtering**: Removes rows with "Kinase, in vitro" text
- **Sequence validation**: Filters out invalid sequences
- **Duplicate removal**: Eliminates redundant entries

## ⚙️ Configuration

### Scraper Configuration
```python
CONFIG = {
    'headless': True,                    # Browser visibility
    'start_protein_id': 583,            # Starting protein ID
    'end_protein_id': 583,              # Ending protein ID
    'max_retries': 3,                   # Retry attempts
    'notification_email': 'your@email.com',  # Email notifications
    'smtp_server': 'smtp.gmail.com',    # SMTP server
    'smtp_port': 587,                   # SMTP port
    'smtp_username': "your@email.com",  # SMTP username
    'smtp_password': "your_password",   # SMTP password
}
```

### Anti-Detection Settings
- **User Agent**: Realistic browser user agent
- **Viewport**: Random viewport sizes
- **Delays**: Random delays between requests
- **Mouse Movements**: Simulates human-like behavior
- **Cookie Management**: Saves and reuses cookies

## 🔧 Troubleshooting

### Common Issues

#### 1. Playwright Browser Not Found
```bash
playwright install chromium
```

#### 2. Dependencies Not Installed
```bash
pip install -r requirements.txt
```

#### 3. Port Already in Use (Streamlit)
```bash
streamlit run streamlit_phosphosite_app.py --server.port 8502
```

#### 4. Scraping Fails
- Check internet connection
- Verify protein ID exists on PhosphoSitePlus
- Try again after a few minutes (rate limiting)
- Check if website structure has changed

### Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "No data found for protein X" | Protein ID doesn't exist | Verify protein ID on PhosphoSitePlus |
| "Error scraping protein X" | Network issue or blocking | Check connection, try again later |
| "No Site Table tab found" | Website structure changed | Update selectors in scraper |
| "Could not find Protein Information tab" | Website structure changed | Update tab detection logic |

### Debug Mode
Set `headless: False` in configuration to see browser actions:
```python
CONFIG = {
    'headless': False,  # Shows browser window
}
```

## 📁 File Structure

```
phosphosite-scraper/
├── streamlit_site_table/
│   ├── phosphosite_site_table_scraper.py    # Main scraper
│   ├── streamlit_phosphosite_app.py         # Streamlit web app
│   ├── cookies.json                         # Saved cookies
│   └── sitetable_data/                      # Output directory
│       ├── logs/                            # Scraping logs
│       └── *.csv                           # Scraped data files
├── requirements.txt                          # Python dependencies
├── README.md                               # This file
└── run_streamlit_app.py                    # Launcher script
```

### Key Files

- **`phosphosite_site_table_scraper.py`**: Main scraping engine
- **`streamlit_phosphosite_app.py`**: Web interface
- **`requirements.txt`**: Python dependencies
- **`cookies.json`**: Browser cookies (auto-generated)

## 🛠️ Technical Details

### Web Scraping Technology
- **Playwright**: Modern browser automation
- **Cloudscraper**: Cloudflare challenge bypass
- **Stealth Techniques**: Anti-detection measures
- **Async/Await**: Non-blocking operations

### Data Processing
- **Pandas**: Data manipulation and analysis
- **Data Cleaning**: Automatic filtering and validation
- **CSV Export**: Multiple output formats
- **Error Handling**: Robust error recovery

### Web Interface
- **Streamlit**: Interactive web application
- **Plotly**: Data visualizations
- **File Upload**: CSV import capabilities
- **Progress Tracking**: Real-time updates

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Add docstrings to functions
- Include error handling
- Add debug logging

### Testing
- Test with different protein IDs
- Verify data accuracy
- Check error handling
- Test web interface

## 📄 License

This project is for educational and research purposes. Please respect PhosphoSitePlus's terms of service.

## 🙏 Acknowledgments

- **PhosphoSitePlus**: Data source and website
- **Playwright**: Browser automation framework
- **Streamlit**: Web application framework
- **Pandas**: Data manipulation library

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review error messages in the app
3. Verify protein IDs on PhosphoSitePlus
4. Check network connectivity

---

**Note**: This tool is designed for research purposes. Please use responsibly and respect the PhosphoSitePlus website's terms of service. 