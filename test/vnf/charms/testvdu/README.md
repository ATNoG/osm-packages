# sshproxy

## Description

SSHProxy Charm example for Open Source MANO.

The purpose of this charm is to operate a VNF via SSH. For this, the charm should know the hostname of the VNF (ip address), and the username. The charm will be in a blocked state until it has the hostname, username, and the credentials for SSH-ing to the VNF. Both hostname and username are set via config, with `ssh-hostname` and `ssh-username` respectively.

There are two ways of specifying the credentials: password, keys. (See next section)


## Usage

This charm works for both LXD and K8s. By default, it will work on LXD. To make it work in K8s, just change the following in the `metadata.yaml`

```yaml
series:
# - focal
# - bionic
# - xenial
 - kubernetes
 deployment:
    mode: operator
```

### Prepare the environment:

- LXD:

```bash
sudo snap install juju --classic
juju bootstrap lxd
juju add-model test
```

- K8s:

```bash
sudo snap install juju --classic
sudo snap install microk8s --classic
sudo microk8s.status --wait-ready
sudo microk8s.enable storage dns
juju bootstrap microk8s
juju add-model test
```


```bash
mkdir -p charms/samplecharm/
cd charms/samplecharm/
mkdir hooks lib mod src
touch src/charm.py
touch actions.yaml metadata.yaml config.yaml
chmod +x src/charm.py
ln -s ../src/charm.py hooks/upgrade-charm
ln -s ../src/charm.py hooks/install
ln -s ../src/charm.py hooks/start
git clone https://github.com/canonical/operator mod/operator
git clone https://github.com/charmed-osm/charms.osm mod/charms.osm
ln -s ../mod/operator/ops lib/ops
ln -s ../mod/charms.osm/charms lib/charms
```


### Deploying charm:

```bash
charmcraft build
juju deploy ./sshproxy.charm
```

### Configuring the charm:

First of all, set the username and hostname of the VNF:
```bash
juju config sshproxy ssh-hostname=<hostname> \
                     ssh-username=<username>
```

### Credentials

There are two ways to set up the credentials for the charm to be able to SSH the VNF.

With password:

```bash
juju config sshproxy ssh-password=<password>
```

With public keys:

1. First get the public key from the charm

```bash
$ juju run-action sshproxy/0 get-ssh-public-key --wait
unit-sshproxy-0:
  UnitId: sshproxy/0
  id: "12"
  results:
    pubkey: |
      ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC0IgSXMsu/5tY9QjsQfiAqcs6MBMO/7BDJB1ohbJFfvFrPiGg3+5FohKOsgu3SPiZbBhTITmI1YdaiZK7Dye2tHUfQKXhPFVFFVRtyWG6U/QJqEn+6OvAhjladcBlah4cb//r8V2Lvk/PshBJPzgvYSNJOhMhpfAMc7SMMpS8VxGBDIuTE0JFlHcRALJy3YBg70DPea2xrLsxqfA2pTA33KcjK2GyLgfOcZavmkqudEA/WaFb0xCY16TB/hDQBSwZm3l2kJ2aHyAWyWMmLNGL0TT14HUQKR1a8NS/kAnKY/yQf04dKoicmCvl4B3ndIYFT5Pq9b07mVfZvEH5Blle/x48iUF6JHWH2383SXwZfGy3XcX+lRx3u+IIkzS/Pmgt175JVdpu8bktk1c3Ekc0aL9v1gJ8rmZo+C6cilBoaziPfbqIatGPeGxnTDdw0JSfpxUGIQF4H98VOdWf3cHGC1hJZubZt0MGYeK4bk7GfsVPMlGaBWDyTaBQ5d9dHGxJpJX5OMBCDD4MfBYvg9IlgsVr1vDbpB4OFoAmQqFgnUWxRg2w0Iv3HBeMCvvOMM7DBOjwgjgbwa693Oyt/Rxd3GOwvy6vRQkFTgVS6f69SyIMCj9aIl1zxkIcOsfM5aU6vgio1BVWt9Xrj1TA3dTYJ7fkC5LJetqJ1knO67u67ww== root@juju-73fac6-2
  status: completed
  timing:
    completed: 2020-11-18 15:42:03 +0000 UTC
    enqueued: 2020-11-18 15:42:00 +0000 UTC
    started: 2020-11-18 15:42:03 +0000 UTC
```
2. Inject that key in `~/.ssh/authorized_keys` at the VNF
3. Verify the ssh credentials

```bash
$ juju run-action sshproxy/0 verify-ssh-credentials --wait
unit-sshproxy-0:
  UnitId: sshproxy/0
  id: "14"
  results:
    verified: "True"
  status: completed
  timing:
    completed: 2020-11-18 15:39:30 +0000 UTC
    enqueued: 2020-11-18 15:39:29 +0000 UTC
    started: 2020-11-18 15:39:29 +0000 UTC
```


## Developing

Create and activate a virtualenv with the development requirements:

    virtualenv -p python3 venv
    source venv/bin/activate
    pip install -r requirements-dev.txt

## Testing

The Python operator framework includes a very nice harness for testing
operator behaviour without full deployment. Just `run_tests`:

    ./run_tests
