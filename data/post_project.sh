curl -X POST "http://127.0.0.1:8000/api/v2/projects?apiKey=valid_api_key_12345" \
     -d "name=テストプロジェクト2" \
     -d "key=TEST_PRJ2" \
     -d "chartEnabled=true" \
     -d "useWiki=true"