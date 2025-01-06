import streamlit as st
from elasticsearch import Elasticsearch
import json
import os


# Access Environment Variables from Streamlit Cloud
username = os.getenv("ES_USERNAME")
password = os.getenv("ES_PASSWORD")
connection_url = os.getenv("ES_URL")

ca_cert = os.getenv("CERTIFICATE")
# Write the certificate to a temporary file
with open("ca_certificate.pem", "w") as cert_file:
    cert_file.write(ca_cert)

# Initialize Elasticsearch client
@st.cache_resource
def init_es():
    return Elasticsearch(
        connection_url,
        http_auth=(username, password),
        ca_certs="ca_certificate.pem",
        verify_certs=True
    )

def search_documents(es, query_text, index_name="judgements-index"):
    try:
        query = {
            "query": {
                "multi_match": {
                    "query": query_text,
                    "fields": ["*"]
                }
            }
        }

        response = es.search(
            index=index_name,
            body=query,
            size=10  # Increased to show more results
        )
        
        return response['hits']
    except Exception as e:
        st.error(f"Error during search: {e}")
        return None

if __name__ == "__main__":

    st.title("Legal Case Search")
    
    # Initialize Elasticsearch
    es = init_es()
    
    # Search input
    query = st.text_input("Enter your search query:", placeholder="Type to search cases...")
    
    if query:
        hits = search_documents(es, query)
        
        if hits and hits['total']['value'] > 0:
            st.write(f"Found {hits['total']['value']} matches")
            
            # Display results
            for hit in hits['hits']:
                with st.expander(f"📄 {hit['_source'].get('Case Title', 'Untitled Case')} (Score: {hit['_score']:.2f})"):
                    # Create two columns for better organization
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Case Details:**")
                        st.write(f"Document ID: {hit['_id']}")
                        if 'year' in hit['_source']:
                            st.write(f"Year: {hit['_source']['year']}")
                        if 'court' in hit['_source']:
                            st.write(f"Court: {hit['_source']['court']}")
                    
                    with col2:
                        st.write("**Full Document:**")
                        # Show all fields in a formatted way
                        st.json(hit['_source'])
        
        else:
            st.info("No results found.")

