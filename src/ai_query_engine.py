import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional, Union, Tuple
from database import Database
from analytics import Analytics
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIQueryEngine:
    def __init__(self, db: Database, analytics: Analytics):
        self.db = db
        self.analytics = analytics
        self.query_patterns = self._initialize_query_patterns()
    
    def _initialize_query_patterns(self) -> Dict:
        """Initialize regex patterns for query understanding"""
        return {
            'sales_trend': r'(?i)(show|display|get)\s+(sales|revenue)\s+trend',
            'top_products': r'(?i)(show|list|what\s+are)\s+top\s+(\d+)?\s*products',
            'category_performance': r'(?i)(show|display|get)\s+category\s+performance',
            'time_period': r'(?i)(last|past)\s+(\d+)\s+(days|weeks|months)',
            'specific_dates': r'(?i)between\s+([\w\s,]+)\s+and\s+([\w\s,]+)',
            'comparison': r'(?i)compare\s+(\w+)\s+with\s+(\w+)',
            'calculation': r'(?i)(calculate|compute|what\s+is)\s+([\w\s]+)'}
    
    def process_natural_query(self, query: str) -> Tuple[go.Figure, str]:
        """Process natural language query and return visualization"""
        try:
            # Identify query type and parameters
            query_type, params = self._analyze_query(query)
            
            # Generate appropriate visualization
            if query_type == 'sales_trend':
                fig = self._generate_sales_trend(**params)
                description = "Sales trend over the specified time period"
            
            elif query_type == 'top_products':
                fig = self._generate_top_products(**params)
                description = f"Top {params.get('limit', 10)} products by revenue"
            
            elif query_type == 'category_performance':
                fig = self._generate_category_performance(**params)
                description = "Performance comparison across product categories"
            
            else:
                raise ValueError(f"Unsupported query type: {query_type}")
            
            return fig, description
        
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise
    
    def _analyze_query(self, query: str) -> Tuple[str, Dict]:
        """Analyze natural language query and extract parameters"""
        params = {}
        
        # Extract time period
        time_match = re.search(self.query_patterns['time_period'], query)
        if time_match:
            number = int(time_match.group(2))
            unit = time_match.group(3)
            params['time_period'] = (number, unit)
        
        # Extract specific dates
        date_match = re.search(self.query_patterns['specific_dates'], query)
        if date_match:
            params['start_date'] = date_match.group(1)
            params['end_date'] = date_match.group(2)
        
        # Determine query type
        if re.search(self.query_patterns['sales_trend'], query):
            return 'sales_trend', params
        
        elif re.search(self.query_patterns['top_products'], query):
            limit_match = re.search(r'top\s+(\d+)', query)
            params['limit'] = int(limit_match.group(1)) if limit_match else 10
            return 'top_products', params
        
        elif re.search(self.query_patterns['category_performance'], query):
            return 'category_performance', params
        
        else:
            raise ValueError("Unable to determine query type")
    
    def _generate_sales_trend(self, **params) -> go.Figure:
        """Generate sales trend visualization"""
        return self.analytics.create_sales_trend_chart(
            start_date=params.get('start_date'),
            end_date=params.get('end_date')
        )
    
    def _generate_top_products(self, limit: int = 10, **params) -> go.Figure:
        """Generate top products visualization"""
        # Get sales data from database
        sales_data = self.db.get_top_products(limit)
        df = pd.DataFrame(sales_data)
        
        fig = px.bar(
            df,
            x='product_name',
            y='total_revenue',
            title=f'Top {limit} Products by Revenue',
            labels={
                'product_name': 'Product',
                'total_revenue': 'Total Revenue'
            }
        )
        return fig
    
    def _generate_category_performance(self, **params) -> go.Figure:
        """Generate category performance visualization"""
        return self.analytics.create_category_performance_chart(
            self.db.get_category_performance()
        )
    
    def add_calculated_field(self, df: pd.DataFrame, field_name: str,
                           calculation: str) -> pd.DataFrame:
        """Add calculated field based on natural language description"""
        try:
            # Parse calculation description
            if 'profit margin' in calculation.lower():
                df[field_name] = (df['total_price'] - df['cost']) / df['total_price'] * 100
            
            elif 'days since order' in calculation.lower():
                df[field_name] = (pd.Timestamp.now() - df['order_date']).dt.days
            
            elif 'average order value' in calculation.lower():
                df[field_name] = df.groupby('order_number')['total_price'].transform('mean')
            
            else:
                raise ValueError(f"Unsupported calculation: {calculation}")
            
            return df
        
        except Exception as e:
            logger.error(f"Error adding calculated field: {e}")
            raise
    
    def generate_chart(self, df: pd.DataFrame, chart_type: str,
                      x_column: str, y_column: str, **kwargs) -> go.Figure:
        """Generate chart based on natural language description"""
        chart_types = {
            'line': px.line,
            'bar': px.bar,
            'scatter': px.scatter,
            'pie': px.pie
        }
        
        if chart_type not in chart_types:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        
        fig = chart_types[chart_type](
            df,
            x=x_column,
            y=y_column,
            **kwargs
        )
        return fig