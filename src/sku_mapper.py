from typing import Dict, List, Optional, Union
import pandas as pd
import polars as pl
from pathlib import Path
import logging
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SKUMapper:
    def __init__(self, config_path: Optional[str] = None):
        self.mapping_data: Dict = {}
        self.config = self._load_config(config_path) if config_path else {}
        
    def _load_config(self, config_path: str) -> Dict:
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def load_master_mapping(self, mapping_file: Union[str, Path]) -> None:
        """Load master SKU mapping from Excel/CSV file"""
        try:
            if str(mapping_file).endswith('.csv'):
                df = pd.read_csv(mapping_file)
            else:
                df = pd.read_excel(mapping_file)
            
            self.mapping_data = dict(zip(df['SKU'], df['MSKU']))
            logger.info(f"Loaded {len(self.mapping_data)} SKU mappings")
        except Exception as e:
            logger.error(f"Error loading mapping file: {e}")
            raise
    
    def map_sku(self, sku: str) -> Optional[str]:
        """Map a single SKU to its master SKU"""
        return self.mapping_data.get(sku)
    
    def batch_map_skus(self, skus: List[str]) -> Dict[str, Optional[str]]:
        """Map multiple SKUs to their master SKUs"""
        return {sku: self.map_sku(sku) for sku in skus}
    
    def validate_sku_format(self, sku: str) -> bool:
        """Validate SKU format based on configured rules"""
        if not self.config.get('sku_validation_rules'):
            return True
            
        rules = self.config['sku_validation_rules']
        # Add custom validation logic based on rules
        return True  # Placeholder for actual validation
    
    def process_sales_data(self, sales_file: Union[str, Path]) -> pd.DataFrame:
        """Process sales data and map SKUs to MSKUs"""
        try:
            # Use polars for faster data processing
            df = pl.read_csv(sales_file) if str(sales_file).endswith('.csv') else pl.read_excel(sales_file)
            df = df.to_pandas()
            
            if 'SKU' not in df.columns:
                raise ValueError("Sales data must contain 'SKU' column")
            
            df['MSKU'] = df['SKU'].map(self.mapping_data)
            df['Mapping_Status'] = df['MSKU'].notna().map({True: 'Mapped', False: 'Missing'})
            
            missing_skus = df[df['MSKU'].isna()]['SKU'].unique()
            if len(missing_skus) > 0:
                logger.warning(f"Found {len(missing_skus)} unmapped SKUs")
                
            return df
            
        except Exception as e:
            logger.error(f"Error processing sales data: {e}")
            raise
    
    def add_mapping(self, sku: str, msku: str) -> None:
        """Add new SKU to MSKU mapping"""
        if self.validate_sku_format(sku):
            self.mapping_data[sku] = msku
            logger.info(f"Added mapping: {sku} -> {msku}")
        else:
            raise ValueError(f"Invalid SKU format: {sku}")
    
    def remove_mapping(self, sku: str) -> None:
        """Remove SKU mapping"""
        if sku in self.mapping_data:
            del self.mapping_data[sku]
            logger.info(f"Removed mapping for SKU: {sku}")
        else:
            logger.warning(f"SKU not found in mapping: {sku}")
    
    def export_mapping(self, output_file: Union[str, Path]) -> None:
        """Export current mapping to file"""
        try:
            df = pd.DataFrame(list(self.mapping_data.items()), columns=['SKU', 'MSKU'])
            if str(output_file).endswith('.csv'):
                df.to_csv(output_file, index=False)
            else:
                df.to_excel(output_file, index=False)
            logger.info(f"Exported {len(df)} mappings to {output_file}")
        except Exception as e:
            logger.error(f"Error exporting mapping: {e}")
            raise