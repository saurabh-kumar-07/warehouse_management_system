import pandas as pd
import polars as pl
from typing import Dict, List, Optional, Union
from pathlib import Path
import logging
from pandera import DataFrameSchema, Column, Check
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        self.sales_schema = DataFrameSchema({
            'order_number': Column(str, Check.not_null()),
            'order_date': Column(pd.Timestamp, Check.not_null()),
            'SKU': Column(str, Check.not_null()),
            'quantity': Column(int, Check(lambda x: x >= 0)),
            'unit_price': Column(float, Check(lambda x: x >= 0)),
            'total_price': Column(float, Check(lambda x: x >= 0))
        })
    
    def clean_sales_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate sales data"""
        try:
            # Convert date columns
            if 'order_date' in df.columns:
                df['order_date'] = pd.to_datetime(df['order_date'])
            
            # Remove duplicates
            df = df.drop_duplicates()
            
            # Handle missing values
            df = df.fillna({
                'quantity': 0,
                'unit_price': 0,
                'total_price': 0
            })
            
            # Calculate total price if missing
            mask = df['total_price'] == 0
            df.loc[mask, 'total_price'] = df.loc[mask, 'quantity'] * df.loc[mask, 'unit_price']
            
            # Validate against schema
            self.sales_schema.validate(df)
            
            return df
        
        except Exception as e:
            logger.error(f"Error cleaning sales data: {e}")
            raise
    
    def process_marketplace_data(self, df: pd.DataFrame, marketplace: str) -> pd.DataFrame:
        """Process data from different marketplaces"""
        processors = {
            'amazon': self._process_amazon_data,
            'ebay': self._process_ebay_data,
            'shopify': self._process_shopify_data
        }
        
        if marketplace.lower() not in processors:
            raise ValueError(f"Unsupported marketplace: {marketplace}")
        
        return processors[marketplace.lower()](df)
    
    def _process_amazon_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process Amazon marketplace data"""
        # Rename columns to standard format
        column_mapping = {
            'Order ID': 'order_number',
            'Purchase Date': 'order_date',
            'SKU': 'SKU',
            'Quantity': 'quantity',
            'Item Price': 'unit_price'
        }
        
        df = df.rename(columns=column_mapping)
        return self.clean_sales_data(df)
    
    def _process_ebay_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process eBay marketplace data"""
        column_mapping = {
            'Transaction ID': 'order_number',
            'Sale Date': 'order_date',
            'Custom Label': 'SKU',
            'Quantity': 'quantity',
            'Sale Price': 'unit_price'
        }
        
        df = df.rename(columns=column_mapping)
        return self.clean_sales_data(df)
    
    def _process_shopify_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process Shopify marketplace data"""
        column_mapping = {
            'Order Number': 'order_number',
            'Created At': 'order_date',
            'Variant SKU': 'SKU',
            'Quantity': 'quantity',
            'Price': 'unit_price'
        }
        
        df = df.rename(columns=column_mapping)
        return self.clean_sales_data(df)
    
    def combine_marketplace_data(self, dataframes: List[pd.DataFrame]) -> pd.DataFrame:
        """Combine data from multiple marketplaces"""
        try:
            # Ensure all dataframes have the same structure
            combined_df = pd.concat(dataframes, ignore_index=True)
            
            # Remove duplicates across marketplaces
            combined_df = combined_df.drop_duplicates(subset=['order_number', 'SKU'])
            
            # Sort by date
            combined_df = combined_df.sort_values('order_date')
            
            return combined_df
        
        except Exception as e:
            logger.error(f"Error combining marketplace data: {e}")
            raise
    
    def validate_data_quality(self, df: pd.DataFrame) -> Dict:
        """Validate data quality and return metrics"""
        metrics = {
            'total_rows': len(df),
            'duplicate_rows': len(df) - len(df.drop_duplicates()),
            'missing_values': df.isnull().sum().to_dict(),
            'negative_values': {
                'quantity': len(df[df['quantity'] < 0]),
                'unit_price': len(df[df['unit_price'] < 0]),
                'total_price': len(df[df['total_price'] < 0])
            },
            'date_range': {
                'start': df['order_date'].min(),
                'end': df['order_date'].max()
            }
        }
        
        return metrics
    
    def export_processed_data(self, df: pd.DataFrame, output_path: Union[str, Path],
                            format: str = 'excel') -> None:
        """Export processed data to file"""
        try:
            if format.lower() == 'excel':
                df.to_excel(output_path, index=False)
            elif format.lower() == 'csv':
                df.to_csv(output_path, index=False)
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            logger.info(f"Data exported successfully to {output_path}")
        
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            raise