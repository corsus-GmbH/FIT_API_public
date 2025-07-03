-- Schema export from FIT_eeb3795.db
-- Generated on: 2025-07-08
-- Original database before index optimizations

CREATE TABLE geographies (
	geo_id INTEGER NOT NULL, 
	international_code INTEGER NOT NULL, 
	geo_shorthand_2 VARCHAR NOT NULL, 
	geo_shorthand_3 VARCHAR NOT NULL, 
	country_name VARCHAR NOT NULL, 
	PRIMARY KEY (geo_id)
);

CREATE TABLE groups (
	group_id INTEGER NOT NULL, 
	group_name VARCHAR NOT NULL, 
	PRIMARY KEY (group_id)
);

CREATE TABLE impactcategories (
	ic_id INTEGER NOT NULL, 
	ic_name VARCHAR NOT NULL, 
	ic_shorthand VARCHAR NOT NULL, 
	normalization_value FLOAT NOT NULL, 
	normalization_unit VARCHAR NOT NULL, 
	PRIMARY KEY (ic_id)
);

CREATE TABLE impactcategoryweights (
	scheme_id INTEGER NOT NULL, 
	ic_id INTEGER NOT NULL, 
	ic_weight FLOAT NOT NULL, 
	PRIMARY KEY (scheme_id, ic_id), 
	FOREIGN KEY(scheme_id) REFERENCES weightingschemes (scheme_id), 
	FOREIGN KEY(ic_id) REFERENCES impactcategories (ic_id)
);

CREATE TABLE lifecyclestages (
	lc_stage_id INTEGER NOT NULL, 
	lc_stage_shorthand VARCHAR NOT NULL, 
	lc_name VARCHAR NOT NULL, 
	PRIMARY KEY (lc_stage_id)
);

CREATE TABLE metadata (
	item_id VARCHAR NOT NULL, 
	geo_id INTEGER NOT NULL, 
	code_ciqual VARCHAR, 
	name_lci VARCHAR NOT NULL, 
	group_id INTEGER, 
	subgroup_id INTEGER, 
	proxy_flag BOOLEAN NOT NULL, 
	PRIMARY KEY (item_id), 
	FOREIGN KEY(geo_id) REFERENCES geographies (geo_id), 
	FOREIGN KEY(group_id) REFERENCES groups (group_id), 
	FOREIGN KEY(subgroup_id) REFERENCES subgroups (subgroup_id)
);

CREATE TABLE normalizedlciavalues (
	item_id VARCHAR NOT NULL, 
	geo_id INTEGER NOT NULL, 
	ic_id INTEGER NOT NULL, 
	lc_stage_id INTEGER NOT NULL, 
	normalized_lcia_value FLOAT, 
	non_normalized_lcia_value FLOAT, 
	PRIMARY KEY (item_id, geo_id, ic_id, lc_stage_id), 
	FOREIGN KEY(item_id) REFERENCES metadata (item_id), 
	FOREIGN KEY(geo_id) REFERENCES geographies (geo_id), 
	FOREIGN KEY(ic_id) REFERENCES impactcategories (ic_id), 
	FOREIGN KEY(lc_stage_id) REFERENCES lifecyclestages (lc_stage_id)
);

CREATE TABLE singlescores (
	item_id VARCHAR NOT NULL, 
	geo_id INTEGER NOT NULL, 
	scheme_id INTEGER NOT NULL, 
	single_score FLOAT, 
	PRIMARY KEY (item_id, geo_id, scheme_id), 
	FOREIGN KEY(item_id) REFERENCES metadata (item_id), 
	FOREIGN KEY(geo_id) REFERENCES geographies (geo_id), 
	FOREIGN KEY(scheme_id) REFERENCES weightingschemes (scheme_id)
);

CREATE TABLE subgroups (
	subgroup_id INTEGER NOT NULL, 
	subgroup_name VARCHAR NOT NULL, 
	PRIMARY KEY (subgroup_id)
);

CREATE TABLE weightedresults (
	item_id VARCHAR NOT NULL, 
	geo_id INTEGER NOT NULL, 
	ic_id INTEGER NOT NULL, 
	lc_stage_id INTEGER NOT NULL, 
	scheme_id INTEGER NOT NULL, 
	weighted_value FLOAT, 
	PRIMARY KEY (item_id, geo_id, ic_id, lc_stage_id, scheme_id), 
	FOREIGN KEY(item_id) REFERENCES metadata (item_id), 
	FOREIGN KEY(geo_id) REFERENCES geographies (geo_id), 
	FOREIGN KEY(ic_id) REFERENCES impactcategories (ic_id), 
	FOREIGN KEY(lc_stage_id) REFERENCES lifecyclestages (lc_stage_id), 
	FOREIGN KEY(scheme_id) REFERENCES weightingschemes (scheme_id)
);

CREATE TABLE weightingschemes (
	scheme_id INTEGER NOT NULL, 
	name VARCHAR NOT NULL, 
	PRIMARY KEY (scheme_id)
);

-- Indexes
CREATE INDEX idx_geographies_geo_id ON geographies(geo_id);

CREATE INDEX idx_groups_group_id ON groups(group_id);

CREATE INDEX idx_metadata_geo_id ON metadata(geo_id);

CREATE INDEX idx_metadata_group_id ON metadata(group_id);

CREATE INDEX idx_metadata_item_geo ON metadata(item_id, geo_id);

CREATE INDEX idx_metadata_subgroup_id ON metadata(subgroup_id);

CREATE INDEX idx_subgroups_subgroup_id ON subgroups(subgroup_id);

