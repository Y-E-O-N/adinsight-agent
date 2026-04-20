-- ============================================================================= 
-- 01_extensions.sql                                                                                   
-- ----------------------------------------------------------------------------
-- 목적: Postgres 컨테이너 최초 기동 시 필요한 extension 을 활성화한다.                                
-- 실행 시점: /docker-entrypoint-initdb.d/ 에 마운트되어 최초 1회 자동 실행.     
-- 재실행 안전(idempotent): IF NOT EXISTS 로 이미 있으면 스킵.                                         
-- ============================================================================= 
                                                                                                        
-- 벡터 검색용 (Phase 6 Text2SQL 스키마 임베딩 저장·유사도 검색)
CREATE EXTENSION IF NOT EXISTS vector;                                                                 
                                                                                
-- 문자열 trigram 유사 검색 (fuzzy matching, GIN 인덱스 지원)                                          
CREATE EXTENSION IF NOT EXISTS pg_trgm;               
                                                                                                        
-- 쿼리별 실행 통계 (Phase 5 핫쿼리 분석)                                        
-- 주의: postgresql.conf 의 shared_preload_libraries 에도 등록돼야 함.                                 
--       → docker-compose 의 postgres command 플래그로 이미 처리됨.                                    
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;   