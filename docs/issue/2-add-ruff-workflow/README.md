# #2 Add ruff workflow

## 이슈
- GitHub Actions에 ruff 검사가 없다.
- `pyproject.toml`에 의존성 선언이 남아 있다.

## 해결책
- `.github/workflows/ruff.yml`을 추가한다. `ruff check .`와 `ruff format --check .`를 실행한다.
- `pyproject.toml`에 `[tool.ruff]` 설정을 추가한다.
- `pyproject.toml`에서 `dependencies`를 지운다. 의존성은 `requirements.txt`에만 적는다.
- `ruff format`으로 2개 파일의 형식을 맞춘다. `dependencies`와 `[dependency-groups]`를 지우고 테스트 의존성은 `tests/requirements.txt`로 옮긴다.
- 버전을 1.0.1로 올린다.

## 테스트 계획
| 테스트 | 기대 결과 |
|---|---|
| `ruff check .` | `All checks passed!` |
| `ruff format --check .` | 다시 형식을 맞출 파일이 없다 |

## 테스트 결과
### 수정 전
```
All checks passed!
unformatted: File would be reformatted
   --> nodes/danbooru.py:26:1
    |
25  |
    -
26  | # Cache TTL (seconds) for volatile endpoints — popular / related / search,
--------------------------------------------------------------------------------
100 |             return url, {}
    -         return f"https://{CONNECT_HOST}/" + url[len(prefix):], {"Host": DANBOORU_HOST}
101 +         return f"https://{CONNECT_HOST}/" + url[len(prefix) :], {"Host": DANBOORU_HOST}
102 |
--------------------------------------------------------------------------------
119 |         connect_url, headers = cls.route(url)
    -         resp = _get_session().get(connect_url, headers=headers, proxies=cls.get_proxies(), timeout=30)
120 +         resp = _get_session().get(
121 +             connect_url, headers=headers, proxies=cls.get_proxies(), timeout=30
122 +         )
123 |         if not resp.ok:
--------------------------------------------------------------------------------
152 |             pass
    -         elif (match := re.search(r"^(\(+)(.+?)(\)+)$", tag)) or (match := re.search(r"^(\[+)(.+?)(\]+)$", tag)):
153 +         elif (match := re.search(r"^(\(+)(.+?)(\)+)$", tag)) or (
154 +             match := re.search(r"^(\[+)(.+?)(\]+)$", tag)
155 +         ):
156 |             # Example: ((cat)) / [[cat]] -- non-greedy so the closing brackets are not kept
157 |             tag = match.group(2)
158 |         return tag
159 +
160 |     @staticmethod
--------------------------------------------------------------------------------
166 |         tag = tag.strip()
    -         if (match := re.search(rf"^\(({_TAG_BODY}):[0-9.-]+:[0-9.-]+\)$", tag)) or (match := re.search(rf"^\(({_TAG_BODY}):[0-9.-]+\)$", tag)):
167 +         if (match := re.search(rf"^\(({_TAG_BODY}):[0-9.-]+:[0-9.-]+\)$", tag)) or (
168 +             match := re.search(rf"^\(({_TAG_BODY}):[0-9.-]+\)$", tag)
169 +         ):
170 |             tag = match.group(1)
171 |         elif match := re.search(r"^([\(\[]+)(.+?)([\)\]]+)$", tag):
172 |             tag = match.group(2)
173 |         return tag
174 +
175 |     @staticmethod
    |

unformatted: File would be reformatted
  --> nodes/lib/utils.py:55:42
   |
54 |             node = match.group(1)
   -             message = message[match.end():]
55 +             message = message[match.end() :]
56 |         else:
--------------------------------------------------------------------------------
72 |         # INFO/WARNING/ERROR are the levels actually used; 7 fits the longest.
   -         handler.setFormatter(_NodeTagFormatter(
   -             "%(asctime)s | %(levelname)-7s | %(message)s",
   -             datefmt="%Y-%m-%d %H:%M:%S",
   -         ))
73 +         handler.setFormatter(
74 +             _NodeTagFormatter(
75 +                 "%(asctime)s | %(levelname)-7s | %(message)s",
76 +                 datefmt="%Y-%m-%d %H:%M:%S",
77 +             )
78 +         )
79 |         logger.addHandler(handler)
--------------------------------------------------------------------------------
95 |         except Exception:
   -             get_logger().error("unexpected error in '%s'", func.__name__,
   -                                exc_info=True)
96 +             get_logger().error("unexpected error in '%s'", func.__name__, exc_info=True)
97 |             raise
98 |
99 |     return wrapper
   -
   |

2 files would be reformatted, 8 files already formatted
```

### 수정 후
```
All checks passed!
10 files already formatted
```
