# Session 04 개념 정리 — Phase 1 디버깅 (2026-04-20)

> 오늘 `make up` 실행 중 만난 버그 3개를 디버깅하며 배운 개념들.

---

## 1. Docker ARG 스코프 규칙

### 무슨 일이 일어났나
```
ARG PYTHON_VERSION=3.11       ← 여기서 선언
FROM apache/airflow:...-python${PYTHON_VERSION}
                               ← 이 경계에서 ARG 소멸!
ARG CONSTRAINTS_URL="...constraints-${PYTHON_VERSION}.txt"
                               ← PYTHON_VERSION이 없어서 베이스 이미지 ENV 사용
                               → constraints-3.11.9.txt (404 에러)
```

### 왜 이런가
Docker는 `FROM` 을 기준으로 빌드 스테이지를 나눈다. ARG는 **선언된 스테이지에서만 유효**하고, 새 스테이지(FROM 이후)에서는 소멸한다.

베이스 이미지 `apache/airflow` 내부에 `ENV PYTHON_VERSION=3.11.9` 가 박혀 있어서, ARG가 없으면 셸이 이 ENV를 대신 사용했다.

### 해결책
FROM 이후에 ARG를 **다시 선언**한다.

```dockerfile
ARG PYTHON_VERSION=3.11           # ① FROM 구문용
FROM apache/airflow:...-python${PYTHON_VERSION}

ARG PYTHON_VERSION=3.11           # ② FROM 이후 스테이지용 재선언
ARG CONSTRAINTS_URL="...constraints-${PYTHON_VERSION}.txt"
```

### 기억할 규칙
> **ARG는 FROM을 넘어가지 못한다. 멀티스테이지면 스테이지마다 재선언.**

---

## 2. pip constraints vs requirements 분업

### 무슨 일이 일어났나
```
requirements.txt:  apache-airflow-providers-postgres==5.10.2
constraints 파일:  apache-airflow-providers-postgres==5.11.2
→ 충돌! ResolutionImpossible
```

### 왜 이런가
Airflow는 공식 `constraints-X.Y.txt` 파일을 제공한다. 이 파일에 Airflow 버전(2.9.3)과 **호환되는 모든 provider 버전이 이미 고정**되어 있다.

requirements.txt에서 다른 버전을 지정하면 두 군데서 동시에 고정하는 셈이라 충돌한다.

### 올바른 분업

| 패키지 종류 | 버전 고정 위치 | 이유 |
|---|---|---|
| `apache-airflow-providers-*` | constraints 파일에 위임 (버전 생략) | Airflow가 호환 버전을 이미 관리 |
| 일반 패키지 (`psycopg2-binary`, `pgvector`) | requirements.txt에 직접 핀 | constraints 파일에 없거나 독립적 |

```
# requirements.txt 올바른 예시
apache-airflow-providers-postgres        # 버전 없음 → constraints가 결정
psycopg2-binary==2.9.9                   # 직접 핀
pgvector==0.3.1                          # constraints와 일치하게 핀
```

---

## 3. 파일 실행 권한 (`chmod +x`)

### 무슨 일이 일어났나
```
/docker-entrypoint-initdb.d/02_databases.sh: bad interpreter: Permission denied
```

### 왜 이런가
파일의 권한(permission)에는 읽기(r)·쓰기(w)·실행(x) 세 가지가 있다.

```
-rw-r--r--  02_databases.sh   ← 실행(x) 권한 없음
-rwxr-xr-x  02_databases.sh   ← 실행 가능
```

Mac에서 파일을 만들면 기본적으로 실행 권한이 없다. `.sh` 파일이어도 실행 권한을 따로 줘야 한다.

### 해결책
```bash
chmod +x infra/postgres/init/02_databases.sh
```

### Git과 실행 권한
`chmod +x` 후 커밋하면 git이 실행 권한을 기록한다.
```
create mode 100755 infra/postgres/init/02_databases.sh
                   ↑ 755 = rwxr-xr-x (실행 가능)
```
`100644` 는 실행 불가, `100755` 는 실행 가능.

---

## 4. Postgres init 스크립트 실행 조건

### 무슨 일이 일어났나
`02_databases.sh`가 한 번 실패한 후, 다시 `make up`을 해도 스크립트가 실행되지 않았다.

```
PostgreSQL Database directory appears to contain a database; Skipping initialization
```

### 왜 이런가
Postgres 공식 이미지는 `/docker-entrypoint-initdb.d/` 스크립트를 **볼륨이 완전히 비어있을 때만** 실행한다. 한 번이라도 기동되면 데이터 디렉토리가 생기고, 이후엔 스크립트를 건너뛴다.

### 해결책 — 볼륨 삭제 후 재기동
```bash
make down
docker volume rm adinsight_postgres_data
make up
```

### 기억할 규칙
> **init 스크립트 수정 후엔 반드시 볼륨을 삭제하고 재기동해야 반영된다.**

---

## 5. Docker 포트 충돌

### 무슨 일이 일어났나
```
Bind for 0.0.0.0:8080 failed: port is already allocated
```

Docker Desktop 자체가 8080 포트를 점유하고 있었다.

### 해결책
`docker-compose.yml`에서 **호스트 포트만** 변경 (컨테이너 내부 포트는 유지):

```yaml
ports:
  - "8081:8080"   # 호스트:컨테이너
```

이후 접속 주소: `http://localhost:8081`

### 포트 매핑 읽는 법
```
"8081:8080"
  ↑     ↑
  호스트  컨테이너 내부
(내 Mac) (도커 안)
```
