# Checkout Repo

```bash
git clone https://github.com/gleanerio/archetype.git
cd archetype
git checkout master
```

# Create directories

```bash
cd persona/aggregator/serverArch
mkdir ./gleaner
mkdir ./gleaner/datavol
mkdir ./gleaner/datavol/s3
mkdir ./gleaner/datavol/graph
```

# Start services

```bash
sudo docker-compose up -d
```

While starting the services some directories are created in the gleaner directory. If there are permissions issues you will need to chmod 777 the folders to allow docker access to them. This is likely only an issue if you are working on a vm.

# Harvest into minio bucket

```bash
cd ../harvesting/rundir
../scripts/cliGleaner.sh -init
../scripts/cliGleaner.sh -a docker --cfg 09022023_iow.yml --source cioos --rude
```

Browse to http://local.dev:9000 and login with minio root username and password to confirm harvest worked. `minioadmin` for both inless you changed it in the docker-compose.yml and 09022023_iow.yml file

# Create graphdb repository

Create respository in graphdb. Here I am calling it `Store`. To change the repo name you can modify it in `repo-config.ttl`

```bash
curl -X POST\
    http://local.dev:7200/rest/repositories\
    -H 'Content-Type: multipart/form-data'\
    -F "config=@repo-config.ttl"
```

Browse to `http://local.dev:7200` to confirm the repository was created.

# Load triplestore with graph data from json-ld in minio bucket

```bash
cd ../../serverArch
./minio2graphdb_jsonld.sh oih/gleaner.oih/prov/cioos http://local.dev:7200/repositories/Store/statements
./minio2graphdb_jsonld.sh oih/gleaner.oih/summoned/cioos http://local.dev:7200/repositories/Store/statements
./minio2graphdb_nq.sh oih/gleaner.oih/orgs http://local.dev:7200/repositories/Store/statements
```

At `http://local.dev:7200` you should now see many statments in a repository called Store.
