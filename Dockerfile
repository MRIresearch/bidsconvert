# Use Ubuntu 16.04 LTS
FROM ubuntu:xenial-20161213

RUN mkdir -p /dicom /nifti /pyenv

RUN apt update && \
    apt install -y  build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libbz2-dev libsqlite3-dev llvm wget cmake git pigz nodejs-legacy npm python3 python3-pip python3-setuptools

WORKDIR /tmp
RUN wget https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tgz
RUN tar -xf Python-3.7.3.tgz
WORKDIR /tmp/Python-3.7.3
RUN ./configure --enable-optimizations --enable-loadable-sqlite-extensions
RUN make -j 1 && \
    make altinstall

#set up python virtual environment
RUN pip3 install --upgrade pip
RUN pip3 install virtualenv
ENV VENV=/pyenv/py373
RUN mkdir $VENV
WORKDIR $VENV
RUN virtualenv -p /usr/local/bin/python3.7 $VENV
RUN . $VENV/bin/activate
ENV PATH="$VENV/bin:$PATH"

RUN npm install -g bids-validator

#Install dcm2niix from github
RUN cd /usr/local/src && \
    git clone https://github.com/rordenlab/dcm2niix.git && \
    cd dcm2niix && \
    git checkout tags/v1.0.20181125 -b install && \
    mkdir build  && \
    cd build && \
    cmake ..  && \
    make install 

#Install dcm2bids from github
RUN cd /usr/local/src && \
    git clone https://github.com/cbedetti/Dcm2Bids.git

RUN cd /usr/local/src/Dcm2Bids && \
    git checkout -f tags/2.1.4 

RUN cd /usr/local/src/Dcm2Bids && sed -i 's/datetime.now().isoformat()/(datetime.now() - datetime(1970,1,1)).total_seconds()/g' ./dcm2bids/dcm2bids.py    
RUN cd /usr/local/src/Dcm2Bids && pip install .

RUN pip install pybids 

WORKDIR /src
COPY ./bidsconvert.py /src
ENV PATH="/src/:$PATH"
ENV TZ=America/Phoenix
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timSezone

RUN ldconfig
WORKDIR /tmp/

ARG BUILD_DATE
ARG VCS_REF
ARG VERSION
LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="bidsconvert" \
      org.label-schema.description="Bids Conversion based on Dcm2Bids" \
      org.label-schema.url="https://cbedetti.github.io/Dcm2Bids" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/cbedetti/Dcm2Bids" \
      org.label-schema.version=$VERSION \
      org.label-schema.schema-version="1.0"
