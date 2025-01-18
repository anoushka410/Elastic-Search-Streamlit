import streamlit as st
from elasticsearch import Elasticsearch
import json

# Initialize Elasticsearch client
@st.cache_resource
def init_es():
    return Elasticsearch(
        "https://elasticsearch-190712-0.cloudclusters.net:10043",
        http_auth=("elastic", "HmtoTvKY"),
        headers={"Content-Type": "application/json"},
        ca_certs="ca_certificate.pem",
        verify_certs=True
    )

def search_documents(es, query_text, year_from=None, year_to=None, court_type=None, sort_by="_score", index_name="judgements-index"):
    try:
        # Build the query with filters
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query_text,
                                "fields": ["*"]
                            }
                        }
                    ],
                    "filter": []
                }
            },
            "sort": []  # Initialize sorting
        }

        # Add year range filter if provided
        if year_from and year_to:
            query['query']['bool']['filter'].append({
                "range": {
                    "JudgmentMetadata.CaseDetails.JudgmentYear": {
                        "gte": year_from,
                        "lte": year_to
                    }
                }
            })

        # Add court type filter if provided
        if court_type:
            query['query']['bool']['filter'].append({
                "match_phrase": {
                    "JudgmentMetadata.CaseDetails.Court": court_type
                }
            })

        # Add sorting based on user selection
        # if sort_by == "Year (Ascending)":
        #     query["sort"].append({"JudgmentMetadata.CaseDetails.JudgmentYear": {"order": "asc"}})
        # elif sort_by == "Year (Descending)":
        #     query["sort"].append({"JudgmentMetadata.CaseDetails.JudgmentYear": {"order": "desc"}})
        # else:
        #     # Default sorting by relevance
        #     query["sort"].append({"_score": {"order": "desc"}})

        response = es.search(
            index=index_name,
            body=query,
            size=10
        )
        
        return response['hits']
    except Exception as e:
        st.error(f"Error during search: {e}")
        return None

if __name__ == "__main__":

    st.title("Legal Case Search")
    
    # Initialize Elasticsearch
    es = init_es()
    
    # Search input and filters
    query = st.text_input("Enter your search query:", placeholder="Type to search cases...")
    
    # Add filters in columns
    col1, col2, col3 = st.columns(3)
    with col1:
        year_from = st.selectbox("From Year", options=[None] + list(range(1940, 2024)))
    with col2:
        year_to = st.selectbox("To Year", options=[None] + list(range(1940, 2024)))
    with col3:
        court_type = st.selectbox("Court Type", options=[None, "High Court", "Supreme Court"])

    # Add sorting dropdown
    # sort_options = {
    #     "Relevance": "_score",
    #     "Year (Ascending)": "JudgmentMetadata.CaseDetails.JudgmentYear",
    #     "Year (Descending)": "JudgmentMetadata.CaseDetails.JudgmentYear:desc"
    # }
    # sort_by = st.selectbox("Sort by", options=list(sort_options.keys()))

    if query:
        hits = search_documents(es, query, year_from, year_to, court_type)
        
        if hits and hits['total']['value'] > 0:
            st.write(f"Found {hits['total']['value']} matches")
            
            # Display results
            for hit in hits['hits']:
                source = hit['_source']
                metadata = source.get('JudgmentMetadata', {})
                case_details = metadata.get('CaseDetails', {})
                
                with st.expander(f"📄 {case_details.get('CaseTitle', 'Untitled Case')} (Score: {hit['_score']:.2f})"):
                    # Display basic information
                    st.write(f"**Name of Judgement:** {case_details.get('CaseTitle', 'N/A')}")
                    st.write(f"**Short Description:** {metadata.get('Summary', 'No description available')}")
                    
                    # Display keywords
                    keywords = metadata.get('Keywords', [])
                    if keywords:
                        st.write("**Keywords:** " + ", ".join(keywords))
                    else:
                        st.write("**Keywords:** N/A")
                    
                    # Create columns for details and actions
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write("**Case Details:**")
                        st.write(f"Document ID: {hit['_id']}")
                        # if 'year' in source:
                        st.write(f"Year: {case_details['JudgmentYear']}")
                        # if 'court' in source:
                        st.write(f"Court: {case_details['Court']}")
                    
                    with col2:
                        st.write("**Actions:**")
                        # Add buttons for detailed summary and PDF
                        if st.button("📄 Detailed Summary", key=f"summary_{hit['_id']}"):
                            st.session_state[f"show_summary_{hit['_id']}"] = True
                        
                        if st.button("📑 View PDF", key=f"pdf_{hit['_id']}"):
                            st.session_state[f"show_pdf_{hit['_id']}"] = True
                    
                    # Handle popups for summary and PDF
                    if st.session_state.get(f"show_summary_{hit['_id']}", False):
                        st.subheader("Detailed Summary")
                        # st.write(metadata.get('FullSummary', 'No detailed summary available'))
                        st.write(source.get('JudgmentSummary', 'No detailed summary available')['JudgmentName'])
                        if st.button("Close", key=f"close_summary_{hit['_id']}"):
                            st.session_state[f"show_summary_{hit['_id']}"] = False
                    
                    if st.session_state.get(f"show_pdf_{hit['_id']}", False):
                        st.warning("No PDF available for this case")
                        # with st.popup("PDF Viewer"):
                        #     pdf_url = metadata.get('PDFUrl')
                        #     if pdf_url:
                        #         st.write(f"PDF URL: {pdf_url}")
                        #         # You can use an iframe or other method to display the PDF
                        #     else:
                        #         st.warning("No PDF available for this case")
                        #     if st.button("Close", key=f"close_pdf_{hit['_id']}"):
                        #         st.session_state[f"show_pdf_{hit['_id']}"] = False
        
        else:
            st.info("No results found.")
