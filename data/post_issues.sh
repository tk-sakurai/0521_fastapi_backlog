curl -X POST "http://127.0.0.1:8000/api/v2/issues?apiKey=valid_api_key_12345" \
     -d "projectId=3" \
     -d "summary=ログイン画面のバグ修正" \
     -d "issueTypeId=1" \
     -d "priorityId=3" \
     -d "description=ボタンを押しても反応しない不具合を修正する。" \
     -d "dueDate=2026-06-15"