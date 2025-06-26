### 2025-06-26

- Choosing a clustering method on graph load
- Added Similarity distribution histogram

### 2025-06-25

- Creative count in the side-menu turned into a link which opens a dialog with a list of creatives in the current context and export to json and csv (inc. asset media links)

### 2025-05-15

- Dark theme introduced (can be toggled in main header)

### 2025-05-05

- TagsDashboard: tag cards, finding common nodes for selected tags, navigating back to the graph

### 2025-05-02

- TagsDashboard: trends detection
- Display graph's period (if present in graph data file)
- Tags: added calculating of average score, tags are shown on the Tags tab sorted by avg.score

### 2025-04-30

- Reworked node positioning and layouting: introduced ForceLayoutManager to encapsulate working with D3 simulation and layouting

### 2025-03-20

- three modes of displaying metric in any context: "distribution" (histograms as before), "pareto" (accumulated histograms of percentiles) and "top performers" (searching top performing creatives)

### 2025-03-10

- Open files from Google Drive (via Picker API), open from GCS links (gs://)
- Manual node selection: clicking on nodes holding Ctrl/Cmd adds them to current selection

### 2025-03-03

- Show metric totals for each columns in table comparison interfaces (creatives, clusters, tags)

### 2025-02-21

- Optimized graph loading: 1. remove excessive edges (by default); 2. ability to filter edges by similarity threshold (advanced optional feature); 3. sorting clusters by a metric (cost)

### 2025-02-03

- breadcrumbs with selection context
- 'Compare Nodes' now compares currently selected nodes in the context
- Added filtering in Tags tab
- Additional computed metrics for nodes (cr, cpa, roas, cpm)

### 2025-01

- search creatives by name
- added ZoomIn and ZoomOut commands, and extended zoom range
- Using logarithmic scale for histograms
- NodeComparison: displaying creative previews and open full-size images/video player in dialog on click
- select nodes by clicking on bars in 'cluster size' distribution histogram
- ability to select a field to use as node size
- display built time and git hash at the bottom
- Show only top 5 tags in node's tooltip, sort all tags in nodes by score
- added 'Re-layout graph' command in the main toolbar
- Displaying metrics in the global context (when no nodes or clusters selected)
- Presentation of string metrics (on the 'Metrics' tab in the main right-side menu)
