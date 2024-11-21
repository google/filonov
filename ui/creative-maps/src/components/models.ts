/**
 * Asset node.
 */
export interface Node {
  /**
   * Asset id (in Google Ads).
   */
  name: string;
  /**
   * Internal unique node identifier.
   */
  id: number;
  /**
   * Description label for node: title for YouTube videos, asset_name for images.
   */
  label: string;
  /**
   * cluster id.
   */
  cluster: string;
  /**
   * Url to preview image.
   */
  image: string;
  /**
   * Url to creative: for videos - youtube.com/watch, for images the same as image.
   */
  media_path: string;
  //color?: string;
  size?: number;
  /**
   * Additional metrics (from Ads or other sources) of the current asset.
   * Examples: cost, impressions, clicks, duration
   */
  info?: Record<string, string | number | boolean | undefined>;
  /**
   * Same metrics as in `info` but segmented by day (time series).
   */
  series?: Array<Record<string, string | number | boolean | undefined>>;
  /**
   * Current asset' tags.
   */
  tags?: Array<{ tag: string; score: number }>;
}

/**
 * Edge between two nodes.
 */
export interface Edge {
  /**
   * Source node's id.
   */
  from: number;
  /**
   * Target node's id.
   */
  to: number;
  /**
   * Similarity score of the connected nodes.
   */
  similarity: number;
}

/**
 * A graph of nodes connected by similarity.
 */
export interface GraphData {
  /**
   * Nodes
   */
  nodes: Node[];
  /**
   * Edges
   */
  edges: Edge[];
}

/**
 * Currently selected cluster of nodes.
 */
export interface ClusterInfo {
  nodeCount: number;
  metrics: Record<string, string | number | boolean | undefined>;
  nodes: Node[];
}

/**
 * A tag description.
 */
export interface TagStats {
  tag: string;
  freq: number;
  nodes: Node[];
}
