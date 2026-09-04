import requests  # noqa: I001
import streamlit as st

API = "http://localhost:8000"


st.set_page_config(
    page_title="IdeaOS",
    page_icon="🧠",
    layout="wide",
)


st.title("IdeaOS")
st.caption("An Operating System for Human Knowledge")

st.divider()

st.subheader("Research Document")

uploaded_file = st.file_uploader(
    "Upload a research paper",
    type=["pdf"],
)

if uploaded_file is not None:

    st.success(f"Selected: {uploaded_file.name}")

    if st.button("Analyze Document", type="primary"):

        with st.spinner("IdeaOS is analyzing the document..."):

            try:
                response = requests.post(
                    f"{API}/api/v1/documents/analyze",
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "application/pdf",
                        )
                    },
                    timeout=120,
                )

                if response.status_code != 200:
                    st.error(
                        f"Analysis failed: {response.status_code}"
                    )
                else:
                    result = response.json()

                    st.session_state["analysis"] = result

                    st.success("Document analyzed successfully.")

            except requests.exceptions.ConnectionError:
                st.error(
                    "Could not connect to the IdeaOS backend. "
                    "Make sure FastAPI is running on port 8000."
                )

            except requests.exceptions.Timeout:
                st.error(
                    "The analysis took too long. "
                    "Please try the document again."
                )



if "analysis" in st.session_state:

    analysis = st.session_state["analysis"]

    st.divider()

    st.subheader("Research Intelligence Dashboard")

    graph = analysis.get("graph", {})

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    citations = analysis.get("citations", [])
    claims = analysis.get("claims", graph.get("claims", []))

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Graph Nodes", len(nodes))

    with col2:
        st.metric("Relationships", len(edges))

    with col3:
        st.metric("Citations", len(citations))

    with col4:
        st.metric("Claims", len(claims))

    st.divider()

    st.subheader("Document Overview")

    st.write(
        "IdeaOS has transformed the research document into a "
        "structured knowledge representation containing concepts, "
        "claims, citations, and relationships."
    )

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Academic Structure",
            "Idea Genome",
            "Knowledge Graph",
            "Evidence",
        ]
    )

    with tab1:

        st.subheader("Academic Structure")

        sections = analysis.get("sections", [])

        if sections:

            for section in sections:

                if isinstance(section, dict):

                    title = section.get(
                        "title",
                        "Untitled Section",
                    )

                    st.markdown(f"### {title}")

                    content = section.get(
                        "content",
                        "",
                    )

                    if content:
                        st.write(content)

                else:
                    st.write(section)

        else:
            st.info("No academic structure detected.")

    with tab2:

        st.subheader("Idea Genome")

        concept_nodes = [
            node
            for node in nodes
            if node.get("type") == "concept"
        ]

        concept_nodes = sorted(
            concept_nodes,
            key=lambda node: node.get("size", 0),
            reverse=True,
        )

        for concept in concept_nodes[:20]:

            label = concept.get(
                "label",
                concept.get("id", "Unknown"),
            )

            size = concept.get("size", 0)

            st.write(
                f"**{label}** · importance: {size}"
            )

    with tab3:

        st.subheader("Knowledge Graph")

        relationship_edges = [
            edge
            for edge in edges
            if edge.get("type") == "related_to"
        ]

        st.write(
            f"{len(nodes)} nodes · "
            f"{len(relationship_edges)} concept relationships"
        )

        for edge in relationship_edges[:20]:

            source = next(
                (
                    node.get("label")
                    for node in nodes
                    if node.get("id") == edge.get("source")
                ),
                edge.get("source"),
            )

            target = next(
                (
                    node.get("label")
                    for node in nodes
                    if node.get("id") == edge.get("target")
                ),
                edge.get("target"),
            )

            st.write(
                f"**{source}** → **{target}** "
                f"· strength: {edge.get('weight', 1)}"
            )

    with tab4:

        st.subheader("Evidence")

        relationship_edges = [
            edge
            for edge in edges
            if edge.get("type") == "related_to"
        ]

        for edge in relationship_edges[:10]:

            source = edge.get("source")
            target = edge.get("target")

            source_label = next(
                (
                    node.get("label")
                    for node in nodes
                    if node.get("id") == source
                ),
                source,
            )

            target_label = next(
                (
                    node.get("label")
                    for node in nodes
                    if node.get("id") == target
                ),
                target,
            )

            st.markdown(
                f"### {source_label} → {target_label}"
            )

            st.write(
                f"Relationship strength: "
                f"{edge.get('weight', 1)}"
            )

            claim_ids = edge.get("claim_ids", [])

            supporting_claims = [
                claim
                for claim in claims
                if claim.get("id") in claim_ids
            ]

            if supporting_claims:

                for claim in supporting_claims:

                    st.write(
                        f"• {claim.get('text', '')}"
                    )

                    confidence = claim.get("confidence")

                    if confidence is not None:
                        st.caption(
                            f"Confidence: "
                            f"{round(confidence * 100)}%"
                        )

            else:
                st.caption(
                    "No supporting claims found."
                )