FROM alpine:3.7

RUN apk add --no-cache --update python3 python3-dev gcc g++ linux-headers make musl-dev openblas-dev

# Install gRPC & protobufs for Python
RUN pip3 install grpcio
RUN pip3 install protobuf
RUN pip3 install numpy
RUN pip3 install scipy
RUN python3 -m pip install scikit-surprise

ENV PYTHONPATH="/repo/build_out"

CMD ["python3", "-u", "-B", "/repo/build_out/recommend_follows/main.py", "-v"]
