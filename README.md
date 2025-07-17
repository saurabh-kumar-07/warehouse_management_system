# Warehouse Management System (WMS)

A comprehensive Warehouse Management System that handles SKU mapping, sales data processing, and analytics visualization.

## Features

- **SKU Mapping Management**
  - Automated SKU to Master SKU (MSKU) mapping
  - Support for multiple marketplace formats
  - Validation rules for SKU formats
  - Batch processing capabilities

- **Data Processing**
  - Sales data cleaning and transformation
  - Error handling and logging
  - Support for various input formats (CSV, Excel)

- **Analytics Dashboard**
  - Real-time visualization of mapping statistics
  - Sales data analysis
  - Interactive data exploration

- **Database Integration**
  - PostgreSQL database for data persistence
  - Relational data model for products and sales
  - Analytics query support

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **Database**: PostgreSQL
- **Data Processing**: Pandas, Polars
- **Visualization**: Plotly

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd warehouse-management-system
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Database**
   - Install PostgreSQL if not already installed
   - Create a new database named 'wms_db'
   - Update database configuration in `config/config.yaml`

5. **Run the Application**
   ```bash
   cd src
   streamlit run app.py
   ```

## Project Structure

```
├── config/
│   └── config.yaml         # Configuration settings
├── src/
│   ├── app.py             # Streamlit web interface
│   ├── sku_mapper.py      # SKU mapping logic
│   └── database.py        # Database operations
├── requirements.txt       # Python dependencies
└── README.md             # Project documentation
```

## Usage Guide

1. **Data Processing**
   - Upload SKU mapping file (Excel/CSV)
   - Upload sales data file
   - View processing results and statistics

2. **Mapping Management**
   - Add new SKU to MSKU mappings
   - Remove existing mappings
   - Export current mapping data

3. **Analytics Dashboard**
   - View mapping coverage statistics
   - Analyze sales data
   - Export processed data

## Development

1. **Adding New Features**
   - Follow the modular architecture
   - Update configuration as needed
   - Add appropriate error handling and logging

2. **Testing**
   - Run unit tests: `python -m pytest tests/`
   - Validate SKU mapping logic
   - Test database operations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.