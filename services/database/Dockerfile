FROM alpine:3.7

RUN apk add --no-cache --update python3 python3-dev gcc g++ linux-headers make musl-dev

# Install gRPC & protobufs for Python
RUN pip3 install grpcio
RUN pip3 install protobuf

ENV PYTHONPATH="/repo/build_out"
ARG DBPATH

CMD ["python3", "-u", "-B", "/repo/build_out/database/main.py", \
     "-v", "--schema", "/repo/build_out/database/rabble_schema.sql", \
     "--db_path", "$DBPATH"]
