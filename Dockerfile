FROM python:3.8-buster as builder

WORKDIR /app

COPY psi /app/psi
COPY setup.py /app/setup.py

RUN pip wheel -w whls . -i https://mirrors.ustc.edu.cn/pypi/web/simple

FROM python:3.8-slim-buster

WORKDIR /app

COPY --from=builder /app/whls /app/whls

RUN pip install --no-cache-dir whls/*.whl &&  rm -rf whls

ENTRYPOINT [ "psi_run" ]