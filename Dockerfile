FROM python:3.8.10 as env

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
ADD requirements.txt /opt/xapp-mho/
RUN pip install -r /opt/xapp-mho/requirements.txt

ADD onos-e2-sm/python /opt/onos-e2-sm
RUN pip install /opt/onos-e2-sm --no-cache-dir

FROM env

ADD . /opt/xapp-mho/
