import subprocess
subprocess.run(["playwright", "install", "chromium"], check=True)
import streamlit as st
import pandas as pd
import asyncio
import os
import json
import time
from datetime import datetime
import base64
from io import BytesIO
import zipfile
import tempfile


# Import the scraper functions
from phosphosite_site_table_scraper import (
    scrape_phosphosite_site_table,
    process_site_data,
    get_random_delay,
    handle_cloudflare_challenge,
    add_random_behavior,
    load_cookies,
    save_cookies
)
from playwright.async_api import async_playwright
import random

# Page configuration
st.set_page_config(
    page_title="PhosphoSite Site Table Scraper",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #f5c6cb;
    }
    .info-message {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #bee5eb;
    }
</style>
""", unsafe_allow_html=True)

def download_csv(df, filename):
    """Generate a download link for CSV file"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV</a>'
    return href

def download_zip(files_dict):
    """Create and download a zip file containing multiple CSV files"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
        with zipfile.ZipFile(tmp_file.name, 'w') as zip_file:
            for filename, df in files_dict.items():
                csv_data = df.to_csv(index=False)
                zip_file.writestr(filename, csv_data)
        
        with open(tmp_file.name, 'rb') as f:
            zip_data = f.read()
    
    os.unlink(tmp_file.name)
    return zip_data

async def scrape_single_protein(protein_id, progress_bar, status_text):
    """Scrape a single protein and update progress"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-gpu',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            
            page = await context.new_page()
            
            # Load cookies if available
            await load_cookies(context)
            
            # Scrape the protein
            result = await scrape_phosphosite_site_table(protein_id, f"Protein_{protein_id}", page)
            
            # Save cookies
            await save_cookies(context)
            
            await browser.close()
            
            if result:
                df = process_site_data(result)
                return df
            else:
                return None
                
    except Exception as e:
        st.error(f"Error scraping protein {protein_id}: {str(e)}")
        return None

async def scrape_batch_proteins(protein_ids, progress_bar, status_text):
    """Scrape multiple proteins in batch"""
    results = {}
    
    for i, protein_id in enumerate(protein_ids):
        status_text.text(f"Scraping protein {protein_id}... ({i+1}/{len(protein_ids)})")
        
        result = await scrape_single_protein(protein_id, progress_bar, status_text)
        
        if result is not None and not result.empty:
            protein_name = result['Protein'].iloc[0] if 'Protein' in result.columns else f"Protein_{protein_id}"
            results[f"{protein_name}_site_data.csv"] = result
        
        # Update progress
        progress = (i + 1) / len(protein_ids)
        progress_bar.progress(progress)
        
        # Add delay between requests
        await asyncio.sleep(random.uniform(2, 5))
    
    return results

def main():
    # Header
    st.markdown('<h1 class="main-header">🧬 PhosphoSite Site Table Scraper</h1>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("Configuration")
    
    # Mode selection
    mode = st.sidebar.selectbox(
        "Select Scraping Mode",
        ["Single Protein", "Batch Processing"]
    )
    
    if mode == "Single Protein":
        st.header("Single Protein Scraping")
        
        col1, col2 = st.columns(2)
        
        with col1:
            protein_id = st.number_input(
                "Enter Protein ID",
                min_value=1,
                value=583,
                help="Enter the PhosphoSite protein ID you want to scrape"
            )
            
            if st.button("Scrape Protein", type="primary"):
                if protein_id:
                    with st.spinner(f"Scraping protein {protein_id}..."):
                        # Create progress bar
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Run the scraping
                        result = asyncio.run(scrape_single_protein(protein_id, progress_bar, status_text))
                        
                        if result is not None and not result.empty:
                            # Display results
                            st.success(f"Successfully scraped {len(result)} sites for protein {protein_id}")
                            
                            # Show data
                            st.subheader("Scraped Data")
                            st.dataframe(result, use_container_width=True)
                            
                            # Download button
                            st.subheader("Download Data")
                            st.markdown(download_csv(result, f"protein_{protein_id}_site_data.csv"), unsafe_allow_html=True)
                        else:
                            st.error(f"No data found for protein {protein_id}")
        
        with col2:
            st.info("""
            **Instructions:**
            1. Enter a PhosphoSite protein ID
            2. Click "Scrape Protein" to start scraping
            3. Wait for the process to complete
            4. View and download the results
            
            **Note:** The scraping process may take a few minutes depending on the website response time.
            """)
    
    elif mode == "Batch Processing":
        st.header("Batch Protein Scraping")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Input method selection
            input_method = st.radio(
                "Choose input method:",
                ["Range", "List", "Upload CSV"]
            )
            
            protein_ids = []
            
            if input_method == "Range":
                start_id = st.number_input("Start Protein ID", min_value=1, value=580)
                end_id = st.number_input("End Protein ID", min_value=1, value=585)
                protein_ids = list(range(start_id, end_id + 1))
                
            elif input_method == "List":
                protein_list = st.text_area(
                    "Enter protein IDs (one per line or comma-separated)",
                    value="580,581,582,583,584,585",
                    help="Enter protein IDs separated by commas or new lines"
                )
                
                if protein_list:
                    # Parse the input
                    ids = protein_list.replace('\n', ',').split(',')
                    protein_ids = [int(id.strip()) for id in ids if id.strip().isdigit()]
            
            elif input_method == "Upload CSV":
                uploaded_file = st.file_uploader("Upload CSV file with protein IDs", type=['csv'])
                if uploaded_file is not None:
                    try:
                        df = pd.read_csv(uploaded_file)
                        if 'protein_id' in df.columns:
                            protein_ids = df['protein_id'].tolist()
                        elif 'Protein_ID' in df.columns:
                            protein_ids = df['Protein_ID'].tolist()
                        else:
                            st.error("CSV must contain a column named 'protein_id' or 'Protein_ID'")
                    except Exception as e:
                        st.error(f"Error reading CSV file: {str(e)}")
            
            if protein_ids:
                st.write(f"**Proteins to scrape:** {len(protein_ids)} proteins")
                st.write(f"**Protein IDs:** {protein_ids[:10]}{'...' if len(protein_ids) > 10 else ''}")
                
                if st.button("Start Batch Scraping", type="primary"):
                    with st.spinner("Starting batch scraping..."):
                        # Create progress bar
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Run batch scraping
                        results = asyncio.run(scrape_batch_proteins(protein_ids, progress_bar, status_text))
                        
                        if results:
                            st.success(f"Successfully scraped {len(results)} proteins")
                            
                            # Display summary
                            st.subheader("Scraping Summary")
                            summary_data = []
                            for filename, df in results.items():
                                protein_name = filename.replace('_site_data.csv', '')
                                summary_data.append({
                                    'Protein': protein_name,
                                    'Sites Found': len(df),
                                    'Upstream Sites': df['Upstream'].sum() if 'Upstream' in df.columns else 0,
                                    'Downstream Sites': df['Downstream'].sum() if 'Downstream' in df.columns else 0
                                })
                            
                            summary_df = pd.DataFrame(summary_data)
                            st.dataframe(summary_df, use_container_width=True)
                            
                            # Download options
                            st.subheader("Download Results")
                            
                            col_download1, col_download2 = st.columns(2)
                            
                            with col_download1:
                                if len(results) == 1:
                                    # Single file download
                                    filename, df = list(results.items())[0]
                                    st.markdown(download_csv(df, filename), unsafe_allow_html=True)
                                else:
                                    # Zip file download
                                    zip_data = download_zip(results)
                                    st.download_button(
                                        label="Download All Files (ZIP)",
                                        data=zip_data,
                                        file_name=f"phosphosite_batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                                        mime="application/zip"
                                    )
                            
                            with col_download2:
                                # Combined CSV
                                combined_df = pd.concat(results.values(), ignore_index=True)
                                st.markdown(download_csv(combined_df, "combined_site_data.csv"), unsafe_allow_html=True)
                        else:
                            st.error("No data was scraped successfully")
        
        with col2:
            st.info("""
            **Batch Processing Tips:**
            - Use ranges for sequential protein IDs
            - Use lists for specific protein IDs
            - Upload CSV for large datasets
            - Processing time increases with more proteins
            - Results are saved automatically
            """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>PhosphoSite Site Table Scraper | Built with Streamlit</p>
        <p>Data source: <a href='https://www.phosphosite.org' target='_blank'>PhosphoSitePlus</a></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()