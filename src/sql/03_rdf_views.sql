-- =============================================================================
-- SQL RDF Triples View for CPSV-AP 3.2.0 Export
-- Base URI: http://procedures_administratives_cpsv.ma/id/
-- =============================================================================

DROP VIEW IF EXISTS v_rdf_triples;

CREATE VIEW v_rdf_triples AS

-- 1. PublicService Class Assignment
SELECT 
    'http://procedures_administratives_cpsv.ma/id/public_service/' || ps_uuid AS subject,
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#type' AS predicate,
    'http://purl.org/vocab/cpsv#PublicService' AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM public_services

UNION ALL

-- 2. PublicService Identifier
SELECT 
    'http://procedures_administratives_cpsv.ma/id/public_service/' || ps_uuid AS subject,
    'http://purl.org/dc/terms/identifier' AS predicate,
    ps_uuid AS object,
    1 AS is_literal, 'http://www.w3.org/2001/XMLSchema#string' AS datatype, NULL AS lang
FROM public_services

UNION ALL

-- 3. PublicService Title (dct:title @ar)
SELECT 
    'http://procedures_administratives_cpsv.ma/id/public_service/' || ps_uuid AS subject,
    'http://purl.org/dc/terms/title' AS predicate,
    procedure_name_cleaned AS object,
    1 AS is_literal, NULL AS datatype, 'ar' AS lang
FROM public_services
WHERE procedure_name_cleaned IS NOT NULL AND procedure_name_cleaned != ''

UNION ALL

-- 4. PublicService Description (dct:description @ar)
SELECT 
    'http://procedures_administratives_cpsv.ma/id/public_service/' || ps_uuid AS subject,
    'http://purl.org/dc/terms/description' AS predicate,
    description_cleaned AS object,
    1 AS is_literal, NULL AS datatype, 'ar' AS lang
FROM public_services
WHERE description_cleaned IS NOT NULL AND description_cleaned != ''

UNION ALL

-- 5. PublicService Primary Topic / Web Link (foaf:isPrimaryTopicOf)
SELECT 
    'http://procedures_administratives_cpsv.ma/id/public_service/' || ps_uuid AS subject,
    'http://xmlns.com/foaf/0.1/isPrimaryTopicOf' AS predicate,
    url_source AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM public_services
WHERE url_source IS NOT NULL AND url_source != ''

UNION ALL

-- 6. PublicService Language & Spatial Coverage
SELECT 
    'http://procedures_administratives_cpsv.ma/id/public_service/' || ps_uuid AS subject,
    'http://purl.org/dc/terms/language' AS predicate,
    'http://publications.europa.eu/resource/authority/language/ARA' AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM public_services

UNION ALL

SELECT 
    'http://procedures_administratives_cpsv.ma/id/public_service/' || ps_uuid AS subject,
    'http://purl.org/dc/terms/spatial' AS predicate,
    'http://publications.europa.eu/resource/authority/country/MAR' AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM public_services

UNION ALL

-- 7. PublicService -> Competent Authority (cv:hasCompetentAuthority)
SELECT 
    'http://procedures_administratives_cpsv.ma/id/public_service/' || ps.ps_uuid AS subject,
    'http://data.europa.eu/m8g/hasCompetentAuthority' AS predicate,
    'http://procedures_administratives_cpsv.ma/id/organisation/' || o.org_slug AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM public_services ps
JOIN organisations o ON ps.authority_id = o.org_id

UNION ALL

-- 8. PublicOrganisation Attributes (rdf:type, dct:identifier, skos:prefLabel @ar, dct:spatial)
SELECT 
    'http://procedures_administratives_cpsv.ma/id/organisation/' || org_slug AS subject,
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#type' AS predicate,
    'http://data.europa.eu/m8g/PublicOrganisation' AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM organisations

UNION ALL

SELECT 
    'http://procedures_administratives_cpsv.ma/id/organisation/' || org_slug AS subject,
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#type' AS predicate,
    'http://www.w3.org/ns/org#Organization' AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM organisations

UNION ALL

SELECT 
    'http://procedures_administratives_cpsv.ma/id/organisation/' || org_slug AS subject,
    'http://purl.org/dc/terms/identifier' AS predicate,
    org_slug AS object,
    1 AS is_literal, 'http://www.w3.org/2001/XMLSchema#string' AS datatype, NULL AS lang
FROM organisations

UNION ALL

SELECT 
    'http://procedures_administratives_cpsv.ma/id/organisation/' || org_slug AS subject,
    'http://www.w3.org/2004/02/skos/core#prefLabel' AS predicate,
    org_name AS object,
    1 AS is_literal, NULL AS datatype, 'ar' AS lang
FROM organisations

UNION ALL

SELECT 
    'http://procedures_administratives_cpsv.ma/id/organisation/' || org_slug AS subject,
    'http://purl.org/dc/terms/spatial' AS predicate,
    'http://publications.europa.eu/resource/authority/country/MAR' AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM organisations

UNION ALL

-- 9. PublicService -> Evidence (cpsv:hasInput)
SELECT 
    'http://procedures_administratives_cpsv.ma/id/public_service/' || ps.ps_uuid AS subject,
    'http://purl.org/vocab/cpsv#hasInput' AS predicate,
    'http://procedures_administratives_cpsv.ma/id/evidence/' || e.evidence_slug AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM service_evidences se
JOIN public_services ps ON se.ps_id = ps.ps_id
JOIN evidences e ON se.evidence_id = e.evidence_id

UNION ALL

-- 10. Evidence Attributes (rdf:type, dct:identifier, dct:title @ar, dct:language)
SELECT 
    'http://procedures_administratives_cpsv.ma/id/evidence/' || evidence_slug AS subject,
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#type' AS predicate,
    'http://data.europa.eu/m8g/Evidence' AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM evidences

UNION ALL

SELECT 
    'http://procedures_administratives_cpsv.ma/id/evidence/' || evidence_slug AS subject,
    'http://purl.org/dc/terms/identifier' AS predicate,
    evidence_slug AS object,
    1 AS is_literal, 'http://www.w3.org/2001/XMLSchema#string' AS datatype, NULL AS lang
FROM evidences

UNION ALL

SELECT 
    'http://procedures_administratives_cpsv.ma/id/evidence/' || evidence_slug AS subject,
    'http://purl.org/dc/terms/title' AS predicate,
    evidence_title AS object,
    1 AS is_literal, NULL AS datatype, 'ar' AS lang
FROM evidences

UNION ALL

SELECT 
    'http://procedures_administratives_cpsv.ma/id/evidence/' || evidence_slug AS subject,
    'http://purl.org/dc/terms/language' AS predicate,
    'http://publications.europa.eu/resource/authority/language/ARA' AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM evidences

UNION ALL

-- 11. PublicService -> Output (cpsv:produces)
SELECT 
    'http://procedures_administratives_cpsv.ma/id/public_service/' || ps.ps_uuid AS subject,
    'http://purl.org/vocab/cpsv#produces' AS predicate,
    'http://procedures_administratives_cpsv.ma/id/output/' || out.output_slug AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM public_services ps
JOIN outputs out ON ps.output_id = out.output_id

UNION ALL

-- 12. Output Attributes (rdf:type, dct:identifier, dct:title @ar, dct:language)
SELECT 
    'http://procedures_administratives_cpsv.ma/id/output/' || output_slug AS subject,
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#type' AS predicate,
    'http://data.europa.eu/m8g/Output' AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM outputs

UNION ALL

SELECT 
    'http://procedures_administratives_cpsv.ma/id/output/' || output_slug AS subject,
    'http://purl.org/dc/terms/identifier' AS predicate,
    output_slug AS object,
    1 AS is_literal, 'http://www.w3.org/2001/XMLSchema#string' AS datatype, NULL AS lang
FROM outputs

UNION ALL

SELECT 
    'http://procedures_administratives_cpsv.ma/id/output/' || output_slug AS subject,
    'http://purl.org/dc/terms/title' AS predicate,
    output_title AS object,
    1 AS is_literal, NULL AS datatype, 'ar' AS lang
FROM outputs

UNION ALL

SELECT 
    'http://procedures_administratives_cpsv.ma/id/output/' || output_slug AS subject,
    'http://purl.org/dc/terms/language' AS predicate,
    'http://publications.europa.eu/resource/authority/language/ARA' AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM outputs

UNION ALL

-- 13. PublicService -> Channel (cv:hasChannel)
SELECT 
    'http://procedures_administratives_cpsv.ma/id/public_service/' || ps.ps_uuid AS subject,
    'http://data.europa.eu/m8g/hasChannel' AS predicate,
    'http://procedures_administratives_cpsv.ma/id/channel/' || ch.channel_slug AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM service_channels sc
JOIN public_services ps ON sc.ps_id = ps.ps_id
JOIN channels ch ON sc.channel_id = ch.channel_id

UNION ALL

-- 14. Channel Attributes (rdf:type, dct:identifier, rdfs:label @ar, cv:ownedBy)
SELECT 
    'http://procedures_administratives_cpsv.ma/id/channel/' || channel_slug AS subject,
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#type' AS predicate,
    'http://data.europa.eu/m8g/Channel' AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM channels

UNION ALL

SELECT 
    'http://procedures_administratives_cpsv.ma/id/channel/' || channel_slug AS subject,
    'http://purl.org/dc/terms/identifier' AS predicate,
    channel_slug AS object,
    1 AS is_literal, 'http://www.w3.org/2001/XMLSchema#string' AS datatype, NULL AS lang
FROM channels

UNION ALL

SELECT 
    'http://procedures_administratives_cpsv.ma/id/channel/' || channel_slug AS subject,
    'http://www.w3.org/2000/01/rdf-schema#label' AS predicate,
    channel_name AS object,
    1 AS is_literal, NULL AS datatype, 'ar' AS lang
FROM channels

UNION ALL

SELECT 
    'http://procedures_administratives_cpsv.ma/id/channel/' || ch.channel_slug AS subject,
    'http://data.europa.eu/m8g/ownedBy' AS predicate,
    'http://procedures_administratives_cpsv.ma/id/organisation/' || o.org_slug AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM channels ch
JOIN organisations o ON ch.owned_by_org_id = o.org_id
WHERE ch.owned_by_org_id IS NOT NULL

UNION ALL

-- 15. PublicService -> ProcessingTime (cv:processingTime xsd:duration)
SELECT 
    'http://procedures_administratives_cpsv.ma/id/public_service/' || ps_uuid AS subject,
    'http://data.europa.eu/m8g/processingTime' AS predicate,
    processing_time_iso AS object,
    1 AS is_literal, 'http://www.w3.org/2001/XMLSchema#duration' AS datatype, NULL AS lang
FROM public_services
WHERE processing_time_iso IS NOT NULL AND processing_time_iso != ''

UNION ALL

-- 16. PublicService -> Cost (cv:hasCost)
SELECT 
    'http://procedures_administratives_cpsv.ma/id/public_service/' || ps.ps_uuid AS subject,
    'http://data.europa.eu/m8g/hasCost' AS predicate,
    'http://procedures_administratives_cpsv.ma/id/cost/' || c.cost_slug AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM costs c
JOIN public_services ps ON c.ps_id = ps.ps_id

UNION ALL

-- 17. Cost Attributes (rdf:type, dct:identifier, cv:hasValue, cv:currency, dct:description @ar, cv:isDefinedBy)
SELECT 
    'http://procedures_administratives_cpsv.ma/id/cost/' || cost_slug AS subject,
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#type' AS predicate,
    'http://data.europa.eu/m8g/Cost' AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM costs

UNION ALL

SELECT 
    'http://procedures_administratives_cpsv.ma/id/cost/' || cost_slug AS subject,
    'http://purl.org/dc/terms/identifier' AS predicate,
    cost_slug AS object,
    1 AS is_literal, 'http://www.w3.org/2001/XMLSchema#string' AS datatype, NULL AS lang
FROM costs

UNION ALL

SELECT 
    'http://procedures_administratives_cpsv.ma/id/cost/' || cost_slug AS subject,
    'http://data.europa.eu/m8g/hasValue' AS predicate,
    CAST(cost_value AS TEXT) AS object,
    1 AS is_literal, 'http://www.w3.org/2001/XMLSchema#double' AS datatype, NULL AS lang
FROM costs
WHERE cost_value IS NOT NULL

UNION ALL

SELECT 
    'http://procedures_administratives_cpsv.ma/id/cost/' || cost_slug AS subject,
    'http://data.europa.eu/m8g/currency' AS predicate,
    currency AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM costs
WHERE currency IS NOT NULL AND currency != ''

UNION ALL

SELECT 
    'http://procedures_administratives_cpsv.ma/id/cost/' || cost_slug AS subject,
    'http://purl.org/dc/terms/description' AS predicate,
    description_cleaned AS object,
    1 AS is_literal, NULL AS datatype, 'ar' AS lang
FROM costs
WHERE description_cleaned IS NOT NULL AND description_cleaned != ''

UNION ALL

SELECT 
    'http://procedures_administratives_cpsv.ma/id/cost/' || c.cost_slug AS subject,
    'http://data.europa.eu/m8g/isDefinedBy' AS predicate,
    'http://procedures_administratives_cpsv.ma/id/organisation/' || o.org_slug AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM costs c
JOIN organisations o ON c.defined_by_org_id = o.org_id
WHERE c.defined_by_org_id IS NOT NULL

UNION ALL

-- 18. PublicService -> Sector (cv:sector)
SELECT 
    'http://procedures_administratives_cpsv.ma/id/public_service/' || ps.ps_uuid AS subject,
    'http://data.europa.eu/m8g/sector' AS predicate,
    'http://procedures_administratives_cpsv.ma/id/concept/sector/' || s.sector_slug AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM public_services ps
JOIN sectors s ON ps.sector_id = s.sector_id

UNION ALL

-- 19. Sector Attributes (rdf:type skos:Concept, dct:identifier, skos:prefLabel @ar, skos:broader)
SELECT 
    'http://procedures_administratives_cpsv.ma/id/concept/sector/' || sector_slug AS subject,
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#type' AS predicate,
    'http://www.w3.org/2004/02/skos/core#Concept' AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM sectors

UNION ALL

SELECT 
    'http://procedures_administratives_cpsv.ma/id/concept/sector/' || sector_slug AS subject,
    'http://purl.org/dc/terms/identifier' AS predicate,
    sector_slug AS object,
    1 AS is_literal, 'http://www.w3.org/2001/XMLSchema#string' AS datatype, NULL AS lang
FROM sectors

UNION ALL

SELECT 
    'http://procedures_administratives_cpsv.ma/id/concept/sector/' || sector_slug AS subject,
    'http://www.w3.org/2004/02/skos/core#prefLabel' AS predicate,
    sector_name AS object,
    1 AS is_literal, NULL AS datatype, 'ar' AS lang
FROM sectors

UNION ALL

SELECT 
    'http://procedures_administratives_cpsv.ma/id/concept/sector/' || s.sector_slug AS subject,
    'http://www.w3.org/2004/02/skos/core#broader' AS predicate,
    'http://procedures_administratives_cpsv.ma/id/concept/sector/' || p.sector_slug AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM sectors s
JOIN sectors p ON s.parent_sector_id = p.sector_id
WHERE s.parent_sector_id IS NOT NULL

UNION ALL

-- 20. Sector Collection (rdf:type skos:Collection, rdfs:label @ar, skos:member)
SELECT 
    'http://procedures_administratives_cpsv.ma/id/concept/collection/' || collection_slug AS subject,
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#type' AS predicate,
    'http://www.w3.org/2004/02/skos/core#Collection' AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM collections

UNION ALL

SELECT 
    'http://procedures_administratives_cpsv.ma/id/concept/collection/' || collection_slug AS subject,
    'http://www.w3.org/2000/01/rdf-schema#label' AS predicate,
    collection_name AS object,
    1 AS is_literal, NULL AS datatype, 'ar' AS lang
FROM collections

UNION ALL

SELECT 
    'http://procedures_administratives_cpsv.ma/id/concept/collection/moroccan_sectors' AS subject,
    'http://www.w3.org/2004/02/skos/core#member' AS predicate,
    'http://procedures_administratives_cpsv.ma/id/concept/sector/' || sector_slug AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang
FROM sectors

UNION ALL

-- 21. External Vocabulary Declarations for Closed SHACL Class Validation
SELECT 
    'http://publications.europa.eu/resource/authority/language/ARA' AS subject,
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#type' AS predicate,
    'http://purl.org/dc/terms/LinguisticSystem' AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang

UNION ALL

SELECT 
    'http://publications.europa.eu/resource/authority/country/MAR' AS subject,
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#type' AS predicate,
    'http://purl.org/dc/terms/Location' AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang

UNION ALL

SELECT 
    'http://publications.europa.eu/resource/authority/currency/MAD' AS subject,
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#type' AS predicate,
    'http://www.w3.org/2004/02/skos/core#Concept' AS object,
    0 AS is_literal, NULL AS datatype, NULL AS lang;
