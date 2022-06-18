        docker.server.config.yaml 
        log:
          level: "INFO"

        host: "0.0.0.0"
        port: 10000
        data: "server_data.txt"
        result: "server_result.txt"


        docker.client.config.yaml 
        log:
          level: "INFO"

        host: "0.0.0.0"
        port: 10000
        data: "client_data.txt"
        result: "client_result.txt"


        安装包：
        psi.tar

        安装步骤：
        1、解压缩tar xvf psi.tar -C dockerpsi
        2、cd dockerpsi/psi/python-psi
        3、修改psi\pair\socket\pair.py
            def recv(self) -> bytes:
                length = bytes_to_int(self._recv(4))
                data = self._recv(length)
                return data

            def _recv(self, count: int) -> bytes:
                buffer = bytearray(count)
                view = memoryview(buffer)

                while count > 0:
                    n = self._sock.recv_into(view, count)
                    view = view[n:]
                    count -= n

                return bytes(buffer)

        4、修改Dockerfile文件：
        FROM python:3.8-buster as builder

        WORKDIR /app

        COPY psi /app/psi
        COPY setup.py /app/setup.py

        RUN pip wheel -w whls . -i https://pypi.tuna.tsinghua.edu.cn/simple

        FROM python:3.8-slim-buster

        WORKDIR /app

        COPY --from=builder /app/whls /app/whls

        RUN pip install --no-cache-dir whls/*.whl &&  rm -rf whls

        ENTRYPOINT [ "psi_run" ]
        5、docker build -f Dockerfile -t delta_psi:1.0.0 .
        生成镜像文件suning_psi:1.0.0
        6、docker save -o delta_psi.tar  delta_psi:1.0.0
        镜像保存到：delta_psi.tar
        并同步到对端scp delta_psi.tar fate@对端IP:/data
        7、在对端执行docker load < delta_psi.tar，加载镜像

        8、执行命令
        docker run -p 10000:10000 -e PSI_CONFIG=config/docker.server.config.yaml -v /data/psi/python-psi/config:/app/config -v  /data/psi/python-psi/server_data.txt:/app/server_data.txt -t -i delta_psi:1.0.0 server 10.237.73.82:10000
        docker run -p 10000:10000 -e PSI_CONFIG=config/docker.client.config.yaml -v /data/python-psi/config:/app/config -v /data/python-psi/client_data.txt:/app/client_data.txt -t -i delta_psi:1.0.0 client 10.237.73.14:10000

        9、docker和宿主机之间复制数据
        docker cp  /usr/local/python3/lib/python3.8/site-packages/psi/pair/socket/pair.py cff880d0f153:/usr/local/lib/python3.8/site-packages/psi/pair/socket/pair.py
        docker cp  c9e39bf6a9db:/usr/local/lib/python3.8/site-packages/psi/pair/socket/pair.py /data
