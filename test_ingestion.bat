@echo off
REM Quick test script for ingestion pipeline (Windows)
REM Usage: test_ingestion.bat

echo ==========================================
echo Testing Ingestion Pipeline
echo ==========================================
echo.

echo 1. Running quick test (no API required)...
python -m ingestion.quick_test

echo.
echo 2. Running component tests...
python -m ingestion.test_pipeline --test html_parser
python -m ingestion.test_pipeline --test cleaner
python -m ingestion.test_pipeline --test chunker
python -m ingestion.test_pipeline --test embedder
python -m ingestion.test_pipeline --test vector_store

echo.
echo 3. Testing with mock data...
python -m ingestion.test_pipeline --test mock

echo.
echo ==========================================
echo If you have Discourse API credentials set:
echo   python -m ingestion.test_pipeline --test fetch
echo   python -m ingestion.test_pipeline --test pipeline
echo ==========================================
pause

