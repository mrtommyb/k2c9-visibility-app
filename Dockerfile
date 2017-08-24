FROM heroku/miniconda

# Grab requirements.txt.
ADD ./requirements.txt /tmp/requirements.txt

RUN apt-get update \
# && apt-get -yq dist-upgrade \
 && apt-get install -yq --no-install-recommends \
    gfortran
# RUN conda install gcc

# Install dependencies
RUN pip install numpy
RUN pip install -r /tmp/requirements.txt

# Add our code
ADD ./tesstvgapp /opt/tesstvgapp/
WORKDIR /opt

# RUN conda install scikit-learn

RUN conda install -c anaconda basemap 

#CMD gunicorn --bind 0.0.0.0:$PORT wsgi
CMD ["gunicorn","tesstvgapp.app:tvgapp","--log-file -"]