FROM rabblenetwork/recommend_follows

# TODO(iandioch): Do this in a better way.
# Requires RUN apk add openblas-dev
# Then pip3 install numpy, scipy, pandas, scikit-surprise

RUN pip3 install requests
RUN pip3 install requests-http-signature

ENV PYTHONPATH="/repo/build_out"

CMD ["python3", "-u", "-B", "/repo/build_out/recommend_follows/main.py", "-v"]
