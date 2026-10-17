# #8 Support Danbooru login and skip posts without a file in the downloader

이슈: https://github.com/alchemine/comfyui-danbooru-pack/issues/8

### 이슈
1. Danbooru 계정으로 요청할 방법이 없다.
   * ASIS: 모든 요청이 익명이라 태그를 2개까지만 검색할 수 있다.
   * TOBE: `.env`의 `DANBOORU_LOGIN`, `DANBOORU_API_KEY`로 계정 한도(Gold는 6개)가 적용된다.
2. `DanbooruPostsDownloader`가 요청한 `n`장보다 적게 받는다.
   * ASIS: 차단·삭제된 포스트를 건너뛰기만 해서 결과가 모자란다.
   * TOBE: 다음 결과로 채워 `n`장을 받는다.
3. 같은 포스트를 다시 받는다.
   * ASIS: 파일 이름이 실행 순번(`p_1.jpg`)이라 다시 실행하면 같은 포스트가 새 파일로 또 저장된다.
   * TOBE: `<prefix>_<post id>`(`p_42.jpg`)로 저장하고 이미 있으면 받지 않는다.

### 원인 분석
1. API 요청에 인증 정보를 붙이는 경로가 없다.
2. `request`가 `ceil(n / 20)`쪽만 받고, `file_url`이 없는 포스트는 그 뒤에 버려진다.
3. 파일 이름이 포스트와 상관없는 순번이라, 이미 받은 포스트를 알아볼 수 없다.

### 솔루션
1. 계정 정보를 넣으면 모든 API 요청이 그 계정으로 간다.
   - `BaseDanbooru.get_auth`가 두 환경 변수를 읽어 HTTP Basic 인증으로 `_get_json`에 넘긴다. 하나라도 비면 익명.
   - `.env.example`, README 두 파일에 설정을 적는다.
2. 받을 수 없는 포스트는 빼고 `n`장이 모일 때까지 다음 쪽을 받는다.
   - `file_url`이 있는 포스트만 모으고, 빈 쪽이 오면 멈춘다.
3. 파일 이름을 포스트 id로 정해, 같은 포스트는 한 번만 받는다.
   - 파일이 이미 있으면 다운로드 없이 경로만 돌려준다.
4. 기능 추가이므로 version을 1.1.0으로 올린다.

### 테스트
테스트: [`tests/issue/8-support-danbooru-login-and-skip-posts-without-a-file-in-the-downloader/test_login_and_downloader.py`](../../../tests/issue/8-support-danbooru-login-and-skip-posts-without-a-file-in-the-downloader/test_login_and_downloader.py)

| 검증 내용 | 개선점 | Before | After |
|---|---|---|---|
| 로그인과 키가 있으면 인증 정보를 만든다 | 계정 한도가 적용된다 | 실패: 기능 없음 | 통과 |
| 키가 없으면 익명으로 요청한다 | 설정 안 한 사용자는 그대로 | 실패: 기능 없음 | 통과 |
| 파일 없는 포스트를 다음 쪽 결과로 채운다 | `n`장을 받는다 | 실패: 1쪽만 받음 | 통과 |
| 검색 결과가 끝나면 멈춘다 | 무한 요청이 없다 | 실패: 파일 없는 포스트를 돌려줌 | 통과 |
| 포스트 id로 저장하고 두 번째는 받지 않는다 | 중복 다운로드가 없다 | 실패: `p_1.png` | 통과 |

이슈 테스트 5개 중 0개(0%) → 5개(100%) 통과. Danbooru 응답을 흉내 내는 오프라인 테스트라 요청을 보내지 않는다. `tests/test_danbooru_live.py`의 실서버 테스트는 실행하지 않았다.

실행 방법:

```bash
.venv/bin/python -m pytest -c tests/pytest.ini tests/issue
```

### References
- https://github.com/alchemine/comfyui-danbooru-pack/issues/8
