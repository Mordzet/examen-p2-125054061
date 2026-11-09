FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV HADOOP_VERSION=3.3.6
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV HADOOP_HOME=/opt/hadoop
ENV HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
ENV PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

# 1. Instalar Java (OpenJDK 17), Python 3, OpenSSH Server y utilidades
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    python3 \
    python3-psycopg2 \
    openssh-server \
    openssh-client \
    curl \
    ca-certificates \
    procps \
    time \
    && rm -rf /var/lib/apt/lists/*

# 2. Instalar Apache Hadoop 3.3.6 en modo standalone (usa cache local si existe o descarga de Apache)
COPY Dockerfile *hadoop-3.3.6.tar.gz /tmp/
RUN if [ ! -f /tmp/hadoop-3.3.6.tar.gz ]; then \
        curl -fSL "https://downloads.apache.org/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz" -o /tmp/hadoop-3.3.6.tar.gz \
        || curl -fSL "https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz" -o /tmp/hadoop-3.3.6.tar.gz; \
    fi \
    && mkdir -p ${HADOOP_HOME} \
    && tar -xzf /tmp/hadoop-3.3.6.tar.gz -C ${HADOOP_HOME} --strip-components=1 \
    && rm -f /tmp/hadoop-3.3.6.tar.gz /tmp/Dockerfile \
    && rm -rf ${HADOOP_HOME}/share/doc

# 3. Configurar variables de entorno en Hadoop y para sesiones SSH
RUN echo "export JAVA_HOME=${JAVA_HOME}" >> ${HADOOP_HOME}/etc/hadoop/hadoop-env.sh \
    && echo "export JAVA_HOME=${JAVA_HOME}" >> /etc/profile.d/hadoop.sh \
    && echo "export HADOOP_HOME=${HADOOP_HOME}" >> /etc/profile.d/hadoop.sh \
    && echo "export HADOOP_CONF_DIR=${HADOOP_CONF_DIR}" >> /etc/profile.d/hadoop.sh \
    && echo "export PATH=\$PATH:${HADOOP_HOME}/bin:${HADOOP_HOME}/sbin" >> /etc/profile.d/hadoop.sh \
    && echo "export JAVA_HOME=${JAVA_HOME}" >> /root/.bashrc \
    && echo "export HADOOP_HOME=${HADOOP_HOME}" >> /root/.bashrc \
    && echo "export HADOOP_CONF_DIR=${HADOOP_CONF_DIR}" >> /root/.bashrc \
    && echo "export PATH=\$PATH:${HADOOP_HOME}/bin:${HADOOP_HOME}/sbin" >> /root/.bashrc

# 4. Configurar OpenSSH Server y acceso sin contraseña por llaves (root y usuario hadoop)
RUN mkdir -p /run/sshd /root/.ssh /ssh_shared \
    && ssh-keygen -t rsa -b 4096 -P "" -f /root/.ssh/id_rsa \
    && cp /root/.ssh/id_rsa.pub /root/.ssh/authorized_keys \
    && chmod 700 /root/.ssh \
    && chmod 600 /root/.ssh/id_rsa /root/.ssh/authorized_keys \
    && useradd -m -s /bin/bash hadoop \
    && mkdir -p /home/hadoop/.ssh \
    && cp /root/.ssh/id_rsa /home/hadoop/.ssh/id_rsa \
    && cp /root/.ssh/id_rsa.pub /home/hadoop/.ssh/id_rsa.pub \
    && cp /root/.ssh/authorized_keys /home/hadoop/.ssh/authorized_keys \
    && echo "export JAVA_HOME=${JAVA_HOME}" >> /home/hadoop/.bashrc \
    && echo "export HADOOP_HOME=${HADOOP_HOME}" >> /home/hadoop/.bashrc \
    && echo "export HADOOP_CONF_DIR=${HADOOP_CONF_DIR}" >> /home/hadoop/.bashrc \
    && echo "export PATH=\$PATH:${HADOOP_HOME}/bin:${HADOOP_HOME}/sbin" >> /home/hadoop/.bashrc \
    && chmod 700 /home/hadoop/.ssh \
    && chmod 600 /home/hadoop/.ssh/id_rsa /home/hadoop/.ssh/authorized_keys \
    && chown -R hadoop:hadoop /home/hadoop/.ssh /home/hadoop/.bashrc \
    && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin without-password/' /etc/ssh/sshd_config \
    && sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config \
    && printf "Host *\n    StrictHostKeyChecking no\n    UserKnownHostsFile /dev/null\n    LogLevel ERROR\n" >> /etc/ssh/ssh_config

WORKDIR /mapreduce

EXPOSE 22

# Al iniciar, comparte la llave en /ssh_shared para comunicación entre contenedores y arranca sshd
CMD ["sh", "-c", "cp /root/.ssh/id_rsa /root/.ssh/id_rsa.pub /ssh_shared/ && chmod 600 /ssh_shared/id_rsa && chmod 644 /ssh_shared/id_rsa.pub && /usr/sbin/sshd -D"]
