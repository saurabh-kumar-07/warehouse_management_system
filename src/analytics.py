import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from database import Database

class Analytics:
    def __init__(self, db: Database):
        self.db = db
    
    def generate_mapping_stats(self, df: pd.DataFrame) -> Dict:
        """Generate statistics about SKU mapping coverage"""
        total_skus = len(df['SKU'].unique())
        mapped_skus = df[df['Mapping_Status'] == 'Mapped']['SKU'].nunique()
        
        return {
            'total_skus': total_skus,
            'mapped_skus': mapped_skus,
            'unmapped_skus': total_skus - mapped_skus,
            'mapping_coverage': (mapped_skus / total_skus * 100) if total_skus > 0 else 0
        }
    
    def create_mapping_status_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create a pie chart showing mapping status distribution"""
        status_counts = df['Mapping_Status'].value_counts()
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="SKU Mapping Status Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        return fig
    
    def create_sales_trend_chart(self, start_date: datetime, end_date: datetime) -> go.Figure:
        """Create a line chart showing sales trends"""
        sales_data = self.db.get_sales_analytics(start_date, end_date)
        df = pd.DataFrame(sales_data)
        
        fig = px.line(
            df,
            x='order_date',
            y='total_revenue',
            title='Sales Trend Over Time',
            labels={'total_revenue': 'Total Revenue', 'order_date': 'Date'}
        )
        return fig
    
    def create_category_performance_chart(self, data: pd.DataFrame) -> go.Figure:
        """Create a bar chart showing performance by category"""
        fig = px.bar(
            data,
            x='category',
            y=['total_quantity', 'total_revenue'],
            title='Category Performance',
            barmode='group',
            labels={
                'category': 'Product Category',
                'total_quantity': 'Total Quantity',
                'total_revenue': 'Total Revenue'
            }
        )
        return fig
    
    def generate_product_insights(self, df: pd.DataFrame) -> Dict:
        """Generate insights about product performance"""
        insights = {
            'top_products': df.groupby('MSKU')['quantity'].sum()
                            .sort_values(ascending=False).head(5).to_dict(),
            'revenue_by_category': df.groupby('category')['total_price'].sum().to_dict(),
            'avg_order_value': df['total_price'].mean(),
            'total_orders': len(df['order_number'].unique())
        }
        return insights
    
    def create_heatmap(self, df: pd.DataFrame, metric: str = 'quantity') -> go.Figure:
        """Create a heatmap showing patterns in the data"""
        pivot_table = df.pivot_table(
            values=metric,
            index=pd.Grouper(key='order_date', freq='W'),
            columns='category',
            aggfunc='sum'
        ).fillna(0)
        
        fig = px.imshow(
            pivot_table,
            title=f'{metric.title()} Heatmap by Category and Week',
            labels=dict(x='Category', y='Week', color=metric.title())
        )
        return fig
    
    def create_forecast_chart(self, df: pd.DataFrame, periods: int = 30) -> go.Figure:
        """Create a simple forecast chart using moving averages"""
        # Calculate moving averages
        df['MA7'] = df['total_revenue'].rolling(window=7).mean()
        df['MA30'] = df['total_revenue'].rolling(window=30).mean()
        
        fig = go.Figure()
        
        # Add actual values
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['total_revenue'],
            name='Actual',
            mode='lines'
        ))
        
        # Add moving averages
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['MA7'],
            name='7-day MA',
            mode='lines'
        ))
        
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['MA30'],
            name='30-day MA',
            mode='lines'
        ))
        
        fig.update_layout(
            title='Sales Forecast',
            xaxis_title='Date',
            yaxis_title='Revenue'
        )
        
        return fig
    
    def generate_summary_report(self, df: pd.DataFrame) -> Dict:
        """Generate a comprehensive summary report"""
        mapping_stats = self.generate_mapping_stats(df)
        product_insights = self.generate_product_insights(df)
        
        report = {
            'mapping_statistics': mapping_stats,
            'product_insights': product_insights,
            'summary_metrics': {
                'total_revenue': df['total_price'].sum(),
                'average_order_value': df['total_price'].mean(),
                'total_orders': len(df['order_number'].unique()),
                'unique_products': len(df['MSKU'].unique())
            }
        }
        
        return report