CREATE TABLE IF NOT EXISTS candidates (
  resource_id TEXT PRIMARY KEY,
  package_id TEXT,
  package_name TEXT,
  title TEXT,
  publisher TEXT,
  licence TEXT,
  resource_url TEXT,
  resource_format TEXT,
  shape TEXT,               -- datastore | pxstat | arcgis | wfs | generic_json | unreachable
  last_probed_at TIMESTAMP,
  reachable BOOLEAN,
  row_estimate INTEGER,
  col_estimate INTEGER,
  has_numeric BOOLEAN,
  has_temporal BOOLEAN,
  has_categorical BOOLEAN,
  interestingness_score INTEGER,
  package_notes TEXT,
  package_last_modified TEXT
);

CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY,
  resource_id TEXT,
  started_at TIMESTAMP,
  status TEXT,              -- success | reroll | skipped | failed
  failure_reason TEXT,
  published_report_id TEXT
);

CREATE TABLE IF NOT EXISTS reports (
  report_id TEXT PRIMARY KEY,
  resource_id TEXT,
  slug TEXT UNIQUE,
  headline TEXT,
  teaser TEXT,
  publisher TEXT,
  published_at TIMESTAMP,
  narrative_json TEXT,
  html_path TEXT,
  interestingness_score INTEGER,
  dataset_last_updated TEXT
);
