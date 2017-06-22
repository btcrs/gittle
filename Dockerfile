FROM python:3.6

# Cmake is a dependency for building libgit2
RUN apt-get update && apt-get install -y cmake

# Downloading and building libgit2
RUN wget https://github.com/libgit2/libgit2/archive/v0.25.0.tar.gz
RUN tar xzf v0.25.0.tar.gz
RUN cd libgit2-0.25.0 \
    && cmake . \
    && make \
    && make install

# The python wrapper for libgit2
RUN pip install pygit2

# flask
RUN pip install flask

# Required for updating the libs
RUN ldconfig



