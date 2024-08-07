FROM python:3.12

RUN apt-get update

# Install required packages for the application
RUN apt install -y libportaudio2 ffmpeg

# Install less and nano for debugging
RUN apt install -y \
    sudo \
    less \
    nano \
    expect \
    openvpn \
    unzip \
    wget

RUN mkdir -p /etc/openvpn/surfshark-config \
    && cd /etc/openvpn/surfshark-config \
    && wget https://my.surfshark.com/vpn/api/v1/server/configurations \
    && unzip configurations \
    && rm configurations

# Set the environment variables
ENV VIRTUAL_ENV=/opt/venv

# Create a virtual environment
RUN python3 -m venv $VIRTUAL_ENV

# Set the environment variables
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy the requirements file
COPY requirements.txt .

# Install the requirements
RUN pip install --no-cache-dir -r requirements.txt

# Set the working directory
WORKDIR /app

# Copy the application
COPY ./python-version /app/python-version

# Copy the environment file
COPY .env.template.txt .env

# Create the log directory
RUN mkdir -p /var/log/songrectiktok

# Run the application
CMD ["tail", "-f", "/dev/null"]
