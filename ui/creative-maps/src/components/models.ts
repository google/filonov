/*
 Copyright 2024 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 */

/**
 * A metric value.
 */
export type MetricValue = string | number | boolean;

/**
 * Metrics for assets and clusters.
 */
export type MetricsObject = Record<string, MetricValue | undefined>;

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
  color?: string;
  size: number;
  /**
   * Additional metrics (from Ads or other sources) of the current asset.
   * Examples: cost, impressions, clicks, duration
   */
  info?: MetricsObject;
  /**
   * Same metrics as in `info` but segmented by day (time series).
   */
  series?: MetricsObject[];
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
  /**
   * Edge width.
   */
  width?: number;
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
  id: string;
  description?: string;
  metrics: MetricsObject;
  nodes: Node[];
}

/**
 * A tag description.
 */
export interface TagStats {
  tag: string;
  freq: number;
  avgScore: number;
  nodes: Node[];
}

/**
 * An abstract node (not necessary an asset node)
 * with id and info object with metric values.
 */
export interface AbstractNode {
  id: number | string;
  info?: MetricsObject;
}

/**
 * Model for histograms.
 */
export interface HistogramData {
  x0: number | string;
  x1?: number;
  count: number;
  nodes: AbstractNode[];
}

export interface ParetoHistogramData {
  nodePercentage: number; // % of total nodes included up to this bucket
  valuePercentage: number; // % of total value contributed by nodes up to this bucket
  bucketValue: number; // Sum of values in this bucket
  accumulatedValue: number; // Accumulated sum of values up to and including this bucket
  nodes: AbstractNode[]; // Array of nodes in this bucket
  label: string; // Label for the bucket (e.g., "Top 20%")
}
