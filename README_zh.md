# Delta PSI

## 概述

Delta PSI是一个隐私集合求交（private set intersection）库，
基于
[KKRT16](https://eprint.iacr.org/2016/799) 
隐私集合求交协议实现。
KKRT16基于不经意传输（OT）和布谷鸟哈希（cuckoo hashing）来实现隐私集合求交。
协议具体的原理介绍，可以参考[知乎文章](https://zhuanlan.zhihu.com/p/367477035) 。

## 安装 

克隆本仓库，运行命令

```
pip install .
```

## 命令

初始化配置文件：

```
psi_run init
```

运行此命令后，可以看到新建的配置文件`config/config.yaml`

启动PSI服务端：

```
PSI_CONFIG=<CONFIG> psi_run server <address>
```

其中，`<CONFIG>`为配置文件位置，`<address>`为PSI客户端的地址。

启动PSI客户端：

```
PSI_CONFIG=<CONFIG> psi_run client <address>
```

其中，`<CONFIG>`为配置文件位置，`<address>`为PSI服务端的地址。


## DEMO

分别运行以下两条命令：

```
PSI_CONFIG=config/server.config.yaml psi_run server 127.0.0.1:2345
```

```
PSI_CONFIG=config/client.config.yaml psi_run client 127.0.0.1:1234
```

以启动demo

其中，PSI服务端的配置文件位于`config/server.config.yaml`，输入数据位于`server_data.txt`，输出结果位于`server_result.txt`；
PSI客户端的配置文件位于`config/client.confg.yaml`，输入数据位于`client_data.txt`，输出结果位于`client_result.txt`。

## 注

本仓库还处于开发阶段，仅供学习交流使用，不可用于生产。

## 联系我们

![image](https://github.com/delta-mpc/python-psi/blob/master/img/qr_code.png)