FROM alpine:3.7

RUN apk add --no-cache --update python3 python3-dev gcc g++ linux-headers make musl-dev libffi-dev openssl-dev

# Install gRPC & protobufs for Python
RUN pip3 install grpcio
RUN pip3 install protobuf
RUN pip3 install requests
RUN pip3 install requests-http-signature

ENV PYTHONPATH="/repo/build_out"

CMD ["python3", "-u", "-B", "/repo/build_out/follows/main.py", "-v"]
