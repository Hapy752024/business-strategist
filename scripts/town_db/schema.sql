-- Italy town key-data store, v1.
-- One row per town. Every fact field carries its own source + checked_date.
-- Key fields (buy price, tax7) carry a second-source confirmation flag:
-- confirmed = 1 only when an independent --confirm-url was recorded.

CREATE TABLE IF NOT EXISTS towns (
  -- identity (static)
  slug            TEXT PRIMARY KEY,
  name            TEXT NOT NULL,
  province        TEXT NOT NULL,
  region          TEXT NOT NULL,
  pattern         TEXT NOT NULL,

  -- population (ISTAT)
  population               INTEGER,
  population_ref_date      TEXT,
  population_source_label  TEXT,
  population_source_url    TEXT,
  population_checked_date  TEXT,

  -- purchase cost (OMI or dated secondary)
  buy_eur_m2_low      REAL,
  buy_eur_m2_high     REAL,
  buy_semester        TEXT,
  buy_source_label    TEXT,
  buy_source_url      TEXT,
  buy_confirm_url     TEXT,
  buy_confirmed       INTEGER NOT NULL DEFAULT 0,  -- 1 = second independent source recorded
  buy_checked_date    TEXT,

  -- rent (manual, dated)
  rent_1bed_eur        REAL,
  rent_source_label    TEXT,
  rent_source_url      TEXT,
  rent_checked_date    TEXT,

  -- 7% flat-tax regime (art. 24-ter TUIR)
  tax7_status        TEXT NOT NULL DEFAULT 'unverified'
                     CHECK (tax7_status IN ('eligible', 'not_eligible', 'unverified')),
  tax7_source_label  TEXT,
  tax7_source_url    TEXT,
  tax7_confirm_url   TEXT,
  tax7_confirmed     INTEGER NOT NULL DEFAULT 0,
  tax7_checked_date  TEXT,

  -- healthcare access (manual, dated)
  hospital_name         TEXT,
  hospital_town         TEXT,
  hospital_drive_min    INTEGER,
  hospital_source_label TEXT,
  hospital_checked_date TEXT,

  -- airport access (manual, dated)
  airport              TEXT,
  airport_drive_min    INTEGER,
  airport_source_label TEXT,
  airport_checked_date TEXT,

  -- character (manual, dated)
  expat_presence     TEXT CHECK (expat_presence IN ('low', 'medium', 'high') OR expat_presence IS NULL),
  expat_source_label TEXT,
  expat_checked_date TEXT,
  climate_note       TEXT,
  fit_note           TEXT,

  -- meta (script-maintained)
  last_verified TEXT,
  stale         INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_towns_pattern ON towns(pattern);
CREATE INDEX IF NOT EXISTS idx_towns_tax7 ON towns(tax7_status);
CREATE INDEX IF NOT EXISTS idx_towns_stale ON towns(stale);

-- Write-ahead audit log: every upsert appends one row per field written.
CREATE TABLE IF NOT EXISTS write_log (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  slug         TEXT NOT NULL,
  field        TEXT NOT NULL,
  old_value    TEXT,
  new_value    TEXT,
  source_label TEXT,
  source_url   TEXT,
  confirm_url  TEXT,
  written_at   TEXT NOT NULL,
  session_id   TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_write_log_session ON write_log(session_id);
