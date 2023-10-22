FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

# Switch to root user to perform operations requiring root privileges
USER root

# Step 2: Install micromamba
RUN apt-get update && \
    apt-get install -y wget bzip2 && \
    wget -qO- https://micromamba.snakepit.net/api/micromamba/linux-64/latest | tar -xvj -C /usr/local/ && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Step 3: Copy the conda-environment.yaml and app.py files into the container
COPY conda-environment.yaml /root/conda-environment.yaml
COPY app.py /root/app.py

# Step 4: Use micromamba to create a Python environment based on the conda-environment.yaml
RUN /usr/local/bin/micromamba create -f /root/conda-environment.yaml -p /root/micromamba

# # Step 5: Install and configure an SSH server
# RUN apt-get update && \
#     apt-get install -y openssh-server && \
#     echo "root:Docker!" | chpasswd && \
#     sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
#     mkdir /var/run/sshd

# Step 6: Copy the app.service file into the container (you would need to add this file to your context)
# COPY app.service /etc/systemd/system/app.service

# Step 7: Expose the necessary ports in the Dockerfile
EXPOSE 15781 15788 22

# Step 8: Set the entrypoint script
COPY entrypoint.sh /root/entrypoint.sh
CMD ["/bin/bash", "/root/entrypoint.sh"]
