import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add src directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from sku_mapper import SKUMapper
from data_processor import DataProcessor
from database import Database
from analytics import Analytics

class TestSKUMapper(unittest.TestCase):
    def setUp(self):
        self.sku_mapper = SKUMapper()
        self.test_mapping = {
            'SKU1': 'MSKU1',
            'SKU2': 'MSKU2',
            'SKU3': 'MSKU2'  # Multiple SKUs mapping to same MSKU
        }
    
    def test_add_mapping(self):
        self.sku_mapper.add_mapping('TEST1', 'MTEST1')
        self.assertEqual(self.sku_mapper.map_sku('TEST1'), 'MTEST1')
    
    def test_batch_mapping(self):
        for sku, msku in self.test_mapping.items():
            self.sku_mapper.add_mapping(sku, msku)
        
        result = self.sku_mapper.batch_map_skus(['SKU1', 'SKU2', 'SKU3', 'SKU4'])
        self.assertEqual(result['SKU1'], 'MSKU1')
        self.assertEqual(result['SKU2'], 'MSKU2')
        self.assertEqual(result['SKU3'], 'MSKU2')
        self.assertIsNone(result['SKU4'])

class TestDataProcessor(unittest.TestCase):
    def setUp(self):
        self.data_processor = DataProcessor()
        
        # Create sample test data
        self.test_data = pd.DataFrame({
            'order_number': ['ORD1', 'ORD2', 'ORD3'],
            'order_date': ['2023-01-01', '2023-01-02', '2023-01-03'],
            'SKU': ['SKU1', 'SKU2', 'SKU3'],
            'quantity': [1, 2, -1],  # Include invalid quantity
            'unit_price': [10.0, 20.0, 15.0],
            'total_price': [10.0, 40.0, -15.0]  # Include invalid price
        })
    
    def test_clean_sales_data(self):
        cleaned_df = self.data_processor.clean_sales_data(self.test_data.copy())
        
        # Check date conversion
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(cleaned_df['order_date']))
        
        # Check negative values handling
        self.assertTrue((cleaned_df['quantity'] >= 0).all())
        self.assertTrue((cleaned_df['total_price'] >= 0).all())
        
        # Check total price calculation
        expected_total = cleaned_df['quantity'] * cleaned_df['unit_price']
        pd.testing.assert_series_equal(cleaned_df['total_price'], expected_total)
    
    def test_marketplace_processing(self):
        # Test Amazon data processing
        amazon_data = pd.DataFrame({
            'Order ID': ['A1', 'A2'],
            'Purchase Date': ['2023-01-01', '2023-01-02'],
            'SKU': ['SKU1', 'SKU2'],
            'Quantity': [1, 2],
            'Item Price': [10.0, 20.0]
        })
        
        processed_df = self.data_processor.process_marketplace_data(amazon_data, 'amazon')
        self.assertIn('order_number', processed_df.columns)
        self.assertIn('order_date', processed_df.columns)
        self.assertIn('SKU', processed_df.columns)

class TestAnalytics(unittest.TestCase):
    def setUp(self):
        self.db = Database()  # Mock database for testing
        self.analytics = Analytics(self.db)
        
        # Create sample test data
        self.test_data = pd.DataFrame({
            'SKU': ['SKU1', 'SKU2', 'SKU3'],
            'MSKU': ['MSKU1', 'MSKU2', None],
            'Mapping_Status': ['Mapped', 'Mapped', 'Missing'],
            'quantity': [1, 2, 3],
            'total_price': [100, 200, 300]
        })
    
    def test_mapping_stats(self):
        stats = self.analytics.generate_mapping_stats(self.test_data)
        
        self.assertEqual(stats['total_skus'], 3)
        self.assertEqual(stats['mapped_skus'], 2)
        self.assertEqual(stats['unmapped_skus'], 1)
        self.assertAlmostEqual(stats['mapping_coverage'], 66.67, places=2)
    
    def test_generate_summary_report(self):
        report = self.analytics.generate_summary_report(self.test_data)
        
        self.assertIn('mapping_statistics', report)
        self.assertIn('summary_metrics', report)
        
        metrics = report['summary_metrics']
        self.assertEqual(metrics['total_revenue'], 600)
        self.assertEqual(metrics['unique_products'], 2)  # Only mapped MSKUs

def run_tests():
    unittest.main()

if __name__ == '__main__':
    run_tests()