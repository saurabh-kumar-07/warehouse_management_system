from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import text
from datetime import datetime
import yaml
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseMigration:
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.engine = self._create_engine()
        self.metadata = MetaData()
        
    def _load_config(self, config_path: str) -> dict:
        if not config_path:
            config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
        
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                return config['database']
        except Exception as e:
            logger.error(f"Error loading database config: {e}")
            raise
    
    def _create_engine(self):
        db_url = f"postgresql://{self.config['user']}:{self.config['password']}@"\
                 f"{self.config['host']}:{self.config['port']}/{self.config['name']}"
        return create_engine(db_url)
    
    def create_initial_schema(self):
        """Create initial database schema"""
        try:
            # Products table
            products = Table('products', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('sku', String(50), unique=True, nullable=False),
                Column('msku', String(50), nullable=False),
                Column('name', String(200)),
                Column('description', Text),
                Column('category', String(100)),
                Column('created_at', DateTime, default=datetime.utcnow),
                Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            )
            
            # Sales Orders table
            sales_orders = Table('sales_orders', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('order_number', String(50), unique=True, nullable=False),
                Column('order_date', DateTime, nullable=False),
                Column('customer_name', String(200)),
                Column('total_amount', Float),
                Column('status', String(50)),
                Column('created_at', DateTime, default=datetime.utcnow)
            )
            
            # Order Items table
            order_items = Table('order_items', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('order_id', Integer, ForeignKey('sales_orders.id')),
                Column('product_id', Integer, ForeignKey('products.id')),
                Column('quantity', Integer),
                Column('unit_price', Float),
                Column('total_price', Float)
            )
            
            # Create all tables
            self.metadata.create_all(self.engine)
            logger.info("Initial schema created successfully")
            
        except Exception as e:
            logger.error(f"Error creating initial schema: {e}")
            raise
    
    def add_indexes(self):
        """Add database indexes for performance"""
        try:
            with self.engine.connect() as conn:
                # Add index on SKU and MSKU
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_products_sku ON products (sku);
                    CREATE INDEX IF NOT EXISTS idx_products_msku ON products (msku);
                """))
                
                # Add index on order dates
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_sales_orders_date 
                    ON sales_orders (order_date);
                """))
                
                # Add composite indexes
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_order_items_composite 
                    ON order_items (order_id, product_id);
                """))
                
                conn.commit()
                logger.info("Indexes added successfully")
                
        except Exception as e:
            logger.error(f"Error adding indexes: {e}")
            raise
    
    def add_constraints(self):
        """Add database constraints"""
        try:
            with self.engine.connect() as conn:
                # Add check constraints
                conn.execute(text("""
                    ALTER TABLE order_items 
                    ADD CONSTRAINT check_positive_quantity 
                    CHECK (quantity > 0);
                    
                    ALTER TABLE order_items 
                    ADD CONSTRAINT check_positive_price 
                    CHECK (unit_price >= 0);
                """))
                
                conn.commit()
                logger.info("Constraints added successfully")
                
        except Exception as e:
            logger.error(f"Error adding constraints: {e}")
            raise
    
    def create_views(self):
        """Create database views for common queries"""
        try:
            with self.engine.connect() as conn:
                # Sales summary view
                conn.execute(text("""
                    CREATE OR REPLACE VIEW sales_summary AS
                    SELECT 
                        p.category,
                        DATE_TRUNC('month', so.order_date) as month,
                        COUNT(DISTINCT so.id) as total_orders,
                        SUM(oi.quantity) as total_quantity,
                        SUM(oi.total_price) as total_revenue
                    FROM sales_orders so
                    JOIN order_items oi ON so.id = oi.order_id
                    JOIN products p ON oi.product_id = p.id
                    GROUP BY p.category, DATE_TRUNC('month', so.order_date);
                """))
                
                # Product performance view
                conn.execute(text("""
                    CREATE OR REPLACE VIEW product_performance AS
                    SELECT 
                        p.id,
                        p.sku,
                        p.msku,
                        p.name,
                        p.category,
                        COUNT(DISTINCT oi.order_id) as order_count,
                        SUM(oi.quantity) as total_quantity,
                        SUM(oi.total_price) as total_revenue
                    FROM products p
                    LEFT JOIN order_items oi ON p.id = oi.product_id
                    GROUP BY p.id, p.sku, p.msku, p.name, p.category;
                """))
                
                conn.commit()
                logger.info("Views created successfully")
                
        except Exception as e:
            logger.error(f"Error creating views: {e}")
            raise
    
    def run_migrations(self):
        """Run all migrations in sequence"""
        try:
            self.create_initial_schema()
            self.add_indexes()
            self.add_constraints()
            self.create_views()
            logger.info("All migrations completed successfully")
            
        except Exception as e:
            logger.error(f"Error running migrations: {e}")
            raise