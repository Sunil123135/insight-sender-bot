BEGIN;
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.

INFO  [alembic.runtime.migration] Generating static SQL
INFO  [alembic.runtime.migration] Will assume transactional DDL.
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

INFO  [alembic.runtime.migration] Running upgrade  -> 20260510_0001, Module: alembic/versions/20260510_0001_initial_schema.py
Purpose: Initial ScrapeSignal schema migration
Author: ScrapeSignal Team
Created: 2026-05-10
-- Running upgrade  -> 20260510_0001

CREATE TABLE articles (
    id SERIAL NOT NULL, 
    source_key VARCHAR(100) NOT NULL, 
    source_name VARCHAR(200) NOT NULL, 
    title VARCHAR(500) NOT NULL, 
    url VARCHAR(2048) NOT NULL, 
    canonical_url VARCHAR(2048), 
    body TEXT NOT NULL, 
    summary TEXT, 
    image_url VARCHAR(2048), 
    author VARCHAR(300), 
    published_at TIMESTAMP WITH TIME ZONE, 
    scraped_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    relevance_score FLOAT NOT NULL, 
    content_hash VARCHAR(64) NOT NULL, 
    email_sent_date TIMESTAMP WITH TIME ZONE, 
    raw_metadata JSONB NOT NULL, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_articles_url ON articles (url);

CREATE UNIQUE INDEX ix_articles_content_hash ON articles (content_hash);

CREATE INDEX ix_articles_relevance_score ON articles (relevance_score);

CREATE INDEX ix_articles_email_sent_date ON articles (email_sent_date);

CREATE INDEX idx_articles_score_sent ON articles (relevance_score, email_sent_date);

CREATE INDEX idx_articles_source_published ON articles (source_key, published_at);

CREATE TABLE source_configs (
    id SERIAL NOT NULL, 
    source_key VARCHAR(100) NOT NULL, 
    name VARCHAR(200) NOT NULL, 
    url VARCHAR(2048) NOT NULL, 
    scraper_type VARCHAR(50) NOT NULL, 
    enabled BOOLEAN NOT NULL, 
    priority INTEGER NOT NULL, 
    max_articles INTEGER NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_source_configs_source_key ON source_configs (source_key);

CREATE INDEX ix_source_configs_enabled ON source_configs (enabled);

CREATE TABLE keywords_master (
    id SERIAL NOT NULL, 
    keyword VARCHAR(200) NOT NULL, 
    tier INTEGER NOT NULL, 
    weight FLOAT NOT NULL, 
    category VARCHAR(100) NOT NULL, 
    enabled BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_keyword_tier UNIQUE (keyword, tier)
);

CREATE INDEX ix_keywords_master_keyword ON keywords_master (keyword);

CREATE INDEX ix_keywords_master_tier ON keywords_master (tier);

CREATE INDEX ix_keywords_master_category ON keywords_master (category);

CREATE TABLE dedup_hashes (
    id SERIAL NOT NULL, 
    content_hash VARCHAR(64) NOT NULL, 
    article_id INTEGER, 
    first_seen_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(article_id) REFERENCES articles (id)
);

CREATE UNIQUE INDEX ix_dedup_hashes_content_hash ON dedup_hashes (content_hash);

CREATE INDEX ix_dedup_hashes_expires_at ON dedup_hashes (expires_at);

CREATE TABLE scrape_logs (
    id SERIAL NOT NULL, 
    run_id VARCHAR(100) NOT NULL, 
    source_config_id INTEGER, 
    status VARCHAR(50) NOT NULL, 
    articles_found INTEGER NOT NULL, 
    articles_saved INTEGER NOT NULL, 
    error_message TEXT, 
    started_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    completed_at TIMESTAMP WITH TIME ZONE, 
    duration_seconds FLOAT, 
    PRIMARY KEY (id), 
    FOREIGN KEY(source_config_id) REFERENCES source_configs (id)
);

CREATE INDEX ix_scrape_logs_run_id ON scrape_logs (run_id);

CREATE INDEX ix_scrape_logs_status ON scrape_logs (status);

CREATE INDEX idx_scrape_logs_run_status ON scrape_logs (run_id, status);

CREATE TABLE email_logs (
    id SERIAL NOT NULL, 
    run_id VARCHAR(100) NOT NULL, 
    recipient_email VARCHAR(320) NOT NULL, 
    subject VARCHAR(500) NOT NULL, 
    article_count INTEGER NOT NULL, 
    status VARCHAR(50) NOT NULL, 
    sendgrid_message_id VARCHAR(200), 
    error_message TEXT, 
    sent_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_email_logs_run_id ON email_logs (run_id);

CREATE INDEX ix_email_logs_recipient_email ON email_logs (recipient_email);

CREATE INDEX ix_email_logs_status ON email_logs (status);

CREATE INDEX ix_email_logs_sent_at ON email_logs (sent_at);

INSERT INTO alembic_version (version_num) VALUES ('20260510_0001') RETURNING alembic_version.version_num;

COMMIT;

