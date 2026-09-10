# File contracts (column names are fixed; skills must write exactly these)

Key: `apt_id` = the first Collin CAD `propid` of the community (stable across runs).

## 1-apartments.csv
apt_id, name, address, city, zip, units, year_built, owner, parcels, cad_prop_ids (";"-joined), cad_use_code

## 2-websites.csv
apt_id, website, website_source (search | cad | manual), confidence (high | medium | low | none), query, notes

## 3-software.csv
apt_id, software (RealPage | Yardi | Entrata | AppFolio | Buildium | ResMan | Yotta | MRI/RentManager | in-house:<name> | unknown),
signal (portal | hop-portal | asset | none), proof_url, checked_at (ISO date), unknown_reason (no-website | blocked | in-house-portal | no-portal-link | error | "")

## master.csv
all columns of 1 + website, website_confidence, software, signal, proof_url, checked_at, unknown_reason

## 5-sales.csv
apt_id, name, sale_date, deed_type, new_owner, previous_owner, units, source (e.g. "Collin CAD 2026 vs 2025"), source_url

## 6-upcoming.csv
project_id (slug), project, address, city, units, developer, stage (zoning-filed | zoning-approved | site-plan-approved | permit | under-construction | leasing),
stage_date, expected_open, source_type (legistar | tabs | news | city), source_url, first_seen (ISO date)

## leads.csv
rank, score (0–100), score_size, score_timing, score_signal, score_open, signal (sold | upcoming), ref_id (apt_id or project_id),
name, city, units, software (or "not chosen yet"), why (one sentence, agent-written, facts only from sources), sources (";"-joined URLs)

## runs/<timestamp>-<skill>.json
skill, area, started, finished, duration_s, status, inputs, outputs, counts{}, api_calls{}, errors[], notes[]
