FROM python:3.6

RUN apt-get update && apt-get install -y cmake
RUN wget https://github.com/libgit2/libgit2/archive/v0.25.0.tar.gz
RUN tar xzf v0.25.0.tar.gz
RUN cd libgit2-0.25.0 \
    && cmake . \
    && make \
    && make install

RUN git clone https://github.com/btcrs/groot
COPY . /git_code
RUN pip3 install -r ./git_code/requirements.txt

run ls
RUN ldconfig
