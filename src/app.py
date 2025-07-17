import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from sku_mapper import SKUMapper
import logging

st.set_page_config(page_title="WMS Dashboard", layout="wide")

# Initialize session state
if 'sku_mapper' not in st.session_state:
    st.session_state.sku_mapper = SKUMapper()

if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None

def load_mapping_file():
    mapping_file = st.file_uploader("Upload SKU Mapping File (Excel/CSV)", type=['xlsx', 'csv'])
    if mapping_file:
        try:
            st.session_state.sku_mapper.load_master_mapping(mapping_file)
            st.success("✅ Mapping file loaded successfully!")
        except Exception as e:
            st.error(f"Error loading mapping file: {e}")

def process_sales_data():
    sales_file = st.file_uploader("Upload Sales Data (Excel/CSV)", type=['xlsx', 'csv'])
    if sales_file:
        try:
            df = st.session_state.sku_mapper.process_sales_data(sales_file)
            st.session_state.processed_data = df
            st.success("✅ Sales data processed successfully!")
            return df
        except Exception as e:
            st.error(f"Error processing sales data: {e}")
            return None

def display_mapping_management():
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Add New Mapping")
        new_sku = st.text_input("SKU")
        new_msku = st.text_input("Master SKU")
        if st.button("Add Mapping"):
            try:
                st.session_state.sku_mapper.add_mapping(new_sku, new_msku)
                st.success(f"✅ Added mapping: {new_sku} -> {new_msku}")
            except Exception as e:
                st.error(f"Error adding mapping: {e}")
    
    with col2:
        st.subheader("Remove Mapping")
        sku_to_remove = st.text_input("SKU to Remove")
        if st.button("Remove Mapping"):
            try:
                st.session_state.sku_mapper.remove_mapping(sku_to_remove)
                st.success(f"✅ Removed mapping for SKU: {sku_to_remove}")
            except Exception as e:
                st.error(f"Error removing mapping: {e}")

def display_data_analysis():
    if st.session_state.processed_data is not None:
        df = st.session_state.processed_data
        
        # Display summary statistics
        st.subheader("Summary Statistics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_skus = len(df['SKU'].unique())
            st.metric("Total Unique SKUs", total_skus)
            
        with col2:
            mapped_skus = df[df['Mapping_Status'] == 'Mapped']['SKU'].nunique()
            st.metric("Mapped SKUs", mapped_skus)
            
        with col3:
            mapping_coverage = (mapped_skus / total_skus * 100) if total_skus > 0 else 0
            st.metric("Mapping Coverage", f"{mapping_coverage:.1f}%")
        
        # Display mapping status chart
        st.subheader("Mapping Status Distribution")
        status_counts = df['Mapping_Status'].value_counts()
        fig = px.pie(values=status_counts.values, names=status_counts.index,
                     title="SKU Mapping Status Distribution")
        st.plotly_chart(fig)
        
        # Display data tables
        st.subheader("Processed Data")
        st.dataframe(df)
        
        # Export functionality
        if st.button("Export Processed Data"):
            output_path = Path("processed_data.xlsx")
            df.to_excel(output_path, index=False)
            st.success(f"✅ Data exported to {output_path}")

def main():
    st.title("Warehouse Management System")
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["Data Processing", "Mapping Management", "Analysis Dashboard"]
    )
    
    if page == "Data Processing":
        st.header("Data Processing")
        st.subheader("1. Load SKU Mapping")
        load_mapping_file()
        
        st.subheader("2. Process Sales Data")
        process_sales_data()
        
    elif page == "Mapping Management":
        st.header("SKU Mapping Management")
        display_mapping_management()
        
    else:  # Analysis Dashboard
        st.header("Analysis Dashboard")
        display_data_analysis()

if __name__ == "__main__":
    main()