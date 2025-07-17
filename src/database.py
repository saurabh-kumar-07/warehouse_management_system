from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import yaml
from pathlib import Path
import logging

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    sku = Column(String(50), unique=True, nullable=False)
    msku = Column(String(50), nullable=False)
    name = Column(String(200))
    description = Column(Text)
    category = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SalesOrder(Base):
    __tablename__ = 'sales_orders'
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String(50), unique=True, nullable=False)
    order_date = Column(DateTime, nullable=False)
    customer_name = Column(String(200))
    total_amount = Column(Float)
    status = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

class OrderItem(Base):
    __tablename__ = 'order_items'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('sales_orders.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Integer)
    unit_price = Column(Float)
    total_price = Column(Float)
    
    order = relationship('SalesOrder', backref='items')
    product = relationship('Product')

class Database:
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.engine = self._create_engine()
        self.Session = sessionmaker(bind=self.engine)
        
    def _load_config(self, config_path: str) -> dict:
        if not config_path:
            config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
        
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                return config['database']
        except Exception as e:
            logging.error(f"Error loading database config: {e}")
            raise
    
    def _create_engine(self):
        db_url = f"postgresql://{self.config['user']}:{self.config['password']}@"\
                 f"{self.config['host']}:{self.config['port']}/{self.config['name']}"
        return create_engine(db_url)
    
    def init_db(self):
        """Initialize database tables"""
        Base.metadata.create_all(self.engine)
    
    def add_product(self, sku: str, msku: str, **kwargs):
        """Add a new product to the database"""
        session = self.Session()
        try:
            product = Product(sku=sku, msku=msku, **kwargs)
            session.add(product)
            session.commit()
            return product
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_product_by_sku(self, sku: str):
        """Retrieve a product by SKU"""
        session = self.Session()
        try:
            return session.query(Product).filter(Product.sku == sku).first()
        finally:
            session.close()
    
    def create_sales_order(self, order_data: dict, items: list):
        """Create a new sales order with items"""
        session = self.Session()
        try:
            # Create sales order
            order = SalesOrder(**order_data)
            session.add(order)
            session.flush()
            
            # Add order items
            for item in items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    unit_price=item['unit_price'],
                    total_price=item['quantity'] * item['unit_price']
                )
                session.add(order_item)
            
            session.commit()
            return order
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_sales_analytics(self, start_date: datetime = None, end_date: datetime = None):
        """Get sales analytics for a given date range"""
        session = self.Session()
        try:
            query = session.query(
                Product.category,
                func.count(OrderItem.id).label('total_orders'),
                func.sum(OrderItem.quantity).label('total_quantity'),
                func.sum(OrderItem.total_price).label('total_revenue')
            ).join(OrderItem).join(SalesOrder)
            
            if start_date:
                query = query.filter(SalesOrder.order_date >= start_date)
            if end_date:
                query = query.filter(SalesOrder.order_date <= end_date)
            
            return query.group_by(Product.category).all()
        finally:
            session.close()