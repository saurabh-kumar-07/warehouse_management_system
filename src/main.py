import streamlit as st
from pathlib import Path
import logging
from database import Database
from migrations import DatabaseMigration
from sku_mapper import SKUMapper
from data_processor import DataProcessor
from analytics import Analytics
from ai_query_engine import AIQueryEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WarehouseManagementSystem:
    def __init__(self):
        self.config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
        self.initialize_components()
    
    def initialize_components(self):
        """Initialize all system components"""
        try:
            # Initialize database
            self.db = Database(self.config_path)
            
            # Run database migrations
            migrator = DatabaseMigration(self.config_path)
            migrator.run_migrations()
            
            # Initialize other components
            self.sku_mapper = SKUMapper(self.config_path)
            self.data_processor = DataProcessor()
            self.analytics = Analytics(self.db)
            self.ai_query_engine = AIQueryEngine(self.db, self.analytics)
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    def run_streamlit_app(self):
        """Run the Streamlit web application"""
        try:
            st.set_page_config(page_title="WMS Dashboard", layout="wide")
            
            # Sidebar navigation
            page = st.sidebar.selectbox(
                "Navigation",
                ["Home", "Data Processing", "SKU Mapping", "Analytics", "AI Query"]
            )
            
            if page == "Home":
                self.render_home_page()
            elif page == "Data Processing":
                self.render_data_processing_page()
            elif page == "SKU Mapping":
                self.render_sku_mapping_page()
            elif page == "Analytics":
                self.render_analytics_page()
            else:  # AI Query
                self.render_ai_query_page()
            
        except Exception as e:
            logger.error(f"Error running Streamlit app: {e}")
            st.error(f"An error occurred: {str(e)}")
    
    def render_home_page(self):
        """Render the home page"""
        st.title("Warehouse Management System")
        st.write("""
        Welcome to the Warehouse Management System dashboard. This system provides:
        - Automated SKU mapping
        - Sales data processing
        - Advanced analytics
        - AI-powered querying
        """)
        
        # Display system status
        st.subheader("System Status")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Database Status", "Connected" if self.db else "Disconnected")
        with col2:
            st.metric("Mapped SKUs", len(self.sku_mapper.mapping_data))
        with col3:
            st.metric("Active Sessions", st.session_state.get('session_count', 0))
    
    def render_data_processing_page(self):
        """Render the data processing page"""
        st.title("Data Processing")
        
        uploaded_file = st.file_uploader("Upload Sales Data", type=['csv', 'xlsx'])
        if uploaded_file:
            marketplace = st.selectbox(
                "Select Marketplace",
                ["Amazon", "eBay", "Shopify"]
            )
            
            if st.button("Process Data"):
                with st.spinner("Processing data..."):
                    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') \
                        else pd.read_excel(uploaded_file)
                    
                    processed_df = self.data_processor.process_marketplace_data(
                        df, marketplace.lower()
                    )
                    
                    st.success("✅ Data processed successfully!")
                    st.dataframe(processed_df)
    
    def render_sku_mapping_page(self):
        """Render the SKU mapping page"""
        st.title("SKU Mapping Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Add New Mapping")
            new_sku = st.text_input("SKU")
            new_msku = st.text_input("Master SKU")
            
            if st.button("Add Mapping"):
                try:
                    self.sku_mapper.add_mapping(new_sku, new_msku)
                    st.success(f"✅ Added mapping: {new_sku} -> {new_msku}")
                except Exception as e:
                    st.error(str(e))
        
        with col2:
            st.subheader("Current Mappings")
            if self.sku_mapper.mapping_data:
                df = pd.DataFrame(list(self.sku_mapper.mapping_data.items()),
                                columns=['SKU', 'MSKU'])
                st.dataframe(df)
    
    def render_analytics_page(self):
        """Render the analytics page"""
        st.title("Analytics Dashboard")
        
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date")
        with col2:
            end_date = st.date_input("End Date")
        
        if start_date and end_date:
            # Sales trend
            st.subheader("Sales Trend")
            sales_trend = self.analytics.create_sales_trend_chart(start_date, end_date)
            st.plotly_chart(sales_trend)
            
            # Category performance
            st.subheader("Category Performance")
            category_chart = self.analytics.create_category_performance_chart(
                self.db.get_category_performance()
            )
            st.plotly_chart(category_chart)
    
    def render_ai_query_page(self):
        """Render the AI query page"""
        st.title("AI Query Engine")
        
        query = st.text_input("Enter your query (e.g., 'Show sales trend for last 30 days')")
        
        if query:
            try:
                fig, description = self.ai_query_engine.process_natural_query(query)
                st.write(description)
                st.plotly_chart(fig)
            except Exception as e:
                st.error(f"Error processing query: {str(e)}")

def main():
    try:
        wms = WarehouseManagementSystem()
        wms.run_streamlit_app()
    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error("An error occurred while starting the application. Please check the logs.")

if __name__ == "__main__":
    main()