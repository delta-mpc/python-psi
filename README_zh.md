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
python setup.py install
```

## 使用

运行以下两个脚本

```
python psi_server.py
```



```
python psi_client.py
```

两个脚本会输出求得的交集。

脚本`psi_server.py`和`psi_client.py`中的`words`字段代表双方需要求交集的集合，
可以修改`words`字段，改变要求交集的集合。

## 注

本仓库还处于开发阶段，仅供学习交流使用，不可用于生产。

## 联系我们

![image](https://github.com/delta-mpc/python-psi/blob/master/img/qr_code.png)