import os


BASE_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(BASE_DIR)


def get_db_uri():
    protocol = os.getenv("db_protocol","")
    db_name = os.getenv("db_name","")

    if protocol == 'sqlite':
        # SQLite는 호스트와 사용자 이름, 비밀번호 등을 사용하지 않습니다.
        # 따라서 데이터베이스 URI는 'sqlite:///데이터베이스_파일_경로' 형식입니다.
        return "{}:///{}".format(protocol, os.path.join(ROOT_DIR, db_name))
    else:
        return "{}://{}:{}@{}:{}/{}".format(
            protocol,
            os.getenv("db_user",""),
            os.getenv("db_password",""),
            os.getenv("db_host",""),
            os.getenv("db_port",""),
            db_name,
        )

def get_secret_key():
    secret_key = os.getenv("SECRET_KEY","")

    return secret_key
