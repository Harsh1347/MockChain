import streamlit as st
import json
from pyvis.network import Network
from streamlit_autorefresh import st_autorefresh

LOG_FILE = "app.log"  # Your actual log file path

def render_graph(column):
    graph_placeholder = column.empty()
    seen_edges = set()
    nodes = {}
    edges = []

    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        column.warning("Log file not found.")
        return

    for line in lines:
        if "- INFO -" not in line:
            continue

        try:
            _, _, json_part = line.partition("- INFO -")
            entry = json.loads(json_part.strip().replace("'", '"'))

            from_agents = entry.get("From", [])
            to_agent = entry.get("To")
            desc = entry.get("Desc", "")

            for source in from_agents:
                if source not in nodes:
                    nodes[source] = {"label": source}
                if to_agent not in nodes:
                    nodes[to_agent] = {"label": to_agent}

                edge_key = (source, to_agent, desc)
                if edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    edges.append((source, to_agent, {"label": desc}))

        except Exception as e:
            #column.warning(f"Log parsing failed: {e}")
            continue

    # Determine the latest edge for highlight
    latest_edge = edges[-1] if edges else None
    highlight_nodes = set()
    if latest_edge:
        highlight_nodes.add(latest_edge[0])
        highlight_nodes.add(latest_edge[1])

    # Create the Pyvis network
    net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black", notebook=True)

    # Add nodes (default grey, latest ones colored)
    for node, data in nodes.items():
        if node in highlight_nodes:
            net.add_node(node, label=data["label"], color="#EF4444")  # Red
        else:
            net.add_node(node, label=data["label"], color="#D1D5DB")  # Grey

    # Add edges (highlight latest)
    for edge in edges:
        if edge == latest_edge:
            net.add_edge(edge[0], edge[1], label='', color="red", width=4, arrows="to")
        else:
            net.add_edge(edge[0], edge[1], label='', arrows="to")

    # Render
    with graph_placeholder:
        net.show("temp_graph.html")
        st.components.v1.html(open("temp_graph.html", "r").read(), height=600, width=800)
    with open("temp_graph.html", "r", encoding="utf-8") as file:
        html_content = file.read()

    # Inject custom body style to remove padding/margin and overflow
    html_content = html_content.replace(
        "<body>",
        '<body style="margin:0;padding:0;overflow:hidden;background:#ffffff;">'
    )

    # Inject extra custom style (optional) to fully control spacing
    custom_style = """
    <style>
        html, body {
            margin: 0 !important;
            padding: 0 !important;
            height: 100% !important;
            overflow: hidden;
        }
    </style>
    """
    html_content = html_content.replace("</head>", f"{custom_style}</head>")

# Auto-refresh
st_autorefresh(interval=2000, key="graph_refresh")

# Layout
col1, col2,col3 = st.columns([1,6,10 ])
with col1:
  
    pass

with col2:
    st.markdown("## 🧠 Live Agent Graph")
    render_graph(col2)
